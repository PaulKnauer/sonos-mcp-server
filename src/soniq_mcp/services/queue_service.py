"""Queue orchestration service for SoniqMCP."""

from __future__ import annotations

import logging

from soniq_mcp.domain.exceptions import QueueValidationError
from soniq_mcp.domain.models import QueueItem

log = logging.getLogger(__name__)

# Upper bound on URIs accepted by add_multiple_to_queue in one call.
MAX_BATCH_URIS = 100


class QueueService:
    """Orchestration boundary for room-targeted Sonos queue operations."""

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def get_queue(self, room_name: str) -> list[QueueItem]:
        room = self._room_service.get_room(room_name)
        return self._adapter.get_queue(room.ip_address)

    def add_to_queue(self, room_name: str, uri: str, as_next: bool = False) -> int:
        room = self._room_service.get_room(room_name)
        return self._adapter.add_to_queue(room.ip_address, uri, as_next=as_next)

    def add_multiple_to_queue(self, room_name: str, uris: list[str]) -> int:
        """Append several URIs to the queue and return how many were added.

        Raises:
            QueueValidationError: If the list is empty, too long, or has a blank URI.
            RoomNotFoundError: If the room is not found.
            QueueError: If the adapter call fails.
        """
        validated = self._validate_uris(uris)
        room = self._room_service.get_room(room_name)
        return self._adapter.add_multiple_to_queue(room.ip_address, validated)

    def remove_from_queue(self, room_name: str, position: int) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.remove_from_queue(room.ip_address, position)

    def clear_queue(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.clear_queue(room.ip_address)

    def play_from_queue(self, room_name: str, position: int) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.play_from_queue(room.ip_address, position)

    @staticmethod
    def _validate_uris(uris: object) -> list[str]:
        if not isinstance(uris, list) or not uris:
            raise QueueValidationError("Invalid uris. Expected a non-empty list of URI strings.")
        if len(uris) > MAX_BATCH_URIS:
            raise QueueValidationError(
                f"Too many uris ({len(uris)}). Add at most {MAX_BATCH_URIS} per call."
            )
        validated = []
        for uri in uris:
            if not isinstance(uri, str) or not uri.strip():
                raise QueueValidationError("Invalid uris. Every entry must be a non-empty string.")
            validated.append(uri.strip())
        return validated
