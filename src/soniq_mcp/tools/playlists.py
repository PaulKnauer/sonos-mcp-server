"""Playlists MCP tools for SoniqMCP.

Exposes playlist inventory, playback, and lifecycle tools that delegate
to ``PlaylistService``.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    PlaylistError,
    PlaylistValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import (
    PlaylistDeleteResponse,
    PlaylistPlaybackResponse,
    PlaylistResponse,
    PlaylistsListResponse,
)

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

_DESTRUCTIVE_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, playlist_service: object) -> None:
    """Register playlists tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        playlist_service: A ``PlaylistService`` instance (or compatible fake).
    """

    if "list_playlists" not in config.tools_disabled:

        @app.tool(title="List Playlists", annotations=_READ_ONLY_TOOL_HINTS)
        def list_playlists() -> dict:
            """Return all Sonos playlists in the household.

            Each playlist entry includes a stable ``item_id`` that can be used
            as the ``playlist_id`` argument for lifecycle operations such as
            ``update_playlist`` and ``delete_playlist``.
            """
            assert_tool_permitted("list_playlists", config)
            try:
                items = playlist_service.list_playlists()
                return PlaylistsListResponse.from_domain(items).model_dump()
            except PlaylistError as exc:
                log.warning("Playlist error in list_playlists: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in list_playlists: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in list_playlists")
                return ErrorResponse.from_internal_error(exc, field="playlist").model_dump()

    if "play_playlist" not in config.tools_disabled:

        @app.tool(title="Play Playlist", annotations=_CONTROL_TOOL_HINTS)
        def play_playlist(room: str, uri: str) -> dict:
            """Play a Sonos playlist by URI in the specified room.

            Args:
                room: Name of the target room (use ``list_rooms`` for valid names).
                uri: Content URI of the playlist (from ``list_playlists``).
            """
            assert_tool_permitted("play_playlist", config)
            try:
                playlist_service.play_playlist(room, uri)
                return PlaylistPlaybackResponse(room=room, uri=uri).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaylistError as exc:
                log.warning("Playlist error in play_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in play_playlist: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in play_playlist")
                return ErrorResponse.from_internal_error(exc, field="playlist").model_dump()

    if "create_playlist" not in config.tools_disabled:

        @app.tool(title="Create Playlist", annotations=_CONTROL_TOOL_HINTS)
        def create_playlist(title: str) -> dict:
            """Create a new empty Sonos playlist with the given title.

            Args:
                title: Title for the new playlist. Must not be empty.

            Returns a ``PlaylistResponse`` with the new playlist's ``item_id``,
            ``title``, and ``uri``.
            """
            assert_tool_permitted("create_playlist", config)
            try:
                result = playlist_service.create_playlist(title)
                return PlaylistResponse.from_domain(result).model_dump()
            except PlaylistValidationError as exc:
                log.warning("Validation error in create_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except PlaylistError as exc:
                log.warning("Playlist error in create_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in create_playlist: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in create_playlist")
                return ErrorResponse.from_internal_error(exc, field="playlist").model_dump()

    if "update_playlist" not in config.tools_disabled:

        @app.tool(title="Update Playlist", annotations=_CONTROL_TOOL_HINTS)
        def update_playlist(playlist_id: str, room: str) -> dict:
            """Replace a playlist's contents with the current queue from a room.

            The specified room's active playback queue replaces all existing
            tracks in the playlist. The queue must be non-empty before calling
            this tool. Playlist title and ``item_id`` are preserved.

            Args:
                playlist_id: The ``item_id`` of the target playlist
                    (from ``list_playlists``).
                room: Name of the room whose queue provides the new content
                    (use ``list_rooms`` for valid names).
            """
            assert_tool_permitted("update_playlist", config)
            try:
                result = playlist_service.update_playlist(playlist_id, room)
                return PlaylistResponse.from_domain(result).model_dump()
            except PlaylistValidationError as exc:
                log.warning("Validation error in update_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except PlaylistError as exc:
                log.warning("Playlist error in update_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in update_playlist: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in update_playlist")
                return ErrorResponse.from_internal_error(exc, field="playlist").model_dump()

    if "delete_playlist" not in config.tools_disabled:

        @app.tool(title="Delete Playlist", annotations=_DESTRUCTIVE_TOOL_HINTS)
        def delete_playlist(playlist_id: str) -> dict:
            """Permanently delete a Sonos playlist.

            This operation is irreversible. The playlist and all its contents
            will be removed from the Sonos household.

            Args:
                playlist_id: The ``item_id`` of the playlist to delete
                    (from ``list_playlists``).
            """
            assert_tool_permitted("delete_playlist", config)
            try:
                result = playlist_service.delete_playlist(playlist_id)
                return PlaylistDeleteResponse(
                    playlist_id=result["playlist_id"],
                    status=result["status"],
                ).model_dump()
            except PlaylistValidationError as exc:
                log.warning("Validation error in delete_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except PlaylistError as exc:
                log.warning("Playlist error in delete_playlist: %s", exc)
                return ErrorResponse.from_playlist_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in delete_playlist: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in delete_playlist")
                return ErrorResponse.from_internal_error(exc, field="playlist").model_dump()
