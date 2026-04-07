"""Unit tests for SoCoAdapter play mode methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import PlaybackError
from soniq_mcp.domain.models import PlayModeState


def make_fake_zone(play_mode: str = "NORMAL", cross_fade: bool = False) -> MagicMock:
    zone = MagicMock()
    zone.play_mode = play_mode
    zone.cross_fade = cross_fade
    return zone


def _patch_soco(zone: MagicMock):
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
        zone = MagicMock()
        type(zone).play_mode = property(fct := lambda self: (_ for _ in ()).throw(RuntimeError("UPnP error")))
        with _patch_soco(zone):
            with pytest.raises(PlaybackError, match="UPnP error"):
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
        zone.cross_fade.__set__(zone, True)  # verify cross_fade was set

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

    def test_soco_error_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        zone = make_fake_zone(play_mode="NORMAL", cross_fade=False)
        zone.play_mode = "NORMAL"  # readable
        # Make assignment raise
        def _raise(val):
            raise RuntimeError("Device busy")
        zone.__class__ = type("FakeZone", (), {
            "play_mode": property(lambda self: "NORMAL", lambda self, v: (_ for _ in ()).throw(RuntimeError("Device busy"))),
            "cross_fade": property(lambda self: False),
        })
        with _patch_soco(zone):
            with pytest.raises(PlaybackError):
                adapter.set_play_mode("192.168.1.10", "Living Room", shuffle=True)
