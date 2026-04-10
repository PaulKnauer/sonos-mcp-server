"""Domain exceptions for SoniqMCP.

All domain errors inherit from ``SoniqDomainError`` so callers can
catch the base type or specific subtypes as needed.
"""

from __future__ import annotations

from enum import StrEnum


class ErrorCategory(StrEnum):
    """Stable categories for user-facing diagnostics."""

    CONFIGURATION = "configuration"
    CONNECTIVITY = "connectivity"
    VALIDATION = "validation"
    OPERATION = "operation"


class SoniqDomainError(Exception):
    """Base class for all SoniqMCP domain errors."""

    error_category: ErrorCategory = ErrorCategory.OPERATION


class VolumeCapExceeded(SoniqDomainError):
    """Raised when a requested volume exceeds the configured safe maximum.

    Args:
        requested: The volume level that was requested (0-100).
        cap: The configured maximum volume allowed.
    """

    error_category = ErrorCategory.VALIDATION

    def __init__(self, requested: int, cap: int) -> None:
        self.requested = requested
        self.cap = cap
        super().__init__(
            f"Requested volume {requested} exceeds the safe maximum of {cap}. "
            f"Lower your request or raise max_volume_pct in configuration."
        )


class ToolNotPermitted(SoniqDomainError):
    """Raised when a tool is invoked but has been disabled by configuration.

    Args:
        tool_name: The name of the suppressed tool.
    """

    error_category = ErrorCategory.CONFIGURATION

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}' is disabled by server configuration.")


class RoomNotFoundError(SoniqDomainError):
    """Raised when a requested room name does not match any discovered zone.

    Args:
        room_name: The room name that could not be found.
    """

    error_category = ErrorCategory.VALIDATION

    def __init__(self, room_name: str) -> None:
        self.room_name = room_name
        super().__init__(
            f"Room '{room_name}' was not found in the Sonos household. "
            "Use 'list_rooms' to see available rooms."
        )


class VolumeError(SoniqDomainError):
    """Raised when a SoCo volume or mute operation fails.

    Args:
        message: Human-readable description of the failure.
    """

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class SonosDiscoveryError(SoniqDomainError):
    """Raised when Sonos network discovery fails due to a connectivity problem.

    Args:
        message: Human-readable description of the failure.
    """

    error_category = ErrorCategory.CONNECTIVITY

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PlaybackError(SoniqDomainError):
    """Raised when a Sonos playback operation fails.

    Wraps SoCo UPnP errors and other zone-level failures so they never
    leak past the adapter layer.

    Args:
        message: Human-readable description of the failure.
    """

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PlaybackValidationError(PlaybackError):
    """Raised when a playback request fails local validation."""

    error_category = ErrorCategory.VALIDATION


class FavouritesError(SoniqDomainError):
    """Raised when a Sonos favourites or playlists operation fails."""

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class QueueError(SoniqDomainError):
    """Raised when a Sonos queue operation fails.

    Wraps SoCo UPnP errors and queue-level failures so they never
    leak past the adapter layer.

    Args:
        message: Human-readable description of the failure.
    """

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class GroupError(SoniqDomainError):
    """Raised when a Sonos grouping operation fails.

    Args:
        message: Human-readable description of the failure.
    """

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class GroupValidationError(GroupError):
    """Raised when a group-audio request fails local validation.

    Covers non-grouped targets, coordinator-resolution failures, and
    invalid-target paths.
    """

    error_category = ErrorCategory.VALIDATION


class AudioSettingsError(SoniqDomainError):
    """Raised when a Sonos audio EQ operation fails.

    Covers adapter-level SoCo failures and other operational EQ problems.

    Args:
        message: Human-readable description of the failure.
    """

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AudioSettingsValidationError(AudioSettingsError):
    """Raised when an audio EQ request fails local validation."""

    error_category = ErrorCategory.VALIDATION


class InputError(SoniqDomainError):
    """Raised when a Sonos input-switching operation fails."""

    error_category = ErrorCategory.OPERATION

    def __init__(self, message: str) -> None:
        super().__init__(message)


class InputValidationError(InputError):
    """Raised when an input-switching request fails local validation."""

    error_category = ErrorCategory.VALIDATION
