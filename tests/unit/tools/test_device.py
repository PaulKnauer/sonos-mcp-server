"""Unit tests for device MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

from soniq_mcp.domain.exceptions import DeviceError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import BatteryInfo


def _register_and_get(tool_name, service=None, disabled=None):
    from soniq_mcp.tools.device import register

    tools = {}
    app = MagicMock()

    def tool_decorator(title=None, annotations=None):
        def decorator(fn):
            tools[fn.__name__] = fn
            return fn

        return decorator

    app.tool.side_effect = tool_decorator
    config = MagicMock()
    config.tools_disabled = disabled or []
    service = service or MagicMock()
    register(app, config, service)
    return tools.get(tool_name), service


class TestGetBatteryInfoTool:
    def test_returns_battery_state(self):
        svc = MagicMock()
        svc.get_battery_info.return_value = BatteryInfo("Patio", True, 80, "GREEN", None, "BATTERY")
        fn, _ = _register_and_get("get_battery_info", svc)

        result = fn(room="Patio")

        assert result["room"] == "Patio"
        assert result["supported"] is True
        assert result["level"] == 80
        assert result["power_source"] == "BATTERY"

    def test_unsupported_room_is_not_an_error(self):
        svc = MagicMock()
        svc.get_battery_info.return_value = BatteryInfo("Kitchen", False)
        fn, _ = _register_and_get("get_battery_info", svc)

        result = fn(room="Kitchen")

        assert result["supported"] is False
        assert "error" not in result

    def test_device_error(self):
        svc = MagicMock()
        svc.get_battery_info.side_effect = DeviceError("boom")
        fn, _ = _register_and_get("get_battery_info", svc)

        assert fn(room="Patio")["field"] == "device"

    def test_room_not_found(self):
        svc = MagicMock()
        svc.get_battery_info.side_effect = RoomNotFoundError("Garage")
        fn, _ = _register_and_get("get_battery_info", svc)

        assert fn(room="Garage")["field"] == "room"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.get_battery_info.side_effect = SonosDiscoveryError("down")
        fn, _ = _register_and_get("get_battery_info", svc)

        assert fn(room="Patio")["category"] == "connectivity"

    def test_disabled_tool_not_registered(self):
        fn, _ = _register_and_get("get_battery_info", disabled=["get_battery_info"])

        assert fn is None
