"""Playback MCP tools for SoniqMCP.

Exposes play, pause, stop, next_track, previous_track, get_playback_state,
and get_track_info as thin handlers that delegate to ``PlaybackService``.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import PlaybackError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import PlaybackStateResponse, TrackInfoResponse

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


def register(app: FastMCP, config: SoniqConfig, playback_service: object) -> None:
    """Register playback tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        playback_service: A ``PlaybackService`` instance (or compatible fake).
    """

    if "play" not in config.tools_disabled:

        @app.tool(
            title="Play",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def play(room: str) -> dict:
            """Start or resume playback in the specified Sonos room."""
            assert_tool_permitted("play", config)
            try:
                playback_service.play(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in play: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in play: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "pause" not in config.tools_disabled:

        @app.tool(
            title="Pause",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def pause(room: str) -> dict:
            """Pause playback in the specified Sonos room."""
            assert_tool_permitted("pause", config)
            try:
                playback_service.pause(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in pause: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in pause: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "stop" not in config.tools_disabled:

        @app.tool(
            title="Stop",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def stop(room: str) -> dict:
            """Stop playback in the specified Sonos room."""
            assert_tool_permitted("stop", config)
            try:
                playback_service.stop(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in stop: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in stop: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "next_track" not in config.tools_disabled:

        @app.tool(
            title="Next Track",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def next_track(room: str) -> dict:
            """Skip to the next track in the specified Sonos room."""
            assert_tool_permitted("next_track", config)
            try:
                playback_service.next_track(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in next_track: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in next_track: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "previous_track" not in config.tools_disabled:

        @app.tool(
            title="Previous Track",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def previous_track(room: str) -> dict:
            """Return to the previous track in the specified Sonos room."""
            assert_tool_permitted("previous_track", config)
            try:
                playback_service.previous_track(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in previous_track: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in previous_track: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "get_playback_state" not in config.tools_disabled:

        @app.tool(
            title="Get Playback State",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_playback_state(room: str) -> dict:
            """Return the current transport state for the specified Sonos room."""
            assert_tool_permitted("get_playback_state", config)
            try:
                state = playback_service.get_playback_state(room)
                return PlaybackStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in get_playback_state: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_playback_state: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "get_track_info" not in config.tools_disabled:

        @app.tool(
            title="Get Track Info",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_track_info(room: str) -> dict:
            """Return current track details for the specified Sonos room."""
            assert_tool_permitted("get_track_info", config)
            try:
                info = playback_service.get_track_info(room)
                return TrackInfoResponse.from_domain(info, room_name=room).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in get_track_info: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_track_info: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
