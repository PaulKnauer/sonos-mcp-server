"""Unit tests for shared SonosService orchestration."""

from __future__ import annotations

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import RoomNotFoundError, SonosDiscoveryError, VolumeCapExceeded
from soniq_mcp.domain.models import PlaybackState, Room, TrackInfo, VolumeState
from soniq_mcp.services.sonos_service import SonosService


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
    def __init__(self, rooms: list[Room] | None = None, raise_discovery: bool = False) -> None:
        self._rooms = {room.name.lower(): room for room in (rooms or [])}
        self._raise_discovery = raise_discovery

    def get_room(self, name: str, timeout: float = 5.0) -> Room:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        room = self._rooms.get(name.strip().lower())
        if room is None:
            raise RoomNotFoundError(name)
        return room

    def list_rooms(self, timeout: float = 5.0) -> list[Room]:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        return list(self._rooms.values())


class FakeSoCoAdapter:
    def __init__(self, volume: int = 40, muted: bool = False) -> None:
        self.volume = volume
        self.muted = muted
        self.calls: list[tuple[str, str, object | None]] = []

    def play(self, ip_address: str) -> None:
        self.calls.append(("play", ip_address, None))

    def get_playback_state(self, ip_address: str, room_name: str) -> PlaybackState:
        self.calls.append(("get_playback_state", ip_address, room_name))
        return PlaybackState(transport_state="PLAYING", room_name=room_name)

    def get_track_info(self, ip_address: str) -> TrackInfo:
        self.calls.append(("get_track_info", ip_address, None))
        return TrackInfo(title="Song")

    def get_volume(self, ip_address: str) -> int:
        self.calls.append(("get_volume", ip_address, None))
        return self.volume

    def set_volume(self, ip_address: str, volume: int) -> None:
        self.calls.append(("set_volume", ip_address, volume))
        self.volume = volume

    def get_mute(self, ip_address: str) -> bool:
        self.calls.append(("get_mute", ip_address, None))
        return self.muted

    def set_mute(self, ip_address: str, muted: bool) -> None:
        self.calls.append(("set_mute", ip_address, muted))
        self.muted = muted


def make_service(
    rooms: list[Room] | None = None,
    volume: int = 40,
    muted: bool = False,
    max_volume_pct: int = 80,
) -> tuple[SonosService, FakeSoCoAdapter]:
    room_service = FakeRoomService(rooms=rooms or [make_room()])
    adapter = FakeSoCoAdapter(volume=volume, muted=muted)
    service = SonosService(room_service, adapter, SoniqConfig(max_volume_pct=max_volume_pct))
    return service, adapter


class TestPlaybackOrchestration:
    def test_play_uses_room_ip(self) -> None:
        service, adapter = make_service()
        service.play("Living Room")
        assert ("play", "192.168.1.10", None) in adapter.calls

    def test_get_track_info_routes_group_member_to_coordinator(self) -> None:
        coordinator = make_room(uid="RINCON_COORD", ip_address="192.168.1.10")
        member = make_room(
            name="Kitchen",
            uid="RINCON_MEMBER",
            ip_address="192.168.1.11",
            is_coordinator=False,
            group_coordinator_uid="RINCON_COORD",
        )
        service, adapter = make_service(rooms=[coordinator, member])
        info = service.get_track_info("Kitchen")
        assert isinstance(info, TrackInfo)
        assert ("get_track_info", "192.168.1.10", None) in adapter.calls


class TestVolumeOrchestration:
    def test_get_volume_state_returns_domain_model(self) -> None:
        service, _ = make_service(volume=55, muted=True)
        state = service.get_volume_state("Living Room")
        assert isinstance(state, VolumeState)
        assert state.volume == 55
        assert state.is_muted is True

    def test_adjust_volume_clamps_and_returns_state(self) -> None:
        service, adapter = make_service(volume=10)
        state = service.adjust_volume("Living Room", -30)
        assert state.volume == 0
        assert adapter.volume == 0

    def test_set_volume_enforces_cap(self) -> None:
        service, _ = make_service(max_volume_pct=60)
        with pytest.raises(VolumeCapExceeded):
            service.set_volume("Living Room", 70)
