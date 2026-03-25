"""Sensible defaults for SoniqMCP configuration."""

from __future__ import annotations

DEFAULTS: dict[str, object] = {
    "transport": "stdio",
    "exposure": "local",
    "log_level": "INFO",
    "default_room": None,
    "config_file": None,
    "max_volume_pct": 80,
    "tools_disabled": [],
}
