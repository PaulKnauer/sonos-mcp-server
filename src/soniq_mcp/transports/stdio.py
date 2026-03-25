"""stdio transport for SoniqMCP.

Runs the MCP server over stdin/stdout for same-machine AI clients
such as Claude Desktop.  No network socket is opened.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

log = logging.getLogger(__name__)


def run_stdio(app: FastMCP) -> None:
    """Start the MCP server using the stdio transport.

    This call blocks until the client disconnects or the process is
    terminated.  It must only be called after preflight succeeds.
    """
    log.info("Starting SoniqMCP over stdio transport")
    app.run(transport="stdio")


def stdio_transport_name() -> str:
    """Return the canonical transport identifier."""
    return "stdio"
