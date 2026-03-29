"""Startup preflight validation for SoniqMCP.

Call ``run_preflight()`` before any Sonos or transport initialisation.
Errors identify the specific field that must be corrected and are safe
to surface to the user.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import SoniqConfig


class ConfigValidationError(ValueError):
    """Raised when configuration fails preflight checks."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


def run_preflight(overrides: dict | None = None) -> SoniqConfig:
    """Load and validate configuration; raise before runtime on failure."""
    try:
        return load_config(overrides=overrides)
    except (ValidationError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            messages = [_fmt(error) for error in exc.errors()]
        else:
            messages = [str(exc)]
        raise ConfigValidationError(messages) from exc


def _fmt(error: dict[str, Any]) -> str:
    """Format a single pydantic error dict into a user-facing string."""
    loc = ".".join(str(part) for part in error.get("loc", []))
    msg = error.get("msg", "invalid value").removeprefix("Value error, ")
    return f"{loc}: {msg}" if loc else msg
