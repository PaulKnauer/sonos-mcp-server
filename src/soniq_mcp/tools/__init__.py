"""Tools package for SoniqMCP.

Each module exposes a ``register(app, config)`` function that registers
its tools onto the FastMCP application. Sonos-specific tools arrive
in Story 2+.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig


def register_all(app: FastMCP, config: SoniqConfig) -> None:
    """Register all available tools, respecting tools_disabled."""
    from soniq_mcp.adapters.discovery_adapter import DiscoveryAdapter
    from soniq_mcp.services.room_service import RoomService
    from soniq_mcp.tools.setup_support import register as register_setup
    from soniq_mcp.tools.system import register as register_system

    register_setup(app, config)

    room_service = RoomService(DiscoveryAdapter())
    register_system(app, config, room_service)
