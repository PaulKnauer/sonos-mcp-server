"""Unit tests for play mode MCP tools using a fake PlayModeService."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    PlaybackError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import PlayModeState, Room
from soniq_mcp.services.play_mode_service import PlayModeService
from soniq_mcp.tools.play_modes import register


class FakePlayModeService:
    def __init__(
        self,
        raise_room_not_found: bool = False,
        raise_playback_error: bool = False,
        raise_discovery_error: bool = False,
        state: PlayModeState | None = None,
    ) -> None:
        self._raise_room_not_found = raise_room_not_found
        self._raise_playback_error = raise_playback_error
        self._raise_discovery_error = raise_discovery_error
        self._state = state or PlayModeState(
            room_name="Living Room", shuffle=False, repeat="none", cross_fade=False
        )
        self.get_calls: list[str] = []
        self.set_calls: list[tuple] = []

    def _check_errors(self, room: str) -> None:
        if self._raise_room_not_found:
            raise RoomNotFoundError(room)
        if self._raise_playback_error:
            raise PlaybackError("mode unavailable")
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")

    def get_play_mode(self, room: str) -> PlayModeState:
        self.get_calls.append(room)
        self._check_errors(room)
        return PlayModeState(
            room_name=room,
            shuffle=self._state.shuffle,
            repeat=self._state.repeat,
            cross_fade=self._state.cross_fade,
        )

    def set_play_mode(
        self,
        room: str,
        shuffle=None,
        repeat=None,
        cross_fade=None,
    ) -> PlayModeState:
        self.set_calls.append((room, shuffle, repeat, cross_fade))
        self._check_errors(room)
        new_shuffle = shuffle if shuffle is not None else self._state.shuffle
        new_repeat = repeat if repeat is not None else self._state.repeat
        new_cross_fade = cross_fade if cross_fade is not None else self._state.cross_fade
        return PlayModeState(
            room_name=room,
            shuffle=new_shuffle,
            repeat=new_repeat,
            cross_fade=new_cross_fade,
        )


def make_app(
    raise_room_not_found: bool = False,
    raise_playback_error: bool = False,
    raise_discovery_error: bool = False,
    tools_disabled: list[str] | None = None,
    state: PlayModeState | None = None,
) -> tuple[FastMCP, FakePlayModeService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    svc = FakePlayModeService(
        raise_room_not_found=raise_room_not_found,
        raise_playback_error=raise_playback_error,
        raise_discovery_error=raise_discovery_error,
        state=state,
    )
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


class TestGetPlayModeTool:
    @pytest.mark.anyio
    async def test_returns_play_mode_state(self) -> None:
        app, svc = make_app(state=PlayModeState("r", True, "all", True))
        result = await app.call_tool("get_play_mode", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["shuffle"] is True
        assert data["repeat"] == "all"
        assert data["cross_fade"] is True
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_delegates_to_service(self) -> None:
        app, svc = make_app()
        await app.call_tool("get_play_mode", {"room": "Kitchen"})
        assert svc.get_calls == ["Kitchen"]

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("get_play_mode", {"room": "Nowhere"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert "error" in data

    @pytest.mark.anyio
    async def test_playback_error_returns_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        result = await app.call_tool("get_play_mode", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.anyio
    async def test_discovery_error_returns_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("get_play_mode", {"room": "Living Room"})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["get_play_mode"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "get_play_mode" not in tools


class TestSetPlayModeTool:
    @pytest.mark.anyio
    async def test_sets_shuffle_returns_updated_state(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "shuffle": True})
        data = json.loads(result[0].text)
        assert data["shuffle"] is True
        assert svc.set_calls[0][1] is True  # shuffle arg

    @pytest.mark.anyio
    async def test_sets_repeat_all(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "repeat": "all"})
        data = json.loads(result[0].text)
        assert data["repeat"] == "all"

    @pytest.mark.anyio
    async def test_sets_cross_fade(self) -> None:
        app, svc = make_app()
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "cross_fade": True})
        data = json.loads(result[0].text)
        assert data["cross_fade"] is True

    @pytest.mark.anyio
    async def test_room_not_found_returns_error(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        result = await app.call_tool("set_play_mode", {"room": "Nowhere", "shuffle": True})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_playback_error_returns_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "shuffle": True})
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.anyio
    async def test_discovery_error_returns_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "shuffle": True})
        data = json.loads(result[0].text)
        assert data["category"] == "connectivity"

    def test_tool_not_registered_when_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["set_play_mode"])
        tools = {t.name for t in app._tool_manager.list_tools()}
        assert "set_play_mode" not in tools


class _ValidatingRoomService:
    def __init__(self, room: Room | None = None) -> None:
        self._room = room or Room(
            name="Living Room",
            uid="RINCON_1",
            ip_address="192.168.1.10",
            is_coordinator=True,
            group_coordinator_uid=None,
        )

    def get_room(self, name: str) -> Room:
        if name != self._room.name:
            raise RoomNotFoundError(name)
        return self._room

    def list_rooms(self) -> list[Room]:
        return [self._room]


class _ValidatingAdapter:
    def __init__(self) -> None:
        self.set_calls: list[tuple[str, str, object, object, object]] = []

    def get_play_mode(self, ip_address: str, room_name: str) -> PlayModeState:
        return PlayModeState(room_name=room_name, shuffle=False, repeat="none", cross_fade=False)

    def set_play_mode(
        self,
        ip_address: str,
        room_name: str,
        shuffle=None,
        repeat=None,
        cross_fade=None,
    ) -> PlayModeState:
        self.set_calls.append((ip_address, room_name, shuffle, repeat, cross_fade))
        return PlayModeState(
            room_name=room_name,
            shuffle=False if shuffle is None else shuffle,
            repeat="none" if repeat is None else repeat,
            cross_fade=False if cross_fade is None else cross_fade,
        )


def make_validating_app() -> tuple[FastMCP, _ValidatingAdapter]:
    adapter = _ValidatingAdapter()
    service = PlayModeService(_ValidatingRoomService(), adapter, None)
    app = FastMCP("test")
    register(app, SoniqConfig(), service)
    return app, adapter


class TestSetPlayModeRawValidation:
    @pytest.mark.anyio
    async def test_invalid_string_shuffle_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "shuffle": "true"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "playback"
        assert "shuffle" in data["error"]
        assert adapter.set_calls == []

    @pytest.mark.anyio
    async def test_invalid_string_cross_fade_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "cross_fade": "true"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "playback"
        assert "cross_fade" in data["error"]
        assert adapter.set_calls == []

    @pytest.mark.anyio
    async def test_invalid_repeat_value_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_play_mode", {"room": "Living Room", "repeat": "loop"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "playback"
        assert "repeat" in data["error"]
        assert adapter.set_calls == []
