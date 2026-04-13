"""Audio EQ MCP tools for SoniqMCP.

Exposes ``get_eq_settings``, ``set_bass``, ``set_treble``, and
``set_loudness`` as thin handlers that delegate all logic to
``AudioSettingsService``. No SoCo calls here.
"""

from __future__ import annotations

import logging
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    AudioSettingsError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import AudioSettingsResponse

log = logging.getLogger(__name__)

_INTEGER_INPUT = Annotated[object, Field(json_schema_extra={"type": "integer"})]
_BOOLEAN_INPUT = Annotated[object, Field(json_schema_extra={"type": "boolean"})]

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


def register(app: FastMCP, config: SoniqConfig, audio_settings_service: object) -> None:
    """Register audio EQ tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        audio_settings_service: An ``AudioSettingsService`` instance (or compatible fake).
    """

    if "get_eq_settings" not in config.tools_disabled:

        @app.tool(title="Get EQ Settings", annotations=_READ_ONLY_TOOL_HINTS)
        def get_eq_settings(room: str) -> dict:
            """Get the current bass, treble, and loudness EQ settings for a Sonos room."""
            assert_tool_permitted("get_eq_settings", config)
            try:
                state = audio_settings_service.get_audio_settings(room)
                return AudioSettingsResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except AudioSettingsError as exc:
                return ErrorResponse.from_audio_settings_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in get_eq_settings: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in get_eq_settings")
                return ErrorResponse.from_internal_error(exc, field="audio_settings").model_dump()

    if "set_bass" not in config.tools_disabled:

        @app.tool(title="Set Bass", annotations=_CONTROL_TOOL_HINTS)
        def set_bass(room: str, level: _INTEGER_INPUT) -> dict:
            """Set the bass level (-10 to 10) for a Sonos room."""
            assert_tool_permitted("set_bass", config)
            try:
                state = audio_settings_service.set_bass(room, level)
                return AudioSettingsResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except AudioSettingsError as exc:
                return ErrorResponse.from_audio_settings_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in set_bass: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in set_bass")
                return ErrorResponse.from_internal_error(exc, field="audio_settings").model_dump()

    if "set_treble" not in config.tools_disabled:

        @app.tool(title="Set Treble", annotations=_CONTROL_TOOL_HINTS)
        def set_treble(room: str, level: _INTEGER_INPUT) -> dict:
            """Set the treble level (-10 to 10) for a Sonos room."""
            assert_tool_permitted("set_treble", config)
            try:
                state = audio_settings_service.set_treble(room, level)
                return AudioSettingsResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except AudioSettingsError as exc:
                return ErrorResponse.from_audio_settings_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in set_treble: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in set_treble")
                return ErrorResponse.from_internal_error(exc, field="audio_settings").model_dump()

    if "set_loudness" not in config.tools_disabled:

        @app.tool(title="Set Loudness", annotations=_CONTROL_TOOL_HINTS)
        def set_loudness(room: str, enabled: _BOOLEAN_INPUT) -> dict:
            """Enable or disable loudness compensation for a Sonos room."""
            assert_tool_permitted("set_loudness", config)
            try:
                state = audio_settings_service.set_loudness(room, enabled)
                return AudioSettingsResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except AudioSettingsError as exc:
                return ErrorResponse.from_audio_settings_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in set_loudness: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in set_loudness")
                return ErrorResponse.from_internal_error(exc, field="audio_settings").model_dump()
