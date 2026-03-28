"""Group service for SoniqMCP.

Orchestrates room grouping operations: topology inspection, join, unjoin,
and party mode. Delegates Sonos interaction to SoCoAdapter and room
resolution to RoomService.
"""

from __future__ import annotations

from soniq_mcp.domain.exceptions import GroupError
from soniq_mcp.domain.models import Room


class GroupService:
    """Service for Sonos room grouping operations."""

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def get_group_topology(self) -> list[Room]:
        """Return all rooms with group membership information.

        Group topology is derived from Room.is_coordinator and
        Room.group_coordinator_uid at the schema layer.
        """
        return self._room_service.list_rooms()

    def join_group(self, room_name: str, coordinator_name: str) -> None:
        """Join room_name to the group coordinated by coordinator_name."""
        room = self._room_service.get_room(room_name)
        coordinator = self._room_service.get_room(coordinator_name)
        self._adapter.join_group(room.ip_address, coordinator.ip_address)

    def unjoin_room(self, room_name: str) -> None:
        """Remove room_name from its current group."""
        room = self._room_service.get_room(room_name)
        self._adapter.unjoin_room(room.ip_address)

    def party_mode(self) -> None:
        """Join all rooms into a single whole-home group."""
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise GroupError("No Sonos rooms found — cannot execute party mode")
        self._adapter.party_mode(rooms[0].ip_address)
