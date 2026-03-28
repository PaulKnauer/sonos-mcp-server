"""Unit tests for group MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import GroupError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import Room


COORDINATOR = Room(
    name="Living Room", uid="UID1", ip_address="192.168.1.10", is_coordinator=True
)
MEMBER = Room(
    name="Kitchen",
    uid="UID2",
    ip_address="192.168.1.20",
    is_coordinator=False,
    group_coordinator_uid="UID1",
)


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


class TestGetGroupTopology:
    def test_returns_topology_response_on_success(self):
        gs = MagicMock()
        gs.get_group_topology.return_value = [COORDINATOR, MEMBER]

        fn, _, _ = _register_and_get("get_group_topology", gs)
        result = fn()

        assert "groups" in result
        assert result["total_rooms"] == 2
        assert result["total_groups"] == 1
        assert result["groups"][0]["coordinator"] == "Living Room"
        assert "Kitchen" in result["groups"][0]["members"]

    def test_empty_household_returns_zero_groups(self):
        gs = MagicMock()
        gs.get_group_topology.return_value = []

        fn, _, _ = _register_and_get("get_group_topology", gs)
        result = fn()

        assert result["total_groups"] == 0
        assert result["total_rooms"] == 0
        assert result["groups"] == []

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.get_group_topology.side_effect = GroupError("discovery failed")

        fn, _, _ = _register_and_get("get_group_topology", gs)
        result = fn()

        assert "error" in result
        assert result["field"] == "group"

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.get_group_topology.side_effect = SonosDiscoveryError("no speakers")

        fn, _, _ = _register_and_get("get_group_topology", gs)
        result = fn()

        assert "error" in result
        assert result["field"] == "sonos_network"

    def test_tool_disabled_is_not_registered(self):
        fn, _, _ = _register_and_get("get_group_topology", disabled=["get_group_topology"])
        assert fn is None

    def test_is_read_only_tool(self):
        from mcp.server.fastmcp import FastMCP
        from soniq_mcp.tools.groups import register

        app = FastMCP("test")
        gs = MagicMock()
        gs.get_group_topology.return_value = []
        register(app, _make_config(), gs)
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        assert tools["get_group_topology"].annotations.readOnlyHint is True


class TestJoinGroup:
    def test_returns_ok_on_success(self):
        gs = MagicMock()

        fn, _, _ = _register_and_get("join_group", gs)
        result = fn(room="Kitchen", coordinator="Living Room")

        gs.join_group.assert_called_once_with("Kitchen", "Living Room")
        assert result == {"status": "ok", "room": "Kitchen", "coordinator": "Living Room"}

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.join_group.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("join_group", gs)
        result = fn(room="Kitchen", coordinator="Living Room")

        assert "error" in result
        assert result["field"] == "room"
        assert result["error"] == "Room 'Kitchen' was not found in the Sonos household."

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.join_group.side_effect = GroupError("join failed")

        fn, _, _ = _register_and_get("join_group", gs)
        result = fn(room="Kitchen", coordinator="Living Room")

        assert "error" in result
        assert result["field"] == "group"

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.join_group.side_effect = SonosDiscoveryError("no network")

        fn, _, _ = _register_and_get("join_group", gs)
        result = fn(room="Kitchen", coordinator="Living Room")

        assert "error" in result

    def test_tool_disabled_is_not_registered(self):
        fn, _, _ = _register_and_get("join_group", disabled=["join_group"])
        assert fn is None


class TestUnjoinRoom:
    def test_returns_ok_on_success(self):
        gs = MagicMock()

        fn, _, _ = _register_and_get("unjoin_room", gs)
        result = fn(room="Kitchen")

        gs.unjoin_room.assert_called_once_with("Kitchen")
        assert result == {"status": "ok", "room": "Kitchen"}

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.unjoin_room.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("unjoin_room", gs)
        result = fn(room="Kitchen")

        assert "error" in result
        assert result["field"] == "room"

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.unjoin_room.side_effect = GroupError("unjoin failed")

        fn, _, _ = _register_and_get("unjoin_room", gs)
        result = fn(room="Kitchen")

        assert "error" in result
        assert result["field"] == "group"

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.unjoin_room.side_effect = SonosDiscoveryError("no network")

        fn, _, _ = _register_and_get("unjoin_room", gs)
        result = fn(room="Kitchen")

        assert "error" in result

    def test_tool_disabled_is_not_registered(self):
        fn, _, _ = _register_and_get("unjoin_room", disabled=["unjoin_room"])
        assert fn is None


class TestPartyMode:
    def test_returns_ok_on_success(self):
        gs = MagicMock()

        fn, _, _ = _register_and_get("party_mode", gs)
        result = fn()

        gs.party_mode.assert_called_once_with()
        assert result == {"status": "ok"}

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.party_mode.side_effect = GroupError("no rooms")

        fn, _, _ = _register_and_get("party_mode", gs)
        result = fn()

        assert "error" in result
        assert result["field"] == "group"

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.party_mode.side_effect = SonosDiscoveryError("network issue")

        fn, _, _ = _register_and_get("party_mode", gs)
        result = fn()

        assert "error" in result

    def test_tool_disabled_is_not_registered(self):
        fn, _, _ = _register_and_get("party_mode", disabled=["party_mode"])
        assert fn is None
