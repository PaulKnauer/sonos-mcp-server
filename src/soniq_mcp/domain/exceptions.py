"""Domain exceptions for SoniqMCP.

All domain errors inherit from ``SoniqDomainError`` so callers can
catch the base type or specific subtypes as needed.
"""

from __future__ import annotations


class SoniqDomainError(Exception):
    """Base class for all SoniqMCP domain errors."""


class VolumeCapExceeded(SoniqDomainError):
    """Raised when a requested volume exceeds the configured safe maximum.

    Args:
        requested: The volume level that was requested (0-100).
        cap: The configured maximum volume allowed.
    """

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

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' is disabled by server configuration."
        )


class RoomNotFoundError(SoniqDomainError):
    """Raised when a requested room name does not match any discovered zone.

    Args:
        room_name: The room name that could not be found.
    """

    def __init__(self, room_name: str) -> None:
        self.room_name = room_name
        super().__init__(
            f"Room '{room_name}' was not found in the Sonos household. "
            "Use 'list_rooms' to see available rooms."
        )


class SonosDiscoveryError(SoniqDomainError):
    """Raised when Sonos network discovery fails due to a connectivity problem.

    Args:
        message: Human-readable description of the failure.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class PlaybackError(SoniqDomainError):
    """Raised when a Sonos playback operation fails.

    Wraps SoCo UPnP errors and other zone-level failures so they never
    leak past the adapter layer.

    Args:
        message: Human-readable description of the failure.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
