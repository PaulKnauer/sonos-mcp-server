"""Contract tests for group-audio tool schemas.

Validates that tool names, descriptions, and parameter schemas remain
stable. These tests act as a breaking-change guard for MCP clients.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import GroupAudioState
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

    def get_group_audio_state(self, room_name):
        return _make_state(room_name)

    def set_group_volume(self, room_name, volume):
        return _make_state(room_name, volume=volume)

    def adjust_group_volume(self, room_name, delta):
        return _make_state(room_name, volume=40 + delta)

    def group_mute(self, room_name):
        return _make_state(room_name, is_muted=True)

    def group_unmute(self, room_name):
        return _make_state(room_name, is_muted=False)


def _make_state(room_name="Living Room", volume=40, is_muted=False):
    return GroupAudioState(
        room_name=room_name,
        coordinator_room_name=room_name,
        member_room_names=(room_name, "Kitchen"),
        volume=volume,
        is_muted=is_muted,
    )


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubGroupService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestGetGroupVolumeContract:
    def test_tool_name_is_stable(self, registered_app):
        assert "get_group_volume" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app):
        desc = get_tools(registered_app)["get_group_volume"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app):
        schema = get_tools(registered_app)["get_group_volume"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_read_only(self, registered_app):
        annotations = get_tools(registered_app)["get_group_volume"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_shape(self, registered_app):
        import json

        result = await registered_app.call_tool("get_group_volume", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "coordinator_room_name" in data
        assert "member_room_names" in data
        assert "volume" in data
        assert "is_muted" in data


class TestSetGroupVolumeContract:
    def test_tool_name_is_stable(self, registered_app):
        assert "set_group_volume" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app):
        desc = get_tools(registered_app)["set_group_volume"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_and_volume_parameters(self, registered_app):
        schema = get_tools(registered_app)["set_group_volume"].parameters
        props = schema.get("properties", {})
        required = schema.get("required", [])
        assert "room" in props and "room" in required
        assert "volume" in props and "volume" in required

    def test_tool_is_not_read_only(self, registered_app):
        annotations = get_tools(registered_app)["set_group_volume"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestAdjustGroupVolumeContract:
    def test_tool_name_is_stable(self, registered_app):
        assert "adjust_group_volume" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app):
        desc = get_tools(registered_app)["adjust_group_volume"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_and_delta_parameters(self, registered_app):
        schema = get_tools(registered_app)["adjust_group_volume"].parameters
        props = schema.get("properties", {})
        required = schema.get("required", [])
        assert "room" in props and "room" in required
        assert "delta" in props and "delta" in required

    def test_tool_is_not_read_only(self, registered_app):
        annotations = get_tools(registered_app)["adjust_group_volume"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestGroupMuteContract:
    def test_tool_name_is_stable(self, registered_app):
        assert "group_mute" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app):
        desc = get_tools(registered_app)["group_mute"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app):
        schema = get_tools(registered_app)["group_mute"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app):
        annotations = get_tools(registered_app)["group_mute"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_shape(self, registered_app):
        import json

        result = await registered_app.call_tool("group_mute", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "is_muted" in data
        assert data["is_muted"] is True


class TestGroupUnmuteContract:
    def test_tool_name_is_stable(self, registered_app):
        assert "group_unmute" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app):
        desc = get_tools(registered_app)["group_unmute"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app):
        schema = get_tools(registered_app)["group_unmute"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app):
        annotations = get_tools(registered_app)["group_unmute"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_response_shape(self, registered_app):
        import json

        result = await registered_app.call_tool("group_unmute", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "is_muted" in data
        assert data["is_muted"] is False
