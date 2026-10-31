"""Unit tests for DeviceService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import DeviceError, RoomNotFoundError
from soniq_mcp.domain.models import BatteryInfo, Room
from soniq_mcp.services.device_service import DeviceService

ROOM = Room(name="Patio", uid="UID1", ip_address="192.168.1.20", is_coordinator=True)


class FakeDeviceAdapter:
    def __init__(self, info=None, error=None):
        self._info = info
        self._error = error
        self.calls: list[tuple[str, str]] = []

    def get_battery_info(self, ip_address, room_name):
        self.calls.append((ip_address, room_name))
        if self._error:
            raise self._error
        return self._info or BatteryInfo(room_name=room_name, supported=False)


def _make_service(adapter):
    room_service = MagicMock()
    room_service.get_room.return_value = ROOM
    return DeviceService(room_service, adapter), room_service


class TestGetBatteryInfo:
    def test_resolves_room_and_delegates(self):
        info = BatteryInfo(room_name="Patio", supported=True, level=50)
        adapter = FakeDeviceAdapter(info)
        svc, _ = _make_service(adapter)

        assert svc.get_battery_info("patio") == info
        assert adapter.calls == [(ROOM.ip_address, "Patio")]

    def test_unsupported_room_returns_unsupported(self):
        svc, _ = _make_service(FakeDeviceAdapter())

        assert svc.get_battery_info("Patio").supported is False

    def test_propagates_room_not_found(self):
        svc, rs = _make_service(FakeDeviceAdapter())
        rs.get_room.side_effect = RoomNotFoundError("Garage")

        with pytest.raises(RoomNotFoundError):
            svc.get_battery_info("Garage")

    def test_propagates_device_error(self):
        svc, _ = _make_service(FakeDeviceAdapter(error=DeviceError("boom")))

        with pytest.raises(DeviceError):
            svc.get_battery_info("Patio")
