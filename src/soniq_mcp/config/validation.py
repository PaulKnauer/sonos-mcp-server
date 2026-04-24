"""Startup preflight validation for SoniqMCP.

Call ``run_preflight()`` before any Sonos or transport initialisation.
Errors identify the specific field that must be corrected and are safe
to surface to the user.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import AuthMode, SoniqConfig, TransportMode


class ConfigValidationError(ValueError):
    """Raised when configuration fails preflight checks."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


def run_preflight(overrides: dict | None = None) -> SoniqConfig:
    """Load and validate configuration; raise before runtime on failure."""
    try:
        config = load_config(overrides=overrides)
    except (ValidationError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            messages = [_fmt(error) for error in exc.errors()]
        else:
            messages = [str(exc)]
        raise ConfigValidationError(messages) from exc

    auth_errors = _validate_auth_preflight(config)
    if auth_errors:
        raise ConfigValidationError(auth_errors)

    return config


def _validate_auth_preflight(config: SoniqConfig) -> list[str]:
    """Return user-facing error messages for blocking auth misconfiguration.

    Only HTTP transport failures are blocking.  Stdio with auth fields present
    is allowed; the operator may be testing locally before enabling HTTP.
    Secret values are never included in returned messages.
    """
    if config.transport == TransportMode.STDIO:
        return []

    errors: list[str] = []

    if config.auth_mode == AuthMode.STATIC and config.auth_token is None:
        errors.append(
            "auth_mode=static requires auth_token to be set. "
            "Set SONIQ_MCP_AUTH_TOKEN to a non-empty bearer token value."
        )

    return errors


def _fmt(error: Mapping[str, Any]) -> str:
    """Format a single pydantic error dict into a user-facing string."""
    loc = ".".join(str(part) for part in error.get("loc", []))
    msg = error.get("msg", "invalid value").removeprefix("Value error, ")
    return f"{loc}: {msg}" if loc else msg
