"""Group management MCP tools for SoniqMCP.

Exposes get_group_topology, join_group, unjoin_room, and party_mode as
thin handlers that delegate to GroupService.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import GroupError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import GroupTopologyResponse

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


def register(app: FastMCP, config: SoniqConfig, group_service: object) -> None:
    """Register grouping tools onto the FastMCP application."""

    if "get_group_topology" not in config.tools_disabled:

        @app.tool(
            title="Get Group Topology",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_group_topology() -> dict:
            """Return the current Sonos room grouping topology."""
            assert_tool_permitted("get_group_topology", config)
            try:
                rooms = group_service.get_group_topology()
                return GroupTopologyResponse.from_rooms(rooms).model_dump()
            except GroupError as exc:
                log.warning("Group error in get_group_topology: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_group_topology: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "join_group" not in config.tools_disabled:

        @app.tool(
            title="Join Group",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def join_group(room: str, coordinator: str) -> dict:
            """Add a room to the group coordinated by another room."""
            assert_tool_permitted("join_group", config)
            try:
                group_service.join_group(room, coordinator)
                return {"status": "ok", "room": room, "coordinator": coordinator}
            except RoomNotFoundError as exc:
                return ErrorResponse.from_room_not_found(exc.room_name).model_dump()
            except GroupError as exc:
                log.warning("Group error in join_group: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in join_group: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "unjoin_room" not in config.tools_disabled:

        @app.tool(
            title="Unjoin Room",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def unjoin_room(room: str) -> dict:
            """Remove a room from its current group so it plays independently."""
            assert_tool_permitted("unjoin_room", config)
            try:
                group_service.unjoin_room(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except GroupError as exc:
                log.warning("Group error in unjoin_room: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in unjoin_room: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "party_mode" not in config.tools_disabled:

        @app.tool(
            title="Party Mode",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def party_mode() -> dict:
            """Join all Sonos rooms into a single whole-home group."""
            assert_tool_permitted("party_mode", config)
            try:
                group_service.party_mode()
                return {"status": "ok"}
            except GroupError as exc:
                log.warning("Group error in party_mode: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in party_mode: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
