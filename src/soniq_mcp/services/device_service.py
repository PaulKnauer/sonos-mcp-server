"""Device service for speaker-level queries such as battery state."""

from __future__ import annotations

from soniq_mcp.domain.models import BatteryInfo


class DeviceService:
    """Orchestrates speaker-level device queries.

    Args:
        room_service: A ``RoomService`` instance for room/IP resolution.
        adapter: A ``SoCoAdapter`` instance for SoCo operations.
    """

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def get_battery_info(self, room_name: str) -> BatteryInfo:
        """Return battery state for the named room.

        Rooms without a portable speaker return ``supported=False`` rather
        than raising.

        Raises:
            RoomNotFoundError: If the room is not found.
            DeviceError: If the battery query fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._room_service.get_room(room_name)
        return self._adapter.get_battery_info(room.ip_address, room.name)
