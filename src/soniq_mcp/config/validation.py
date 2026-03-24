"""Startup preflight validation for SoniqMCP."""

from __future__ import annotations

from pydantic import ValidationError

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import SoniqConfig


class ConfigValidationError(ValueError):
    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


def run_preflight(overrides: dict | None = None) -> SoniqConfig:
    """Load and validate config; raise ConfigValidationError on failure."""
    try:
        return load_config(overrides=overrides)
    except ValidationError as exc:
        messages = [_fmt(e) for e in exc.errors()]
        raise ConfigValidationError(messages) from exc


def _fmt(error: dict) -> str:
    loc = ".".join(str(p) for p in error.get("loc", []))
    msg = error.get("msg", "invalid value").removeprefix("Value error, ")
    return f"{loc}: {msg}" if loc else msg
