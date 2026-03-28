"""FavouritesService — orchestrates favourites and playlists operations."""

from __future__ import annotations

from soniq_mcp.domain.exceptions import FavouritesError
from soniq_mcp.domain.models import Favourite, SonosPlaylist


class FavouritesService:
    """Orchestrates Sonos favourites and playlists operations.

    Args:
        room_service: A ``RoomService`` instance for room/IP resolution.
        adapter: A ``SoCoAdapter`` instance for SoCo operations.
    """

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def _get_any_ip(self) -> str:
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise FavouritesError("No Sonos rooms found — cannot fetch favourites/playlists")
        return rooms[0].ip_address

    def _lookup_favourite_meta(self, ip_address: str, uri: str) -> str | None:
        for favourite in self._adapter.get_favourites(ip_address):
            if favourite.uri == uri:
                return favourite.meta
        return None

    def get_favourites(self) -> list[Favourite]:
        """Return all saved Sonos favourites for the household.

        Raises:
            FavouritesError: If no rooms are reachable or the operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        ip = self._get_any_ip()
        return self._adapter.get_favourites(ip)

    def play_favourite(self, room_name: str, uri: str, meta: str | None) -> None:
        """Play a favourite in the specified room.

        Args:
            room_name: Human-readable room name.
            uri: Content URI of the favourite.
            meta: Optional DIDL-Lite XML metadata string.

        Raises:
            RoomNotFoundError: If the room is not found.
            FavouritesError: If the play operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._room_service.get_room(room_name)
        resolved_meta = meta
        if resolved_meta is None:
            resolved_meta = self._lookup_favourite_meta(room.ip_address, uri)
        self._adapter.play_favourite(room.ip_address, uri, resolved_meta)

    def get_playlists(self) -> list[SonosPlaylist]:
        """Return all saved Sonos playlists for the household.

        Raises:
            FavouritesError: If no rooms are reachable or the operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        ip = self._get_any_ip()
        return self._adapter.get_playlists(ip)

    def play_playlist(self, room_name: str, uri: str) -> None:
        """Play a playlist in the specified room.

        Args:
            room_name: Human-readable room name.
            uri: Content URI of the playlist.

        Raises:
            RoomNotFoundError: If the room is not found.
            FavouritesError: If the play operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._room_service.get_room(room_name)
        self._adapter.play_playlist(room.ip_address, uri)
