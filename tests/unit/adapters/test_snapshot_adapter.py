"""Unit tests for SnapshotAdapter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.snapshot_adapter import SnapshotAdapter
from soniq_mcp.domain.exceptions import SnapshotError

IP = "192.168.1.10"


def _make_device(transport_state="PLAYING", media_uri="x-rincon-queue:RINCON_1#0"):
    device = MagicMock()
    device.is_coordinator = True
    device.avTransport.GetMediaInfo.return_value = {
        "CurrentURI": media_uri,
        "CurrentURIMetaData": "<meta/>",
    }
    device.volume = 30
    device.mute = False
    device.bass = 0
    device.treble = 0
    device.loudness = True
    device.play_mode = "NORMAL"
    device.cross_fade = False
    device.get_current_track_info.return_value = {
        "playlist_position": "3",
        "position": "0:01:00",
    }
    device.get_current_transport_info.return_value = {"current_transport_state": transport_state}
    device.get_queue.return_value = []
    return device


def _queue_item(uri):
    item = MagicMock(spec=["get_uri"])
    item.get_uri.return_value = uri
    return item


class TestCapture:
    def test_serializes_state_to_plain_dict(self):
        device = _make_device()
        with patch("soco.SoCo", return_value=device):
            state = SnapshotAdapter().capture(IP, include_queue=False)

        assert state["media_uri"] == "x-rincon-queue:RINCON_1#0"
        assert state["is_playing_queue"] is True
        assert state["volume"] == 30
        assert state["transport_state"] == "PLAYING"
        assert state["playlist_position"] == 3
        assert "queue" not in state

    def test_includes_queue_uris_via_get_uri(self):
        device = _make_device()
        device.get_queue.side_effect = [[_queue_item("uri:1"), _queue_item("uri:2")], []]
        with patch("soco.SoCo", return_value=device):
            state = SnapshotAdapter().capture(IP, include_queue=True)

        assert state["queue"] == ["uri:1", "uri:2"]

    def test_soco_error_raises_snapshot_error(self):
        device = _make_device()
        device.avTransport.GetMediaInfo.side_effect = RuntimeError("timeout")
        with patch("soco.SoCo", return_value=device):
            with pytest.raises(SnapshotError, match="Failed to capture snapshot"):
                SnapshotAdapter().capture(IP, include_queue=False)


class TestRestore:
    def _capture(self, device, include_queue=False):
        with patch("soco.SoCo", return_value=device):
            return SnapshotAdapter().capture(IP, include_queue=include_queue)

    def test_restores_playing_queue_and_resumes(self):
        state = self._capture(_make_device("PLAYING"))
        device = _make_device("PLAYING", media_uri="http://tts/announce.mp3")
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=False)

        device.play_from_queue.assert_called_once_with(2, False)
        device.seek.assert_called_once_with("0:01:00")
        device.play.assert_called_once()
        assert device.volume == 30

    def test_stopped_room_is_not_started(self):
        state = self._capture(_make_device("STOPPED"))
        device = _make_device("PLAYING", media_uri="http://tts/announce.mp3")
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=False)

        device.play.assert_not_called()
        device.stop.assert_called_once()

    def test_paused_room_stays_paused(self):
        state = self._capture(_make_device("PAUSED_PLAYBACK"))
        device = _make_device("PLAYING", media_uri="http://tts/announce.mp3")
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=False)

        device.pause.assert_called_once()
        device.play.assert_not_called()

    def test_stream_state_restored_without_starting(self):
        state = self._capture(_make_device("PLAYING", media_uri="x-sonosapi-stream:s1"))
        device = _make_device("PLAYING", media_uri="http://tts/announce.mp3")
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=False)

        device.play_uri.assert_called_once_with("x-sonosapi-stream:s1", "<meta/>", start=False)

    def test_fade_ramps_volume(self):
        state = self._capture(_make_device())
        device = _make_device()
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=True)

        device.ramp_to_volume.assert_called_once_with(30)

    def test_restores_captured_queue(self):
        source = _make_device()
        source.get_queue.side_effect = [[_queue_item("uri:1")], []]
        state = self._capture(source, include_queue=True)
        device = _make_device()
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=False)

        device.clear_queue.assert_called_once()
        device.add_uri_to_queue.assert_called_once_with("uri:1")

    def test_queue_untouched_when_not_captured(self):
        state = self._capture(_make_device())
        device = _make_device()
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=False)

        device.clear_queue.assert_not_called()

    def test_restore_volume_false_keeps_current_volume(self):
        state = self._capture(_make_device())
        device = _make_device()
        device.volume = 12
        with patch("soco.SoCo", return_value=device):
            SnapshotAdapter().restore(IP, state, fade=True, restore_volume=False)

        assert device.volume == 12
        device.ramp_to_volume.assert_not_called()

    def test_soco_error_raises_snapshot_error(self):
        state = self._capture(_make_device())
        device = _make_device()
        device.get_current_transport_info.side_effect = RuntimeError("boom")
        with patch("soco.SoCo", return_value=device):
            with pytest.raises(SnapshotError, match="Failed to restore snapshot"):
                SnapshotAdapter().restore(IP, state, fade=False)
