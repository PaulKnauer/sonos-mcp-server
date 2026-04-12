"""Local music-library MCP tools for SoniqMCP."""

from __future__ import annotations

import logging
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import LibraryError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import LibraryBrowseResponse, LibraryPlaybackResponse

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


def register(app: FastMCP, config: SoniqConfig, library_service: object) -> None:
    """Register local music-library browse tools onto the FastMCP application."""

    if "browse_library" not in config.tools_disabled:

        @app.tool(title="Browse Music Library", annotations=_READ_ONLY_TOOL_HINTS)
        def browse_library(
            category: str,
            start: Annotated[object, Field(json_schema_extra={"type": "integer"})] = 0,
            limit: Annotated[object, Field(json_schema_extra={"type": "integer"})] = 100,
            parent_id: str | None = None,
        ) -> dict:
            """Browse a bounded slice of the local Sonos music library."""
            assert_tool_permitted("browse_library", config)
            try:
                result = library_service.browse_library(
                    category=category,
                    start=start,
                    limit=limit,
                    parent_id=parent_id,
                )
                return LibraryBrowseResponse.from_domain(**result).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in browse_library: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except LibraryError as exc:
                return ErrorResponse.from_library_error(exc).model_dump()

    if "play_library_item" not in config.tools_disabled:

        @app.tool(title="Play Library Item", annotations=_CONTROL_TOOL_HINTS)
        def play_library_item(
            room: str,
            title: Annotated[object, Field(json_schema_extra={"type": "string"})],
            uri: Annotated[object, Field(json_schema_extra={"type": "string"})],
            is_playable: Annotated[object, Field(json_schema_extra={"type": "boolean"})],
            item_id: Annotated[
                object,
                Field(json_schema_extra={"anyOf": [{"type": "string"}, {"type": "null"}]}),
            ] = None,
        ) -> dict:
            """Play a normalized local music-library selection in the specified room."""
            assert_tool_permitted("play_library_item", config)
            try:
                result = library_service.play_library_item(
                    room=room,
                    title=title,
                    uri=uri,
                    item_id=item_id,
                    is_playable=is_playable,
                )
                return LibraryPlaybackResponse.from_domain(
                    room=result["room"],
                    title=result["title"],
                    uri=result["uri"],
                    item_id=result.get("item_id"),
                ).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in play_library_item: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except LibraryError as exc:
                log.warning("Library error in play_library_item: %s", exc)
                return ErrorResponse.from_library_error(exc).model_dump()
