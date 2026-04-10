"""Input-switching service for SoniqMCP."""

from __future__ import annotations

from soniq_mcp.domain.exceptions import InputError, InputValidationError
from soniq_mcp.domain.models import InputState, Room, Speaker


class InputService:
    """Service for capability-aware Sonos input switching."""

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def switch_to_line_in(self, room_name: str) -> InputState:
        room = self._room_service.get_room(room_name)
        speakers = self._room_service.get_speakers_for_room(room_name)
        self._ensure_support(room_name, speakers, supports_line_in=True)
        self._adapter.switch_to_line_in(room.ip_address)
        return self._build_input_state(room, expected_source="line_in")

    def switch_to_tv(self, room_name: str) -> InputState:
        room = self._room_service.get_room(room_name)
        speakers = self._room_service.get_speakers_for_room(room_name)
        self._ensure_support(room_name, speakers, supports_tv=True)
        self._adapter.switch_to_tv(room.ip_address)
        return self._build_input_state(room, expected_source="tv")

    def _ensure_support(
        self,
        room_name: str,
        speakers: list[Speaker],
        *,
        supports_line_in: bool = False,
        supports_tv: bool = False,
    ) -> None:
        if not speakers:
            raise InputError(
                f"No speaker capability data was found for room {room_name!r}. "
                "Refresh discovery and try again."
            )

        if supports_line_in and not any(speaker.supports_line_in for speaker in speakers):
            raise InputValidationError(
                f"Room {room_name!r} does not support line-in input switching."
            )

        if supports_tv and not any(speaker.supports_tv for speaker in speakers):
            raise InputValidationError(f"Room {room_name!r} does not support TV input switching.")

    def _build_input_state(self, room: Room, *, expected_source: str) -> InputState:
        source = self._adapter.get_music_source(room.ip_address)
        normalized = self._normalize_source(source)
        if normalized is None:
            raise InputError(
                f"Unrecognized music source {source!r} after switching — "
                "the device may not have completed the switch."
            )

        coordinator_uid = room.group_coordinator_uid
        if coordinator_uid:
            coordinator_room_name: str | None = None
            for candidate in self._room_service.list_rooms():
                if candidate.uid == coordinator_uid:
                    coordinator_room_name = candidate.name
                    break
        else:
            coordinator_room_name = room.name

        return InputState(
            room_name=room.name,
            input_source=normalized,
            coordinator_room_name=coordinator_room_name,
        )

    @staticmethod
    def _normalize_source(source: object) -> str | None:
        if not isinstance(source, str):
            return None
        normalized = source.strip().upper()
        if normalized == "LINE_IN":
            return "line_in"
        if normalized == "TV":
            return "tv"
        return None
