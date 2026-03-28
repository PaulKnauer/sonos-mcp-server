"""SoCo playback adapter for SoniqMCP.

Connects to a Sonos zone by IP address and executes playback operations.
This is the ONLY module that imports ``soco`` for playback control.
All other layers receive domain objects and never touch SoCo directly.
"""

from __future__ import annotations

import logging

from soniq_mcp.domain.exceptions import PlaybackError
from soniq_mcp.domain.models import PlaybackState, TrackInfo

log = logging.getLogger(__name__)

# SoCo values to treat as "no value" when normalising track info fields
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


class PlaybackAdapter:
    """Wraps SoCo zone playback operations for a room identified by IP address.

    Connects to the zone via ``soco.SoCo(ip_address)`` on each call so
    services and tools can be tested without real hardware by substituting
    a fake adapter.
    """

    def play(self, ip_address: str) -> None:
        """Start or resume playback on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._call(ip_address, lambda z: z.play())

    def pause(self, ip_address: str) -> None:
        """Pause playback on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._call(ip_address, lambda z: z.pause())

    def stop(self, ip_address: str) -> None:
        """Stop playback on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._call(ip_address, lambda z: z.stop())

    def next_track(self, ip_address: str) -> None:
        """Skip to the next track on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception (e.g. end of queue).
        """
        self._call(ip_address, lambda z: z.next())

    def previous_track(self, ip_address: str) -> None:
        """Return to the previous track on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._call(ip_address, lambda z: z.previous())

    def get_playback_state(self, ip_address: str, room_name: str) -> PlaybackState:
        """Return the current transport state for the zone.

        Args:
            ip_address: LAN IP of the Sonos zone.
            room_name: Human-readable room name (included in the result).

        Returns:
            ``PlaybackState`` with ``transport_state`` and ``room_name``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            import soco  # local import keeps module loadable without hardware

            zone = soco.SoCo(ip_address)
            info = zone.get_current_transport_info()
            transport_state = info.get("current_transport_state", "STOPPED")
            log.debug("Zone %s transport_state=%s", ip_address, transport_state)
            return PlaybackState(
                transport_state=str(transport_state),
                room_name=room_name,
            )
        except PlaybackError:
            raise
        except Exception as exc:
            raise PlaybackError(
                f"Failed to get playback state for {room_name!r}: {exc}"
            ) from exc

    def get_track_info(self, ip_address: str) -> TrackInfo:
        """Return current track details for the zone.

        SoCo returns empty strings (and "NOT_IMPLEMENTED" for duration on
        streams) rather than None — these are normalised to None.

        Args:
            ip_address: LAN IP of the Sonos zone.

        Returns:
            ``TrackInfo`` with all available track metadata.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        try:
            import soco  # local import keeps module loadable without hardware

            zone = soco.SoCo(ip_address)
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
        except PlaybackError:
            raise
        except Exception as exc:
            raise PlaybackError(
                f"Failed to get track info: {exc}"
            ) from exc

    def _call(self, ip_address: str, action) -> None:
        """Connect to zone by IP, run action, convert exceptions to PlaybackError."""
        try:
            import soco  # local import keeps module loadable without hardware

            zone = soco.SoCo(ip_address)
            action(zone)
        except PlaybackError:
            raise
        except Exception as exc:
            raise PlaybackError(str(exc)) from exc
