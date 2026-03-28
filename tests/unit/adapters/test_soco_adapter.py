"""Unit tests for shared SoCo adapter behavior."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import PlaybackError, VolumeError
from soniq_mcp.domain.models import PlaybackState, TrackInfo


def make_fake_zone(
    transport_state: str = "PLAYING",
    volume: int = 30,
    muted: bool = False,
    playlist_position: object = 1,
) -> MagicMock:
    zone = MagicMock()
    zone.volume = volume
    zone.mute = muted
    zone.get_current_transport_info.return_value = {
        "current_transport_state": transport_state,
    }
    zone.get_current_track_info.return_value = {
        "title": "Song",
        "artist": "Artist",
        "album": "Album",
        "duration": "0:03:45",
        "position": "0:01:00",
        "uri": "x-sonos-http://track.mp3",
        "album_art": "http://example.com/art.jpg",
        "playlist_position": playlist_position,
    }
    return zone


class TestSoCoAdapterPlayback:
    def test_play_calls_zone_play(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone()
        with _patch_soco(zone):
            adapter.play("192.168.1.10")
        zone.play.assert_called_once()

    def test_get_playback_state_returns_domain_model(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(transport_state="PAUSED_PLAYBACK")
        with _patch_soco(zone):
            state = adapter.get_playback_state("192.168.1.10", "Living Room")
        assert isinstance(state, PlaybackState)
        assert state.transport_state == "PAUSED_PLAYBACK"
        assert state.room_name == "Living Room"

    def test_get_track_info_normalizes_string_queue_position(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(playlist_position="3")
        with _patch_soco(zone):
            info = adapter.get_track_info("192.168.1.10")
        assert isinstance(info, TrackInfo)
        assert info.queue_position == 3

    def test_play_wraps_errors_as_playback_error(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone()
        zone.play.side_effect = RuntimeError("UPnP failure")
        with _patch_soco(zone):
            with pytest.raises(PlaybackError, match="UPnP failure"):
                adapter.play("192.168.1.10")


class TestSoCoAdapterVolume:
    def test_get_volume_returns_zone_volume(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(volume=55)
        with _patch_soco(zone):
            volume = adapter.get_volume("192.168.1.10")
        assert volume == 55

    def test_set_mute_updates_zone_property(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(muted=False)
        with _patch_soco(zone):
            adapter.set_mute("192.168.1.10", True)
        assert zone.mute is True

    def test_volume_calls_wrap_errors_as_volume_error(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone()
        type(zone).volume = property(lambda self: (_ for _ in ()).throw(RuntimeError("boom")))
        with _patch_soco(zone):
            with pytest.raises(VolumeError, match="boom"):
                adapter.get_volume("192.168.1.10")


def _patch_soco(zone: MagicMock):
    from unittest.mock import patch

    return patch("soco.SoCo", return_value=zone)
