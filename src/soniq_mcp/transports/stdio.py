"""stdio transport for SoniqMCP."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

log = logging.getLogger(__name__)


def run_stdio(app: FastMCP) -> None:
    log.info("Starting SoniqMCP over stdio transport")
    app.run(transport="stdio")


def stdio_transport_name() -> str:
    return "stdio"
