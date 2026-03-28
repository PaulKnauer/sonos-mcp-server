"""Queue orchestration service for SoniqMCP."""

from __future__ import annotations

import logging

from soniq_mcp.domain.models import QueueItem

log = logging.getLogger(__name__)


class QueueService:
    """Orchestration boundary for room-targeted Sonos queue operations."""

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def get_queue(self, room_name: str) -> list[QueueItem]:
        room = self._room_service.get_room(room_name)
        return self._adapter.get_queue(room.ip_address)

    def add_to_queue(self, room_name: str, uri: str) -> int:
        room = self._room_service.get_room(room_name)
        return self._adapter.add_to_queue(room.ip_address, uri)

    def remove_from_queue(self, room_name: str, position: int) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.remove_from_queue(room.ip_address, position)

    def clear_queue(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.clear_queue(room.ip_address)

    def play_from_queue(self, room_name: str, position: int) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.play_from_queue(room.ip_address, position)
