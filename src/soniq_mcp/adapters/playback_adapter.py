"""Playback adapter facade over the shared SoCo adapter."""

from __future__ import annotations

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.models import PlaybackState, TrackInfo


class PlaybackAdapter:
    """Compatibility adapter that delegates to ``SoCoAdapter``."""

    def __init__(self, soco_adapter: SoCoAdapter | None = None) -> None:
        self._adapter = soco_adapter or SoCoAdapter()

    def play(self, ip_address: str) -> None:
        """Start or resume playback on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._adapter.play(ip_address)

    def pause(self, ip_address: str) -> None:
        """Pause playback on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._adapter.pause(ip_address)

    def stop(self, ip_address: str) -> None:
        """Stop playback on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._adapter.stop(ip_address)

    def next_track(self, ip_address: str) -> None:
        """Skip to the next track on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception (e.g. end of queue).
        """
        self._adapter.next_track(ip_address)

    def previous_track(self, ip_address: str) -> None:
        """Return to the previous track on the zone at ``ip_address``.

        Raises:
            PlaybackError: If SoCo raises any exception.
        """
        self._adapter.previous_track(ip_address)

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
        return self._adapter.get_playback_state(ip_address, room_name)

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
        return self._adapter.get_track_info(ip_address)
