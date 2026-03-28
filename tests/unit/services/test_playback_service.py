"""Unit tests for PlaybackService using fake RoomService and PlaybackAdapter."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import PlaybackError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import PlaybackState, Room, TrackInfo
from soniq_mcp.services.playback_service import PlaybackService


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
) -> Room:
    return Room(name=name, uid=uid, ip_address=ip_address, is_coordinator=True)


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


class FakePlaybackAdapter:
    def __init__(self, raise_error: bool = False) -> None:
        self._raise_error = raise_error
        self.calls: list[tuple[str, str]] = []  # (method, ip_address)

    def _track(self, method: str, ip_address: str) -> None:
        self.calls.append((method, ip_address))
        if self._raise_error:
            raise PlaybackError("zone unreachable")

    def play(self, ip_address: str) -> None:
        self._track("play", ip_address)

    def pause(self, ip_address: str) -> None:
        self._track("pause", ip_address)

    def stop(self, ip_address: str) -> None:
        self._track("stop", ip_address)

    def next_track(self, ip_address: str) -> None:
        self._track("next_track", ip_address)

    def previous_track(self, ip_address: str) -> None:
        self._track("previous_track", ip_address)

    def get_playback_state(self, ip_address: str, room_name: str) -> PlaybackState:
        self._track("get_playback_state", ip_address)
        return PlaybackState(transport_state="PLAYING", room_name=room_name)

    def get_track_info(self, ip_address: str) -> TrackInfo:
        self._track("get_track_info", ip_address)
        return TrackInfo(title="Test Song", artist="Test Artist")


def make_service(
    rooms: list[Room] | None = None,
    raise_discovery: bool = False,
    raise_playback: bool = False,
) -> tuple[PlaybackService, FakePlaybackAdapter]:
    room_svc = FakeRoomService(rooms=rooms, raise_discovery=raise_discovery)
    adapter = FakePlaybackAdapter(raise_error=raise_playback)
    svc = PlaybackService(room_service=room_svc, adapter=adapter)
    return svc, adapter


class TestPlaybackServicePlay:
    def test_play_delegates_to_adapter(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        svc.play("Living Room")
        assert ("play", "192.168.1.10") in adapter.calls

    def test_raises_room_not_found(self) -> None:
        svc, _ = make_service(rooms=[])
        with pytest.raises(RoomNotFoundError, match="Bedroom"):
            svc.play("Bedroom")

    def test_raises_discovery_error(self) -> None:
        svc, _ = make_service(raise_discovery=True)
        with pytest.raises(SonosDiscoveryError):
            svc.play("Living Room")

    def test_raises_playback_error(self) -> None:
        room = make_room("Living Room")
        svc, _ = make_service(rooms=[room], raise_playback=True)
        with pytest.raises(PlaybackError):
            svc.play("Living Room")


class TestPlaybackServicePause:
    def test_pause_delegates(self) -> None:
        room = make_room(ip_address="192.168.1.20")
        svc, adapter = make_service(rooms=[room])
        svc.pause("Living Room")
        assert ("pause", "192.168.1.20") in adapter.calls


class TestPlaybackServiceStop:
    def test_stop_delegates(self) -> None:
        room = make_room(ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        svc.stop("Living Room")
        assert ("stop", "192.168.1.10") in adapter.calls


class TestPlaybackServiceNextTrack:
    def test_next_delegates(self) -> None:
        room = make_room(ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        svc.next_track("Living Room")
        assert ("next_track", "192.168.1.10") in adapter.calls


class TestPlaybackServicePreviousTrack:
    def test_previous_delegates(self) -> None:
        room = make_room(ip_address="192.168.1.10")
        svc, adapter = make_service(rooms=[room])
        svc.previous_track("Living Room")
        assert ("previous_track", "192.168.1.10") in adapter.calls


class TestPlaybackServiceGetPlaybackState:
    def test_returns_playback_state(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, _ = make_service(rooms=[room])
        state = svc.get_playback_state("Living Room")
        assert isinstance(state, PlaybackState)
        assert state.transport_state == "PLAYING"
        assert state.room_name == "Living Room"

    def test_raises_room_not_found(self) -> None:
        svc, _ = make_service(rooms=[])
        with pytest.raises(RoomNotFoundError):
            svc.get_playback_state("Nowhere")


class TestPlaybackServiceGetTrackInfo:
    def test_returns_track_info(self) -> None:
        room = make_room("Living Room", ip_address="192.168.1.10")
        svc, _ = make_service(rooms=[room])
        info = svc.get_track_info("Living Room")
        assert isinstance(info, TrackInfo)
        assert info.title == "Test Song"

    def test_raises_room_not_found(self) -> None:
        svc, _ = make_service(rooms=[])
        with pytest.raises(RoomNotFoundError):
            svc.get_track_info("Nowhere")
