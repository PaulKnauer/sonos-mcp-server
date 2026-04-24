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
    "max_volume_pct": 80,
    "tools_disabled": [],
    "http_host": "127.0.0.1",
    "http_port": 8000,
    "auth_mode": "none",
    "auth_token": None,
    "oidc_issuer": None,
    "oidc_audience": None,
    "oidc_jwks_uri": None,
    "oidc_ca_bundle": None,
    "oidc_resource_url": None,
}
