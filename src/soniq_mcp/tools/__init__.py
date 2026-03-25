"""Tools package for SoniqMCP.

Each module exposes a ``register(app, config)`` function that registers
its tools onto the FastMCP application.  Sonos-specific tools arrive
in Story 2+.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig


def register_all(app: FastMCP, config: SoniqConfig) -> None:
    """Register all available tools onto ``app``."""
    from soniq_mcp.tools.setup_support import register as register_setup
    register_setup(app, config)
