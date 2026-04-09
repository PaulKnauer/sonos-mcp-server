"""Unit tests for audio EQ MCP tools using a fake AudioSettingsService."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import AudioSettingsError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import AudioSettingsState, Room
from soniq_mcp.services.audio_settings_service import AudioSettingsService
from soniq_mcp.tools.audio import register


def make_state(
    room_name: str = "Living Room",
    bass: int = 2,
    treble: int = -1,
    loudness: bool = True,
) -> AudioSettingsState:
    return AudioSettingsState(room_name=room_name, bass=bass, treble=treble, loudness=loudness)


class FakeAudioSettingsService:
    def __init__(
        self,
        raise_room_not_found: bool = False,
        raise_audio_settings_error: bool = False,
        raise_discovery_error: bool = False,
        state: AudioSettingsState | None = None,
    ) -> None:
        self._raise_room_not_found = raise_room_not_found
        self._raise_audio_settings_error = raise_audio_settings_error
        self._raise_discovery_error = raise_discovery_error
        self._state = state or make_state()
        self.get_calls: list[str] = []
        self.set_bass_calls: list[tuple] = []
        self.set_treble_calls: list[tuple] = []
        self.set_loudness_calls: list[tuple] = []

    def _check_errors(self, room: str) -> None:
        if self._raise_room_not_found:
            raise RoomNotFoundError(room)
        if self._raise_audio_settings_error:
            raise AudioSettingsError("EQ operation failed")
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")

    def get_audio_settings(self, room: str) -> AudioSettingsState:
        self.get_calls.append(room)
        self._check_errors(room)
        return AudioSettingsState(
            room_name=room,
            bass=self._state.bass,
            treble=self._state.treble,
            loudness=self._state.loudness,
        )

    def set_bass(self, room: str, level: int) -> AudioSettingsState:
        self.set_bass_calls.append((room, level))
        self._check_errors(room)
        return AudioSettingsState(
            room_name=room, bass=level, treble=self._state.treble, loudness=self._state.loudness
        )

    def set_treble(self, room: str, level: int) -> AudioSettingsState:
        self.set_treble_calls.append((room, level))
        self._check_errors(room)
        return AudioSettingsState(
            room_name=room, bass=self._state.bass, treble=level, loudness=self._state.loudness
        )

    def set_loudness(self, room: str, enabled: bool) -> AudioSettingsState:
        self.set_loudness_calls.append((room, enabled))
        self._check_errors(room)
        return AudioSettingsState(
            room_name=room, bass=self._state.bass, treble=self._state.treble, loudness=enabled
        )


class FakeRoomService:
    def __init__(self, room: Room | None = None) -> None:
        self._room = room or Room(
            name="Living Room",
            uid="RINCON_1",
            ip_address="192.168.1.10",
            is_coordinator=True,
        )

    def get_room(self, name: str) -> Room:
        if name != self._room.name:
            raise RoomNotFoundError(name)
        return self._room


class FakeAdapter:
    def __init__(self, state: AudioSettingsState | None = None) -> None:
        self._state = state or make_state()
        self.set_bass_calls: list[tuple[str, object]] = []
        self.set_treble_calls: list[tuple[str, object]] = []
        self.set_loudness_calls: list[tuple[str, object]] = []

    def get_audio_settings(self, ip_address: str, room_name: str) -> AudioSettingsState:
        return AudioSettingsState(
            room_name=room_name,
            bass=self._state.bass,
            treble=self._state.treble,
            loudness=self._state.loudness,
        )

    def set_bass(self, ip_address: str, level: object) -> None:
        self.set_bass_calls.append((ip_address, level))

    def set_treble(self, ip_address: str, level: object) -> None:
        self.set_treble_calls.append((ip_address, level))

    def set_loudness(self, ip_address: str, enabled: object) -> None:
        self.set_loudness_calls.append((ip_address, enabled))


def make_app(
    raise_room_not_found: bool = False,
    raise_audio_settings_error: bool = False,
    raise_discovery_error: bool = False,
    tools_disabled: list[str] | None = None,
    state: AudioSettingsState | None = None,
) -> tuple[FastMCP, FakeAudioSettingsService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    svc = FakeAudioSettingsService(
        raise_room_not_found=raise_room_not_found,
        raise_audio_settings_error=raise_audio_settings_error,
        raise_discovery_error=raise_discovery_error,
        state=state,
    )
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


def make_validating_app(
    state: AudioSettingsState | None = None,
) -> tuple[FastMCP, FakeAdapter]:
    config = SoniqConfig()
    adapter = FakeAdapter(state=state)
    app = FastMCP("test")
    register(app, config, AudioSettingsService(FakeRoomService(), adapter))
    return app, adapter


class TestGetEqSettingsTool:
    @pytest.mark.anyio
    async def test_returns_eq_state(self) -> None:
        app, _ = make_app(state=make_state(bass=5, treble=-3, loudness=False))
        result = await app.call_tool("get_eq_settings", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["bass"] == 5
        assert data["treble"] == -3
        assert data["loudness"] is False
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_delegates_to_service(self) -> None:
        app, svc = make_app()
        await app.call_tool("get_eq_settings", {"room": "Kitchen"})
        assert svc.get_calls == ["Kitchen"]

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("get_eq_settings", {"room": "Nowhere"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert "error" in data

    @pytest.mark.anyio
    async def test_audio_settings_error_returns_error(self) -> None:
        app, _ = make_app(raise_audio_settings_error=True)
        result = await app.call_tool("get_eq_settings", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "error" in data
        assert data["field"] == "audio_settings"

    @pytest.mark.anyio
    async def test_discovery_error_returns_connectivity_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("get_eq_settings", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["get_eq_settings"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "get_eq_settings" not in tools

    def test_tool_is_read_only(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["get_eq_settings"].annotations
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False


class TestSetBassTool:
    @pytest.mark.anyio
    async def test_sets_bass_and_returns_state(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("set_bass", {"room": "Living Room", "level": 7})
        data = json.loads(result[0].text)
        assert data["bass"] == 7
        assert svc.set_bass_calls == [("Living Room", 7)]

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("set_bass", {"room": "Nowhere", "level": 0})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_audio_settings_error_returns_error(self) -> None:
        app, _ = make_app(raise_audio_settings_error=True)
        result = await app.call_tool("set_bass", {"room": "Living Room", "level": 5})
        data = json.loads(result[0].text)
        assert data["field"] == "audio_settings"

    @pytest.mark.anyio
    async def test_discovery_error_returns_connectivity_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("set_bass", {"room": "Living Room", "level": 3})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["set_bass"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "set_bass" not in tools

    def test_tool_is_control_not_read_only(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["set_bass"].annotations
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_invalid_string_level_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_bass", {"room": "Living Room", "level": "5"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "audio_settings"
        assert adapter.set_bass_calls == []


class TestSetTrebleTool:
    @pytest.mark.anyio
    async def test_sets_treble_and_returns_state(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("set_treble", {"room": "Living Room", "level": -5})
        data = json.loads(result[0].text)
        assert data["treble"] == -5
        assert svc.set_treble_calls == [("Living Room", -5)]

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("set_treble", {"room": "Nowhere", "level": 0})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_audio_settings_error_returns_error(self) -> None:
        app, _ = make_app(raise_audio_settings_error=True)
        result = await app.call_tool("set_treble", {"room": "Living Room", "level": 2})
        data = json.loads(result[0].text)
        assert data["field"] == "audio_settings"

    @pytest.mark.anyio
    async def test_discovery_error_returns_connectivity_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("set_treble", {"room": "Living Room", "level": 1})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["set_treble"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "set_treble" not in tools

    def test_tool_is_control_not_read_only(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["set_treble"].annotations
        assert annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_invalid_bool_level_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_treble", {"room": "Living Room", "level": True})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "audio_settings"
        assert adapter.set_treble_calls == []


class TestSetLoudnessTool:
    @pytest.mark.anyio
    async def test_enables_loudness_and_returns_state(self) -> None:
        app, svc = make_app(state=make_state(loudness=False))
        result = await app.call_tool("set_loudness", {"room": "Living Room", "enabled": True})
        data = json.loads(result[0].text)
        assert data["loudness"] is True
        assert svc.set_loudness_calls == [("Living Room", True)]

    @pytest.mark.anyio
    async def test_disables_loudness_and_returns_state(self) -> None:
        app, svc = make_app(state=make_state(loudness=True))
        result = await app.call_tool("set_loudness", {"room": "Living Room", "enabled": False})
        data = json.loads(result[0].text)
        assert data["loudness"] is False

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("set_loudness", {"room": "Nowhere", "enabled": True})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_audio_settings_error_returns_error(self) -> None:
        app, _ = make_app(raise_audio_settings_error=True)
        result = await app.call_tool("set_loudness", {"room": "Living Room", "enabled": True})
        data = json.loads(result[0].text)
        assert data["field"] == "audio_settings"

    @pytest.mark.anyio
    async def test_discovery_error_returns_connectivity_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("set_loudness", {"room": "Living Room", "enabled": False})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["set_loudness"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "set_loudness" not in tools

    def test_tool_is_control_not_read_only(self) -> None:
        app, _ = make_app()
        tools = {t.name: t for t in app._tool_manager.list_tools()}
        annotations = tools["set_loudness"].annotations
        assert annotations.readOnlyHint is False

    @pytest.mark.anyio
    async def test_invalid_string_enabled_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_loudness", {"room": "Living Room", "enabled": "true"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "audio_settings"
        assert adapter.set_loudness_calls == []

    @pytest.mark.anyio
    async def test_invalid_integer_enabled_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_loudness", {"room": "Living Room", "enabled": 2})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "audio_settings"
        assert adapter.set_loudness_calls == []
