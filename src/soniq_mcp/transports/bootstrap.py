"""Transport selection and bootstrap for SoniqMCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, TransportMode


def run_transport(app: FastMCP, config: SoniqConfig) -> None:
    if config.transport == TransportMode.STDIO:
        from soniq_mcp.transports.stdio import run_stdio
        run_stdio(app)
    else:
        raise NotImplementedError(
            f"Transport '{config.transport.value}' is not yet implemented"
        )


def bootstrap_transport() -> str:
    return "stdio"
