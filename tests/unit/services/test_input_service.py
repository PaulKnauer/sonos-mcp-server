"""Unit tests for InputService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import InputError, InputValidationError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import InputState, Room, Speaker
from soniq_mcp.services.input_service import InputService


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


def make_speaker(
    *,
    room_name: str = "Living Room",
    room_uid: str = "RINCON_001",
    supports_line_in: bool = False,
    supports_tv: bool = False,
) -> Speaker:
    return Speaker(
        name=room_name,
        uid=f"{room_uid}-speaker",
        ip_address="192.168.1.10",
        room_name=room_name,
        room_uid=room_uid,
        model_name="Test Device",
        is_visible=True,
        supports_line_in=supports_line_in,
        supports_tv=supports_tv,
    )


class FakeRoomService:
    def __init__(
        self,
        rooms: list[Room],
        speakers: list[Speaker],
        *,
        raise_discovery_in_speakers: bool = False,
    ) -> None:
        self._rooms = {room.name: room for room in rooms}
        self._speakers = list(speakers)
        self._raise_discovery_in_speakers = raise_discovery_in_speakers

    def get_room(self, name: str) -> Room:
        if name not in self._rooms:
            raise RoomNotFoundError(name)
        return self._rooms[name]

    def list_rooms(self) -> list[Room]:
        return list(self._rooms.values())

    def get_speakers_for_room(self, name: str) -> list[Speaker]:
        if self._raise_discovery_in_speakers:
            raise SonosDiscoveryError("network unreachable")
        room = self.get_room(name)
        return [speaker for speaker in self._speakers if speaker.room_uid == room.uid]


class FakeAdapter:
    def __init__(self, source: str = "TV") -> None:
        self.source = source
        self.line_in_calls: list[str] = []
        self.tv_calls: list[str] = []

    def switch_to_line_in(self, ip_address: str) -> None:
        self.line_in_calls.append(ip_address)
        self.source = "LINE_IN"

    def switch_to_tv(self, ip_address: str) -> None:
        self.tv_calls.append(ip_address)
        self.source = "TV"

    def get_music_source(self, ip_address: str) -> str:
        return self.source


def test_switch_to_line_in_returns_normalized_state() -> None:
    room = make_room()
    svc = InputService(
        FakeRoomService([room], [make_speaker(supports_line_in=True)]),
        FakeAdapter(source="LINE_IN"),
    )

    result = svc.switch_to_line_in("Living Room")

    assert result == InputState(
        room_name="Living Room",
        input_source="line_in",
        coordinator_room_name="Living Room",
    )


def test_switch_to_tv_returns_normalized_state() -> None:
    room = make_room()
    svc = InputService(
        FakeRoomService([room], [make_speaker(supports_tv=True)]),
        FakeAdapter(source="TV"),
    )

    result = svc.switch_to_tv("Living Room")

    assert result.input_source == "tv"
    assert result.room_name == "Living Room"


def test_switch_to_tv_uses_group_coordinator_name_when_present() -> None:
    coordinator = make_room(name="Kitchen", uid="RINCON_002", ip_address="192.168.1.20")
    member = make_room(
        name="Living Room",
        uid="RINCON_001",
        group_coordinator_uid="RINCON_002",
        is_coordinator=False,
    )
    svc = InputService(
        FakeRoomService([coordinator, member], [make_speaker(supports_tv=True)]),
        FakeAdapter(source="TV"),
    )

    result = svc.switch_to_tv("Living Room")

    assert result.coordinator_room_name == "Kitchen"


def test_line_in_requires_capability_support() -> None:
    svc = InputService(
        FakeRoomService([make_room()], [make_speaker(supports_line_in=False)]),
        FakeAdapter(),
    )

    with pytest.raises(InputValidationError, match="line-in"):
        svc.switch_to_line_in("Living Room")


def test_tv_requires_capability_support() -> None:
    svc = InputService(
        FakeRoomService([make_room()], [make_speaker(supports_tv=False)]),
        FakeAdapter(),
    )

    with pytest.raises(InputValidationError, match="TV"):
        svc.switch_to_tv("Living Room")


def test_missing_speaker_capability_data_raises_input_error() -> None:
    svc = InputService(FakeRoomService([make_room()], []), FakeAdapter())

    with pytest.raises(InputError, match="capability data"):
        svc.switch_to_tv("Living Room")


def test_room_not_found_propagates() -> None:
    svc = InputService(FakeRoomService([], []), FakeAdapter())

    with pytest.raises(RoomNotFoundError):
        svc.switch_to_tv("Missing")


def test_unrecognized_music_source_raises_input_error() -> None:
    class _StuckAdapter(FakeAdapter):
        """Adapter whose music_source never changes regardless of switch calls."""

        def switch_to_line_in(self, ip_address: str) -> None:
            self.line_in_calls.append(ip_address)

        def switch_to_tv(self, ip_address: str) -> None:
            self.tv_calls.append(ip_address)

    room = make_room()
    svc = InputService(
        FakeRoomService([room], [make_speaker(supports_line_in=True)]),
        _StuckAdapter(source="UNKNOWN"),
    )

    with pytest.raises(InputError, match="Unrecognized music source"):
        svc.switch_to_line_in("Living Room")


def test_discovery_error_in_speakers_propagates() -> None:
    svc = InputService(
        FakeRoomService([make_room()], [], raise_discovery_in_speakers=True),
        FakeAdapter(),
    )

    with pytest.raises(SonosDiscoveryError):
        svc.switch_to_tv("Living Room")
