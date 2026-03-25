"""Startup preflight validation for SoniqMCP.

Call ``run_preflight()`` before any Sonos or transport initialisation.
Errors identify the specific field that must be corrected and are safe
to surface to the user (no host, token, or network detail leaked).
"""

from __future__ import annotations

from pydantic import ValidationError

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import SoniqConfig


class ConfigValidationError(ValueError):
    """Raised when configuration fails preflight checks.

    ``messages`` is a list of human-readable, field-level error strings.
    """
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


def run_preflight(overrides: dict | None = None) -> SoniqConfig:
    """Load and validate configuration; raise before runtime on failure.

    Args:
        overrides: Optional dict of field overrides (used in tests).

    Returns:
        A fully validated :class:`SoniqConfig`.

    Raises:
        ConfigValidationError: if any field is invalid or missing.
    """
    try:
        return load_config(overrides=overrides)
    except ValidationError as exc:
        messages = [_fmt(e) for e in exc.errors()]
        raise ConfigValidationError(messages) from exc


def _fmt(error: dict) -> str:
    """Format a single pydantic error dict into a user-facing string."""
    loc = ".".join(str(p) for p in error.get("loc", []))
    msg = error.get("msg", "invalid value")
    # Strip pydantic's "Value error, " prefix for cleaner output
    msg = msg.removeprefix("Value error, ")
    return f"{loc}: {msg}" if loc else msg
