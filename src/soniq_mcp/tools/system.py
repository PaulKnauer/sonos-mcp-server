"""System-level MCP tools for SoniqMCP.

Exposes ``list_rooms`` and ``get_system_topology`` as thin handlers that
delegate all logic to ``RoomService``. No SoCo calls here.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import RoomListResponse, SystemTopologyResponse

log = logging.getLogger(__name__)

_READ_ONLY_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, room_service: object) -> None:
    """Register system tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        room_service: A ``RoomService`` instance (or compatible fake).
    """

    if "list_rooms" not in config.tools_disabled:

        @app.tool(
            title="List Rooms",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def list_rooms() -> dict:
            """List all available Sonos rooms that the server can control."""
            assert_tool_permitted("list_rooms", config)
            try:
                rooms = room_service.list_rooms()
                return RoomListResponse.from_domain(rooms).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Room discovery failed: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "get_system_topology" not in config.tools_disabled:

        @app.tool(
            title="Get System Topology",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_system_topology() -> dict:
            """Return system-level Sonos room and speaker topology."""
            assert_tool_permitted("get_system_topology", config)
            try:
                topology = room_service.get_topology()
                return SystemTopologyResponse.from_domain(topology).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Topology discovery failed: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
