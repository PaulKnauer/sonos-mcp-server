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


def _build_auth_kwargs(config: SoniqConfig) -> None:
    """Seam for future auth wiring in Epic 2/3.

    Epic 2/3 will populate this and pass the result into the FastMCP constructor.
    For auth_mode=none this must never be called — the guard in create_server()
    ensures that.
    """


def create_server(config: SoniqConfig | None = None) -> FastMCP:
    """Create and configure the MCP application."""
    if config is None:
        config = run_preflight()

    warnings = validate_exposure_posture(config)
    for warning in warnings:
        log.warning("Exposure posture: %s", warning)

    if config.auth_mode != AuthMode.NONE:
        _build_auth_kwargs(config)  # Epic 2/3 wires this result into FastMCP

    app = FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)
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
