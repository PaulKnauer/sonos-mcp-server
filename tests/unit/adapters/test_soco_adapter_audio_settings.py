"""Unit tests for SoCoAdapter audio EQ methods."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import AudioSettingsError
from soniq_mcp.domain.models import AudioSettingsState


class FakeZone:
    def __init__(self, bass: int = 0, treble: int = 0, loudness: bool = True) -> None:
        self._bass = bass
        self._treble = treble
        self._loudness = loudness
        self.bass_writes: list[int] = []
        self.treble_writes: list[int] = []
        self.loudness_writes: list[bool] = []

    @property
    def bass(self) -> int:
        return self._bass

    @bass.setter
    def bass(self, value: int) -> None:
        self.bass_writes.append(value)
        self._bass = value

    @property
    def treble(self) -> int:
        return self._treble

    @treble.setter
    def treble(self, value: int) -> None:
        self.treble_writes.append(value)
        self._treble = value

    @property
    def loudness(self) -> bool:
        return self._loudness

    @loudness.setter
    def loudness(self, value: bool) -> None:
        self.loudness_writes.append(value)
        self._loudness = value


def _patch_soco(zone: FakeZone):
    return patch("soco.SoCo", return_value=zone)


class TestGetAudioSettings:
    def test_returns_audio_settings_state(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(bass=3, treble=-2, loudness=True)
        with _patch_soco(zone):
            state = adapter.get_audio_settings("192.168.1.10", "Living Room")
        assert isinstance(state, AudioSettingsState)
        assert state.room_name == "Living Room"
        assert state.bass == 3
        assert state.treble == -2
        assert state.loudness is True

    def test_zero_values(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(bass=0, treble=0, loudness=False)
        with _patch_soco(zone):
            state = adapter.get_audio_settings("192.168.1.10", "Kitchen")
        assert state.bass == 0
        assert state.treble == 0
        assert state.loudness is False

    def test_normalizes_loudness_to_bool(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(bass=0, treble=0, loudness=1)  # type: ignore[arg-type]
        with _patch_soco(zone):
            state = adapter.get_audio_settings("192.168.1.10", "Office")
        assert isinstance(state.loudness, bool)
        assert state.loudness is True

    def test_soco_error_raises_audio_settings_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("connection failed")):
            with pytest.raises(AudioSettingsError, match="connection failed"):
                adapter.get_audio_settings("192.168.1.10", "Living Room")


class TestSetBass:
    def test_sets_bass_on_zone(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            adapter.set_bass("192.168.1.10", 5)
        assert zone.bass_writes == [5]
        assert zone.bass == 5

    def test_sets_negative_bass(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            adapter.set_bass("192.168.1.10", -7)
        assert zone.bass_writes == [-7]

    def test_soco_error_raises_audio_settings_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("UPnP error")):
            with pytest.raises(AudioSettingsError, match="UPnP error"):
                adapter.set_bass("192.168.1.10", 3)


class TestSetTreble:
    def test_sets_treble_on_zone(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            adapter.set_treble("192.168.1.10", -4)
        assert zone.treble_writes == [-4]
        assert zone.treble == -4

    def test_sets_positive_treble(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone()
        with _patch_soco(zone):
            adapter.set_treble("192.168.1.10", 10)
        assert zone.treble_writes == [10]

    def test_soco_error_raises_audio_settings_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("timeout")):
            with pytest.raises(AudioSettingsError, match="timeout"):
                adapter.set_treble("192.168.1.10", 2)


class TestSetLoudness:
    def test_enables_loudness(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(loudness=False)
        with _patch_soco(zone):
            adapter.set_loudness("192.168.1.10", True)
        assert zone.loudness_writes == [True]
        assert zone.loudness is True

    def test_disables_loudness(self) -> None:
        adapter = SoCoAdapter()
        zone = FakeZone(loudness=True)
        with _patch_soco(zone):
            adapter.set_loudness("192.168.1.10", False)
        assert zone.loudness_writes == [False]
        assert zone.loudness is False

    def test_soco_error_raises_audio_settings_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("device unreachable")):
            with pytest.raises(AudioSettingsError, match="device unreachable"):
                adapter.set_loudness("192.168.1.10", True)
