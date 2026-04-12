"""Shared SoCo adapter for core Sonos operations.

This module is the shared by-IP Sonos integration boundary used by
playback and volume capability layers. Higher layers must not import
``soco`` directly.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Any, Literal

from soniq_mcp.domain.exceptions import (
    AlarmError,
    AudioSettingsError,
    FavouritesError,
    GroupError,
    InputError,
    LibraryError,
    PlaybackError,
    PlaylistError,
    PlaylistUnsupportedOperationError,
    PlaylistValidationError,
    QueueError,
    SonosDiscoveryError,
    VolumeError,
)
from soniq_mcp.domain.models import (
    AlarmRecord,
    AudioSettingsState,
    Favourite,
    LibraryItem,
    PlaybackState,
    PlayModeState,
    QueueItem,
    SleepTimerState,
    SonosPlaylist,
    TrackInfo,
)

RepeatMode = Literal["none", "all", "one"]

# Maps SoCo play_mode strings to (repeat, shuffle) domain values.
_SOCO_TO_DOMAIN: dict[str, tuple[RepeatMode, bool]] = {
    "NORMAL": ("none", False),
    "REPEAT_ALL": ("all", False),
    "REPEAT_ONE": ("one", False),
    "SHUFFLE_NOREPEAT": ("none", True),
    "SHUFFLE": ("all", True),
    "SHUFFLE_REPEAT_ONE": ("one", True),
}

# Maps (repeat, shuffle) domain values to SoCo play_mode strings.
_DOMAIN_TO_SOCO: dict[tuple[RepeatMode, bool], str] = {v: k for k, v in _SOCO_TO_DOMAIN.items()}

_EMPTY_SENTINELS = {"", "NOT_IMPLEMENTED"}


def _coerce_str(val: object) -> str | None:
    """Return None if val is empty/sentinel; else strip and return."""
    if not isinstance(val, str):
        return None
    stripped = val.strip()
    if stripped in _EMPTY_SENTINELS:
        return None
    return stripped


def _coerce_queue_position(val: object) -> int | None:
    """Return a positive queue position integer or None."""
    if isinstance(val, str):
        val = val.strip()
        if not val:
            return None
        try:
            parsed = int(val)
        except ValueError:
            return None
        return parsed if parsed > 0 else None
    if isinstance(val, int):
        return val if val > 0 else None
    return None


def _decode_play_mode(play_mode: object) -> tuple[RepeatMode, bool]:
    """Normalize a SoCo play_mode value into domain repeat/shuffle state."""
    normalized = str(play_mode).upper()
    decoded = _SOCO_TO_DOMAIN.get(normalized)
    if decoded is None:
        raise PlaybackError(f"Unsupported Sonos play_mode value {normalized!r}.")
    return decoded


class SoCoAdapter:
    """Shared wrapper around ``soco.SoCo(ip_address)`` operations."""

    def play(self, ip_address: str) -> None:
        self._call_playback(ip_address, lambda zone: zone.play())

    def pause(self, ip_address: str) -> None:
        self._call_playback(ip_address, lambda zone: zone.pause())

    def stop(self, ip_address: str) -> None:
        self._call_playback(ip_address, lambda zone: zone.stop())

    def next_track(self, ip_address: str) -> None:
        self._call_playback(ip_address, lambda zone: zone.next())

    def previous_track(self, ip_address: str) -> None:
        self._call_playback(ip_address, lambda zone: zone.previous())

    def get_playback_state(self, ip_address: str, room_name: str) -> PlaybackState:
        try:
            zone = self._make_zone(ip_address)
            info = zone.get_current_transport_info()
            return PlaybackState(
                transport_state=str(info.get("current_transport_state", "STOPPED")),
                room_name=room_name,
            )
        except Exception as exc:
            raise PlaybackError(f"Failed to get playback state for {room_name!r}: {exc}") from exc

    def get_track_info(self, ip_address: str) -> TrackInfo:
        try:
            zone = self._make_zone(ip_address)
            raw = zone.get_current_track_info()
            return TrackInfo(
                title=_coerce_str(raw.get("title")),
                artist=_coerce_str(raw.get("artist")),
                album=_coerce_str(raw.get("album")),
                duration=_coerce_str(raw.get("duration")),
                position=_coerce_str(raw.get("position")),
                uri=_coerce_str(raw.get("uri")),
                album_art_uri=_coerce_str(raw.get("album_art")),
                queue_position=_coerce_queue_position(raw.get("playlist_position")),
            )
        except Exception as exc:
            raise PlaybackError(f"Failed to get track info: {exc}") from exc

    def get_volume(self, ip_address: str) -> int:
        try:
            zone = self._make_zone(ip_address)
            return zone.volume
        except Exception as exc:
            raise VolumeError(f"Failed to get volume from {ip_address}: {exc}") from exc

    def set_volume(self, ip_address: str, volume: int) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.volume = volume
        except Exception as exc:
            raise VolumeError(f"Failed to set volume on {ip_address}: {exc}") from exc

    def get_mute(self, ip_address: str) -> bool:
        try:
            zone = self._make_zone(ip_address)
            return zone.mute
        except Exception as exc:
            raise VolumeError(f"Failed to get mute state from {ip_address}: {exc}") from exc

    def set_mute(self, ip_address: str, muted: bool) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.mute = muted
        except Exception as exc:
            raise VolumeError(f"Failed to set mute on {ip_address}: {exc}") from exc

    def get_favourites(self, ip_address: str) -> list[Favourite]:
        try:
            zone = self._make_zone(ip_address)
            results = zone.music_library.get_sonos_favorites()
            favourites = []
            for item in results:
                meta = getattr(item, "to_didl_string", lambda: "")()
                favourites.append(Favourite(title=item.title, uri=item.uri, meta=meta or None))
            return favourites
        except Exception as exc:
            raise FavouritesError(f"Failed to get favourites: {exc}") from exc

    def play_favourite(self, ip_address: str, uri: str, meta: str | None) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.play_uri(uri=uri, meta=meta or "")
        except Exception as exc:
            raise FavouritesError(f"Failed to play favourite: {exc}") from exc

    def get_playlists(self, ip_address: str) -> list[SonosPlaylist]:
        try:
            zone = self._make_zone(ip_address)
            results = self._list_raw_playlists(zone)
            return [
                SonosPlaylist(
                    title=item.title,
                    uri=item.uri,
                    item_id=getattr(item, "item_id", None),
                )
                for item in results
            ]
        except PlaylistError:
            raise
        except Exception as exc:
            raise PlaylistError(f"Failed to get playlists: {exc}") from exc

    def browse_library(
        self,
        ip_address: str,
        category: str,
        *,
        start: int,
        limit: int,
        parent_id: str | None = None,
    ) -> tuple[list[LibraryItem], int | None]:
        """Browse a bounded slice of the local Sonos music library."""
        from requests import exceptions as requests_exceptions  # noqa: PLC0415

        try:
            zone = self._make_zone(ip_address)
            if parent_id is None:
                results = zone.music_library.get_music_library_information(
                    category,
                    start=start,
                    max_items=limit,
                    full_album_art_uri=False,
                    complete_result=False,
                )
            else:
                results = zone.music_library.browse_by_idstring(
                    category,
                    parent_id,
                    start=start,
                    max_items=limit,
                    full_album_art_uri=False,
                )
            items = [self._normalize_library_item(item) for item in list(results)]
            total_matches = getattr(results, "total_matches", None)
            return items, total_matches if isinstance(total_matches, int) else None
        except (requests_exceptions.RequestException, ConnectionError, OSError) as exc:
            raise SonosDiscoveryError(
                f"Failed to reach Sonos music library on {ip_address}: {exc}"
            ) from exc
        except Exception as exc:
            raise LibraryError(f"Failed to browse local music library: {exc}") from exc

    def play_playlist(self, ip_address: str, uri: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.clear_queue()
            zone.add_uri_to_queue(uri)
            zone.play_from_queue(0)
        except Exception as exc:
            raise PlaylistError(f"Failed to play playlist: {exc}") from exc

    def create_playlist(self, ip_address: str, title: str) -> SonosPlaylist:
        """Create a new Sonos playlist with the given title.

        Args:
            ip_address: LAN IP of any zone in the household.
            title: Title for the new playlist.

        Returns:
            Normalized ``SonosPlaylist`` for the newly created playlist.

        Raises:
            PlaylistError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            result = zone.create_sonos_playlist(title)
            return SonosPlaylist(
                title=result.title,
                uri=result.uri,
                item_id=getattr(result, "item_id", None),
            )
        except PlaylistError:
            raise
        except Exception as exc:
            raise PlaylistError(f"Failed to create playlist: {exc}") from exc

    def rename_playlist(self, ip_address: str, item_id: str, title: str) -> SonosPlaylist:
        """Rename a Sonos playlist.

        The current SoCo API (>=0.30.14) does not expose a stable rename
        endpoint for Sonos playlists. This method raises
        ``PlaylistUnsupportedOperationError`` unconditionally. If a future
        SoCo release adds a clean rename path this is where to implement it.

        Raises:
            PlaylistUnsupportedOperationError: Always, for the current SoCo version.
        """
        raise PlaylistUnsupportedOperationError(
            "Playlist rename is not supported by the current SoCo API version. "
            "Delete the playlist and create a new one with the desired title."
        )

    def update_playlist(self, ip_address: str, item_id: str, source_ip: str) -> SonosPlaylist:
        """Replace a playlist's contents with the current queue from the source zone.

        Clears the target playlist and adds all tracks from the source zone's
        active queue. The source queue must be non-empty.

        Args:
            ip_address: LAN IP of any zone (used for playlist operations).
            item_id: ``item_id`` of the target playlist.
            source_ip: LAN IP of the zone whose queue provides new content.

        Returns:
            Normalized ``SonosPlaylist`` reflecting the updated playlist.

        Raises:
            PlaylistValidationError: If the playlist or source queue is not found.
            PlaylistError: If any SoCo operation fails.
        """
        zone = self._make_zone(ip_address)
        playlist_obj = self._require_playlist(zone, item_id)
        source_zone = self._make_zone(source_ip)
        raw_queue = self._get_full_queue(source_zone)
        if not raw_queue:
            raise PlaylistValidationError(
                "Source room queue is empty. Add tracks to the queue before updating a playlist."
            )
        original_items = self._browse_playlist_items(zone, playlist_obj)
        try:
            zone.clear_sonos_playlist(playlist_obj, update_id=0)
            for item in raw_queue:
                zone.add_item_to_sonos_playlist(item, playlist_obj)
        except Exception as exc:
            self._restore_playlist(zone, playlist_obj, original_items)
            raise PlaylistError(f"Failed to update playlist: {exc}") from exc

        updated = self._find_playlist(zone, item_id)
        if updated is None:
            raise PlaylistError(
                "Failed to update playlist: updated playlist could not be reloaded."
            )
        return SonosPlaylist(
            title=updated.title,
            uri=updated.uri,
            item_id=getattr(updated, "item_id", item_id),
        )

    def delete_playlist(self, ip_address: str, item_id: str) -> None:
        """Delete a Sonos playlist by item_id.

        Args:
            ip_address: LAN IP of any zone in the household.
            item_id: ``item_id`` of the playlist to delete.

        Raises:
            PlaylistValidationError: If the playlist is not found.
            PlaylistError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            playlist_obj = self._require_playlist(zone, item_id)
            zone.remove_sonos_playlist(playlist_obj)
        except PlaylistError:
            raise
        except Exception as exc:
            raise PlaylistError(f"Failed to delete playlist: {exc}") from exc

    @staticmethod
    def _matches_playlist_identifier(playlist: Any, identifier: str) -> bool:
        item_id = getattr(playlist, "item_id", None)
        if item_id == identifier:
            return True
        title = _coerce_str(getattr(playlist, "title", None))
        return item_id is None and title == identifier

    def _normalize_library_item(self, item: Any) -> LibraryItem:
        """Normalize a SoCo music-library item into a stable domain record."""
        title = _coerce_str(getattr(item, "title", None))
        item_id = _coerce_str(getattr(item, "item_id", None))
        uri = _coerce_str(getattr(item, "uri", None))
        item_type = (
            _coerce_str(getattr(item, "item_class", None))
            or _coerce_str(getattr(item, "search_type", None))
            or item.__class__.__name__.lower()
        )
        can_play = getattr(item, "can_play", None)
        can_browse = getattr(item, "can_browse", None)
        is_playable = bool(can_play) if can_play is not None else uri is not None
        if can_browse is not None:
            is_browsable = bool(can_browse)
        else:
            is_browsable = item_id is not None and not is_playable
        return LibraryItem(
            title=title or item_id or "Untitled",
            item_type=item_type,
            item_id=item_id,
            uri=uri,
            album_art_uri=_coerce_str(getattr(item, "album_art_uri", None)),
            is_browsable=is_browsable,
            is_playable=is_playable,
        )

    def _list_raw_playlists(self, zone: Any) -> list[Any]:
        """Return the complete raw Sonos playlist inventory for a household."""
        try:
            return list(
                zone.music_library.get_music_library_information(
                    "sonos_playlists",
                    complete_result=True,
                )
            )
        except Exception as exc:
            raise PlaylistError(f"Failed to get playlists: {exc}") from exc

    def _find_playlist(self, zone: Any, identifier: str) -> Any | None:
        """Look up a raw SoCo playlist object by item_id or bounded title fallback."""
        playlists = self._list_raw_playlists(zone)
        for playlist in playlists:
            if getattr(playlist, "item_id", None) == identifier:
                return playlist

        title_matches = [
            playlist
            for playlist in playlists
            if self._matches_playlist_identifier(playlist, identifier)
        ]
        if len(title_matches) > 1:
            raise PlaylistValidationError(
                f"Playlist '{identifier}' is ambiguous. "
                "Use 'list_playlists' and retry with a stable item_id."
            )
        return title_matches[0] if title_matches else None

    def _require_playlist(self, zone: Any, identifier: str) -> Any:
        playlist = self._find_playlist(zone, identifier)
        if playlist is not None:
            return playlist
        raise PlaylistValidationError(
            f"Playlist '{identifier}' was not found. "
            "Use 'list_playlists' to see available playlists and their IDs."
        )

    def _browse_playlist_items(
        self, zone: Any, playlist_obj: Any, batch_size: int = 100
    ) -> list[Any]:
        """Return all queueable items currently stored in a Sonos playlist."""
        items: list[Any] = []
        start = 0
        while True:
            try:
                batch = zone.music_library.browse(
                    ml_item=playlist_obj,
                    start=start,
                    max_items=batch_size,
                )
            except Exception as exc:
                raise PlaylistError(f"Failed to inspect existing playlist contents: {exc}") from exc
            batch_items = list(batch)
            if not batch_items:
                return items
            items.extend(batch_items)
            total_matches = getattr(batch, "total_matches", None)
            start += len(batch_items)
            if (isinstance(total_matches, int) and start >= total_matches) or len(
                batch_items
            ) < batch_size:
                return items

    def _get_full_queue(self, zone: Any, batch_size: int = 100) -> list[Any]:
        """Return the full active queue from a zone without silent truncation."""
        try:
            items: list[Any] = []
            start = 0
            expected_total = getattr(zone, "queue_size", None)
            while True:
                batch = list(zone.get_queue(start=start, max_items=batch_size))
                if not batch:
                    return items
                items.extend(batch)
                start += len(batch)
                if (isinstance(expected_total, int) and start >= expected_total) or len(
                    batch
                ) < batch_size:
                    return items
        except Exception as exc:
            raise PlaylistError(f"Failed to read source room queue: {exc}") from exc

    def _restore_playlist(self, zone: Any, playlist_obj: Any, original_items: list[Any]) -> None:
        """Best-effort rollback for playlist updates that fail after clearing."""
        try:
            zone.clear_sonos_playlist(playlist_obj, update_id=0)
            for item in original_items:
                zone.add_item_to_sonos_playlist(item, playlist_obj)
        except Exception:
            return

    def get_queue(self, ip_address: str) -> list[QueueItem]:
        try:
            zone = self._make_zone(ip_address)
            raw_queue = zone.get_queue(max_items=200)
            return [
                QueueItem(
                    position=idx + 1,
                    uri=item.uri if hasattr(item, "uri") else "",
                    title=_coerce_str(item.title) if hasattr(item, "title") else None,
                    artist=_coerce_str(item.creator) if hasattr(item, "creator") else None,
                    album=_coerce_str(item.album) if hasattr(item, "album") else None,
                    album_art_uri=_coerce_str(item.album_art_uri)
                    if hasattr(item, "album_art_uri")
                    else None,
                )
                for idx, item in enumerate(raw_queue)
            ]
        except Exception as exc:
            raise QueueError(f"Failed to get queue for {ip_address}: {exc}") from exc

    def add_to_queue(self, ip_address: str, uri: str) -> int:
        try:
            zone = self._make_zone(ip_address)
            position = zone.add_uri_to_queue(uri)
            return int(position)
        except Exception as exc:
            raise QueueError(f"Failed to add to queue on {ip_address}: {exc}") from exc

    def remove_from_queue(self, ip_address: str, position: int) -> None:
        try:
            zone = self._make_zone(ip_address)
            raw_queue = zone.get_queue(max_items=200)
            idx = position - 1
            if idx < 0 or idx >= len(raw_queue):
                raise QueueError(
                    f"Queue position {position} is out of range (queue has {len(raw_queue)} items)."
                )
            zone.remove_from_queue(raw_queue[idx])
        except QueueError:
            raise
        except Exception as exc:
            raise QueueError(f"Failed to remove from queue on {ip_address}: {exc}") from exc

    def clear_queue(self, ip_address: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.clear_queue()
        except Exception as exc:
            raise QueueError(f"Failed to clear queue on {ip_address}: {exc}") from exc

    def play_from_queue(self, ip_address: str, position: int) -> None:
        if position < 1:
            raise QueueError(f"Queue position {position} is invalid; positions are 1-based.")
        try:
            zone = self._make_zone(ip_address)
            zone.play_from_queue(position - 1)
        except QueueError:
            raise
        except Exception as exc:
            raise QueueError(f"Failed to play from queue on {ip_address}: {exc}") from exc

    def get_group_volume(self, ip_address: str) -> int:
        """Return the current group volume for the zone's group.

        Args:
            ip_address: LAN IP of any zone in the group.

        Returns:
            Group volume level (0-100).

        Raises:
            GroupError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            return int(zone.group.volume)
        except Exception as exc:
            raise GroupError(f"Failed to get group volume from {ip_address}: {exc}") from exc

    def set_group_volume(self, ip_address: str, volume: int) -> None:
        """Set the group volume for the zone's group.

        Args:
            ip_address: LAN IP of any zone in the group.
            volume: Target volume level (0-100).

        Raises:
            GroupError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.group.volume = volume
        except Exception as exc:
            raise GroupError(f"Failed to set group volume on {ip_address}: {exc}") from exc

    def adjust_group_volume(self, ip_address: str, delta: int) -> int:
        """Adjust the group volume by a relative delta and return the new level.

        Uses ``set_relative_volume`` to avoid an extra read-modify-write cycle.

        Args:
            ip_address: LAN IP of any zone in the group.
            delta: Volume change amount (can be negative).

        Returns:
            New group volume level after adjustment.

        Raises:
            GroupError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.group.set_relative_volume(delta)
            return int(zone.group.volume)
        except Exception as exc:
            raise GroupError(f"Failed to adjust group volume on {ip_address}: {exc}") from exc

    def get_group_mute(self, ip_address: str) -> bool:
        """Return the current group mute state.

        Args:
            ip_address: LAN IP of any zone in the group.

        Returns:
            True if the group is muted.

        Raises:
            GroupError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            return bool(zone.group.mute)
        except Exception as exc:
            raise GroupError(f"Failed to get group mute state from {ip_address}: {exc}") from exc

    def set_group_mute(self, ip_address: str, muted: bool) -> None:
        """Set the group mute state.

        Args:
            ip_address: LAN IP of any zone in the group.
            muted: True to mute, False to unmute.

        Raises:
            GroupError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.group.mute = muted
        except Exception as exc:
            raise GroupError(f"Failed to set group mute on {ip_address}: {exc}") from exc

    def join_group(self, ip_address: str, coordinator_ip: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            coordinator_zone = self._make_zone(coordinator_ip)
            zone.join(coordinator_zone)
        except Exception as exc:
            raise GroupError(f"Failed to join group: {exc}") from exc

    def unjoin_room(self, ip_address: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.unjoin()
        except Exception as exc:
            raise GroupError(f"Failed to unjoin room: {exc}") from exc

    def party_mode(self, ip_address: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.partymode()
        except Exception as exc:
            raise GroupError(f"Failed to activate party mode: {exc}") from exc

    def switch_to_line_in(self, ip_address: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.switch_to_line_in()
        except Exception as exc:
            raise InputError(f"Failed to switch to line-in on {ip_address}: {exc}") from exc

    def switch_to_tv(self, ip_address: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.switch_to_tv()
        except Exception as exc:
            raise InputError(f"Failed to switch to TV on {ip_address}: {exc}") from exc

    def get_music_source(self, ip_address: str) -> str:
        try:
            zone = self._make_zone(ip_address)
            return str(zone.music_source)
        except Exception as exc:
            raise InputError(f"Failed to inspect music source on {ip_address}: {exc}") from exc

    def seek(self, ip_address: str, position: str) -> None:
        """Seek to a position in the current track.

        Args:
            ip_address: LAN IP of the Sonos zone.
            position: Track position as ``"HH:MM:SS"`` string.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.seek(position)
        except Exception as exc:
            raise PlaybackError(f"Failed to seek to {position!r}: {exc}") from exc

    def get_sleep_timer(self, ip_address: str, room_name: str) -> SleepTimerState:
        """Return the current sleep timer state for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            room_name: Human-readable room name (included in the result).

        Returns:
            ``SleepTimerState`` with active flag and remaining time fields.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            remaining = zone.get_sleep_timer()
            if remaining:
                remaining_seconds = int(remaining)
                return SleepTimerState(
                    room_name=room_name,
                    active=True,
                    remaining_seconds=remaining_seconds,
                    remaining_minutes=remaining_seconds // 60,
                )
            return SleepTimerState(
                room_name=room_name,
                active=False,
                remaining_seconds=None,
                remaining_minutes=None,
            )
        except Exception as exc:
            raise PlaybackError(f"Failed to get sleep timer for {room_name!r}: {exc}") from exc

    def set_sleep_timer(self, ip_address: str, room_name: str, minutes: int) -> SleepTimerState:
        """Set or clear the sleep timer for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            room_name: Human-readable room name (included in the result).
            minutes: Minutes until sleep; ``0`` clears the timer.

        Returns:
            ``SleepTimerState`` reflecting the resulting zone state.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            if minutes == 0:
                zone.set_sleep_timer(None)
            else:
                zone.set_sleep_timer(minutes * 60)
            return self.get_sleep_timer(ip_address, room_name)
        except Exception as exc:
            raise PlaybackError(f"Failed to set sleep timer for {room_name!r}: {exc}") from exc

    def get_play_mode(self, ip_address: str, room_name: str) -> PlayModeState:
        """Return the current play mode settings for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone (must be coordinator for grouped rooms).
            room_name: Human-readable room name (included in the result).

        Returns:
            ``PlayModeState`` with shuffle, repeat, and cross_fade values.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            cross_fade = bool(zone.cross_fade)
            repeat, shuffle = _decode_play_mode(zone.play_mode)
            return PlayModeState(
                room_name=room_name,
                shuffle=shuffle,
                repeat=repeat,
                cross_fade=cross_fade,
            )
        except Exception as exc:
            raise PlaybackError(f"Failed to get play mode for {room_name!r}: {exc}") from exc

    def set_play_mode(
        self,
        ip_address: str,
        room_name: str,
        shuffle: bool | None = None,
        repeat: RepeatMode | None = None,
        cross_fade: bool | None = None,
    ) -> PlayModeState:
        """Apply play mode changes to the zone and return the resulting state.

        Reads the current play_mode and cross_fade first, then applies only
        the fields that were explicitly provided. Writes the computed
        play_mode string back to the zone.

        Args:
            ip_address: LAN IP of the Sonos zone (must be coordinator for grouped rooms).
            room_name: Human-readable room name (included in the result).
            shuffle: If provided, set shuffle on/off.
            repeat: If provided, set repeat mode ("none", "all", or "one").
            cross_fade: If provided, set crossfade on/off.

        Returns:
            ``PlayModeState`` reflecting the resulting zone state.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            current_cross_fade = bool(zone.cross_fade)
            current_repeat, current_shuffle = _decode_play_mode(zone.play_mode)

            new_shuffle = shuffle if shuffle is not None else current_shuffle
            new_repeat = repeat if repeat is not None else current_repeat
            new_cross_fade = cross_fade if cross_fade is not None else current_cross_fade

            new_play_mode = _DOMAIN_TO_SOCO.get((new_repeat, new_shuffle))
            if new_play_mode is None:
                raise PlaybackError(
                    f"Invalid play mode combination: shuffle={new_shuffle}, repeat={new_repeat!r}."
                )

            if new_play_mode != zone.play_mode:
                zone.play_mode = new_play_mode
            if cross_fade is not None:
                zone.cross_fade = new_cross_fade

            return PlayModeState(
                room_name=room_name,
                shuffle=new_shuffle,
                repeat=new_repeat,
                cross_fade=new_cross_fade,
            )
        except PlaybackError:
            raise
        except Exception as exc:
            raise PlaybackError(f"Failed to set play mode for {room_name!r}: {exc}") from exc

    def get_audio_settings(self, ip_address: str, room_name: str) -> AudioSettingsState:
        """Return the current bass, treble, and loudness settings for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            room_name: Human-readable room name (included in the result).

        Returns:
            ``AudioSettingsState`` with bass, treble, and loudness values.

        Raises:
            AudioSettingsError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            return AudioSettingsState(
                room_name=room_name,
                bass=int(zone.bass),
                treble=int(zone.treble),
                loudness=bool(zone.loudness),
            )
        except Exception as exc:
            raise AudioSettingsError(
                f"Failed to get audio settings for {room_name!r}: {exc}"
            ) from exc

    def set_bass(self, ip_address: str, level: int) -> None:
        """Set the bass level for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            level: Bass level (-10 to 10).

        Raises:
            AudioSettingsError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.bass = level
        except Exception as exc:
            raise AudioSettingsError(f"Failed to set bass on {ip_address}: {exc}") from exc

    def set_treble(self, ip_address: str, level: int) -> None:
        """Set the treble level for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            level: Treble level (-10 to 10).

        Raises:
            AudioSettingsError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.treble = level
        except Exception as exc:
            raise AudioSettingsError(f"Failed to set treble on {ip_address}: {exc}") from exc

    def set_loudness(self, ip_address: str, enabled: bool) -> None:
        """Set the loudness compensation for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            enabled: True to enable loudness, False to disable.

        Raises:
            AudioSettingsError: If SoCo raises any exception.
        """
        try:
            zone = self._make_zone(ip_address)
            zone.loudness = enabled
        except Exception as exc:
            raise AudioSettingsError(f"Failed to set loudness on {ip_address}: {exc}") from exc

    def get_alarms(self, ip_address: str) -> list[AlarmRecord]:
        """Return all Sonos alarms in the household.

        Args:
            ip_address: LAN IP of any zone in the household.

        Returns:
            List of normalized ``AlarmRecord`` instances.

        Raises:
            AlarmError: If SoCo raises any exception.
        """
        try:
            import soco.alarms  # noqa: PLC0415

            zone = self._make_zone(ip_address)
            alarms = soco.alarms.get_alarms(zone=zone)
            return [self._normalize_alarm(a) for a in alarms]
        except AlarmError:
            raise
        except Exception as exc:
            raise AlarmError(f"Failed to get alarms: {exc}") from exc

    def is_valid_recurrence(self, recurrence: str) -> bool:
        """Return True when the recurrence string is accepted by SoCo."""
        try:
            import soco.alarms  # noqa: PLC0415

            return bool(soco.alarms.is_valid_recurrence(recurrence))
        except Exception as exc:
            raise AlarmError(f"Failed to validate recurrence: {exc}") from exc

    def create_alarm(
        self,
        ip_address: str,
        start_time: datetime.time,
        recurrence: str,
        enabled: bool,
        volume: int | None,
        include_linked_zones: bool,
    ) -> AlarmRecord:
        """Create a new Sonos alarm and return the resulting record.

        Args:
            ip_address: LAN IP of the target zone.
            start_time: Alarm start time as a ``datetime.time`` object.
            recurrence: Recurrence rule string (e.g. "DAILY", "WEEKDAYS").
            enabled: True to activate the alarm immediately.
            volume: Alarm volume (0-100), or None to use zone default.
            include_linked_zones: True to play on all grouped rooms.

        Returns:
            Normalized ``AlarmRecord`` for the newly created alarm.

        Raises:
            AlarmError: If SoCo raises any exception.
        """
        try:
            import soco.alarms  # noqa: PLC0415

            zone = self._make_zone(ip_address)
            kwargs: dict[str, Any] = {
                "zone": zone,
                "start_time": start_time,
                "recurrence": recurrence,
                "enabled": enabled,
                "include_linked_zones": include_linked_zones,
            }
            if volume is not None:
                kwargs["volume"] = volume
            alarm = soco.alarms.Alarm(**kwargs)
            alarm.save()
            # Reload the alarm list to get the server-assigned alarm_id
            alarms = soco.alarms.get_alarms(zone=zone)
            for saved in alarms:
                if saved.alarm_id == alarm.alarm_id:
                    return self._normalize_alarm(saved)
            # Fallback: normalize the alarm object directly
            return self._normalize_alarm(alarm)
        except AlarmError:
            raise
        except Exception as exc:
            raise AlarmError(f"Failed to create alarm: {exc}") from exc

    def update_alarm(
        self,
        ip_address: str,
        alarm_id: str,
        start_time: datetime.time,
        recurrence: str,
        enabled: bool,
        volume: int | None,
        include_linked_zones: bool,
    ) -> AlarmRecord:
        """Update an existing Sonos alarm and return the resulting record.

        Args:
            ip_address: LAN IP of any zone in the household.
            alarm_id: ID of the alarm to update.
            start_time: New alarm start time.
            recurrence: New recurrence rule string.
            enabled: New enabled state.
            volume: New alarm volume (0-100), or None.
            include_linked_zones: New linked-zones setting.

        Returns:
            Normalized ``AlarmRecord`` reflecting the updated alarm.

        Raises:
            AlarmError: If the alarm is not found or SoCo raises any exception.
        """
        try:
            import soco.alarms  # noqa: PLC0415

            zone = self._make_zone(ip_address)
            alarms = soco.alarms.get_alarms(zone=zone)
            target = next((a for a in alarms if a.alarm_id == alarm_id), None)
            if target is None:
                raise AlarmError(
                    f"Alarm '{alarm_id}' not found. Use 'list_alarms' to see available alarm IDs."
                )
            target.start_time = start_time
            target.recurrence = recurrence
            target.enabled = enabled
            target.volume = volume
            target.include_linked_zones = include_linked_zones
            target.save()
            return self._normalize_alarm(target)
        except AlarmError:
            raise
        except Exception as exc:
            raise AlarmError(f"Failed to update alarm: {exc}") from exc

    def delete_alarm(self, ip_address: str, alarm_id: str) -> None:
        """Delete a Sonos alarm by ID.

        Args:
            ip_address: LAN IP of any zone in the household.
            alarm_id: ID of the alarm to delete.

        Raises:
            AlarmError: If the alarm is not found or SoCo raises any exception.
        """
        try:
            import soco.alarms  # noqa: PLC0415

            zone = self._make_zone(ip_address)
            alarms = soco.alarms.get_alarms(zone=zone)
            target = next((a for a in alarms if a.alarm_id == alarm_id), None)
            if target is None:
                raise AlarmError(
                    f"Alarm '{alarm_id}' not found. Use 'list_alarms' to see available alarm IDs."
                )
            target.remove()
        except AlarmError:
            raise
        except Exception as exc:
            raise AlarmError(f"Failed to delete alarm: {exc}") from exc

    @staticmethod
    def _normalize_alarm(alarm: Any) -> AlarmRecord:
        """Convert a SoCo Alarm object to a domain AlarmRecord.

        Never leaks raw SoCo Alarm objects outside the adapter boundary.
        """
        alarm_id = str(alarm.alarm_id)
        room_name = str(alarm.zone.player_name)
        start = alarm.start_time
        start_time_str = (
            start.strftime("%H:%M:%S") if isinstance(start, datetime.time) else str(start)
        )
        volume = alarm.volume if alarm.volume is not None else None
        return AlarmRecord(
            alarm_id=alarm_id,
            room_name=room_name,
            start_time=start_time_str,
            recurrence=str(alarm.recurrence),
            enabled=bool(alarm.enabled),
            volume=int(volume) if volume is not None else None,
            include_linked_zones=bool(alarm.include_linked_zones),
        )

    def _call_playback(self, ip_address: str, action: Callable[[Any], object]) -> None:
        try:
            zone = self._make_zone(ip_address)
            action(zone)
        except Exception as exc:
            raise PlaybackError(str(exc)) from exc

    @staticmethod
    def _make_zone(ip_address: str) -> Any:
        import soco  # noqa: PLC0415

        return soco.SoCo(ip_address)
