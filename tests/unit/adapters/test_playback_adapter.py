"""Unit tests for PlaybackAdapter — no real Sonos hardware required.

Uses a fake SoCo zone object to test adapter logic without network access.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.adapters.playback_adapter import PlaybackAdapter
from soniq_mcp.domain.exceptions import PlaybackError
from soniq_mcp.domain.models import PlaybackState, TrackInfo


def make_fake_zone(
    transport_state: str = "PLAYING",
    track_title: str = "Test Song",
    track_artist: str = "Test Artist",
    track_album: str = "Test Album",
    track_duration: str = "0:03:45",
    track_position: str = "0:01:00",
    track_uri: str = "x-sonos-http://track.mp3",
    track_album_art: str = "http://example.com/art.jpg",
    playlist_position: int = 1,
) -> MagicMock:
    zone = MagicMock()
    zone.get_current_transport_info.return_value = {
        "current_transport_state": transport_state,
        "current_transport_status": "OK",
        "current_speed": "1",
    }
    zone.get_current_track_info.return_value = {
        "title": track_title,
        "artist": track_artist,
        "album": track_album,
        "duration": track_duration,
        "position": track_position,
        "uri": track_uri,
        "album_art": track_album_art,
        "playlist_position": playlist_position,
    }
    return zone


class TestPlaybackAdapterControls:
    def test_play_calls_zone_play(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone, "192.168.1.10"):
            adapter.play("192.168.1.10")
        zone.play.assert_called_once()

    def test_pause_calls_zone_pause(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone, "192.168.1.10"):
            adapter.pause("192.168.1.10")
        zone.pause.assert_called_once()

    def test_stop_calls_zone_stop(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone, "192.168.1.10"):
            adapter.stop("192.168.1.10")
        zone.stop.assert_called_once()

    def test_next_track_calls_zone_next(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone, "192.168.1.10"):
            adapter.next_track("192.168.1.10")
        zone.next.assert_called_once()

    def test_previous_track_calls_zone_previous(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone, "192.168.1.10"):
            adapter.previous_track("192.168.1.10")
        zone.previous.assert_called_once()

    def test_soco_exception_raises_playback_error(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        zone.play.side_effect = RuntimeError("UPnP error")
        with _patch_soco(zone, "192.168.1.10"):
            with pytest.raises(PlaybackError, match="UPnP error"):
                adapter.play("192.168.1.10")


class TestPlaybackAdapterGetPlaybackState:
    def test_returns_playback_state(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone(transport_state="PLAYING")
        with _patch_soco(zone, "192.168.1.10"):
            state = adapter.get_playback_state("192.168.1.10", "Living Room")
        assert isinstance(state, PlaybackState)
        assert state.transport_state == "PLAYING"
        assert state.room_name == "Living Room"

    def test_stopped_state(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone(transport_state="STOPPED")
        with _patch_soco(zone, "192.168.1.10"):
            state = adapter.get_playback_state("192.168.1.10", "Kitchen")
        assert state.transport_state == "STOPPED"

    def test_soco_exception_raises_playback_error(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        zone.get_current_transport_info.side_effect = RuntimeError("network error")
        with _patch_soco(zone, "192.168.1.10"):
            with pytest.raises(PlaybackError):
                adapter.get_playback_state("192.168.1.10", "Living Room")


class TestPlaybackAdapterGetTrackInfo:
    def test_returns_track_info(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone, "192.168.1.10"):
            info = adapter.get_track_info("192.168.1.10")
        assert isinstance(info, TrackInfo)
        assert info.title == "Test Song"
        assert info.artist == "Test Artist"
        assert info.album == "Test Album"
        assert info.duration == "0:03:45"
        assert info.position == "0:01:00"
        assert info.queue_position == 1

    def test_empty_strings_become_none(self) -> None:
        adapter = PlaybackAdapter()
        zone = MagicMock()
        zone.get_current_track_info.return_value = {
            "title": "",
            "artist": "",
            "album": "",
            "duration": "NOT_IMPLEMENTED",
            "position": "",
            "uri": "",
            "album_art": "",
            "playlist_position": 0,
        }
        with _patch_soco(zone, "192.168.1.10"):
            info = adapter.get_track_info("192.168.1.10")
        assert info.title is None
        assert info.artist is None
        assert info.duration is None
        assert info.position is None
        assert info.queue_position is None

    def test_string_playlist_position_becomes_int(self) -> None:
        adapter = PlaybackAdapter()
        zone = MagicMock()
        zone.get_current_track_info.return_value = {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
            "duration": "0:03:45",
            "position": "0:01:00",
            "uri": "x-sonos-http://track.mp3",
            "album_art": "http://example.com/art.jpg",
            "playlist_position": "3",
        }
        with _patch_soco(zone, "192.168.1.10"):
            info = adapter.get_track_info("192.168.1.10")
        assert info.queue_position == 3

    def test_soco_exception_raises_playback_error(self) -> None:
        adapter = PlaybackAdapter()
        zone = make_fake_zone()
        zone.get_current_track_info.side_effect = RuntimeError("timeout")
        with _patch_soco(zone, "192.168.1.10"):
            with pytest.raises(PlaybackError):
                adapter.get_track_info("192.168.1.10")


def _patch_soco(zone: MagicMock, ip: str):
    """Context manager that patches soco.SoCo(ip) to return the fake zone."""
    from unittest.mock import patch

    return patch("soco.SoCo", return_value=zone)
