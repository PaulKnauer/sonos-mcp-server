"""Volume and mute MCP tools for SoniqMCP.

Exposes ``get_volume``, ``set_volume``, ``adjust_volume``, ``mute``,
``unmute``, and ``get_mute`` as thin handlers that delegate all logic
to ``VolumeService``. No SoCo calls here.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    RoomNotFoundError,
    SonosDiscoveryError,
    VolumeCapExceeded,
    VolumeError,
)
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import VolumeStateResponse

log = logging.getLogger(__name__)

_READ_ONLY_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_CONTROL_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, volume_service: object) -> None:
    """Register volume and mute tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        volume_service: A ``VolumeService`` instance (or compatible fake).
    """

    if "get_volume" not in config.tools_disabled:

        @app.tool(title="Get Volume", annotations=_READ_ONLY_TOOL_HINTS)
        def get_volume(room: str) -> dict:
            """Get the current volume and mute state for a Sonos room."""
            assert_tool_permitted("get_volume", config)
            try:
                state = volume_service.get_volume_state(room)
                return VolumeStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeError as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in get_volume: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "set_volume" not in config.tools_disabled:

        @app.tool(title="Set Volume", annotations=_CONTROL_TOOL_HINTS)
        def set_volume(room: str, volume: int) -> dict:
            """Set the volume for a Sonos room (0-100, capped by max_volume_pct)."""
            assert_tool_permitted("set_volume", config)
            try:
                volume_service.set_volume(room, volume)
                return {"status": "ok", "room": room, "volume": volume}
            except VolumeCapExceeded as exc:
                return ErrorResponse.from_volume_cap(exc.requested, exc.cap).model_dump()
            except (ValueError, VolumeError) as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in set_volume: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "adjust_volume" not in config.tools_disabled:

        @app.tool(title="Adjust Volume", annotations=_CONTROL_TOOL_HINTS)
        def adjust_volume(room: str, delta: int) -> dict:
            """Adjust volume by a relative amount for a Sonos room."""
            assert_tool_permitted("adjust_volume", config)
            try:
                state = volume_service.adjust_volume(room, delta)
                return VolumeStateResponse.from_domain(state).model_dump()
            except VolumeCapExceeded as exc:
                return ErrorResponse.from_volume_cap(exc.requested, exc.cap).model_dump()
            except VolumeError as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in adjust_volume: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "mute" not in config.tools_disabled:

        @app.tool(title="Mute", annotations=_CONTROL_TOOL_HINTS)
        def mute(room: str) -> dict:
            """Mute a Sonos room."""
            assert_tool_permitted("mute", config)
            try:
                volume_service.mute(room)
                return {"status": "ok", "room": room, "is_muted": True}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeError as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in mute: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "unmute" not in config.tools_disabled:

        @app.tool(title="Unmute", annotations=_CONTROL_TOOL_HINTS)
        def unmute(room: str) -> dict:
            """Unmute a Sonos room."""
            assert_tool_permitted("unmute", config)
            try:
                volume_service.unmute(room)
                return {"status": "ok", "room": room, "is_muted": False}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeError as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in unmute: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "get_mute" not in config.tools_disabled:

        @app.tool(title="Get Mute", annotations=_READ_ONLY_TOOL_HINTS)
        def get_mute(room: str) -> dict:
            """Get the current mute state for a Sonos room."""
            assert_tool_permitted("get_mute", config)
            try:
                state = volume_service.get_volume_state(room)
                return {"room": room, "is_muted": state.is_muted}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeError as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in get_mute: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
