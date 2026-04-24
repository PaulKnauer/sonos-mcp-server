"""Configuration loading and normalization for SoniqMCP.

Reads `.env` and environment variables, applies defaults, and produces a
validated SoniqConfig. Independent of transports and Sonos operations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from soniq_mcp.config.defaults import DEFAULTS
from soniq_mcp.config.models import SoniqConfig

# Maps SONIQ_MCP_* env vars to SoniqConfig field names.
_ENV_MAP: dict[str, str] = {
    "SONIQ_MCP_TRANSPORT": "transport",
    "SONIQ_MCP_EXPOSURE": "exposure",
    "SONIQ_MCP_LOG_LEVEL": "log_level",
    "SONIQ_MCP_DEFAULT_ROOM": "default_room",
    "SONIQ_MCP_CONFIG_FILE": "config_file",
    "SONIQ_MCP_MAX_VOLUME_PCT": "max_volume_pct",
    "SONIQ_MCP_TOOLS_DISABLED": "tools_disabled",
    "SONIQ_MCP_HTTP_HOST": "http_host",
    "SONIQ_MCP_HTTP_PORT": "http_port",
    "SONIQ_MCP_AUTH_MODE": "auth_mode",
    "SONIQ_MCP_AUTH_TOKEN": "auth_token",
    "SONIQ_MCP_OIDC_ISSUER": "oidc_issuer",
    "SONIQ_MCP_OIDC_AUDIENCE": "oidc_audience",
    "SONIQ_MCP_OIDC_JWKS_URI": "oidc_jwks_uri",
    "SONIQ_MCP_OIDC_CA_BUNDLE": "oidc_ca_bundle",
    "SONIQ_MCP_OIDC_RESOURCE_URL": "oidc_resource_url",
}


def load_config(overrides: dict[str, Any] | None = None) -> SoniqConfig:
    """Load and validate configuration.

    Resolution order (last wins):
      1. Hardcoded defaults
      2. Project-local ``.env`` file (if present)
      3. SONIQ_MCP_* environment variables
      4. ``overrides`` dict (programmatic or test use)
    """
    raw: dict[str, Any] = dict(DEFAULTS)

    raw.update(_read_dotenv(Path.cwd() / ".env"))

    for env_key, field_name in _ENV_MAP.items():
        value = os.environ.get(env_key)
        if value is not None and value.strip() != "":
            if field_name == "tools_disabled":
                raw[field_name] = [t.strip() for t in value.split(",") if t.strip()]
            else:
                raw[field_name] = value.strip()

    if overrides:
        raw.update(overrides)

    normalized = _normalize(raw)
    return SoniqConfig.model_validate(normalized)


def _read_dotenv(path: Path) -> dict[str, Any]:
    """Read supported SONIQ_MCP_* settings from a project-local `.env` file."""
    if not path.is_file():
        return {}

    raw_dotenv = dotenv_values(path)
    return {
        field_name: value
        for env_key, field_name in _ENV_MAP.items()
        if (value := raw_dotenv.get(env_key)) is not None
    }


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Coerce empty or whitespace-only strings to None for optional fields."""
    return {
        key: (None if isinstance(value, str) and value.strip() == "" else value)
        for key, value in raw.items()
    }
