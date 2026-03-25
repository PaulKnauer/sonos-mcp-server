"""SoCo discovery adapter for SoniqMCP.

This is the ONLY module that imports from ``soco``. All other layers
(services, tools) receive domain objects and never touch SoCo directly.
"""

from __future__ import annotations

import logging

from soniq_mcp.domain.exceptions import SonosDiscoveryError
from soniq_mcp.domain.models import Room

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

    @staticmethod
    def _zone_to_room(zone: object) -> Room:
        """Convert a SoCo zone object to a domain Room.

        Uses attribute access only so we can substitute fakes in tests.
        """
        try:
            coordinator_uid: str | None = None
            group = getattr(zone, "group", None)
            if group is not None:
                coordinator = getattr(group, "coordinator", None)
                if coordinator is not None:
                    coord_uid = getattr(coordinator, "uid", None)
                    zone_uid = getattr(zone, "uid", None)
                    # Only set if this zone is NOT the coordinator itself
                    if coord_uid and coord_uid != zone_uid:
                        coordinator_uid = coord_uid

            return Room(
                name=str(getattr(zone, "player_name", "")),
                uid=str(getattr(zone, "uid", "")),
                ip_address=str(getattr(zone, "ip_address", "")),
                is_coordinator=bool(getattr(zone, "is_coordinator", False)),
                group_coordinator_uid=coordinator_uid,
            )
        except Exception as exc:
            raise SonosDiscoveryError(
                f"Failed to read zone properties: {exc}"
            ) from exc
