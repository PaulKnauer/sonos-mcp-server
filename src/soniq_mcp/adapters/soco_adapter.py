"""Shared SoCo adapter for core Sonos operations.

This module is the shared by-IP Sonos integration boundary used by
playback and volume capability layers. Higher layers must not import
``soco`` directly.
"""

from __future__ import annotations

from soniq_mcp.domain.exceptions import PlaybackError, QueueError, VolumeError
from soniq_mcp.domain.models import PlaybackState, QueueItem, TrackInfo

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
            raise PlaybackError(
                f"Failed to get playback state for {room_name!r}: {exc}"
            ) from exc

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
                    album_art_uri=_coerce_str(item.album_art_uri) if hasattr(item, "album_art_uri") else None,
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
                    f"Queue position {position} is out of range "
                    f"(queue has {len(raw_queue)} items)."
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
            raise QueueError(
                f"Queue position {position} is invalid; positions are 1-based."
            )
        try:
            zone = self._make_zone(ip_address)
            zone.play_from_queue(position - 1)
        except QueueError:
            raise
        except Exception as exc:
            raise QueueError(f"Failed to play from queue on {ip_address}: {exc}") from exc

    def _call_playback(self, ip_address: str, action) -> None:
        try:
            zone = self._make_zone(ip_address)
            action(zone)
        except Exception as exc:
            raise PlaybackError(str(exc)) from exc

    @staticmethod
    def _make_zone(ip_address: str):
        import soco  # noqa: PLC0415

        return soco.SoCo(ip_address)
