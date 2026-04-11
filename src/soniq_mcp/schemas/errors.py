"""Error response schemas for SoniqMCP.

Used by tool handlers to return structured, user-facing error information
without leaking implementation details.
"""

from __future__ import annotations

import re

from pydantic import BaseModel

from soniq_mcp.domain.exceptions import ErrorCategory, SoniqDomainError

_URL_PATTERN = re.compile(r"https?://\S+")
_IPV4_PATTERN = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_WINDOWS_PATH_PATTERN = re.compile(r"\b[A-Za-z]:\\[^\s]+")
_POSIX_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])/(?:[^\s/]+/)*[^\s/]+")


class ErrorResponse(BaseModel):
    """Structured error returned by tool handlers on expected failures."""

    category: ErrorCategory = ErrorCategory.OPERATION
    error: str
    field: str | None = None
    suggestion: str | None = None

    @classmethod
    def _build(
        cls,
        *,
        category: ErrorCategory,
        error: str,
        field: str | None = None,
        suggestion: str | None = None,
    ) -> ErrorResponse:
        return cls(
            category=category,
            error=_sanitize_text(error),
            field=field,
            suggestion=_sanitize_text(suggestion) if suggestion is not None else None,
        )

    @classmethod
    def _from_domain_error(
        cls,
        exc: Exception,
        *,
        field: str,
        suggestion: str,
    ) -> ErrorResponse:
        category = (
            exc.error_category if isinstance(exc, SoniqDomainError) else ErrorCategory.OPERATION
        )
        return cls._build(
            category=category,
            error=str(exc),
            field=field,
            suggestion=suggestion,
        )

    @classmethod
    def from_volume_cap(cls, requested: int, cap: int) -> ErrorResponse:
        return cls._build(
            category=ErrorCategory.VALIDATION,
            error=f"Volume {requested} exceeds the safe maximum of {cap}.",
            field="volume",
            suggestion=f"Use a value of {cap} or lower, or raise max_volume_pct.",
        )

    @classmethod
    def from_tool_not_permitted(cls, tool_name: str) -> ErrorResponse:
        return cls._build(
            category=ErrorCategory.CONFIGURATION,
            error=f"Tool '{tool_name}' is disabled by server configuration.",
            field="tools_disabled",
            suggestion="Remove the tool name from tools_disabled to enable it.",
        )

    @classmethod
    def from_discovery_error(cls, exc: Exception) -> ErrorResponse:
        return cls._build(
            category=ErrorCategory.CONNECTIVITY,
            error=str(exc),
            field="sonos_network",
            suggestion=(
                "Ensure the server is on the same network as your Sonos speakers "
                "and that Sonos is reachable."
            ),
        )

    @classmethod
    def from_room_not_found(cls, room_name: str) -> ErrorResponse:
        return cls._build(
            category=ErrorCategory.VALIDATION,
            error=f"Room '{room_name}' was not found in the Sonos household.",
            field="room",
            suggestion="Use 'list_rooms' to see available rooms and check spelling.",
        )

    @classmethod
    def from_playback_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="playback",
            suggestion=(
                "Check that the room is reachable and has active playback. "
                "Some operations (next/previous) require a queue or loaded track."
            ),
        )

    @classmethod
    def from_volume_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="sonos_volume",
            suggestion="Check that the Sonos speaker is reachable and try again.",
        )

    @classmethod
    def from_favourites_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="favourites",
            suggestion=(
                "Check that the Sonos system is reachable and has saved favourites or playlists. "
                "Use 'list_rooms' to verify the network is discoverable."
            ),
        )

    @classmethod
    def from_queue_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="queue",
            suggestion=(
                "Check that the room is reachable and has queue-capable playback. "
                "Some operations require a non-empty queue or a valid queue position."
            ),
        )

    @classmethod
    def from_group_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="group",
            suggestion=(
                "Check that all rooms are reachable and on the same Sonos network. "
                "Use 'list_rooms' to verify available rooms before grouping operations."
            ),
        )

    @classmethod
    def from_audio_settings_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="audio_settings",
            suggestion=(
                "Check that the room is reachable and that bass/treble are integers "
                "in the range -10..10 and loudness is a boolean."
            ),
        )

    @classmethod
    def from_input_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="input_source",
            suggestion=(
                "Check that the room supports the requested input source and is reachable. "
                "Use 'get_system_topology' to inspect current room and speaker metadata."
            ),
        )

    @classmethod
    def from_alarm_error(cls, exc: Exception) -> ErrorResponse:
        return cls._from_domain_error(
            exc,
            field="alarm",
            suggestion=(
                "Check alarm parameters: start_time must be HH:MM:SS, recurrence must be valid, "
                "volume must be 0-100, and alarm_id must exist. "
                "Use 'list_alarms' to see current alarms."
            ),
        )


def _sanitize_text(text: str) -> str:
    """Redact sensitive transport and filesystem details from user-facing text."""
    sanitized = _URL_PATTERN.sub("<redacted-url>", text)
    sanitized = _IPV4_PATTERN.sub("<redacted-host>", sanitized)
    sanitized = _WINDOWS_PATH_PATTERN.sub("<redacted-path>", sanitized)
    sanitized = _POSIX_PATH_PATTERN.sub("<redacted-path>", sanitized)
    return sanitized
