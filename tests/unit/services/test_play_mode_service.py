"""Unit tests for PlayModeService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import PlaybackError, RoomNotFoundError
from soniq_mcp.domain.models import PlayModeState, Room
from soniq_mcp.services.play_mode_service import PlayModeService


def make_room(
    name: str = "Living Room",
    ip: str = "192.168.1.10",
    uid: str = "RINCON_1",
    is_coordinator: bool = True,
    coordinator_uid: str | None = None,
) -> Room:
    return Room(
        name=name,
        uid=uid,
        ip_address=ip,
        is_coordinator=is_coordinator,
        group_coordinator_uid=coordinator_uid,
    )


def make_play_mode_state(room_name: str = "Living Room") -> PlayModeState:
    return PlayModeState(
        room_name=room_name,
        shuffle=False,
        repeat="none",
        cross_fade=False,
    )


class FakeRoomService:
    def __init__(self, rooms: list[Room]) -> None:
        self._rooms = {r.name: r for r in rooms}

    def get_room(self, name: str) -> Room:
        if name not in self._rooms:
            raise RoomNotFoundError(name)
        return self._rooms[name]

    def list_rooms(self) -> list[Room]:
        return list(self._rooms.values())


class FakeAdapter:
    def __init__(self, state: PlayModeState | None = None) -> None:
        self._state = state or make_play_mode_state()
        self.get_calls: list[tuple[str, str]] = []
        self.set_calls: list[tuple] = []

    def get_play_mode(self, ip_address: str, room_name: str) -> PlayModeState:
        self.get_calls.append((ip_address, room_name))
        return PlayModeState(
            room_name=room_name,
            shuffle=self._state.shuffle,
            repeat=self._state.repeat,
            cross_fade=self._state.cross_fade,
        )

    def set_play_mode(
        self,
        ip_address: str,
        room_name: str,
        shuffle=None,
        repeat=None,
        cross_fade=None,
    ) -> PlayModeState:
        self.set_calls.append((ip_address, room_name, shuffle, repeat, cross_fade))
        new_shuffle = shuffle if shuffle is not None else self._state.shuffle
        new_repeat = repeat if repeat is not None else self._state.repeat
        new_cross_fade = cross_fade if cross_fade is not None else self._state.cross_fade
        return PlayModeState(
            room_name=room_name,
            shuffle=new_shuffle,
            repeat=new_repeat,
            cross_fade=new_cross_fade,
        )


class TestGetPlayMode:
    def test_delegates_to_adapter_with_room_ip(self) -> None:
        room = make_room(name="Living Room", ip="192.168.1.10")
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        svc.get_play_mode("Living Room")

        assert adapter.get_calls == [("192.168.1.10", "Living Room")]

    def test_routes_to_coordinator_ip_for_grouped_room(self) -> None:
        coordinator = make_room(
            name="Kitchen",
            ip="192.168.1.20",
            uid="RINCON_2",
            is_coordinator=True,
        )
        member = make_room(
            name="Living Room",
            ip="192.168.1.10",
            uid="RINCON_1",
            is_coordinator=False,
            coordinator_uid="RINCON_2",
        )
        room_svc = FakeRoomService([coordinator, member])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        svc.get_play_mode("Living Room")

        # Must use coordinator's IP, not the member's IP
        assert adapter.get_calls[0][0] == "192.168.1.20"

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        room_svc = FakeRoomService([])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        with pytest.raises(RoomNotFoundError):
            svc.get_play_mode("Unknown Room")


class TestSetPlayMode:
    def test_delegates_shuffle_to_adapter(self) -> None:
        room = make_room()
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        result = svc.set_play_mode("Living Room", shuffle=True)

        assert adapter.set_calls[0][2] is True  # shuffle arg
        assert result.shuffle is True

    def test_routes_set_to_coordinator_ip(self) -> None:
        coordinator = make_room(
            name="Kitchen",
            ip="192.168.1.20",
            uid="RINCON_2",
            is_coordinator=True,
        )
        member = make_room(
            name="Living Room",
            ip="192.168.1.10",
            uid="RINCON_1",
            is_coordinator=False,
            coordinator_uid="RINCON_2",
        )
        room_svc = FakeRoomService([coordinator, member])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        svc.set_play_mode("Living Room", repeat="all")

        assert adapter.set_calls[0][0] == "192.168.1.20"

    def test_rejects_invalid_repeat_value(self) -> None:
        room = make_room()
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        with pytest.raises(PlaybackError, match="repeat"):
            svc.set_play_mode("Living Room", repeat="loop")

    def test_rejects_non_boolean_shuffle_value(self) -> None:
        room = make_room()
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        with pytest.raises(PlaybackError, match="shuffle"):
            svc.set_play_mode("Living Room", shuffle="true")  # type: ignore[arg-type]

    def test_rejects_non_boolean_cross_fade_value(self) -> None:
        room = make_room()
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        with pytest.raises(PlaybackError, match="cross_fade"):
            svc.set_play_mode("Living Room", cross_fade="true")  # type: ignore[arg-type]

    def test_accepts_all_valid_repeat_values(self) -> None:
        room = make_room()
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        for value in ("none", "all", "one"):
            svc.set_play_mode("Living Room", repeat=value)  # must not raise

    def test_none_repeat_not_validated(self) -> None:
        room = make_room()
        room_svc = FakeRoomService([room])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        svc.set_play_mode("Living Room")  # all None — no validation error

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        room_svc = FakeRoomService([])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        with pytest.raises(RoomNotFoundError):
            svc.set_play_mode("Unknown Room", shuffle=True)

    def test_falls_back_to_room_ip_when_coordinator_uid_not_found(self) -> None:
        member = make_room(
            name="Living Room",
            ip="192.168.1.10",
            uid="RINCON_1",
            is_coordinator=False,
            coordinator_uid="RINCON_MISSING",
        )
        room_svc = FakeRoomService([member])
        adapter = FakeAdapter()
        svc = PlayModeService(room_svc, adapter, None)

        svc.get_play_mode("Living Room")

        # Falls back to the room's own IP
        assert adapter.get_calls[0][0] == "192.168.1.10"
