"""Favourites MCP tools for SoniqMCP.

Exposes list_favourites and play_favourite as tool handlers that delegate
to ``FavouritesService``.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import FavouritesError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import FavouritesListResponse

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


def register(app: FastMCP, config: SoniqConfig, favourites_service: object) -> None:
    """Register favourites tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        favourites_service: A ``FavouritesService`` instance (or compatible fake).
    """

    if "list_favourites" not in config.tools_disabled:

        @app.tool(title="List Favourites", annotations=_READ_ONLY_TOOL_HINTS)
        def list_favourites() -> dict:
            """Return all Sonos favourites in the household."""
            assert_tool_permitted("list_favourites", config)
            try:
                items = favourites_service.get_favourites()
                return FavouritesListResponse.from_domain(items).model_dump()
            except FavouritesError as exc:
                log.warning("Favourites error in list_favourites: %s", exc)
                return ErrorResponse.from_favourites_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in list_favourites: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "play_favourite" not in config.tools_disabled:

        @app.tool(title="Play Favourite", annotations=_CONTROL_TOOL_HINTS)
        def play_favourite(room: str, uri: str) -> dict:
            """Play a Sonos favourite by URI in the specified room."""
            assert_tool_permitted("play_favourite", config)
            try:
                favourites_service.play_favourite(room, uri, meta=None)
                return {"status": "ok", "room": room, "uri": uri}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except FavouritesError as exc:
                log.warning("Favourites error in play_favourite: %s", exc)
                return ErrorResponse.from_favourites_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in play_favourite: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
