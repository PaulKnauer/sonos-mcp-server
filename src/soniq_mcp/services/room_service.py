"""Room service for SoniqMCP.

Owns all room-related business logic. Receives a DiscoveryAdapter via
constructor injection so it can be tested without real Sonos hardware.
"""

from __future__ import annotations

import logging

from soniq_mcp.domain.exceptions import RoomNotFoundError
from soniq_mcp.domain.models import Room, Speaker, SystemTopology

log = logging.getLogger(__name__)


class RoomService:
    """Provides room discovery and lookup operations.

    Args:
        adapter: A DiscoveryAdapter (or compatible fake) that returns
            ``Room`` domain objects.
    """

    def __init__(self, adapter: object) -> None:
        self._adapter = adapter

    def list_rooms(self, timeout: float = 5.0) -> list[Room]:
        """Return all discoverable Sonos rooms, sorted by name.

        Args:
            timeout: Discovery timeout in seconds (passed to adapter).

        Returns:
            List of ``Room`` objects, sorted by ``name``. Empty if none found.

        Raises:
            SonosDiscoveryError: If discovery fails due to a network error.
        """
        rooms: list[Room] = self._adapter.discover_rooms(timeout=timeout)
        return sorted(rooms, key=lambda r: r.name.lower())

    def get_topology(self, timeout: float = 5.0) -> SystemTopology:
        """Return a snapshot of the full household topology.

        Args:
            timeout: Discovery timeout in seconds.

        Returns:
            ``SystemTopology`` built from all discovered rooms.

        Raises:
            SonosDiscoveryError: If discovery fails due to a network error.
        """
        rooms = self.list_rooms(timeout=timeout)
        speakers: list[Speaker] = self._adapter.discover_speakers(timeout=timeout)
        topology = SystemTopology.from_rooms(rooms, speakers=speakers)
        log.debug(
            "Topology: %d room(s), %d speaker(s), %d coordinator(s)",
            topology.total_count,
            topology.speaker_count,
            topology.coordinator_count,
        )
        return topology

    def get_room(self, name: str, timeout: float = 5.0) -> Room:
        """Find a room by name (case-insensitive).

        Args:
            name: The room name to look up.
            timeout: Discovery timeout in seconds.

        Returns:
            The matching ``Room``.

        Raises:
            RoomNotFoundError: If no room with the given name exists.
            SonosDiscoveryError: If discovery fails due to a network error.
        """
        rooms = self.list_rooms(timeout=timeout)
        normalised = name.strip().lower()
        for room in rooms:
            if room.name.lower() == normalised:
                return room
        raise RoomNotFoundError(name)

    def get_speakers_for_room(self, name: str, timeout: float = 5.0) -> list[Speaker]:
        """Return all discovered speaker/device records associated with a room."""
        room = self.get_room(name, timeout=timeout)
        speakers: list[Speaker] = self._adapter.discover_speakers(timeout=timeout)
        room_name = room.name.lower()
        room_uid = room.uid
        return [
            speaker
            for speaker in speakers
            if (speaker.room_uid == room_uid) or (speaker.room_name.lower() == room_name)
        ]
