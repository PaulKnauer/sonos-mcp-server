"""Contract tests for volume tool schemas.

Validates that all 6 volume tool names, descriptions, and parameter schemas
remain stable. These tests act as a breaking-change guard for MCP clients
that depend on the tool surface.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import VolumeState
from soniq_mcp.tools.volume import register


class FakeVolumeService:
    def get_volume_state(self, room_name: str) -> VolumeState:
        return VolumeState(room_name=room_name, volume=50, is_muted=False)

    def set_volume(self, room_name: str, volume: int) -> None:
        pass

    def adjust_volume(self, room_name: str, delta: int) -> VolumeState:
        return VolumeState(room_name=room_name, volume=50, is_muted=False)

    def mute(self, room_name: str) -> None:
        pass

    def unmute(self, room_name: str) -> None:
        pass


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, FakeVolumeService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestGetVolumeContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_volume" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_volume"].description
        assert desc and len(desc) > 0

    def test_requires_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_volume"].parameters
        assert "room" in schema["properties"]
        assert schema["required"] == ["room"]

    def test_is_read_only(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["get_volume"].annotations
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False


class TestSetVolumeContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "set_volume" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["set_volume"].description
        assert desc and len(desc) > 0

    def test_requires_room_and_volume_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_volume"].parameters
        assert "room" in schema["properties"]
        assert "volume" in schema["properties"]
        assert set(schema["required"]) == {"room", "volume"}

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["set_volume"].annotations
        assert ann.readOnlyHint is False


class TestAdjustVolumeContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "adjust_volume" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["adjust_volume"].description
        assert desc and len(desc) > 0

    def test_requires_room_and_delta_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["adjust_volume"].parameters
        assert "room" in schema["properties"]
        assert "delta" in schema["properties"]
        assert set(schema["required"]) == {"room", "delta"}

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["adjust_volume"].annotations
        assert ann.readOnlyHint is False


class TestMuteContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "mute" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["mute"].description
        assert desc and len(desc) > 0

    def test_requires_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["mute"].parameters
        assert "room" in schema["properties"]
        assert schema["required"] == ["room"]

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["mute"].annotations
        assert ann.readOnlyHint is False


class TestUnmuteContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "unmute" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["unmute"].description
        assert desc and len(desc) > 0

    def test_requires_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["unmute"].parameters
        assert "room" in schema["properties"]
        assert schema["required"] == ["room"]

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["unmute"].annotations
        assert ann.readOnlyHint is False


class TestGetMuteContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_mute" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_mute"].description
        assert desc and len(desc) > 0

    def test_requires_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_mute"].parameters
        assert "room" in schema["properties"]
        assert schema["required"] == ["room"]

    def test_is_read_only(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["get_mute"].annotations
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False
