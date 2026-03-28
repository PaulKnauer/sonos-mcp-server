"""Volume service facade over the shared Sonos service."""

from __future__ import annotations

from soniq_mcp.domain.models import VolumeState
from soniq_mcp.services.sonos_service import SonosService


class VolumeService:
    """Compatibility volume facade over ``SonosService``."""

    def __init__(
        self,
        room_service: object | None = None,
        adapter: object | None = None,
        config: object | None = None,
        sonos_service: object | None = None,
    ) -> None:
        if sonos_service is not None:
            self._sonos_service = sonos_service
            return
        if room_service is not None and adapter is not None and config is not None:
            self._sonos_service = SonosService(room_service, adapter, config)
            return
        raise TypeError(
            "VolumeService requires sonos_service=... or room_service+adapter+config"
        )

    def get_volume_state(self, room_name: str) -> VolumeState:
        """Return the current volume and mute state for the named room.

        Args:
            room_name: Human-readable Sonos room name.

        Returns:
            ``VolumeState`` with current volume and mute flag.

        Raises:
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If the SoCo operation fails.
        """
        return self._sonos_service.get_volume_state(room_name)

    def set_volume(self, room_name: str, volume: int) -> None:
        """Set the volume for the named room.

        Args:
            room_name: Human-readable Sonos room name.
            volume: Target volume level (0-100, capped by max_volume_pct).

        Raises:
            VolumeCapExceeded: If ``volume`` exceeds ``config.max_volume_pct``.
            ValueError: If ``volume`` is outside 0-100.
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If the SoCo operation fails.
        """
        self._sonos_service.set_volume(room_name, volume)

    def adjust_volume(self, room_name: str, delta: int) -> VolumeState:
        """Adjust the volume by a relative amount and return the new state.

        The target volume is clamped to 0-100 before the cap check. A delta
        that would go below 0 silently floors to 0. A delta that would push
        above ``max_volume_pct`` raises ``VolumeCapExceeded``.

        Args:
            room_name: Human-readable Sonos room name.
            delta: Amount to adjust (positive = louder, negative = quieter).

        Returns:
            Updated ``VolumeState`` after adjustment.

        Raises:
            VolumeCapExceeded: If the resulting volume exceeds ``max_volume_pct``.
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If a SoCo operation fails.
        """
        return self._sonos_service.adjust_volume(room_name, delta)

    def mute(self, room_name: str) -> None:
        """Mute the named room.

        Args:
            room_name: Human-readable Sonos room name.

        Raises:
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If the SoCo operation fails.
        """
        self._sonos_service.mute(room_name)

    def unmute(self, room_name: str) -> None:
        """Unmute the named room.

        Args:
            room_name: Human-readable Sonos room name.

        Raises:
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If the SoCo operation fails.
        """
        self._sonos_service.unmute(room_name)
