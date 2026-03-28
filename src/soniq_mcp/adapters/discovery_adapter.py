"""SoCo discovery adapter for SoniqMCP.

This is the ONLY module that imports from ``soco``. All other layers
(services, tools) receive domain objects and never touch SoCo directly.
"""

from __future__ import annotations

import logging

from soniq_mcp.domain.exceptions import SonosDiscoveryError
from soniq_mcp.domain.models import Room, Speaker

log = logging.getLogger(__name__)


class DiscoveryAdapter:
    """Wraps ``soco.discover()`` and maps results to domain ``Room`` objects.

    Keeping SoCo isolated here means services and tools can be tested
    without any real Sonos hardware by substituting a fake adapter.
    """

    def discover_rooms(self, timeout: float = 5.0) -> list[Room]:
        """Discover all Sonos zones on the local network.

        Args:
            timeout: Seconds to wait for SSDP responses (default 5.0).

        Returns:
            List of ``Room`` domain objects, empty if none found.

        Raises:
            SonosDiscoveryError: If the SoCo library raises an unexpected
                exception during discovery.
        """
        try:
            import soco  # local import keeps module loadable without hardware

            zones = soco.discover(timeout=timeout)
            if not zones:
                log.debug("soco.discover() returned no zones (timeout=%.1fs)", timeout)
                return []

            rooms = [self._zone_to_room(z) for z in zones]
            log.debug("Discovered %d zone(s)", len(rooms))
            return rooms

        except SonosDiscoveryError:
            raise
        except Exception as exc:
            raise SonosDiscoveryError(
                f"Sonos discovery failed: {exc}. "
                "Check that the server is on the same network as your Sonos speakers."
            ) from exc

    def discover_speakers(self, timeout: float = 5.0) -> list[Speaker]:
        """Discover speaker/device details for the household topology."""
        try:
            import soco  # local import keeps module loadable without hardware

            zones = soco.discover(timeout=timeout)
            if not zones:
                log.debug("soco.discover() returned no speakers (timeout=%.1fs)", timeout)
                return []

            root_zone = next(iter(zones))
            all_zones = getattr(root_zone, "all_zones", None)
            speaker_zones = list(all_zones) if all_zones else list(zones)

            speakers = [self._zone_to_speaker(zone) for zone in speaker_zones]
            deduped: dict[str, Speaker] = {speaker.uid: speaker for speaker in speakers}
            return sorted(
                deduped.values(),
                key=lambda speaker: (
                    speaker.room_name.lower(),
                    speaker.name.lower(),
                    speaker.uid.lower(),
                ),
            )

        except SonosDiscoveryError:
            raise
        except Exception as exc:
            raise SonosDiscoveryError(
                f"Sonos discovery failed: {exc}. "
                "Check that the server is on the same network as your Sonos speakers."
            ) from exc

    @staticmethod
    def _zone_to_room(zone: object) -> Room:
        """Convert a SoCo zone object to a domain Room.

        Uses attribute access only so we can substitute fakes in tests.
        """
        try:
            coordinator_uid: str | None = None
            name = DiscoveryAdapter._required_zone_attr(zone, "player_name")
            uid = DiscoveryAdapter._required_zone_attr(zone, "uid")
            ip_address = DiscoveryAdapter._required_zone_attr(zone, "ip_address")

            group = getattr(zone, "group", None)
            if group is not None:
                coordinator = getattr(group, "coordinator", None)
                if coordinator is not None:
                    coord_uid = getattr(coordinator, "uid", None)
                    # Only set if this zone is NOT the coordinator itself
                    if isinstance(coord_uid, str):
                        coord_uid = coord_uid.strip()
                    if coord_uid and coord_uid != uid:
                        coordinator_uid = coord_uid

            return Room(
                name=name,
                uid=uid,
                ip_address=ip_address,
                is_coordinator=bool(getattr(zone, "is_coordinator", False)),
                group_coordinator_uid=coordinator_uid,
            )
        except Exception as exc:
            raise SonosDiscoveryError(
                f"Failed to read zone properties: {exc}"
            ) from exc

    @staticmethod
    def _zone_to_speaker(zone: object) -> Speaker:
        """Convert a SoCo zone object to a speaker/device record."""
        try:
            name = DiscoveryAdapter._required_zone_attr(zone, "player_name")
            uid = DiscoveryAdapter._required_zone_attr(zone, "uid")
            ip_address = DiscoveryAdapter._required_zone_attr(zone, "ip_address")

            speaker_info: dict[str, object] = {}
            get_speaker_info = getattr(zone, "get_speaker_info", None)
            if callable(get_speaker_info):
                try:
                    maybe_info = get_speaker_info()
                    if isinstance(maybe_info, dict):
                        speaker_info = maybe_info
                except Exception:
                    speaker_info = {}

            room_name = speaker_info.get("zone_name")
            if not isinstance(room_name, str) or not room_name.strip():
                room_name = name

            model_name = speaker_info.get("model_name")
            if not isinstance(model_name, str) or not model_name.strip():
                model_name = None

            is_visible = getattr(zone, "is_visible", True)
            room_uid = uid if is_visible else None

            return Speaker(
                name=name,
                uid=uid,
                ip_address=ip_address,
                room_name=room_name,
                room_uid=room_uid,
                model_name=model_name,
                is_visible=bool(is_visible),
            )
        except Exception as exc:
            raise SonosDiscoveryError(
                f"Failed to read speaker properties: {exc}"
            ) from exc

    @staticmethod
    def _required_zone_attr(zone: object, attr_name: str) -> str:
        value = getattr(zone, attr_name, None)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"zone missing required {attr_name}")
        return value.strip()
