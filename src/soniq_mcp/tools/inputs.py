"""Input-switching MCP tools for SoniqMCP."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import InputError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import InputStateResponse

log = logging.getLogger(__name__)

_CONTROL_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, input_service: object) -> None:
    """Register input-switching tools onto the FastMCP application."""

    if "switch_to_line_in" not in config.tools_disabled:

        @app.tool(title="Switch to Line-In", annotations=_CONTROL_TOOL_HINTS)
        def switch_to_line_in(room: str) -> dict:
            """Switch a supported Sonos room to its line-in input."""
            assert_tool_permitted("switch_to_line_in", config)
            try:
                state = input_service.switch_to_line_in(room)
                return InputStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except InputError as exc:
                return ErrorResponse.from_input_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in switch_to_line_in: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in switch_to_line_in")
                return ErrorResponse.from_internal_error(exc, field="input_source").model_dump()

    if "switch_to_tv" not in config.tools_disabled:

        @app.tool(title="Switch to TV", annotations=_CONTROL_TOOL_HINTS)
        def switch_to_tv(room: str) -> dict:
            """Switch a supported Sonos room to its TV input."""
            assert_tool_permitted("switch_to_tv", config)
            try:
                state = input_service.switch_to_tv(room)
                return InputStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except InputError as exc:
                return ErrorResponse.from_input_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in switch_to_tv: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in switch_to_tv")
                return ErrorResponse.from_internal_error(exc, field="input_source").model_dump()
