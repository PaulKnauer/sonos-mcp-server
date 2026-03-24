"""Configuration loading and normalization for SoniqMCP.

Reads environment variables, applies defaults, and produces a validated
SoniqConfig.  Independent of transports and Sonos operations.
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import ValidationError

from soniq_mcp.config.defaults import DEFAULTS
from soniq_mcp.config.models import SoniqConfig

# Maps SONIQ_MCP_* env vars to SoniqConfig field names.
_ENV_MAP: dict[str, str] = {
    "SONIQ_MCP_TRANSPORT": "transport",
    "SONIQ_MCP_EXPOSURE": "exposure",
    "SONIQ_MCP_LOG_LEVEL": "log_level",
    "SONIQ_MCP_DEFAULT_ROOM": "default_room",
}


def load_config(overrides: dict[str, Any] | None = None) -> SoniqConfig:
    """Load and validate configuration.

    Resolution order (last wins):
      1. Hardcoded defaults
      2. SONIQ_MCP_* environment variables
      3. ``overrides`` dict (programmatic or test use)

    Raises:
        ValidationError: propagated from pydantic when values are invalid.
    """
    raw: dict[str, Any] = dict(DEFAULTS)

    for env_key, field_name in _ENV_MAP.items():
        value = os.environ.get(env_key)
        if value is not None and value.strip() != "":
            raw[field_name] = value.strip()

    if overrides:
        raw.update(overrides)

    return _normalize(raw)


def _normalize(raw: dict[str, Any]) -> SoniqConfig:
    """Coerce empty or whitespace-only strings to None for optional fields, then parse."""
    normalized = {
        k: (None if isinstance(v, str) and v.strip() == "" else v)
        for k, v in raw.items()
    }
    return SoniqConfig.model_validate(normalized)
