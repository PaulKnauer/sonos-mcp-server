"""Unit tests for VolumeAdapter using a fake SoCo zone."""

from __future__ import annotations

import pytest

from soniq_mcp.adapters.volume_adapter import VolumeAdapter
from soniq_mcp.domain.exceptions import VolumeError


class FakeSoCoZone:
    """Fake SoCo zone that stores volume and mute in memory."""

    def __init__(self, volume: int = 50, mute: bool = False) -> None:
        self._volume = volume
        self._mute = mute

    @property
    def volume(self) -> int:
        return self._volume

    @volume.setter
    def volume(self, value: int) -> None:
        self._volume = value

    @property
    def mute(self) -> bool:
        return self._mute

    @mute.setter
    def mute(self, value: bool) -> None:
        self._mute = value


class ErrorSoCoZone:
    """Fake SoCo zone that raises on all property access."""

    @property
    def volume(self) -> int:
        raise RuntimeError("SoCo network error")

    @volume.setter
    def volume(self, value: int) -> None:
        raise RuntimeError("SoCo network error")

    @property
    def mute(self) -> bool:
        raise RuntimeError("SoCo network error")

    @mute.setter
    def mute(self, value: bool) -> None:
        raise RuntimeError("SoCo network error")


class FakeVolumeAdapter(VolumeAdapter):
    """VolumeAdapter subclass that uses a fake SoCo zone instead of the real one."""

    def __init__(self, zone: FakeSoCoZone | ErrorSoCoZone) -> None:
        self._zone = zone

    def _get_zone(self, ip_address: str) -> FakeSoCoZone | ErrorSoCoZone:
        return self._zone

    def get_volume(self, ip_address: str) -> int:
        try:
            return self._get_zone(ip_address).volume
        except Exception as exc:
            raise VolumeError(f"Failed to get volume from {ip_address}: {exc}") from exc

    def set_volume(self, ip_address: str, volume: int) -> None:
        try:
            self._get_zone(ip_address).volume = volume
        except Exception as exc:
            raise VolumeError(f"Failed to set volume on {ip_address}: {exc}") from exc

    def get_mute(self, ip_address: str) -> bool:
        try:
            return self._get_zone(ip_address).mute
        except Exception as exc:
            raise VolumeError(f"Failed to get mute state from {ip_address}: {exc}") from exc

    def set_mute(self, ip_address: str, muted: bool) -> None:
        try:
            self._get_zone(ip_address).mute = muted
        except Exception as exc:
            raise VolumeError(f"Failed to set mute on {ip_address}: {exc}") from exc


IP = "192.168.1.10"


class TestVolumeAdapterGetVolume:
    def test_returns_current_volume(self) -> None:
        adapter = FakeVolumeAdapter(FakeSoCoZone(volume=42))
        assert adapter.get_volume(IP) == 42

    def test_raises_volume_error_on_soco_failure(self) -> None:
        adapter = FakeVolumeAdapter(ErrorSoCoZone())
        with pytest.raises(VolumeError, match="Failed to get volume"):
            adapter.get_volume(IP)


class TestVolumeAdapterSetVolume:
    def test_sets_volume(self) -> None:
        zone = FakeSoCoZone(volume=30)
        adapter = FakeVolumeAdapter(zone)
        adapter.set_volume(IP, 75)
        assert zone.volume == 75

    def test_raises_volume_error_on_soco_failure(self) -> None:
        adapter = FakeVolumeAdapter(ErrorSoCoZone())
        with pytest.raises(VolumeError, match="Failed to set volume"):
            adapter.set_volume(IP, 50)


class TestVolumeAdapterGetMute:
    def test_returns_false_when_not_muted(self) -> None:
        adapter = FakeVolumeAdapter(FakeSoCoZone(mute=False))
        assert adapter.get_mute(IP) is False

    def test_returns_true_when_muted(self) -> None:
        adapter = FakeVolumeAdapter(FakeSoCoZone(mute=True))
        assert adapter.get_mute(IP) is True

    def test_raises_volume_error_on_soco_failure(self) -> None:
        adapter = FakeVolumeAdapter(ErrorSoCoZone())
        with pytest.raises(VolumeError, match="Failed to get mute"):
            adapter.get_mute(IP)


class TestVolumeAdapterSetMute:
    def test_mutes_zone(self) -> None:
        zone = FakeSoCoZone(mute=False)
        adapter = FakeVolumeAdapter(zone)
        adapter.set_mute(IP, True)
        assert zone.mute is True

    def test_unmutes_zone(self) -> None:
        zone = FakeSoCoZone(mute=True)
        adapter = FakeVolumeAdapter(zone)
        adapter.set_mute(IP, False)
        assert zone.mute is False

    def test_raises_volume_error_on_soco_failure(self) -> None:
        adapter = FakeVolumeAdapter(ErrorSoCoZone())
        with pytest.raises(VolumeError, match="Failed to set mute"):
            adapter.set_mute(IP, True)
