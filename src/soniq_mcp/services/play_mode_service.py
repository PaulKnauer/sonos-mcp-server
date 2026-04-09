"""Play mode service for SoniqMCP.

Handles get/set of shuffle, repeat, and crossfade modes for Sonos zones.
All operations route to the group coordinator when the target room is grouped.
"""

from __future__ import annotations

import logging
from typing import Final

from soniq_mcp.domain.exceptions import PlaybackError, PlaybackValidationError
from soniq_mcp.domain.models import PlayModeState, Room

log = logging.getLogger(__name__)

_VALID_REPEAT_VALUES: Final[frozenset[str]] = frozenset({"none", "all", "one"})


class PlayModeService:
    """Service for reading and writing Sonos play mode settings."""

    def __init__(self, room_service: object, adapter: object, config: object) -> None:
        self._room_service = room_service
        self._adapter = adapter
        self._config = config

    def get_play_mode(self, room_name: str) -> PlayModeState:
        """Return the current play mode settings for the named room.

        Routes to the group coordinator when the room is grouped.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        room = self._resolve_coordinator(room_name)
        return self._adapter.get_play_mode(room.ip_address, room_name)

    def set_play_mode(
        self,
        room_name: str,
        shuffle: object = None,
        repeat: object = None,
        cross_fade: object = None,
    ) -> PlayModeState:
        """Apply play mode changes for the named room.

        Routes to the group coordinator when the room is grouped.
        Validates the repeat value before calling the adapter.

        Args:
            room_name: Target room name.
            shuffle: If provided, set shuffle on/off.
            repeat: If provided, set repeat mode. Must be "none", "all", or "one".
            cross_fade: If provided, set crossfade on/off.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            PlaybackError: If repeat value is invalid or the SoCo operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        self._validate_optional_bool(shuffle, "shuffle")
        self._validate_optional_bool(cross_fade, "cross_fade")
        if repeat is not None and (
            not isinstance(repeat, str) or repeat not in _VALID_REPEAT_VALUES
        ):
            raise PlaybackValidationError(
                f"Invalid repeat value {repeat!r}. Allowed values: 'none', 'all', 'one'."
            )
        room = self._resolve_coordinator(room_name)
        return self._adapter.set_play_mode(
            room.ip_address,
            room_name,
            shuffle=shuffle,
            repeat=repeat,
            cross_fade=cross_fade,
        )

    @staticmethod
    def _validate_optional_bool(value: object, field: str) -> None:
        if value is not None and not isinstance(value, bool):
            raise PlaybackValidationError(
                f"Invalid {field} value {value!r}. Expected a boolean."
            )

    def _resolve_coordinator(self, room_name: str) -> Room:
        """Resolve the coordinator room for play mode operations.

        If the target room belongs to a group, returns the coordinator's Room
        so play mode is read/written against the correct zone. Falls back to
        the room itself if the coordinator UID cannot be resolved.
        """
        room = self._room_service.get_room(room_name)
        coordinator_uid = room.group_coordinator_uid
        if not coordinator_uid:
            return room

        for candidate in self._room_service.list_rooms():
            if candidate.uid == coordinator_uid:
                log.debug(
                    "play_mode: room=%r routed to coordinator=%r",
                    room_name,
                    candidate.name,
                )
                return candidate

        log.debug(
            "play_mode: coordinator uid %r not found for room=%r; using room ip",
            coordinator_uid,
            room_name,
        )
        return room
