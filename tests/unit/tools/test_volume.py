"""Unit tests for volume tools using a fake VolumeService."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    RoomNotFoundError,
    SonosDiscoveryError,
    VolumeCapExceeded,
    VolumeError,
)
from soniq_mcp.domain.models import VolumeState
from soniq_mcp.tools.volume import register


class FakeVolumeService:
    """Fake VolumeService with per-method error control."""

    def __init__(
        self,
        volume: int = 50,
        muted: bool = False,
        raise_volume_cap: bool = False,
        raise_room_not_found: bool = False,
        raise_volume_error: bool = False,
        raise_discovery_error: bool = False,
        cap: int = 80,
    ) -> None:
        self._volume = volume
        self._muted = muted
        self._raise_volume_cap = raise_volume_cap
        self._raise_room_not_found = raise_room_not_found
        self._raise_volume_error = raise_volume_error
        self._raise_discovery_error = raise_discovery_error
        self._cap = cap

    def _check_errors(self, room: str) -> None:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_room_not_found:
            raise RoomNotFoundError(room)
        if self._raise_volume_error:
            raise VolumeError("SoCo operation failed")
        if self._raise_volume_cap:
            raise VolumeCapExceeded(self._volume, self._cap)

    def get_volume_state(self, room_name: str) -> VolumeState:
        self._check_errors(room_name)
        return VolumeState(room_name=room_name, volume=self._volume, is_muted=self._muted)

    def set_volume(self, room_name: str, volume: int) -> None:
        self._check_errors(room_name)
        self._volume = volume

    def adjust_volume(self, room_name: str, delta: int) -> VolumeState:
        self._check_errors(room_name)
        self._volume = max(0, min(100, self._volume + delta))
        return VolumeState(room_name=room_name, volume=self._volume, is_muted=self._muted)

    def mute(self, room_name: str) -> None:
        self._check_errors(room_name)
        self._muted = True

    def unmute(self, room_name: str) -> None:
        self._check_errors(room_name)
        self._muted = False


def make_app_with_service(
    volume: int = 50,
    muted: bool = False,
    raise_volume_cap: bool = False,
    raise_room_not_found: bool = False,
    raise_volume_error: bool = False,
    raise_discovery_error: bool = False,
    tools_disabled: list[str] | None = None,
    max_volume_pct: int = 80,
) -> tuple[FastMCP, FakeVolumeService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [], max_volume_pct=max_volume_pct)
    svc = FakeVolumeService(
        volume=volume,
        muted=muted,
        raise_volume_cap=raise_volume_cap,
        raise_room_not_found=raise_room_not_found,
        raise_volume_error=raise_volume_error,
        raise_discovery_error=raise_discovery_error,
    )
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


def get_tool(app: FastMCP, name: str):
    tools = {t.name: t for t in app._tool_manager.list_tools()}
    return tools.get(name)


def parse(result) -> dict:
    return json.loads(result[0].text)


class TestGetVolumeTool:
    def test_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "get_volume") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["get_volume"])
        assert get_tool(app, "get_volume") is None

    @pytest.mark.anyio
    async def test_returns_volume_state(self) -> None:
        app, _ = make_app_with_service(volume=55, muted=False)
        result = await app.call_tool("get_volume", {"room": "Living Room"})
        data = parse(result)
        assert data["room_name"] == "Living Room"
        assert data["volume"] == 55
        assert data["is_muted"] is False

    @pytest.mark.anyio
    async def test_room_not_found_error(self) -> None:
        app, _ = make_app_with_service(raise_room_not_found=True)
        result = await app.call_tool("get_volume", {"room": "Unknown"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_volume_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_error=True)
        result = await app.call_tool("get_volume", {"room": "Living Room"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_volume"

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app_with_service(raise_discovery_error=True)
        result = await app.call_tool("get_volume", {"room": "Living Room"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"

    def test_is_read_only(self) -> None:
        app, _ = make_app_with_service()
        tool = get_tool(app, "get_volume")
        assert tool.annotations.readOnlyHint is True


class TestSetVolumeTool:
    def test_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "set_volume") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["set_volume"])
        assert get_tool(app, "set_volume") is None

    @pytest.mark.anyio
    async def test_returns_ok(self) -> None:
        app, _ = make_app_with_service()
        result = await app.call_tool("set_volume", {"room": "Living Room", "volume": 60})
        data = parse(result)
        assert data["status"] == "ok"
        assert data["room"] == "Living Room"
        assert data["volume"] == 60

    @pytest.mark.anyio
    async def test_volume_cap_exceeded_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_cap=True)
        result = await app.call_tool("set_volume", {"room": "Living Room", "volume": 90})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "volume"

    @pytest.mark.anyio
    async def test_room_not_found_error(self) -> None:
        app, _ = make_app_with_service(raise_room_not_found=True)
        result = await app.call_tool("set_volume", {"room": "Unknown", "volume": 50})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_volume_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_error=True)
        result = await app.call_tool("set_volume", {"room": "Living Room", "volume": 50})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_volume"

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app_with_service(raise_discovery_error=True)
        result = await app.call_tool("set_volume", {"room": "Living Room", "volume": 50})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"

    def test_is_control_tool(self) -> None:
        app, _ = make_app_with_service()
        tool = get_tool(app, "set_volume")
        assert tool.annotations.readOnlyHint is False


class TestAdjustVolumeTool:
    def test_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "adjust_volume") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["adjust_volume"])
        assert get_tool(app, "adjust_volume") is None

    @pytest.mark.anyio
    async def test_returns_updated_state(self) -> None:
        app, _ = make_app_with_service(volume=40)
        result = await app.call_tool("adjust_volume", {"room": "Living Room", "delta": 10})
        data = parse(result)
        assert data["volume"] == 50
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_volume_cap_exceeded_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_cap=True)
        result = await app.call_tool("adjust_volume", {"room": "Living Room", "delta": 30})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "volume"

    @pytest.mark.anyio
    async def test_room_not_found_error(self) -> None:
        app, _ = make_app_with_service(raise_room_not_found=True)
        result = await app.call_tool("adjust_volume", {"room": "Unknown", "delta": 5})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_volume_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_error=True)
        result = await app.call_tool("adjust_volume", {"room": "Living Room", "delta": 5})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_volume"


class TestMuteTool:
    def test_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "mute") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["mute"])
        assert get_tool(app, "mute") is None

    @pytest.mark.anyio
    async def test_returns_ok_muted(self) -> None:
        app, _ = make_app_with_service()
        result = await app.call_tool("mute", {"room": "Living Room"})
        data = parse(result)
        assert data["status"] == "ok"
        assert data["room"] == "Living Room"
        assert data["is_muted"] is True

    @pytest.mark.anyio
    async def test_room_not_found_error(self) -> None:
        app, _ = make_app_with_service(raise_room_not_found=True)
        result = await app.call_tool("mute", {"room": "Unknown"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_volume_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_error=True)
        result = await app.call_tool("mute", {"room": "Living Room"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_volume"

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app_with_service(raise_discovery_error=True)
        result = await app.call_tool("mute", {"room": "Living Room"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"

    def test_is_control_tool(self) -> None:
        app, _ = make_app_with_service()
        tool = get_tool(app, "mute")
        assert tool.annotations.readOnlyHint is False


class TestUnmuteTool:
    def test_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "unmute") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["unmute"])
        assert get_tool(app, "unmute") is None

    @pytest.mark.anyio
    async def test_returns_ok_unmuted(self) -> None:
        app, _ = make_app_with_service(muted=True)
        result = await app.call_tool("unmute", {"room": "Living Room"})
        data = parse(result)
        assert data["status"] == "ok"
        assert data["room"] == "Living Room"
        assert data["is_muted"] is False

    @pytest.mark.anyio
    async def test_room_not_found_error(self) -> None:
        app, _ = make_app_with_service(raise_room_not_found=True)
        result = await app.call_tool("unmute", {"room": "Unknown"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_volume_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_error=True)
        result = await app.call_tool("unmute", {"room": "Living Room"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_volume"

    def test_is_control_tool(self) -> None:
        app, _ = make_app_with_service()
        tool = get_tool(app, "unmute")
        assert tool.annotations.readOnlyHint is False


class TestGetMuteTool:
    def test_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "get_mute") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["get_mute"])
        assert get_tool(app, "get_mute") is None

    @pytest.mark.anyio
    async def test_returns_mute_state_false(self) -> None:
        app, _ = make_app_with_service(muted=False)
        result = await app.call_tool("get_mute", {"room": "Living Room"})
        data = parse(result)
        assert data["room"] == "Living Room"
        assert data["is_muted"] is False

    @pytest.mark.anyio
    async def test_returns_mute_state_true(self) -> None:
        app, _ = make_app_with_service(muted=True)
        result = await app.call_tool("get_mute", {"room": "Living Room"})
        data = parse(result)
        assert data["is_muted"] is True

    @pytest.mark.anyio
    async def test_room_not_found_error(self) -> None:
        app, _ = make_app_with_service(raise_room_not_found=True)
        result = await app.call_tool("get_mute", {"room": "Unknown"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_volume_error(self) -> None:
        app, _ = make_app_with_service(raise_volume_error=True)
        result = await app.call_tool("get_mute", {"room": "Living Room"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_volume"

    def test_is_read_only(self) -> None:
        app, _ = make_app_with_service()
        tool = get_tool(app, "get_mute")
        assert tool.annotations.readOnlyHint is True
