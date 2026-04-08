"""Unit tests for SoCoAdapter seek and sleep timer methods."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import PlaybackError
from soniq_mcp.domain.models import SleepTimerState


class FakeZone:
    def __init__(self, sleep_timer_return=None) -> None:
        self._sleep_timer_return = sleep_timer_return
        self.seek_calls: list[str] = []
        self.set_sleep_timer_calls: list = []

    def seek(self, position: str) -> None:
        self.seek_calls.append(position)

    def get_sleep_timer(self):
        return self._sleep_timer_return

    def set_sleep_timer(self, seconds) -> None:
        self.set_sleep_timer_calls.append(seconds)
        self._sleep_timer_return = seconds


def _patch_soco(zone: FakeZone):
    return patch("soco.SoCo", return_value=zone)


class TestSeek:
    def test_seek_delegates_to_zone(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            adapter.seek("192.168.1.10", "0:01:30")
        assert zone.seek_calls == ["0:01:30"]

    def test_seek_soco_failure_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("UPnP error")):
            with pytest.raises(PlaybackError, match="UPnP error"):
                adapter.seek("192.168.1.10", "0:01:30")

    def test_seek_zone_exception_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()

        class ErrorZone(FakeZone):
            def seek(self, position: str) -> None:
                raise RuntimeError("not supported")

        with _patch_soco(ErrorZone()):
            with pytest.raises(PlaybackError, match="not supported"):
                adapter.seek("192.168.1.10", "0:01:30")


class TestGetSleepTimer:
    def test_active_timer_normalization(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(sleep_timer_return=1800)
        with _patch_soco(zone):
            state = adapter.get_sleep_timer("192.168.1.10", "Living Room")
        assert isinstance(state, SleepTimerState)
        assert state.room_name == "Living Room"
        assert state.active is True
        assert state.remaining_seconds == 1800
        assert state.remaining_minutes == 30

    def test_inactive_timer_returns_active_false(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(sleep_timer_return=None)
        with _patch_soco(zone):
            state = adapter.get_sleep_timer("192.168.1.10", "Kitchen")
        assert state.active is False
        assert state.remaining_seconds is None
        assert state.remaining_minutes is None

    def test_zero_return_treated_as_inactive(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(sleep_timer_return=0)
        with _patch_soco(zone):
            state = adapter.get_sleep_timer("192.168.1.10", "Bedroom")
        assert state.active is False
        assert state.remaining_seconds is None

    def test_soco_failure_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("connection refused")):
            with pytest.raises(PlaybackError, match="connection refused"):
                adapter.get_sleep_timer("192.168.1.10", "Living Room")


class TestSetSleepTimer:
    def test_positive_minutes_converts_to_seconds(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            state = adapter.set_sleep_timer("192.168.1.10", "Living Room", 30)
        assert zone.set_sleep_timer_calls == [1800]
        assert state.active is True
        assert state.remaining_seconds == 1800
        assert state.remaining_minutes == 30

    def test_minutes_zero_clears_timer(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            state = adapter.set_sleep_timer("192.168.1.10", "Living Room", 0)
        assert zone.set_sleep_timer_calls == [None]
        assert state.active is False
        assert state.remaining_seconds is None
        assert state.remaining_minutes is None

    def test_returns_authoritative_post_write_timer_state(self) -> None:
        adapter = SoCoAdapter()

        class RoundingZone(FakeZone):
            def set_sleep_timer(self, seconds) -> None:
                self.set_sleep_timer_calls.append(seconds)
                self._sleep_timer_return = 1795

        zone = RoundingZone()
        with _patch_soco(zone):
            state = adapter.set_sleep_timer("192.168.1.10", "Living Room", 30)

        assert zone.set_sleep_timer_calls == [1800]
        assert state.remaining_seconds == 1795
        assert state.remaining_minutes == 29

    def test_soco_failure_raises_playback_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("UPnP timeout")):
            with pytest.raises(PlaybackError, match="UPnP timeout"):
                adapter.set_sleep_timer("192.168.1.10", "Living Room", 10)
