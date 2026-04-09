"""Play mode MCP tools for SoniqMCP.

Exposes get_play_mode and set_play_mode as thin handlers that delegate
to ``PlayModeService``. Play mode covers shuffle, repeat, and crossfade.
"""

from __future__ import annotations

import logging
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    PlaybackError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import PlayModeResponse

log = logging.getLogger(__name__)

_OPTIONAL_BOOLEAN_INPUT = Annotated[
    object,
    Field(json_schema_extra={"anyOf": [{"type": "boolean"}, {"type": "null"}]}),
]
_OPTIONAL_REPEAT_INPUT = Annotated[
    object,
    Field(
        json_schema_extra={
            "anyOf": [
                {"type": "string", "enum": ["none", "all", "one"]},
                {"type": "null"},
            ]
        }
    ),
]

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


def register(app: FastMCP, config: SoniqConfig, play_mode_service: object) -> None:
    """Register play mode tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        play_mode_service: A ``PlayModeService`` instance (or compatible fake).
    """

    if "get_play_mode" not in config.tools_disabled:

        @app.tool(
            title="Get Play Mode",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_play_mode(room: str) -> dict:
            """Return the current shuffle, repeat, and crossfade settings."""
            assert_tool_permitted("get_play_mode", config)
            try:
                state = play_mode_service.get_play_mode(room)
                return PlayModeResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in get_play_mode: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_play_mode: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "set_play_mode" not in config.tools_disabled:

        @app.tool(
            title="Set Play Mode",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def set_play_mode(
            room: str,
            shuffle: _OPTIONAL_BOOLEAN_INPUT = None,
            repeat: _OPTIONAL_REPEAT_INPUT = None,
            cross_fade: _OPTIONAL_BOOLEAN_INPUT = None,
        ) -> dict:
            """Set shuffle, repeat, and/or crossfade for the specified Sonos room.

            Provide only the fields you want to change; omitted fields are preserved.
            repeat must be one of: "none", "all", "one".
            """
            assert_tool_permitted("set_play_mode", config)
            try:
                state = play_mode_service.set_play_mode(
                    room,
                    shuffle=shuffle,
                    repeat=repeat,
                    cross_fade=cross_fade,
                )
                return PlayModeResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                log.warning("Playback error in set_play_mode: %s", exc)
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in set_play_mode: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
