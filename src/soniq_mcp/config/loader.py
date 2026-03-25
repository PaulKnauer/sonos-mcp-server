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
    "SONIQ_MCP_MAX_VOLUME_PCT": "max_volume_pct",
    "SONIQ_MCP_TOOLS_DISABLED": "tools_disabled",
}


def load_config(overrides: dict[str, Any] | None = None) -> SoniqConfig:
    """Load and validate configuration from env vars with optional overrides."""
    raw: dict[str, Any] = dict(DEFAULTS)

    for env_key, field_name in _ENV_MAP.items():
        value = os.environ.get(env_key)
        if value is not None and value.strip() != "":
            if field_name == "max_volume_pct":
                raw[field_name] = int(value.strip())
            elif field_name == "tools_disabled":
                # Comma-separated list: "ping,server_info"
                raw[field_name] = [t.strip() for t in value.split(",") if t.strip()]
            else:
                raw[field_name] = value.strip()

    if overrides:
        raw.update(overrides)

    normalized = {k: (None if v == "" else v) for k, v in raw.items()}
    return SoniqConfig.model_validate(normalized)
