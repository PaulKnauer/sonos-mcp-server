"""Unit tests for seek and sleep timer operations in PlaybackService / SonosService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import PlaybackError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import PlaybackState, Room, SleepTimerState
from soniq_mcp.services.playback_service import PlaybackService


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
    is_coordinator: bool = True,
    group_coordinator_uid: str | None = None,
) -> Room:
    return Room(
        name=name,
        uid=uid,
        ip_address=ip_address,
        is_coordinator=is_coordinator,
        group_coordinator_uid=group_coordinator_uid,
    )


class FakeRoomService:
    def __init__(
        self,
        rooms: list[Room] | None = None,
        raise_discovery: bool = False,
    ) -> None:
        self._rooms = {r.name.lower(): r for r in (rooms or [])}
        self._raise_discovery = raise_discovery

    def get_room(self, name: str, timeout: float = 5.0) -> Room:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        normalised = name.strip().lower()
        if normalised not in self._rooms:
            raise RoomNotFoundError(name)
        return self._rooms[normalised]

    def list_rooms(self, timeout: float = 5.0) -> list[Room]:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        return list(self._rooms.values())


class FakeAdapter:
    def __init__(self, raise_error: bool = False) -> None:
        self._raise_error = raise_error
        self.seek_calls: list[tuple[str, str]] = []
        self.get_sleep_timer_calls: list[str] = []
        self.set_sleep_timer_calls: list[tuple[str, str, int]] = []
        self.get_playback_state_calls: list[str] = []

    def _maybe_raise(self) -> None:
        if self._raise_error:
            raise PlaybackError("zone unreachable")

    def seek(self, ip_address: str, position: str) -> None:
        self.seek_calls.append((ip_address, position))
        self._maybe_raise()

    def get_sleep_timer(self, ip_address: str, room_name: str) -> SleepTimerState:
        self.get_sleep_timer_calls.append(ip_address)
        self._maybe_raise()
        return SleepTimerState(
            room_name=room_name,
            active=True,
            remaining_seconds=600,
            remaining_minutes=10,
        )

    def set_sleep_timer(self, ip_address: str, room_name: str, minutes: int) -> SleepTimerState:
        self.set_sleep_timer_calls.append((ip_address, room_name, minutes))
        self._maybe_raise()
        if minutes == 0:
            return SleepTimerState(room_name=room_name, active=False)
        return SleepTimerState(
            room_name=room_name,
            active=True,
            remaining_seconds=minutes * 60,
            remaining_minutes=minutes,
        )

    def get_playback_state(self, ip_address: str, room_name: str) -> PlaybackState:
        self.get_playback_state_calls.append(ip_address)
        return PlaybackState(transport_state="PLAYING", room_name=room_name)

    # passthrough stubs needed by SonosService construction
    def play(self, ip_address: str) -> None: ...
    def pause(self, ip_address: str) -> None: ...
    def stop(self, ip_address: str) -> None: ...
    def next_track(self, ip_address: str) -> None: ...
    def previous_track(self, ip_address: str) -> None: ...
    def get_track_info(self, ip_address: str): ...
    def get_volume(self, ip_address: str) -> int:
        return 50

    def get_mute(self, ip_address: str) -> bool:
        return False


def make_service(
    rooms: list[Room] | None = None,
    raise_discovery: bool = False,
    raise_playback: bool = False,
) -> tuple[PlaybackService, FakeAdapter]:
    from soniq_mcp.config.models import SoniqConfig
    from soniq_mcp.services.sonos_service import SonosService

    room_svc = FakeRoomService(rooms=rooms, raise_discovery=raise_discovery)
    adapter = FakeAdapter(raise_error=raise_playback)
    sonos_svc = SonosService(room_svc, adapter, SoniqConfig())
    svc = PlaybackService(sonos_service=sonos_svc)
    return svc, adapter


# ── Seek ─────────────────────────────────────────────────────────────────────


class TestSeek:
    def test_valid_position_calls_adapter(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        state = svc.seek("Living Room", "0:01:30")
        assert ("192.168.1.10", "0:01:30") in adapter.seek_calls
        assert isinstance(state, PlaybackState)

    def test_returns_playback_state_after_seek(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        state = svc.seek("Living Room", "0:30:00")
        assert state.transport_state == "PLAYING"
        assert state.room_name == "Living Room"
        assert adapter.get_playback_state_calls == ["192.168.1.10"]

    def test_invalid_position_raises_playback_error(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room])
        with pytest.raises(PlaybackError, match="Invalid seek position"):
            svc.seek("Living Room", "90")

    def test_invalid_position_missing_seconds_raises(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room])
        with pytest.raises(PlaybackError, match="Invalid seek position"):
            svc.seek("Living Room", "01:30")

    def test_invalid_position_free_form_raises(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room])
        with pytest.raises(PlaybackError, match="Invalid seek position"):
            svc.seek("Living Room", "1 minute 30 seconds")

    def test_invalid_position_with_out_of_range_minutes_raises(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room])
        with pytest.raises(PlaybackError, match="Minutes and seconds must be < 60"):
            svc.seek("Living Room", "00:99:00")

    def test_invalid_position_with_out_of_range_seconds_raises(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room])
        with pytest.raises(PlaybackError, match="Minutes and seconds must be < 60"):
            svc.seek("Living Room", "00:00:99")

    def test_grouped_room_routes_to_coordinator(self) -> None:
        coordinator = make_room("Living Room", uid="RINCON_COORD", ip_address="192.168.1.10")
        member = make_room(
            "Kitchen",
            uid="RINCON_MEMBER",
            ip_address="192.168.1.11",
            is_coordinator=False,
            group_coordinator_uid="RINCON_COORD",
        )
        svc, adapter = make_service(rooms=[coordinator, member])
        svc.seek("Kitchen", "0:01:00")
        assert ("192.168.1.10", "0:01:00") in adapter.seek_calls
        assert adapter.get_playback_state_calls == ["192.168.1.10"]

    def test_room_not_found_raises(self) -> None:
        svc, _ = make_service(rooms=[])
        with pytest.raises(RoomNotFoundError):
            svc.seek("Nowhere", "0:01:00")

    def test_discovery_error_propagates(self) -> None:
        svc, _ = make_service(raise_discovery=True)
        with pytest.raises(SonosDiscoveryError):
            svc.seek("Living Room", "0:01:00")


# ── Get Sleep Timer ──────────────────────────────────────────────────────────


class TestGetSleepTimer:
    def test_returns_sleep_timer_state(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        state = svc.get_sleep_timer("Living Room")
        assert isinstance(state, SleepTimerState)
        assert "192.168.1.10" in adapter.get_sleep_timer_calls

    def test_grouped_room_routes_to_coordinator(self) -> None:
        coordinator = make_room("Living Room", uid="RINCON_COORD", ip_address="192.168.1.10")
        member = make_room(
            "Kitchen",
            uid="RINCON_MEMBER",
            ip_address="192.168.1.11",
            is_coordinator=False,
            group_coordinator_uid="RINCON_COORD",
        )
        svc, adapter = make_service(rooms=[coordinator, member])
        svc.get_sleep_timer("Kitchen")
        assert "192.168.1.10" in adapter.get_sleep_timer_calls

    def test_room_not_found_raises(self) -> None:
        svc, _ = make_service(rooms=[])
        with pytest.raises(RoomNotFoundError):
            svc.get_sleep_timer("Nowhere")

    def test_discovery_error_propagates(self) -> None:
        svc, _ = make_service(raise_discovery=True)
        with pytest.raises(SonosDiscoveryError):
            svc.get_sleep_timer("Living Room")


# ── Set Sleep Timer ──────────────────────────────────────────────────────────


class TestSetSleepTimer:
    def test_valid_minutes_calls_adapter(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        state = svc.set_sleep_timer("Living Room", 30)
        assert ("192.168.1.10", "Living Room", 30) in adapter.set_sleep_timer_calls
        assert state.active is True

    def test_zero_minutes_clears_timer(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        state = svc.set_sleep_timer("Living Room", 0)
        assert ("192.168.1.10", "Living Room", 0) in adapter.set_sleep_timer_calls
        assert state.active is False

    def test_negative_minutes_raises_playback_error(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room])
        with pytest.raises(PlaybackError, match="Invalid minutes"):
            svc.set_sleep_timer("Living Room", -1)

    def test_grouped_room_routes_to_coordinator(self) -> None:
        coordinator = make_room("Living Room", uid="RINCON_COORD", ip_address="192.168.1.10")
        member = make_room(
            "Kitchen",
            uid="RINCON_MEMBER",
            ip_address="192.168.1.11",
            is_coordinator=False,
            group_coordinator_uid="RINCON_COORD",
        )
        svc, adapter = make_service(rooms=[coordinator, member])
        svc.set_sleep_timer("Kitchen", 15)
        assert ("192.168.1.10", "Kitchen", 15) in adapter.set_sleep_timer_calls

    def test_room_not_found_raises(self) -> None:
        svc, _ = make_service(rooms=[])
        with pytest.raises(RoomNotFoundError):
            svc.set_sleep_timer("Nowhere", 10)

    def test_discovery_error_propagates(self) -> None:
        svc, _ = make_service(raise_discovery=True)
        with pytest.raises(SonosDiscoveryError):
            svc.set_sleep_timer("Living Room", 10)
