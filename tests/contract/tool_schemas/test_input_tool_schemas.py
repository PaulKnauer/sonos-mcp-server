"""Contract tests for input-switching tool schemas."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import InputState
from soniq_mcp.tools.inputs import register


class _StubInputService:
    def switch_to_line_in(self, room: str) -> InputState:
        return InputState(room_name=room, input_source="line_in", coordinator_room_name=room)

    def switch_to_tv(self, room: str) -> InputState:
        return InputState(room_name=room, input_source="tv", coordinator_room_name=room)


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubInputService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestSwitchToLineInContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "switch_to_line_in" in get_tools(registered_app)

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["switch_to_line_in"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_annotations_are_stable(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["switch_to_line_in"].annotations
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is False
        assert annotations.openWorldHint is False

    @pytest.mark.anyio
    async def test_response_shape_is_stable(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("switch_to_line_in", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["room_name"] == "Living Room"
        assert data["input_source"] == "line_in"
        assert "coordinator_room_name" in data


class TestSwitchToTvContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "switch_to_tv" in get_tools(registered_app)

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["switch_to_tv"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_annotations_are_stable(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["switch_to_tv"].annotations
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False
        assert annotations.idempotentHint is False
        assert annotations.openWorldHint is False

    @pytest.mark.anyio
    async def test_response_shape_is_stable(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("switch_to_tv", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["room_name"] == "Living Room"
        assert data["input_source"] == "tv"
        assert "coordinator_room_name" in data
