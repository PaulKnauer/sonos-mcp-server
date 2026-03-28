"""Streamable HTTP transport for SoniqMCP.

Runs the MCP server over HTTP for cross-device home-network use.
Requires uvicorn (bundled via mcp[cli]).
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config.models import SoniqConfig

log = logging.getLogger(__name__)


def run_streamable_http(app: FastMCP, config: SoniqConfig) -> None:
    """Start the MCP server using the Streamable HTTP transport."""
    log.info(
        "Starting SoniqMCP over Streamable HTTP transport host=%s port=%s path=/mcp",
        config.http_host,
        config.http_port,
    )
    app.run(transport="streamable-http")


def streamable_http_transport_name() -> str:
    """Return the canonical transport identifier."""
    return "streamable-http"
