"""Application composition boundary for SoniqMCP.

``create_server()`` is the single place where the MCP application is
assembled.  Transport concerns stay in ``transports/``.  Sonos service
wiring arrives in Story 2+.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, run_preflight
from soniq_mcp.tools import register_all

log = logging.getLogger(__name__)


def create_server(config: SoniqConfig | None = None) -> FastMCP:
    """Create and configure the MCP application.

    Runs preflight validation when ``config`` is not provided.

    Args:
        config: Pre-validated config (tests may inject one directly).

    Returns:
        A fully configured :class:`FastMCP` instance.

    Raises:
        ConfigValidationError: if config is invalid and was not pre-supplied.
    """
    if config is None:
        config = run_preflight()

    app = FastMCP("soniq-mcp")
    register_all(app, config)

    log.info(
        "SoniqMCP server created — transport=%s exposure=%s",
        config.transport.value,
        config.exposure.value,
    )
    return app
