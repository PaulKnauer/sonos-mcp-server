"""PlaylistService — orchestrates Sonos playlist lifecycle operations."""

from __future__ import annotations

from soniq_mcp.domain.exceptions import (
    PlaylistValidationError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import SonosPlaylist


def _validate_playlist_id(value: str) -> str:
    """Return a validated non-empty playlist identifier.

    Raises:
        PlaylistValidationError: If the value is blank or not a string.
    """
    if not isinstance(value, str):
        raise PlaylistValidationError("Invalid playlist_id. Expected a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise PlaylistValidationError("Invalid playlist_id. Expected a non-empty string.")
    return normalized


def _validate_title(value: str) -> str:
    """Return a validated non-empty playlist title.

    Raises:
        PlaylistValidationError: If the title is blank or whitespace-only.
    """
    if not isinstance(value, str):
        raise PlaylistValidationError("Invalid title. Expected a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise PlaylistValidationError(
            "Invalid title. Playlist title must not be empty or whitespace-only."
        )
    return normalized


class PlaylistService:
    """Orchestrates Sonos playlist inventory, playback, and lifecycle operations.

    Owns validation, household reachability checks, and lifecycle orchestration.
    All SoCo interaction is delegated to the adapter.

    Args:
        room_service: A ``RoomService`` instance for room/IP resolution.
        adapter: A ``SoCoAdapter`` instance for SoCo operations.
    """

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def list_playlists(self) -> list[SonosPlaylist]:
        """Return all Sonos playlists in the household.

        Raises:
            PlaylistError: If the adapter call fails.
            SonosDiscoveryError: If no rooms are reachable.
        """
        ip = self._get_any_ip()
        return self._adapter.get_playlists(ip)

    def play_playlist(self, room_name: str, uri: str) -> None:
        """Play a playlist by URI in the specified room.

        Args:
            room_name: Human-readable room name.
            uri: Content URI of the playlist.

        Raises:
            RoomNotFoundError: If the room is not found.
            PlaylistError: If the play operation fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._room_service.get_room(room_name)
        self._adapter.play_playlist(room.ip_address, uri)

    def create_playlist(self, title: str) -> SonosPlaylist:
        """Create a new Sonos playlist with the given title.

        Args:
            title: Title for the new playlist. Must not be empty.

        Returns:
            Normalized ``SonosPlaylist`` for the newly created playlist.

        Raises:
            PlaylistValidationError: If the title is blank.
            PlaylistError: If the adapter call fails.
            SonosDiscoveryError: If no rooms are reachable.
        """
        normalized_title = _validate_title(title)
        ip = self._get_any_ip()
        return self._adapter.create_playlist(ip, normalized_title)

    def rename_playlist(self, playlist_id: str, title: str) -> SonosPlaylist:
        """Rename an existing Sonos playlist.

        Args:
            playlist_id: ``item_id`` of the target playlist.
            title: New title. Must not be empty.

        Returns:
            Normalized ``SonosPlaylist`` reflecting the renamed playlist.

        Raises:
            PlaylistValidationError: If the id is blank, title is blank, or
                the playlist is not found.
            PlaylistUnsupportedOperationError: If rename is not supported by
                the current SoCo API version.
            PlaylistError: If the adapter call fails.
        """
        normalized_id = _validate_playlist_id(playlist_id)
        normalized_title = _validate_title(title)
        ip = self._get_any_ip()
        self._ensure_playlist_exists(normalized_id, ip)
        return self._adapter.rename_playlist(ip, normalized_id, normalized_title)

    def update_playlist(self, playlist_id: str, room: str) -> SonosPlaylist:
        """Replace a playlist's contents with the current queue from the given room.

        The source room's active queue must be non-empty before the update is
        applied. Playlist metadata (title, item_id) is preserved; only the
        content changes.

        Args:
            playlist_id: ``item_id`` of the target playlist.
            room: Source room whose queue provides new playlist content.

        Returns:
            Normalized ``SonosPlaylist`` reflecting the updated playlist.

        Raises:
            PlaylistValidationError: If the id is blank, the playlist is not
                found, the room does not exist, or the queue is empty.
            PlaylistError: If the adapter call fails.
        """
        normalized_id = _validate_playlist_id(playlist_id)
        ip = self._get_any_ip()
        self._ensure_playlist_exists(normalized_id, ip)
        room_obj = self._room_service.get_room(room)
        return self._adapter.update_playlist(ip, normalized_id, room_obj.ip_address)

    def delete_playlist(self, playlist_id: str) -> dict:
        """Delete a Sonos playlist by item_id.

        Args:
            playlist_id: ``item_id`` of the playlist to delete.

        Returns:
            Structured confirmation with ``playlist_id`` and ``status``.

        Raises:
            PlaylistValidationError: If the id is blank or the playlist is
                not found.
            PlaylistError: If the adapter call fails.
            SonosDiscoveryError: If no rooms are reachable.
        """
        normalized_id = _validate_playlist_id(playlist_id)
        ip = self._get_any_ip()
        self._ensure_playlist_exists(normalized_id, ip)
        self._adapter.delete_playlist(ip, normalized_id)
        return {"playlist_id": normalized_id, "status": "deleted"}

    def _get_any_ip(self) -> str:
        """Return a reachable room IP for household-wide playlist operations."""
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise SonosDiscoveryError("No Sonos rooms found — cannot access playlists.")
        return rooms[0].ip_address

    def _ensure_playlist_exists(self, playlist_id: str, ip: str) -> None:
        """Raise a validation error when the playlist identifier is unknown."""
        playlists = self._adapter.get_playlists(ip)
        if any(
            p.item_id == playlist_id or (p.item_id is None and p.title == playlist_id)
            for p in playlists
        ):
            return
        raise PlaylistValidationError(
            f"Playlist '{playlist_id}' was not found. "
            "Use 'list_playlists' to see available playlists and their IDs."
        )
