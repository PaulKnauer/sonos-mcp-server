"""Sensible defaults for SoniqMCP configuration.

These values represent the safe, single-household local setup.
Later stories extend supported transport and exposure values.
"""

from __future__ import annotations

DEFAULTS: dict[str, object] = {
    "transport": "stdio",
    "exposure": "local",
    "log_level": "INFO",
    "default_room": None,
    "config_file": None,
}
