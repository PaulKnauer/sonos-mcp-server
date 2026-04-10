"""Contract tests for the group_rooms tool schema."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import GroupValidationError, SonosDiscoveryError
from soniq_mcp.domain.models import Room
from soniq_mcp.tools.groups import register


class _StubGroupService:
    def get_group_topology(self):
        return []

    def join_group(self, room_name, coordinator_name):
        pass

    def unjoin_room(self, room_name):
        pass

    def party_mode(self):
        pass

    def group_rooms(self, room_names, coordinator_name=None):
        coordinator = Room(
            name=room_names[0] if room_names else "Room A",
            uid="UID1",
            ip_address="192.168.1.10",
            is_coordinator=True,
        )
        return [coordinator]

    def get_group_audio_state(self, room_name):
        raise NotImplementedError

    def set_group_volume(self, room_name, volume):
        raise NotImplementedError

    def adjust_group_volume(self, room_name, delta):
        raise NotImplementedError

    def group_mute(self, room_name):
        raise NotImplementedError

    def group_unmute(self, room_name):
        raise NotImplementedError


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubGroupService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestGroupRoomsContract:
    def test_tool_name_is_stable(self, registered_app):
        assert "group_rooms" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app):
        desc = get_tools(registered_app)["group_rooms"].description
        assert desc and len(desc) > 0

    def test_tool_has_rooms_parameter(self, registered_app):
        schema = get_tools(registered_app)["group_rooms"].parameters
        assert "rooms" in schema.get("properties", {})
        assert "rooms" in schema.get("required", [])

    def test_tool_has_coordinator_optional_parameter(self, registered_app):
        schema = get_tools(registered_app)["group_rooms"].parameters
        assert "coordinator" in schema.get("properties", {})
        # coordinator is optional, not required
        assert "coordinator" not in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app):
        annotations = get_tools(registered_app)["group_rooms"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is False
        assert annotations.openWorldHint is False

    @pytest.mark.anyio
    async def test_response_has_group_topology_shape(self, registered_app):
        result = await registered_app.call_tool("group_rooms", {"rooms": ["Room A", "Room B"]})
        data = json.loads(result[0].text)
        assert "groups" in data
        assert "total_groups" in data
        assert "total_rooms" in data

    @pytest.mark.anyio
    async def test_validation_error_shape_is_stable(self):
        class _ValidationService(_StubGroupService):
            def group_rooms(self, room_names, coordinator_name=None):
                raise GroupValidationError("At least two distinct rooms are required.")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _ValidationService())

        result = await app.call_tool("group_rooms", {"rooms": ["Room A"]})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "group"

    @pytest.mark.anyio
    async def test_discovery_error_shape_is_stable(self):
        class _DiscoveryService(_StubGroupService):
            def group_rooms(self, room_names, coordinator_name=None):
                raise SonosDiscoveryError("Discovery failed for 192.168.1.20")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _DiscoveryService())

        result = await app.call_tool("group_rooms", {"rooms": ["Room A", "Room B"]})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"
        assert data["field"] == "sonos_network"
        assert "<redacted-host>" in data["error"]
