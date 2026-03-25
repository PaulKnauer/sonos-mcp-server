"""Error response schemas for SoniqMCP.

Used by tool handlers to return structured, user-facing error information
without leaking implementation details.
"""

from __future__ import annotations

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Structured error returned by tool handlers on expected failures."""

    error: str
    field: str | None = None
    suggestion: str | None = None

    @classmethod
    def from_volume_cap(cls, requested: int, cap: int) -> "ErrorResponse":
        return cls(
            error=f"Volume {requested} exceeds the safe maximum of {cap}.",
            field="volume",
            suggestion=f"Use a value of {cap} or lower, or raise max_volume_pct.",
        )

    @classmethod
    def from_tool_not_permitted(cls, tool_name: str) -> "ErrorResponse":
        return cls(
            error=f"Tool '{tool_name}' is disabled by server configuration.",
            field="tools_disabled",
            suggestion="Remove the tool name from tools_disabled to enable it.",
        )
