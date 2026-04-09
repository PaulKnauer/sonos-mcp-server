"""Contract tests for audio EQ tool schemas.

Validates that audio tool names, descriptions, parameter schemas, and
response shapes remain stable. These act as breaking-change guards for MCP
clients that depend on the get_eq_settings, set_bass, set_treble, and
set_loudness surface.
"""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import AudioSettingsState
from soniq_mcp.tools.audio import register


class _StubAudioSettingsService:
    def get_audio_settings(self, room: str) -> AudioSettingsState:
        return AudioSettingsState(room_name=room, bass=0, treble=0, loudness=True)

    def set_bass(self, room: str, level: int) -> AudioSettingsState:
        return AudioSettingsState(room_name=room, bass=level, treble=0, loudness=True)

    def set_treble(self, room: str, level: int) -> AudioSettingsState:
        return AudioSettingsState(room_name=room, bass=0, treble=level, loudness=True)

    def set_loudness(self, room: str, enabled: bool) -> AudioSettingsState:
        return AudioSettingsState(room_name=room, bass=0, treble=0, loudness=enabled)


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubAudioSettingsService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestGetEqSettingsContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_eq_settings" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_eq_settings"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_eq_settings"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["get_eq_settings"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_eq_fields(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("get_eq_settings", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "bass" in data
        assert "treble" in data
        assert "loudness" in data

    @pytest.mark.anyio
    async def test_response_bass_and_treble_are_ints(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("get_eq_settings", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert isinstance(data["bass"], int)
        assert isinstance(data["treble"], int)

    @pytest.mark.anyio
    async def test_response_loudness_is_bool(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("get_eq_settings", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert isinstance(data["loudness"], bool)


class TestSetBassContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "set_bass" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["set_bass"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_and_level_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_bass"].parameters
        props = schema.get("properties", {})
        assert "room" in props
        assert "level" in props
        required = schema.get("required", [])
        assert "room" in required
        assert "level" in required

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["set_bass"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_eq_fields(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("set_bass", {"room": "Living Room", "level": 3})
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "bass" in data
        assert "treble" in data
        assert "loudness" in data

    @pytest.mark.anyio
    async def test_response_bass_reflects_set_value(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("set_bass", {"room": "Living Room", "level": 7})
        data = json.loads(result[0].text)
        assert data["bass"] == 7


class TestSetTrebleContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "set_treble" in get_tools(registered_app)

    def test_tool_has_room_and_level_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_treble"].parameters
        props = schema.get("properties", {})
        assert "room" in props
        assert "level" in props
        required = schema.get("required", [])
        assert "room" in required
        assert "level" in required

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["set_treble"].annotations
        assert annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_response_includes_eq_fields(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("set_treble", {"room": "Kitchen", "level": -4})
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "bass" in data
        assert "treble" in data
        assert "loudness" in data

    @pytest.mark.anyio
    async def test_response_treble_reflects_set_value(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool("set_treble", {"room": "Kitchen", "level": -4})
        data = json.loads(result[0].text)
        assert data["treble"] == -4


class TestSetLoudnessContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "set_loudness" in get_tools(registered_app)

    def test_tool_has_room_and_enabled_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["set_loudness"].parameters
        props = schema.get("properties", {})
        assert "room" in props
        assert "enabled" in props
        required = schema.get("required", [])
        assert "room" in required
        assert "enabled" in required

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["set_loudness"].annotations
        assert annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_response_includes_eq_fields(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool(
            "set_loudness", {"room": "Bedroom", "enabled": False}
        )
        data = json.loads(result[0].text)
        assert "room_name" in data
        assert "bass" in data
        assert "treble" in data
        assert "loudness" in data

    @pytest.mark.anyio
    async def test_response_loudness_reflects_set_value(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool(
            "set_loudness", {"room": "Bedroom", "enabled": False}
        )
        data = json.loads(result[0].text)
        assert data["loudness"] is False
