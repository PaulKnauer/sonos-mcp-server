"""Contract tests for playback tool schemas.

Validates that playback tool names, descriptions, and parameter schemas
remain stable. These tests act as a breaking-change guard for MCP clients
that depend on the tool surface.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import PlaybackState, TrackInfo
from soniq_mcp.tools.playback import register


class _StubPlaybackService:
    def play(self, room: str) -> None:
        pass

    def pause(self, room: str) -> None:
        pass

    def stop(self, room: str) -> None:
        pass

    def next_track(self, room: str) -> None:
        pass

    def previous_track(self, room: str) -> None:
        pass

    def get_playback_state(self, room: str) -> PlaybackState:
        return PlaybackState(transport_state="PLAYING", room_name=room)

    def get_track_info(self, room: str) -> TrackInfo:
        return TrackInfo()


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubPlaybackService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestPlayContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "play" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["play"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["play"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["play"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False


class TestPauseContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "pause" in get_tools(registered_app)

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["pause"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["pause"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestStopContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "stop" in get_tools(registered_app)

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["stop"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["stop"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestNextTrackContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "next_track" in get_tools(registered_app)

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["next_track"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["next_track"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestPreviousTrackContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "previous_track" in get_tools(registered_app)

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["previous_track"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["previous_track"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestGetPlaybackStateContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_playback_state" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_playback_state"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_playback_state"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["get_playback_state"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_transport_state(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("get_playback_state", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "transport_state" in data
        assert "room_name" in data


class TestGetTrackInfoContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_track_info" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_track_info"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_track_info"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["get_track_info"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_room_name(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("get_track_info", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "room_name" in data
