"""Application composition boundary for SoniqMCP."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, run_preflight
from soniq_mcp.domain.safety import validate_exposure_posture
from soniq_mcp.tools import register_all

log = logging.getLogger(__name__)


def create_server(config: SoniqConfig | None = None) -> FastMCP:
    """Create and configure the MCP application.

    Runs preflight validation when ``config`` is not provided.
    Validates the exposure posture and logs any warnings.
    """
    if config is None:
        config = run_preflight()

    warnings = validate_exposure_posture(config)
    for w in warnings:
        log.warning("Exposure posture: %s", w)

    app = FastMCP("soniq-mcp")
    register_all(app, config)

    log.info(
        "SoniqMCP server created — transport=%s exposure=%s max_volume=%s%%",
        config.transport.value,
        config.exposure.value,
        config.max_volume_pct,
    )
    return app
