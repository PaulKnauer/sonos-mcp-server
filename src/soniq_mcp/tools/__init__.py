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
    from soniq_mcp.adapters.soco_adapter import SoCoAdapter
    from soniq_mcp.services.playback_service import PlaybackService
    from soniq_mcp.services.room_service import RoomService
    from soniq_mcp.services.sonos_service import SonosService
    from soniq_mcp.services.volume_service import VolumeService
    from soniq_mcp.tools.playback import register as register_playback
    from soniq_mcp.tools.setup_support import register as register_setup
    from soniq_mcp.tools.system import register as register_system
    from soniq_mcp.tools.volume import register as register_volume

    register_setup(app, config)

    room_service = RoomService(DiscoveryAdapter())
    register_system(app, config, room_service)

    sonos_service = SonosService(room_service, SoCoAdapter(), config)
    playback_service = PlaybackService(sonos_service=sonos_service)
    register_playback(app, config, playback_service)

    volume_service = VolumeService(sonos_service=sonos_service)
    register_volume(app, config, volume_service)
