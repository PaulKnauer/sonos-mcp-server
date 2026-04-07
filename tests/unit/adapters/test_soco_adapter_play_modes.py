"""Unit tests for SoCoAdapter play mode methods."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import PlaybackError
from soniq_mcp.domain.models import PlayModeState


class FakeZone:
    def __init__(self, play_mode: str = "NORMAL", cross_fade: bool = False) -> None:
        self._play_mode = play_mode
        self._cross_fade = cross_fade
        self.play_mode_writes = 0
        self.cross_fade_writes = 0

    @property
    def play_mode(self) -> str:
        return self._play_mode

    @play_mode.setter
    def play_mode(self, value: str) -> None:
        self.play_mode_writes += 1
        self._play_mode = value

    @property
    def cross_fade(self) -> bool:
        return self._cross_fade

    @cross_fade.setter
    def cross_fade(self, value: bool) -> None:
        self.cross_fade_writes += 1
        self._cross_fade = value


def make_fake_zone(play_mode: str = "NORMAL", cross_fade: bool = False) -> FakeZone:
    return FakeZone(play_mode=play_mode, cross_fade=cross_fade)


def _patch_soco(zone: FakeZone):
    return patch("soco.SoCo", return_value=zone)


class TestGetPlayMode:
    def test_normal_mode_returns_no_shuffle_no_repeat(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=False)
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Living Room")
        assert isinstance(state, PlayModeState)
        assert state.room_name == "Living Room"
        assert state.shuffle is False
        assert state.repeat == "none"
        assert state.cross_fade is False

    def test_repeat_all_mode(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="REPEAT_ALL")
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Kitchen")
        assert state.shuffle is False
        assert state.repeat == "all"

    def test_repeat_one_mode(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="REPEAT_ONE")
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Kitchen")
        assert state.shuffle is False
        assert state.repeat == "one"

    def test_shuffle_norepeat_mode(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="SHUFFLE_NOREPEAT")
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Kitchen")
        assert state.shuffle is True
        assert state.repeat == "none"

    def test_shuffle_repeat_all_mode(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="SHUFFLE")
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Kitchen")
        assert state.shuffle is True
        assert state.repeat == "all"

    def test_shuffle_repeat_one_mode(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="SHUFFLE_REPEAT_ONE")
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Kitchen")
        assert state.shuffle is True
        assert state.repeat == "one"

    def test_cross_fade_true(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=True)
        with _patch_soco(zone):
            state = adapter.get_play_mode("192.168.1.10", "Living Room")
        assert state.cross_fade is True

    def test_soco_error_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("UPnP error")):
            with pytest.raises(PlaybackError, match="UPnP error"):
                adapter.get_play_mode("192.168.1.10", "Living Room")

    def test_unknown_play_mode_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="ALIEN_MODE")
        with _patch_soco(zone):
            with pytest.raises(PlaybackError, match="Unsupported Sonos play_mode value"):
                adapter.get_play_mode("192.168.1.10", "Living Room")


class TestSetPlayMode:
    def test_set_shuffle_only(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=False)
        with _patch_soco(zone):
            state = adapter.set_play_mode("192.168.1.10", "Living Room", shuffle=True)
        assert state.shuffle is True
        assert state.repeat == "none"  # preserved from NORMAL
        assert zone.play_mode == "SHUFFLE_NOREPEAT"

    def test_set_repeat_only(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=False)
        with _patch_soco(zone):
            state = adapter.set_play_mode("192.168.1.10", "Living Room", repeat="all")
        assert state.shuffle is False  # preserved from NORMAL
        assert state.repeat == "all"
        assert zone.play_mode == "REPEAT_ALL"

    def test_set_cross_fade_only(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=False)
        with _patch_soco(zone):
            state = adapter.set_play_mode("192.168.1.10", "Living Room", cross_fade=True)
        assert state.cross_fade is True
        assert zone.cross_fade is True
        assert zone.play_mode_writes == 0

    def test_set_shuffle_and_repeat_together(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=False)
        with _patch_soco(zone):
            state = adapter.set_play_mode("192.168.1.10", "Living Room", shuffle=True, repeat="all")
        assert state.shuffle is True
        assert state.repeat == "all"
        assert zone.play_mode == "SHUFFLE"

    def test_set_clears_shuffle(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="SHUFFLE", cross_fade=False)
        with _patch_soco(zone):
            state = adapter.set_play_mode("192.168.1.10", "Living Room", shuffle=False)
        assert state.shuffle is False
        assert state.repeat == "all"  # preserved from SHUFFLE
        assert zone.play_mode == "REPEAT_ALL"

    def test_no_fields_provided_returns_current_state(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="SHUFFLE_REPEAT_ONE", cross_fade=True)
        with _patch_soco(zone):
            state = adapter.set_play_mode("192.168.1.10", "Living Room")
        assert state.shuffle is True
        assert state.repeat == "one"
        assert state.cross_fade is True
        assert zone.play_mode_writes == 0
        assert zone.cross_fade_writes == 0

    def test_unknown_play_mode_on_set_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="ALIEN_MODE", cross_fade=False)
        with _patch_soco(zone):
            with pytest.raises(PlaybackError, match="Unsupported Sonos play_mode value"):
                adapter.set_play_mode("192.168.1.10", "Living Room", shuffle=True)

    def test_soco_error_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("connection refused")):
            with pytest.raises(PlaybackError, match="connection refused"):
                adapter.set_play_mode("192.168.1.10", "Living Room", shuffle=True)
