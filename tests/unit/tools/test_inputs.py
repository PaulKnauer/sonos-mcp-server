"""Unit tests for input-switching MCP tools."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import InputError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import InputState
from soniq_mcp.tools.inputs import register


class FakeInputService:
    def __init__(
        self,
        *,
        raise_room_not_found: bool = False,
        raise_input_error: bool = False,
        raise_discovery_error: bool = False,
        state: InputState | None = None,
    ) -> None:
        self.raise_room_not_found = raise_room_not_found
        self.raise_input_error = raise_input_error
        self.raise_discovery_error = raise_discovery_error
        self.state = state or InputState(
            room_name="Living Room",
            input_source="tv",
            coordinator_room_name="Living Room",
        )
        self.line_in_calls: list[str] = []
        self.tv_calls: list[str] = []

    def _check(self, room: str) -> None:
        if self.raise_room_not_found:
            raise RoomNotFoundError(room)
        if self.raise_input_error:
            raise InputError("unsupported")
        if self.raise_discovery_error:
            raise SonosDiscoveryError("network down")

    def switch_to_line_in(self, room: str) -> InputState:
        self.line_in_calls.append(room)
        self._check(room)
        return InputState(room_name=room, input_source="line_in", coordinator_room_name=room)

    def switch_to_tv(self, room: str) -> InputState:
        self.tv_calls.append(room)
        self._check(room)
        return InputState(room_name=room, input_source="tv", coordinator_room_name=room)


def make_app(
    *,
    raise_room_not_found: bool = False,
    raise_input_error: bool = False,
    raise_discovery_error: bool = False,
    tools_disabled: list[str] | None = None,
) -> tuple[FastMCP, FakeInputService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    svc = FakeInputService(
        raise_room_not_found=raise_room_not_found,
        raise_input_error=raise_input_error,
        raise_discovery_error=raise_discovery_error,
    )
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


class TestSwitchToLineInTool:
    @pytest.mark.anyio
    async def test_returns_normalized_state(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("switch_to_line_in", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["room_name"] == "Living Room"
        assert data["input_source"] == "line_in"
        assert svc.line_in_calls == ["Living Room"]

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("switch_to_line_in", {"room": "Missing"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_input_error_returns_error(self) -> None:
        app, _ = make_app(raise_input_error=True)
        result = await app.call_tool("switch_to_line_in", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["field"] == "input_source"

    @pytest.mark.anyio
    async def test_discovery_error_returns_connectivity_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("switch_to_line_in", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["switch_to_line_in"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "switch_to_line_in" not in tools


class TestSwitchToTvTool:
    @pytest.mark.anyio
    async def test_returns_normalized_state(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("switch_to_tv", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["room_name"] == "Living Room"
        assert data["input_source"] == "tv"
        assert svc.tv_calls == ["Living Room"]

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["switch_to_tv"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "switch_to_tv" not in tools

    def test_tool_annotations_are_control(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["switch_to_tv"].annotations
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False


class TestInputToolAnnotations:
    def test_switch_to_line_in_annotations_are_control(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["switch_to_line_in"].annotations
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False
