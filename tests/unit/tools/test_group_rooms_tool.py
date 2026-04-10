"""Unit tests for the group_rooms MCP tool handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from soniq_mcp.domain.exceptions import (
    GroupError,
    GroupValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import Room


def _make_rooms(coordinator_name="Living Room", member_name="Kitchen"):
    coordinator = Room(
        name=coordinator_name,
        uid="UID1",
        ip_address="192.168.1.10",
        is_coordinator=True,
    )
    member = Room(
        name=member_name,
        uid="UID2",
        ip_address="192.168.1.20",
        is_coordinator=False,
        group_coordinator_uid="UID1",
    )
    return [coordinator, member]


def _make_config(disabled=None):
    config = MagicMock()
    config.tools_disabled = disabled or []
    return config


def _make_app():
    app = MagicMock()
    _tools = {}

    def tool_decorator(title=None, annotations=None):
        def decorator(fn):
            _tools[fn.__name__] = fn
            return fn

        return decorator

    app.tool.side_effect = tool_decorator
    app._tools = _tools
    return app


def _register_and_get(tool_name, group_service=None, disabled=None):
    from soniq_mcp.tools.groups import register

    app = _make_app()
    config = _make_config(disabled)
    if group_service is None:
        group_service = MagicMock()
    register(app, config, group_service)
    return app._tools.get(tool_name), group_service, config


class TestGroupRoomsTool:
    def test_returns_group_topology_on_success(self):
        gs = MagicMock()
        gs.group_rooms.return_value = _make_rooms()

        fn, _, _ = _register_and_get("group_rooms", gs)
        result = fn(rooms=["Living Room", "Kitchen"])

        gs.group_rooms.assert_called_once_with(["Living Room", "Kitchen"], None)
        assert "groups" in result
        assert "total_rooms" in result
        assert result["total_rooms"] == 2

    def test_passes_coordinator_to_service(self):
        gs = MagicMock()
        gs.group_rooms.return_value = _make_rooms()

        fn, _, _ = _register_and_get("group_rooms", gs)
        fn(rooms=["Living Room", "Kitchen"], coordinator="Kitchen")

        gs.group_rooms.assert_called_once_with(["Living Room", "Kitchen"], "Kitchen")

    def test_group_validation_error_returns_group_error_response(self):
        gs = MagicMock()
        gs.group_rooms.side_effect = GroupValidationError("empty room set")

        fn, _, _ = _register_and_get("group_rooms", gs)
        result = fn(rooms=[])

        assert "error" in result
        assert result["field"] == "group"

    def test_room_not_found_returns_room_error_response(self):
        gs = MagicMock()
        exc = RoomNotFoundError("Ghost Room")
        gs.group_rooms.side_effect = exc

        fn, _, _ = _register_and_get("group_rooms", gs)
        result = fn(rooms=["Living Room", "Ghost Room"])

        assert "error" in result
        assert result["field"] == "room"

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.group_rooms.side_effect = GroupError("SoCo join failed")

        fn, _, _ = _register_and_get("group_rooms", gs)
        result = fn(rooms=["Living Room", "Kitchen"])

        assert "error" in result
        assert result["field"] == "group"

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.group_rooms.side_effect = SonosDiscoveryError("no network")

        fn, _, _ = _register_and_get("group_rooms", gs)
        result = fn(rooms=["Living Room", "Kitchen"])

        assert "error" in result
        assert result["field"] == "sonos_network"

    def test_tool_disabled_is_not_registered(self):
        fn, _, _ = _register_and_get("group_rooms", disabled=["group_rooms"])
        assert fn is None

    def test_response_has_correct_group_structure(self):
        gs = MagicMock()
        gs.group_rooms.return_value = _make_rooms()

        fn, _, _ = _register_and_get("group_rooms", gs)
        result = fn(rooms=["Living Room", "Kitchen"])

        assert "groups" in result
        assert len(result["groups"]) == 1
        group = result["groups"][0]
        assert "coordinator" in group
        assert "members" in group
        assert group["coordinator"] == "Living Room"
        assert "Kitchen" in group["members"]

    def test_is_control_tool(self):
        from mcp.server.fastmcp import FastMCP

        from soniq_mcp.tools.groups import register

        app = FastMCP("test")
        gs = MagicMock()
        gs.group_rooms.return_value = _make_rooms()
        register(app, _make_config(), gs)
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        assert tools["group_rooms"].annotations.readOnlyHint is False
        assert tools["group_rooms"].annotations.destructiveHint is False
