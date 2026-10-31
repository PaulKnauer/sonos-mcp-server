"""Unit tests for SoCoAdapter device queries (battery)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from soco.exceptions import NotSupportedException

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import DeviceError
from soniq_mcp.domain.models import BatteryInfo

IP = "192.168.1.10"


class TestGetBatteryInfo:
    def test_returns_battery_state_for_portable_speaker(self):
        zone = MagicMock()
        zone.get_battery_info.return_value = {
            "Health": "GREEN",
            "Level": 87,
            "Temperature": "NORMAL",
            "PowerSource": "BATTERY",
        }

        with patch("soco.SoCo", return_value=zone):
            info = SoCoAdapter().get_battery_info(IP, "Patio")

        assert info == BatteryInfo(
            room_name="Patio",
            supported=True,
            level=87,
            health="GREEN",
            temperature="NORMAL",
            power_source="BATTERY",
        )

    def test_non_portable_speaker_is_unsupported_not_error(self):
        zone = MagicMock()
        zone.get_battery_info.side_effect = NotSupportedException("no battery")

        with patch("soco.SoCo", return_value=zone):
            info = SoCoAdapter().get_battery_info(IP, "Kitchen")

        assert info == BatteryInfo(room_name="Kitchen", supported=False)

    def test_connection_failure_raises_device_error(self):
        zone = MagicMock()
        zone.get_battery_info.side_effect = ConnectionError("refused")

        with patch("soco.SoCo", return_value=zone):
            with pytest.raises(DeviceError, match="Failed to get battery info"):
                SoCoAdapter().get_battery_info(IP, "Patio")
