"""Volume service for SoniqMCP.

Owns all volume and mute business logic. Delegates hardware operations
to ``VolumeAdapter`` and room lookup to ``RoomService``. Safety rules
(volume cap) are enforced by calling ``domain.safety.check_volume``.
"""

from __future__ import annotations

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.models import VolumeState
from soniq_mcp.domain.safety import check_volume


class VolumeService:
    """Provides volume and mute control for a named Sonos room.

    Args:
        room_service: A ``RoomService`` (or compatible fake) for IP lookup.
        adapter: A ``VolumeAdapter`` (or compatible fake) for SoCo operations.
        config: Active server configuration (used for volume cap enforcement).
    """

    def __init__(self, room_service: object, adapter: object, config: SoniqConfig) -> None:
        self._room_service = room_service
        self._adapter = adapter
        self._config = config

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
        room = self._room_service.get_room(room_name)
        volume = self._adapter.get_volume(room.ip_address)
        is_muted = self._adapter.get_mute(room.ip_address)
        return VolumeState(room_name=room.name, volume=volume, is_muted=is_muted)

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
        check_volume(volume, self._config)
        room = self._room_service.get_room(room_name)
        self._adapter.set_volume(room.ip_address, volume)

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
        room = self._room_service.get_room(room_name)
        current = self._adapter.get_volume(room.ip_address)
        target = max(0, min(100, current + delta))
        check_volume(target, self._config)
        self._adapter.set_volume(room.ip_address, target)
        is_muted = self._adapter.get_mute(room.ip_address)
        return VolumeState(room_name=room.name, volume=target, is_muted=is_muted)

    def mute(self, room_name: str) -> None:
        """Mute the named room.

        Args:
            room_name: Human-readable Sonos room name.

        Raises:
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        self._adapter.set_mute(room.ip_address, True)

    def unmute(self, room_name: str) -> None:
        """Unmute the named room.

        Args:
            room_name: Human-readable Sonos room name.

        Raises:
            RoomNotFoundError: If room is not in the household.
            SonosDiscoveryError: If network discovery fails.
            VolumeError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        self._adapter.set_mute(room.ip_address, False)
