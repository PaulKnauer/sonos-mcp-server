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
