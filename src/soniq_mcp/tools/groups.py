"""Group management MCP tools for SoniqMCP.

Exposes get_group_topology, join_group, unjoin_room, and party_mode as
thin handlers that delegate to GroupService.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    GroupError,
    GroupValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
    VolumeCapExceeded,
)
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import GroupAudioStateResponse, GroupTopologyResponse

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

    if "get_group_volume" not in config.tools_disabled:

        @app.tool(
            title="Get Group Volume",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_group_volume(room: str) -> dict:
            """Return the current group volume and mute state for the active group."""
            assert_tool_permitted("get_group_volume", config)
            try:
                state = group_service.get_group_audio_state(room)
                return GroupAudioStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except GroupValidationError as exc:
                return ErrorResponse.from_group_error(exc).model_dump()
            except GroupError as exc:
                log.warning("Group error in get_group_volume: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_group_volume: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "set_group_volume" not in config.tools_disabled:

        @app.tool(
            title="Set Group Volume",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def set_group_volume(room: str, volume: int) -> dict:
            """Set the group volume to an absolute level for the active group."""
            assert_tool_permitted("set_group_volume", config)
            try:
                state = group_service.set_group_volume(room, volume)
                return GroupAudioStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeCapExceeded as exc:
                return ErrorResponse.from_volume_cap(exc.requested, exc.cap).model_dump()
            except GroupValidationError as exc:
                return ErrorResponse.from_group_error(exc).model_dump()
            except GroupError as exc:
                log.warning("Group error in set_group_volume: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in set_group_volume: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "adjust_group_volume" not in config.tools_disabled:

        @app.tool(
            title="Adjust Group Volume",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def adjust_group_volume(room: str, delta: int) -> dict:
            """Adjust the group volume by a relative amount for the active group."""
            assert_tool_permitted("adjust_group_volume", config)
            try:
                state = group_service.adjust_group_volume(room, delta)
                return GroupAudioStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeCapExceeded as exc:
                return ErrorResponse.from_volume_cap(exc.requested, exc.cap).model_dump()
            except GroupValidationError as exc:
                return ErrorResponse.from_group_error(exc).model_dump()
            except GroupError as exc:
                log.warning("Group error in adjust_group_volume: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in adjust_group_volume: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "group_mute" not in config.tools_disabled:

        @app.tool(
            title="Group Mute",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def group_mute(room: str) -> dict:
            """Mute the active Sonos group that contains the specified room."""
            assert_tool_permitted("group_mute", config)
            try:
                state = group_service.group_mute(room)
                return GroupAudioStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except GroupValidationError as exc:
                return ErrorResponse.from_group_error(exc).model_dump()
            except GroupError as exc:
                log.warning("Group error in group_mute: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in group_mute: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "group_unmute" not in config.tools_disabled:

        @app.tool(
            title="Group Unmute",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def group_unmute(room: str) -> dict:
            """Unmute the active Sonos group that contains the specified room."""
            assert_tool_permitted("group_unmute", config)
            try:
                state = group_service.group_unmute(room)
                return GroupAudioStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except GroupValidationError as exc:
                return ErrorResponse.from_group_error(exc).model_dump()
            except GroupError as exc:
                log.warning("Group error in group_unmute: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in group_unmute: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "group_rooms" not in config.tools_disabled:

        @app.tool(
            title="Group Rooms",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def group_rooms(rooms: list[str], coordinator: str | None = None) -> dict:
            """Group an explicit set of rooms together, with an optional coordinator.

            Resolves the requested rooms from the current household topology,
            validates the room set, and applies the grouping. Returns the resulting
            normalized group topology.
            """
            assert_tool_permitted("group_rooms", config)
            try:
                result_rooms = group_service.group_rooms(rooms, coordinator)
                return GroupTopologyResponse.from_rooms(result_rooms).model_dump()
            except GroupValidationError as exc:
                return ErrorResponse.from_group_error(exc).model_dump()
            except RoomNotFoundError as exc:
                return ErrorResponse.from_room_not_found(exc.room_name).model_dump()
            except GroupError as exc:
                log.warning("Group error in group_rooms: %s", exc)
                return ErrorResponse.from_group_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in group_rooms: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
