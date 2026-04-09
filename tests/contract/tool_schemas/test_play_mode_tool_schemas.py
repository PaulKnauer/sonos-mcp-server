"""Contract tests for play mode tool schemas.

Validates that play mode tool names, descriptions, parameter schemas, and
response shapes remain stable. These act as breaking-change guards for MCP
clients that depend on the get_play_mode and set_play_mode surface.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import PlayModeState
from soniq_mcp.tools.play_modes import register


class _StubPlayModeService:
    def get_play_mode(self, room: str) -> PlayModeState:
        return PlayModeState(room_name=room, shuffle=False, repeat="none", cross_fade=False)

    def set_play_mode(self, room: str, shuffle=None, repeat=None, cross_fade=None) -> PlayModeState:
        return PlayModeState(room_name=room, shuffle=False, repeat="none", cross_fade=False)


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubPlayModeService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestGetPlayModeContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_play_mode" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_play_mode"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_play_mode"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["get_play_mode"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_play_mode_fields(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("get_play_mode", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "shuffle" in data
        assert "repeat" in data
        assert "cross_fade" in data

    @pytest.mark.anyio
    async def test_response_shuffle_is_bool(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("get_play_mode", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert isinstance(data["shuffle"], bool)

    @pytest.mark.anyio
    async def test_response_repeat_is_string(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("get_play_mode", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert isinstance(data["repeat"], str)
        assert data["repeat"] in ("none", "all", "one")


class TestSetPlayModeContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "set_play_mode" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["set_play_mode"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_play_mode"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_has_optional_mode_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_play_mode"].parameters
        props = schema.get("properties", {})
        assert "shuffle" in props
        assert "repeat" in props
        assert "cross_fade" in props
        # All mode params are optional — not in required
        required = schema.get("required", [])
        assert "shuffle" not in required
        assert "repeat" not in required
        assert "cross_fade" not in required

    def test_optional_mode_parameter_types_are_stable(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_play_mode"].parameters
        props = schema["properties"]
        assert props["shuffle"]["anyOf"] == [{"type": "boolean"}, {"type": "null"}]
        assert props["repeat"]["anyOf"] == [
            {"type": "string", "enum": ["none", "all", "one"]},
            {"type": "null"},
        ]
        assert props["cross_fade"]["anyOf"] == [{"type": "boolean"}, {"type": "null"}]

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["set_play_mode"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_play_mode_fields(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool(
            "set_play_mode",
            {"room": "Living Room", "shuffle": True},
        )
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "shuffle" in data
        assert "repeat" in data
        assert "cross_fade" in data

    @pytest.mark.anyio
    async def test_response_field_types_remain_normalized(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool(
            "set_play_mode",
            {"room": "Living Room", "shuffle": True},
        )
        data = json.loads(result[0].text)
        assert isinstance(data["shuffle"], bool)
        assert isinstance(data["repeat"], str)
        assert isinstance(data["cross_fade"], bool)
