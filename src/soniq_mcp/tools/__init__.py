"""Tools package for SoniqMCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig


def register_all(app: FastMCP, config: SoniqConfig) -> None:
    """Register all available tools, respecting tools_disabled."""
    from soniq_mcp.tools.setup_support import register as register_setup
    register_setup(app, config)
