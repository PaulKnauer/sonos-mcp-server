"""Shared Sonos orchestration service for core playback and volume features."""

from __future__ import annotations

import logging

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import PlaybackError, PlaybackValidationError
from soniq_mcp.domain.models import PlaybackState, Room, SleepTimerState, TrackInfo, VolumeState
from soniq_mcp.domain.safety import check_volume

log = logging.getLogger(__name__)


class SonosService:
    """Shared orchestration boundary for room-targeted Sonos operations."""

    def __init__(self, room_service: object, adapter: object, config: SoniqConfig) -> None:
        self._room_service = room_service
        self._adapter = adapter
        self._config = config

    def play(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.play(room.ip_address)

    def pause(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.pause(room.ip_address)

    def stop(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.stop(room.ip_address)

    def next_track(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.next_track(room.ip_address)

    def previous_track(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.previous_track(room.ip_address)

    def get_playback_state(self, room_name: str) -> PlaybackState:
        room = self._room_service.get_room(room_name)
        return self._adapter.get_playback_state(room.ip_address, room.name)

    def get_track_info(self, room_name: str) -> TrackInfo:
        room = self._resolve_coordinator(room_name)
        return self._adapter.get_track_info(room.ip_address)

    def seek(self, room_name: str, position: str) -> PlaybackState:
        """Seek to a position in the current track and return resulting playback state.

        Args:
            room_name: Target room name.
            position: Track position as ``"HH:MM:SS"`` string.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            PlaybackError: If position format is invalid or the SoCo operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        self._validate_seek_position(position)
        room = self._resolve_coordinator(room_name)
        self._adapter.seek(room.ip_address, position)
        return self._adapter.get_playback_state(room.ip_address, room_name)

    def get_sleep_timer(self, room_name: str) -> SleepTimerState:
        """Return the current sleep timer state for the named room.

        Routes to the group coordinator when the room is grouped.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            PlaybackError: If the SoCo operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._resolve_coordinator(room_name)
        return self._adapter.get_sleep_timer(room.ip_address, room_name)

    def set_sleep_timer(self, room_name: str, minutes: object) -> SleepTimerState:
        """Set or clear the sleep timer for the named room.

        Routes to the group coordinator when the room is grouped.

        Args:
            room_name: Target room name.
            minutes: Minutes until sleep; ``0`` clears the timer.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            PlaybackError: If minutes is negative or the SoCo operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        self._validate_sleep_timer_minutes(minutes)
        room = self._resolve_coordinator(room_name)
        return self._adapter.set_sleep_timer(room.ip_address, room_name, minutes)

    def get_volume_state(self, room_name: str) -> VolumeState:
        room = self._room_service.get_room(room_name)
        volume = self._adapter.get_volume(room.ip_address)
        is_muted = self._adapter.get_mute(room.ip_address)
        return VolumeState(room_name=room.name, volume=volume, is_muted=is_muted)

    def set_volume(self, room_name: str, volume: int) -> None:
        check_volume(volume, self._config)
        room = self._room_service.get_room(room_name)
        self._adapter.set_volume(room.ip_address, volume)

    def adjust_volume(self, room_name: str, delta: int) -> VolumeState:
        room = self._room_service.get_room(room_name)
        current = self._adapter.get_volume(room.ip_address)
        target = max(0, min(100, current + delta))
        check_volume(target, self._config)
        self._adapter.set_volume(room.ip_address, target)
        is_muted = self._adapter.get_mute(room.ip_address)
        return VolumeState(room_name=room.name, volume=target, is_muted=is_muted)

    def mute(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.set_mute(room.ip_address, True)

    def unmute(self, room_name: str) -> None:
        room = self._room_service.get_room(room_name)
        self._adapter.set_mute(room.ip_address, False)

    def _resolve_coordinator(self, room_name: str) -> Room:
        """Resolve the coordinator room for session-level operations.

        If the target room belongs to a group, returns the coordinator's Room
        so operations are directed at the correct zone. Falls back to the room
        itself if the coordinator UID cannot be resolved.
        """
        room = self._room_service.get_room(room_name)
        coordinator_uid = room.group_coordinator_uid
        if not coordinator_uid:
            return room

        rooms = self._room_service.list_rooms()
        for candidate in rooms:
            if candidate.uid == coordinator_uid:
                log.debug(
                    "coordinator routing: room=%r routed to coordinator=%r",
                    room_name,
                    candidate.name,
                )
                return candidate

        log.debug(
            "coordinator routing: coordinator uid %r not found for room=%r; using room ip",
            coordinator_uid,
            room_name,
        )
        return room

    def _validate_seek_position(self, position: object) -> None:
        """Validate explicit HH:MM:SS seek positions.

        Sonos accepts positions in HH:MM:SS form, but regex-only validation
        would still allow impossible values like ``00:99:99``.
        """
        if not isinstance(position, str):
            raise PlaybackValidationError(
                f"Invalid seek position {position!r}. Expected HH:MM:SS format."
            )
        parts = position.split(":")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            raise PlaybackValidationError(
                f"Invalid seek position {position!r}. Expected HH:MM:SS format."
            )

        hours, minutes, seconds = (int(part) for part in parts)
        if minutes >= 60 or seconds >= 60:
            raise PlaybackValidationError(
                f"Invalid seek position {position!r}. Minutes and seconds must be < 60."
            )

    def _validate_sleep_timer_minutes(self, minutes: object) -> None:
        if not isinstance(minutes, int) or isinstance(minutes, bool):
            raise PlaybackValidationError(
                f"Invalid minutes value {minutes!r}. Minutes must be an integer >= 0."
            )
        if minutes < 0:
            raise PlaybackValidationError(f"Invalid minutes value {minutes!r}. Must be >= 0.")
