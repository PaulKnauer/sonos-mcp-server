"""Application composition boundary for SoniqMCP.

``create_server()`` is the single place where the MCP application is
assembled. Transport concerns stay in ``transports/``. Sonos service
wiring arrives in Story 2+.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, run_preflight
from soniq_mcp.config.models import AuthMode, TransportMode
from soniq_mcp.domain.safety import validate_exposure_posture
from soniq_mcp.tools import register_all
from soniq_mcp.transports.bootstrap import bootstrap_transport

log = logging.getLogger(__name__)


def _build_auth_kwargs(config: SoniqConfig) -> dict[str, Any]:
    """Build FastMCP auth constructor kwargs for enabled auth modes.

    Only called when HTTP auth is enabled — the guard in create_server() ensures that.
    """
    from mcp.server.auth.settings import AuthSettings

    from soniq_mcp.auth import build_token_verifier

    auth_settings = AuthSettings(
        issuer_url=f"http://{_format_url_host(config.http_host)}:{config.http_port}",
        resource_server_url=config.oidc_resource_url,
        required_scopes=None,
    )
    return {"auth": auth_settings, "token_verifier": build_token_verifier(config)}


def _format_url_host(host: str) -> str:
    """Return host formatted for use in a URL authority."""
    if ":" in host and not host.startswith("["):
        return f"[{host}]"
    return host


def create_server(config: SoniqConfig | None = None) -> FastMCP:
    """Create and configure the MCP application."""
    if config is None:
        config = run_preflight()

    warnings = validate_exposure_posture(config)
    for warning in warnings:
        log.warning("Exposure posture: %s", warning)

    auth_kwargs: dict[str, Any] = {}
    if config.transport == TransportMode.HTTP and config.auth_mode == AuthMode.STATIC:
        auth_kwargs = _build_auth_kwargs(config)

    app = FastMCP("soniq-mcp", host=config.http_host, port=config.http_port, **auth_kwargs)
    register_all(app, config)

    log.info(
        "SoniqMCP server created transport=%s exposure=%s max_volume=%s%%",
        config.transport.value,
        config.exposure.value,
        config.max_volume_pct,
    )
    return app


def create_application() -> Mapping[str, str]:
    """Return minimal app metadata for backward-compatible smoke tests."""
    return {
        "name": "soniq_mcp",
        "transport": bootstrap_transport(),
    }
