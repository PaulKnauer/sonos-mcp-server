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
    from soniq_mcp.adapters.playback_adapter import PlaybackAdapter
    from soniq_mcp.adapters.volume_adapter import VolumeAdapter
    from soniq_mcp.services.playback_service import PlaybackService
    from soniq_mcp.services.room_service import RoomService
    from soniq_mcp.services.volume_service import VolumeService
    from soniq_mcp.tools.playback import register as register_playback
    from soniq_mcp.tools.setup_support import register as register_setup
    from soniq_mcp.tools.system import register as register_system
    from soniq_mcp.tools.volume import register as register_volume

    register_setup(app, config)

    room_service = RoomService(DiscoveryAdapter())
    register_system(app, config, room_service)

    playback_service = PlaybackService(room_service, PlaybackAdapter())
    register_playback(app, config, playback_service)

    volume_adapter = VolumeAdapter()
    volume_service = VolumeService(room_service, volume_adapter, config)
    register_volume(app, config, volume_service)
