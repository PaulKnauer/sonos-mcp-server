"""Unit tests for SoCoAdapter playlist edits, volume ramp, and stereo pairing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import (
    GroupError,
    PlaylistError,
    PlaylistValidationError,
    VolumeError,
)
from soniq_mcp.domain.models import SonosPlaylist

IP = "192.168.1.10"
RIGHT_IP = "192.168.1.11"


def _playlist(item_id="SQ:1", title="Mix"):
    item = MagicMock(spec=["title", "item_id", "get_uri"])
    item.title = title
    item.item_id = item_id
    item.get_uri.return_value = "file:///jffs/settings/savedqueues.rsq#1"
    return item


def _zone_with_playlist(track_count=3):
    zone = MagicMock()
    playlist = _playlist()
    zone.music_library.get_music_library_information.return_value = [playlist]
    zone.music_library.browse.return_value = [MagicMock() for _ in range(track_count)]
    return zone, playlist


class TestSaveQueueAsPlaylist:
    def test_returns_playlist_with_get_uri(self):
        zone = MagicMock()
        zone.create_sonos_playlist_from_queue.return_value = _playlist("SQ:9", "Saved")

        with patch("soco.SoCo", return_value=zone):
            result = SoCoAdapter().save_queue_as_playlist(IP, "Saved")

        zone.create_sonos_playlist_from_queue.assert_called_once_with("Saved")
        assert result == SonosPlaylist(
            title="Saved", uri="file:///jffs/settings/savedqueues.rsq#1", item_id="SQ:9"
        )

    def test_soco_error_raises_playlist_error(self):
        zone = MagicMock()
        zone.create_sonos_playlist_from_queue.side_effect = RuntimeError("empty queue")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaylistError, match="save queue"):
                SoCoAdapter().save_queue_as_playlist(IP, "Saved")


class TestRemoveFromPlaylist:
    def test_converts_to_zero_based_index(self):
        zone, playlist = _zone_with_playlist()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().remove_from_playlist(IP, "SQ:1", 2)

        zone.remove_from_sonos_playlist.assert_called_once_with(playlist, 1, update_id=0)

    def test_out_of_range_position_raises_validation_error(self):
        zone, _ = _zone_with_playlist(track_count=2)

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaylistValidationError, match="out of range"):
                SoCoAdapter().remove_from_playlist(IP, "SQ:1", 3)
        zone.remove_from_sonos_playlist.assert_not_called()

    def test_unknown_playlist_raises_validation_error(self):
        zone, _ = _zone_with_playlist()

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaylistValidationError, match="not found"):
                SoCoAdapter().remove_from_playlist(IP, "SQ:404", 1)

    def test_soco_error_raises_playlist_error(self):
        zone, _ = _zone_with_playlist()
        zone.remove_from_sonos_playlist.side_effect = RuntimeError("upnp 800")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaylistError, match="remove track"):
                SoCoAdapter().remove_from_playlist(IP, "SQ:1", 1)


class TestReorderPlaylist:
    def test_moves_with_zero_based_positions(self):
        zone, playlist = _zone_with_playlist()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().reorder_playlist(IP, "SQ:1", 3, 1)

        zone.move_in_sonos_playlist.assert_called_once_with(playlist, 2, 0, update_id=0)

    def test_out_of_range_target_raises_validation_error(self):
        zone, _ = _zone_with_playlist(track_count=3)

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaylistValidationError, match="position 4"):
                SoCoAdapter().reorder_playlist(IP, "SQ:1", 1, 4)

    def test_soco_error_raises_playlist_error(self):
        zone, _ = _zone_with_playlist()
        zone.move_in_sonos_playlist.side_effect = RuntimeError("upnp")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(PlaylistError, match="reorder"):
                SoCoAdapter().reorder_playlist(IP, "SQ:1", 1, 2)


class TestRampToVolume:
    def test_returns_ramp_seconds(self):
        zone = MagicMock()
        zone.ramp_to_volume.return_value = 16

        with patch("soco.SoCo", return_value=zone):
            seconds = SoCoAdapter().ramp_to_volume(IP, 30, "SLEEP_TIMER_RAMP_TYPE")

        assert seconds == 16
        zone.ramp_to_volume.assert_called_once_with(30, ramp_type="SLEEP_TIMER_RAMP_TYPE")

    def test_soco_error_raises_volume_error(self):
        zone = MagicMock()
        zone.ramp_to_volume.side_effect = RuntimeError("upnp")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(VolumeError, match="ramp volume"):
                SoCoAdapter().ramp_to_volume(IP, 30, "SLEEP_TIMER_RAMP_TYPE")


class TestStereoPair:
    def test_create_passes_right_speaker_zone(self):
        left, right = MagicMock(), MagicMock()

        with patch("soco.SoCo", side_effect=lambda ip: {IP: left, RIGHT_IP: right}[ip]):
            SoCoAdapter().create_stereo_pair(IP, RIGHT_IP)

        left.create_stereo_pair.assert_called_once_with(right)

    def test_create_error_raises_group_error(self):
        zone = MagicMock()
        zone.create_stereo_pair.side_effect = RuntimeError("already paired")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(GroupError, match="create stereo pair"):
                SoCoAdapter().create_stereo_pair(IP, RIGHT_IP)

    def test_separate(self):
        zone = MagicMock()

        with patch("soco.SoCo", return_value=zone):
            SoCoAdapter().separate_stereo_pair(IP)

        zone.separate_stereo_pair.assert_called_once_with()

    def test_separate_error_raises_group_error(self):
        zone = MagicMock()
        zone.separate_stereo_pair.side_effect = RuntimeError("not paired")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(GroupError, match="separate stereo pair"):
                SoCoAdapter().separate_stereo_pair(IP)
