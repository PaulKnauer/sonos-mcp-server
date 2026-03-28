"""Playlists MCP tools for SoniqMCP.

Exposes list_playlists and play_playlist as tool handlers that delegate
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
from soniq_mcp.schemas.responses import PlaylistsListResponse

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
    """Register playlists tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        favourites_service: A ``FavouritesService`` instance (or compatible fake).
    """

    if "list_playlists" not in config.tools_disabled:

        @app.tool(title="List Playlists", annotations=_READ_ONLY_TOOL_HINTS)
        def list_playlists() -> dict:
            """Return all Sonos playlists in the household."""
            assert_tool_permitted("list_playlists", config)
            try:
                items = favourites_service.get_playlists()
                return PlaylistsListResponse.from_domain(items).model_dump()
            except FavouritesError as exc:
                log.warning("Favourites error in list_playlists: %s", exc)
                return ErrorResponse.from_favourites_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in list_playlists: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "play_playlist" not in config.tools_disabled:

        @app.tool(title="Play Playlist", annotations=_CONTROL_TOOL_HINTS)
        def play_playlist(room: str, uri: str) -> dict:
            """Play a Sonos playlist by URI in the specified room."""
            assert_tool_permitted("play_playlist", config)
            try:
                favourites_service.play_playlist(room, uri)
                return {"status": "ok", "room": room, "uri": uri}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except FavouritesError as exc:
                log.warning("Favourites error in play_playlist: %s", exc)
                return ErrorResponse.from_favourites_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in play_playlist: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
