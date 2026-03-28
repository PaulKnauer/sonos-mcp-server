"""Unit tests for VolumeService using fake RoomService and VolumeAdapter."""

from __future__ import annotations

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import (
    RoomNotFoundError,
    SonosDiscoveryError,
    VolumeCapExceeded,
    VolumeError,
)
from soniq_mcp.domain.models import Room, VolumeState
from soniq_mcp.services.volume_service import VolumeService


def make_room(
    name: str = "Living Room",
    ip_address: str = "192.168.1.10",
) -> Room:
    return Room(
        name=name,
        uid="RINCON_001",
        ip_address=ip_address,
        is_coordinator=True,
    )


class FakeRoomService:
    """Fake RoomService that returns a single room or raises errors."""

    def __init__(
        self,
        room: Room | None = None,
        raise_not_found: bool = False,
        raise_discovery: bool = False,
    ) -> None:
        self._room = room or make_room()
        self._raise_not_found = raise_not_found
        self._raise_discovery = raise_discovery

    def get_room(self, name: str, timeout: float = 5.0) -> Room:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_not_found:
            raise RoomNotFoundError(name)
        return self._room


class FakeVolumeAdapter:
    """Fake VolumeAdapter with in-memory volume and mute state."""

    def __init__(
        self,
        volume: int = 50,
        muted: bool = False,
        raise_error: bool = False,
    ) -> None:
        self.volume = volume
        self.muted = muted
        self.raise_error = raise_error

    def get_volume(self, ip_address: str) -> int:
        if self.raise_error:
            raise VolumeError("SoCo volume error")
        return self.volume

    def set_volume(self, ip_address: str, volume: int) -> None:
        if self.raise_error:
            raise VolumeError("SoCo volume error")
        self.volume = volume

    def get_mute(self, ip_address: str) -> bool:
        if self.raise_error:
            raise VolumeError("SoCo mute error")
        return self.muted

    def set_mute(self, ip_address: str, muted: bool) -> None:
        if self.raise_error:
            raise VolumeError("SoCo mute error")
        self.muted = muted


def make_service(
    room: Room | None = None,
    volume: int = 50,
    muted: bool = False,
    raise_not_found: bool = False,
    raise_discovery: bool = False,
    raise_adapter_error: bool = False,
    max_volume_pct: int = 80,
) -> tuple[VolumeService, FakeVolumeAdapter]:
    config = SoniqConfig(max_volume_pct=max_volume_pct)
    room_svc = FakeRoomService(
        room=room,
        raise_not_found=raise_not_found,
        raise_discovery=raise_discovery,
    )
    adapter = FakeVolumeAdapter(volume=volume, muted=muted, raise_error=raise_adapter_error)
    svc = VolumeService(room_svc, adapter, config)
    return svc, adapter


class TestGetVolumeState:
    def test_returns_volume_state(self) -> None:
        svc, _ = make_service(volume=60, muted=False)
        state = svc.get_volume_state("Living Room")
        assert isinstance(state, VolumeState)
        assert state.room_name == "Living Room"
        assert state.volume == 60
        assert state.is_muted is False

    def test_returns_muted_state(self) -> None:
        svc, _ = make_service(volume=0, muted=True)
        state = svc.get_volume_state("Living Room")
        assert state.is_muted is True

    def test_propagates_room_not_found(self) -> None:
        svc, _ = make_service(raise_not_found=True)
        with pytest.raises(RoomNotFoundError):
            svc.get_volume_state("Unknown Room")

    def test_propagates_discovery_error(self) -> None:
        svc, _ = make_service(raise_discovery=True)
        with pytest.raises(SonosDiscoveryError):
            svc.get_volume_state("Living Room")

    def test_propagates_volume_error(self) -> None:
        svc, _ = make_service(raise_adapter_error=True)
        with pytest.raises(VolumeError):
            svc.get_volume_state("Living Room")


class TestSetVolume:
    def test_sets_volume_on_adapter(self) -> None:
        svc, adapter = make_service(volume=50)
        svc.set_volume("Living Room", 70)
        assert adapter.volume == 70

    def test_raises_volume_cap_exceeded(self) -> None:
        svc, _ = make_service(max_volume_pct=60)
        with pytest.raises(VolumeCapExceeded) as exc_info:
            svc.set_volume("Living Room", 75)
        assert exc_info.value.requested == 75
        assert exc_info.value.cap == 60

    def test_raises_value_error_for_out_of_range(self) -> None:
        svc, _ = make_service()
        with pytest.raises(ValueError):
            svc.set_volume("Living Room", 110)

    def test_raises_value_error_for_negative(self) -> None:
        svc, _ = make_service()
        with pytest.raises(ValueError):
            svc.set_volume("Living Room", -1)

    def test_propagates_room_not_found(self) -> None:
        svc, _ = make_service(raise_not_found=True)
        with pytest.raises(RoomNotFoundError):
            svc.set_volume("Unknown Room", 50)

    def test_propagates_volume_error(self) -> None:
        svc, _ = make_service(raise_adapter_error=True)
        with pytest.raises(VolumeError):
            svc.set_volume("Living Room", 50)


class TestAdjustVolume:
    def test_increases_volume(self) -> None:
        svc, adapter = make_service(volume=40)
        state = svc.adjust_volume("Living Room", 10)
        assert state.volume == 50
        assert adapter.volume == 50

    def test_decreases_volume(self) -> None:
        svc, adapter = make_service(volume=40)
        state = svc.adjust_volume("Living Room", -15)
        assert state.volume == 25
        assert adapter.volume == 25

    def test_floors_at_zero_for_large_negative_delta(self) -> None:
        svc, adapter = make_service(volume=10)
        state = svc.adjust_volume("Living Room", -50)
        assert state.volume == 0
        assert adapter.volume == 0

    def test_raises_volume_cap_exceeded_for_large_positive_delta(self) -> None:
        svc, _ = make_service(volume=70, max_volume_pct=80)
        with pytest.raises(VolumeCapExceeded):
            svc.adjust_volume("Living Room", 20)

    def test_returns_volume_state_with_mute(self) -> None:
        svc, _ = make_service(volume=40, muted=True)
        state = svc.adjust_volume("Living Room", 5)
        assert state.is_muted is True
        assert state.room_name == "Living Room"

    def test_propagates_room_not_found(self) -> None:
        svc, _ = make_service(raise_not_found=True)
        with pytest.raises(RoomNotFoundError):
            svc.adjust_volume("Unknown Room", 5)


class TestMute:
    def test_mutes_room(self) -> None:
        svc, adapter = make_service(muted=False)
        svc.mute("Living Room")
        assert adapter.muted is True

    def test_propagates_room_not_found(self) -> None:
        svc, _ = make_service(raise_not_found=True)
        with pytest.raises(RoomNotFoundError):
            svc.mute("Unknown Room")

    def test_propagates_volume_error(self) -> None:
        svc, _ = make_service(raise_adapter_error=True)
        with pytest.raises(VolumeError):
            svc.mute("Living Room")


class TestUnmute:
    def test_unmutes_room(self) -> None:
        svc, adapter = make_service(muted=True)
        svc.unmute("Living Room")
        assert adapter.muted is False

    def test_propagates_room_not_found(self) -> None:
        svc, _ = make_service(raise_not_found=True)
        with pytest.raises(RoomNotFoundError):
            svc.unmute("Unknown Room")

    def test_propagates_volume_error(self) -> None:
        svc, _ = make_service(raise_adapter_error=True)
        with pytest.raises(VolumeError):
            svc.unmute("Living Room")
