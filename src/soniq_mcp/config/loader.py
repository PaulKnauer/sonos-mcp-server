"""Configuration loading and normalization for SoniqMCP."""

from __future__ import annotations

import os
from typing import Any

from soniq_mcp.config.defaults import DEFAULTS
from soniq_mcp.config.models import SoniqConfig

_ENV_MAP: dict[str, str] = {
    "SONIQ_MCP_TRANSPORT": "transport",
    "SONIQ_MCP_EXPOSURE": "exposure",
    "SONIQ_MCP_LOG_LEVEL": "log_level",
    "SONIQ_MCP_DEFAULT_ROOM": "default_room",
    "SONIQ_MCP_CONFIG_FILE": "config_file",
}


def load_config(overrides: dict[str, Any] | None = None) -> SoniqConfig:
    """Load and validate configuration from env vars with optional overrides."""
    raw: dict[str, Any] = dict(DEFAULTS)

    for env_key, field_name in _ENV_MAP.items():
        value = os.environ.get(env_key)
        if value is not None and value.strip() != "":
            raw[field_name] = value.strip()

    if overrides:
        raw.update(overrides)

    normalized = {k: (None if v == "" else v) for k, v in raw.items()}
    return SoniqConfig.model_validate(normalized)
