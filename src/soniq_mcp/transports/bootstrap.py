"""Transport selection and bootstrap for SoniqMCP.

Reads the validated config and dispatches to the appropriate transport
runner. New transports are added here without touching server.py or
__main__.py.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, TransportMode

log = logging.getLogger(__name__)


def run_transport(app: FastMCP, config: SoniqConfig) -> None:
    """Start the appropriate transport for ``config.transport``."""
    if config.transport == TransportMode.STDIO:
        from soniq_mcp.transports.stdio import run_stdio

        run_stdio(app)
    elif config.transport == TransportMode.HTTP:
        from soniq_mcp.transports.streamable_http import run_streamable_http

        run_streamable_http(app, config)
    else:
        raise NotImplementedError(f"Transport '{config.transport.value}' is not yet implemented")


def bootstrap_transport() -> str:
    """Return the default transport name used by tests and docs."""
    return "stdio"
