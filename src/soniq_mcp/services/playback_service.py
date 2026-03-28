"""Playback service facade over the shared Sonos service."""

from __future__ import annotations

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.services.sonos_service import SonosService


class PlaybackService:
    """Compatibility playback facade over ``SonosService``."""

    def __init__(
        self,
        room_service: object | None = None,
        adapter: object | None = None,
        config: SoniqConfig | None = None,
        sonos_service: object | None = None,
    ) -> None:
        if sonos_service is not None:
            self._sonos_service = sonos_service
            return
        if room_service is not None and adapter is not None:
            self._sonos_service = SonosService(
                room_service,
                adapter,
                config or SoniqConfig(),
            )
            return
        raise TypeError(
            "PlaybackService requires sonos_service=... or room_service+adapter"
        )

    def play(self, room_name: str) -> None:
        """Start or resume playback in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        self._sonos_service.play(room_name)

    def pause(self, room_name: str) -> None:
        """Pause playback in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        self._sonos_service.pause(room_name)

    def stop(self, room_name: str) -> None:
        """Stop playback in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        self._sonos_service.stop(room_name)

    def next_track(self, room_name: str) -> None:
        """Skip to the next track in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails (e.g. end of queue).
        """
        self._sonos_service.next_track(room_name)

    def previous_track(self, room_name: str) -> None:
        """Return to the previous track in the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        self._sonos_service.previous_track(room_name)

    def get_playback_state(self, room_name: str) -> PlaybackState:
        """Return the current transport state for the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        return self._sonos_service.get_playback_state(room_name)

    def get_track_info(self, room_name: str) -> TrackInfo:
        """Return current track details for the named room.

        Raises:
            RoomNotFoundError: If room_name does not match any discovered zone.
            SonosDiscoveryError: If network discovery fails.
            PlaybackError: If the SoCo operation fails.
        """
        return self._sonos_service.get_track_info(room_name)
