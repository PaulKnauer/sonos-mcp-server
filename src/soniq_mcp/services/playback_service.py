"""Playback service for SoniqMCP.

Orchestrates room lookup and playback operations. Receives both
``RoomService`` and ``PlaybackAdapter`` via constructor injection so
it can be tested without real Sonos hardware.
"""

from __future__ import annotations

import logging

from soniq_mcp.domain.models import PlaybackState, TrackInfo

log = logging.getLogger(__name__)


class PlaybackService:
    """Provides playback control and state query operations for a named room.

    Args:
        room_service: A ``RoomService`` (or compatible fake) for room lookup.
        adapter: A ``PlaybackAdapter`` (or compatible fake) for SoCo calls.
    """

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def play(self, room_name: str) -> None:
        """Start or resume playback in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        log.debug("play: room=%r ip=%s", room_name, room.ip_address)
        self._adapter.play(room.ip_address)

    def pause(self, room_name: str) -> None:
        """Pause playback in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        log.debug("pause: room=%r ip=%s", room_name, room.ip_address)
        self._adapter.pause(room.ip_address)

    def stop(self, room_name: str) -> None:
        """Stop playback in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        log.debug("stop: room=%r ip=%s", room_name, room.ip_address)
        self._adapter.stop(room.ip_address)

    def next_track(self, room_name: str) -> None:
        """Skip to the next track in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails (e.g. end of queue).
        """
        room = self._room_service.get_room(room_name)
        log.debug("next_track: room=%r ip=%s", room_name, room.ip_address)
        self._adapter.next_track(room.ip_address)

    def previous_track(self, room_name: str) -> None:
        """Return to the previous track in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        log.debug("previous_track: room=%r ip=%s", room_name, room.ip_address)
        self._adapter.previous_track(room.ip_address)

    def get_playback_state(self, room_name: str) -> PlaybackState:
        """Return the current transport state for the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        return self._adapter.get_playback_state(room.ip_address, room.name)

    def get_track_info(self, room_name: str) -> TrackInfo:
        """Return current track details for the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._room_service.get_room(room_name)
        return self._adapter.get_track_info(room.ip_address)
