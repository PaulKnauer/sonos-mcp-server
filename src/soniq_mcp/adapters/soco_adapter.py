"""Shared SoCo adapter for core Sonos operations.

This module is the shared by-IP Sonos integration boundary used by
playback and volume capability layers. Higher layers must not import
``soco`` directly.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from soniq_mcp.domain.exceptions import (
    FavouritesError,
    GroupError,
    PlaybackError,
    QueueError,
    VolumeError,
)
from soniq_mcp.domain.models import (
    Favourite,
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
            results = zone.music_library.get_music_library_information("sonos_playlists")
            return [
                SonosPlaylist(
                    title=item.title,
                    uri=item.uri,
                    item_id=getattr(item, "item_id", None),
                )
                for item in results
            ]
        except Exception as exc:
            raise FavouritesError(f"Failed to get playlists: {exc}") from exc

    def play_playlist(self, ip_address: str, uri: str) -> None:
        try:
            zone = self._make_zone(ip_address)
            zone.clear_queue()
            zone.add_uri_to_queue(uri)
            zone.play_from_queue(0)
        except Exception as exc:
            raise FavouritesError(f"Failed to play playlist: {exc}") from exc

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
