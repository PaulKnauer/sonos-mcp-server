"""Unit tests for AudioSettingsService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import AudioSettingsError, RoomNotFoundError
from soniq_mcp.domain.models import AudioSettingsState, Room
from soniq_mcp.services.audio_settings_service import AudioSettingsService


def make_room(
    name: str = "Living Room",
    ip: str = "192.168.1.10",
    uid: str = "RINCON_1",
    is_coordinator: bool = True,
) -> Room:
    return Room(name=name, uid=uid, ip_address=ip, is_coordinator=is_coordinator)


def make_state(
    room_name: str = "Living Room",
    bass: int = 0,
    treble: int = 0,
    loudness: bool = True,
) -> AudioSettingsState:
    return AudioSettingsState(room_name=room_name, bass=bass, treble=treble, loudness=loudness)


class FakeRoomService:
    def __init__(self, rooms: list[Room]) -> None:
        self._rooms = {r.name: r for r in rooms}

    def get_room(self, name: str) -> Room:
        if name not in self._rooms:
            raise RoomNotFoundError(name)
        return self._rooms[name]


class FakeAdapter:
    def __init__(self, state: AudioSettingsState | None = None) -> None:
        self._state = state or make_state()
        self.get_calls: list[tuple[str, str]] = []
        self.set_bass_calls: list[tuple[str, int]] = []
        self.set_treble_calls: list[tuple[str, int]] = []
        self.set_loudness_calls: list[tuple[str, bool]] = []

    def get_audio_settings(self, ip_address: str, room_name: str) -> AudioSettingsState:
        self.get_calls.append((ip_address, room_name))
        return AudioSettingsState(
            room_name=room_name,
            bass=self._state.bass,
            treble=self._state.treble,
            loudness=self._state.loudness,
        )

    def set_bass(self, ip_address: str, level: int) -> None:
        self.set_bass_calls.append((ip_address, level))
        self._state = AudioSettingsState(
            room_name=self._state.room_name,
            bass=level,
            treble=self._state.treble,
            loudness=self._state.loudness,
        )

    def set_treble(self, ip_address: str, level: int) -> None:
        self.set_treble_calls.append((ip_address, level))
        self._state = AudioSettingsState(
            room_name=self._state.room_name,
            bass=self._state.bass,
            treble=level,
            loudness=self._state.loudness,
        )

    def set_loudness(self, ip_address: str, enabled: bool) -> None:
        self.set_loudness_calls.append((ip_address, enabled))
        self._state = AudioSettingsState(
            room_name=self._state.room_name,
            bass=self._state.bass,
            treble=self._state.treble,
            loudness=enabled,
        )


class TestGetAudioSettings:
    def test_delegates_to_adapter_with_room_ip(self) -> None:
        room = make_room(ip="192.168.1.10")
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        svc.get_audio_settings("Living Room")
        # check that adapter was called with correct IP
        assert svc._adapter.get_calls == [("192.168.1.10", "Living Room")]

    def test_returns_audio_settings_state(self) -> None:
        room = make_room()
        adapter = FakeAdapter(make_state(bass=3, treble=-2, loudness=False))
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        state = svc.get_audio_settings("Living Room")
        assert state.bass == 3
        assert state.treble == -2
        assert state.loudness is False

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        svc = AudioSettingsService(FakeRoomService([]), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.get_audio_settings("Unknown Room")


class TestSetBass:
    def test_valid_bass_at_lower_boundary(self) -> None:
        room = make_room()
        adapter = FakeAdapter()
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_bass("Living Room", -10)
        assert adapter.set_bass_calls == [("192.168.1.10", -10)]
        assert result.bass == -10

    def test_valid_bass_at_upper_boundary(self) -> None:
        room = make_room()
        adapter = FakeAdapter()
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_bass("Living Room", 10)
        assert adapter.set_bass_calls == [("192.168.1.10", 10)]
        assert result.bass == 10

    def test_valid_bass_zero(self) -> None:
        room = make_room()
        adapter = FakeAdapter()
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_bass("Living Room", 0)
        assert result.bass == 0

    def test_invalid_bass_below_range_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="bass"):
            svc.set_bass("Living Room", -11)

    def test_invalid_bass_above_range_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="bass"):
            svc.set_bass("Living Room", 11)

    def test_invalid_bass_float_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="integer"):
            svc.set_bass("Living Room", 3.5)  # type: ignore[arg-type]

    def test_invalid_bass_string_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="integer"):
            svc.set_bass("Living Room", "5")  # type: ignore[arg-type]

    def test_returns_authoritative_state_after_write(self) -> None:
        room = make_room()
        adapter = FakeAdapter(make_state(bass=0, treble=3, loudness=True))
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_bass("Living Room", 7)
        # Adapter re-read should have been called after write
        assert len(adapter.get_calls) == 1
        assert result.bass == 7
        assert result.treble == 3

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        svc = AudioSettingsService(FakeRoomService([]), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.set_bass("Unknown Room", 5)

    def test_bool_not_accepted_as_bass_level(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="integer"):
            svc.set_bass("Living Room", True)  # type: ignore[arg-type]


class TestSetTreble:
    def test_valid_treble_at_lower_boundary(self) -> None:
        room = make_room()
        adapter = FakeAdapter()
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_treble("Living Room", -10)
        assert adapter.set_treble_calls == [("192.168.1.10", -10)]
        assert result.treble == -10

    def test_valid_treble_at_upper_boundary(self) -> None:
        room = make_room()
        adapter = FakeAdapter()
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_treble("Living Room", 10)
        assert result.treble == 10

    def test_invalid_treble_below_range_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="treble"):
            svc.set_treble("Living Room", -11)

    def test_invalid_treble_above_range_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="treble"):
            svc.set_treble("Living Room", 11)

    def test_invalid_treble_float_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="integer"):
            svc.set_treble("Living Room", 2.5)  # type: ignore[arg-type]

    def test_invalid_treble_string_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="integer"):
            svc.set_treble("Living Room", "3")  # type: ignore[arg-type]

    def test_returns_authoritative_state_after_write(self) -> None:
        room = make_room()
        adapter = FakeAdapter(make_state(bass=2, treble=0, loudness=False))
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_treble("Living Room", -5)
        assert len(adapter.get_calls) == 1
        assert result.treble == -5
        assert result.bass == 2

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        svc = AudioSettingsService(FakeRoomService([]), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.set_treble("Unknown Room", 0)


class TestSetLoudness:
    def test_enables_loudness(self) -> None:
        room = make_room()
        adapter = FakeAdapter(make_state(loudness=False))
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_loudness("Living Room", True)
        assert adapter.set_loudness_calls == [("192.168.1.10", True)]
        assert result.loudness is True

    def test_disables_loudness(self) -> None:
        room = make_room()
        adapter = FakeAdapter(make_state(loudness=True))
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_loudness("Living Room", False)
        assert result.loudness is False

    def test_invalid_loudness_string_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="boolean"):
            svc.set_loudness("Living Room", "true")  # type: ignore[arg-type]

    def test_invalid_loudness_int_raises_audio_settings_error(self) -> None:
        room = make_room()
        svc = AudioSettingsService(FakeRoomService([room]), FakeAdapter())
        with pytest.raises(AudioSettingsError, match="boolean"):
            svc.set_loudness("Living Room", 1)  # type: ignore[arg-type]

    def test_returns_authoritative_state_after_write(self) -> None:
        room = make_room()
        adapter = FakeAdapter(make_state(bass=5, treble=-3, loudness=False))
        svc = AudioSettingsService(FakeRoomService([room]), adapter)
        result = svc.set_loudness("Living Room", True)
        assert len(adapter.get_calls) == 1
        assert result.loudness is True
        assert result.bass == 5

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        svc = AudioSettingsService(FakeRoomService([]), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.set_loudness("Unknown Room", True)
