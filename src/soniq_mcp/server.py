"""Application composition boundary for SoniqMCP.

``create_server()`` is the single place where the MCP application is
assembled. Transport concerns stay in ``transports/``. Sonos service
wiring arrives in Story 2+.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, run_preflight
from soniq_mcp.config.models import AuthMode
from soniq_mcp.domain.safety import validate_exposure_posture
from soniq_mcp.tools import register_all
from soniq_mcp.transports.bootstrap import bootstrap_transport

log = logging.getLogger(__name__)


def _build_auth_kwargs(config: SoniqConfig) -> dict[str, object]:
    """Return auth constructor kwargs for FastMCP when auth is enabled.

    This seam is intentionally empty until Epic 2/3 wire real verifiers.
    For auth_mode=none it must never be called — the guard in create_server()
    ensures that.
    """
    return {}


def create_server(config: SoniqConfig | None = None) -> FastMCP:
    """Create and configure the MCP application."""
    if config is None:
        config = run_preflight()

    warnings = validate_exposure_posture(config)
    for warning in warnings:
        log.warning("Exposure posture: %s", warning)

    auth_kwargs: dict[str, object] = {}
    if config.auth_mode != AuthMode.NONE:
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
