"""Unit tests for playback tools using a fake PlaybackService."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import PlaybackError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import PlaybackState, Room, SleepTimerState, TrackInfo
from soniq_mcp.services.playback_service import PlaybackService
from soniq_mcp.tools.playback import register


class FakePlaybackService:
    def __init__(
        self,
        raise_room_not_found: bool = False,
        raise_playback_error: bool = False,
        raise_discovery_error: bool = False,
        room_name: str = "Living Room",
    ) -> None:
        self._raise_room_not_found = raise_room_not_found
        self._raise_playback_error = raise_playback_error
        self._raise_discovery_error = raise_discovery_error
        self._room_name = room_name
        self.calls: list[tuple[str, str]] = []

    def _check_errors(self, room: str) -> None:
        if self._raise_room_not_found:
            raise RoomNotFoundError(room)
        if self._raise_playback_error:
            raise PlaybackError("zone unreachable")
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")

    def play(self, room: str) -> None:
        self.calls.append(("play", room))
        self._check_errors(room)

    def pause(self, room: str) -> None:
        self.calls.append(("pause", room))
        self._check_errors(room)

    def stop(self, room: str) -> None:
        self.calls.append(("stop", room))
        self._check_errors(room)

    def next_track(self, room: str) -> None:
        self.calls.append(("next_track", room))
        self._check_errors(room)

    def previous_track(self, room: str) -> None:
        self.calls.append(("previous_track", room))
        self._check_errors(room)

    def get_playback_state(self, room: str) -> PlaybackState:
        self.calls.append(("get_playback_state", room))
        self._check_errors(room)
        return PlaybackState(transport_state="PLAYING", room_name=self._room_name)

    def get_track_info(self, room: str) -> TrackInfo:
        self.calls.append(("get_track_info", room))
        self._check_errors(room)
        return TrackInfo(title="Test Song", artist="Test Artist", duration="0:03:45")

    def seek(self, room: str, position: str) -> PlaybackState:
        self.calls.append(("seek", room))
        self._check_errors(room)
        return PlaybackState(transport_state="PLAYING", room_name=self._room_name)

    def get_sleep_timer(self, room: str) -> SleepTimerState:
        self.calls.append(("get_sleep_timer", room))
        self._check_errors(room)
        return SleepTimerState(
            room_name=self._room_name,
            active=True,
            remaining_seconds=600,
            remaining_minutes=10,
        )

    def set_sleep_timer(self, room: str, minutes: int) -> SleepTimerState:
        self.calls.append(("set_sleep_timer", room))
        self._check_errors(room)
        if minutes == 0:
            return SleepTimerState(room_name=self._room_name, active=False)
        return SleepTimerState(
            room_name=self._room_name,
            active=True,
            remaining_seconds=minutes * 60,
            remaining_minutes=minutes,
        )


def make_app(
    raise_room_not_found: bool = False,
    raise_playback_error: bool = False,
    raise_discovery_error: bool = False,
    tools_disabled: list[str] | None = None,
) -> tuple[FastMCP, FakePlaybackService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    svc = FakePlaybackService(
        raise_room_not_found=raise_room_not_found,
        raise_playback_error=raise_playback_error,
        raise_discovery_error=raise_discovery_error,
    )
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


def get_tool(app: FastMCP, name: str):
    tools = {t.name: t for t in app._tool_manager.list_tools()}
    return tools.get(name)


async def call_and_parse(app: FastMCP, tool: str, args: dict) -> dict:
    result = await app.call_tool(tool, args)
    return json.loads(result[0].text)


# ── Registration ────────────────────────────────────────────────────────────


class TestToolRegistration:
    TOOL_NAMES = [
        "play",
        "pause",
        "stop",
        "next_track",
        "previous_track",
        "get_playback_state",
        "get_track_info",
        "seek",
        "get_sleep_timer",
        "set_sleep_timer",
    ]

    def test_all_tools_registered(self) -> None:
        app, _ = make_app()
        for name in self.TOOL_NAMES:
            assert get_tool(app, name) is not None, f"{name} not registered"

    def test_tool_disabled_when_in_tools_disabled(self) -> None:
        for name in self.TOOL_NAMES:
            app, _ = make_app(tools_disabled=[name])
            assert get_tool(app, name) is None, f"{name} should be disabled"


# ── Play ─────────────────────────────────────────────────────────────────────


class TestPlayTool:
    @pytest.mark.anyio
    async def test_success_returns_ok(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "play", {"room": "Living Room"})
        assert data["status"] == "ok"
        assert data["room"] == "Living Room"

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "play", {"room": "Nowhere"})
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_playback_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        data = await call_and_parse(app, "play", {"room": "Living Room"})
        assert "error" in data
        assert data["field"] == "playback"

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        data = await call_and_parse(app, "play", {"room": "Living Room"})
        assert "error" in data
        assert data["field"] == "sonos_network"

    def test_has_control_annotations(self) -> None:
        app, _ = make_app()
        tool = get_tool(app, "play")
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False


# ── Pause ─────────────────────────────────────────────────────────────────────


class TestPauseTool:
    @pytest.mark.anyio
    async def test_success_returns_ok(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "pause", {"room": "Living Room"})
        assert data["status"] == "ok"

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "pause", {"room": "X"})
        assert "error" in data


# ── Stop ──────────────────────────────────────────────────────────────────────


class TestStopTool:
    @pytest.mark.anyio
    async def test_success_returns_ok(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "stop", {"room": "Living Room"})
        assert data["status"] == "ok"


# ── Next Track ────────────────────────────────────────────────────────────────


class TestNextTrackTool:
    @pytest.mark.anyio
    async def test_success_returns_ok(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "next_track", {"room": "Living Room"})
        assert data["status"] == "ok"

    @pytest.mark.anyio
    async def test_playback_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        data = await call_and_parse(app, "next_track", {"room": "Living Room"})
        assert "error" in data
        assert data["field"] == "playback"


# ── Previous Track ────────────────────────────────────────────────────────────


class TestPreviousTrackTool:
    @pytest.mark.anyio
    async def test_success_returns_ok(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "previous_track", {"room": "Living Room"})
        assert data["status"] == "ok"


# ── Get Playback State ────────────────────────────────────────────────────────


class TestGetPlaybackStateTool:
    @pytest.mark.anyio
    async def test_returns_state(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "get_playback_state", {"room": "Living Room"})
        assert data["transport_state"] == "PLAYING"
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "get_playback_state", {"room": "X"})
        assert "error" in data
        assert data["field"] == "room"

    def test_has_read_only_annotations(self) -> None:
        app, _ = make_app()
        tool = get_tool(app, "get_playback_state")
        assert tool.annotations.readOnlyHint is True


# ── Get Track Info ────────────────────────────────────────────────────────────


class TestGetTrackInfoTool:
    @pytest.mark.anyio
    async def test_returns_track_info(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "get_track_info", {"room": "Living Room"})
        assert data["title"] == "Test Song"
        assert data["artist"] == "Test Artist"
        assert data["duration"] == "0:03:45"
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "get_track_info", {"room": "X"})
        assert "error" in data

    def test_has_read_only_annotations(self) -> None:
        app, _ = make_app()
        tool = get_tool(app, "get_track_info")
        assert tool.annotations.readOnlyHint is True


# ── Seek ──────────────────────────────────────────────────────────────────────


class TestSeekTool:
    @pytest.mark.anyio
    async def test_success_returns_playback_state(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "seek", {"room": "Living Room", "position": "0:01:30"})
        assert data["transport_state"] == "PLAYING"
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "seek", {"room": "X", "position": "0:01:00"})
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_playback_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        data = await call_and_parse(app, "seek", {"room": "Living Room", "position": "0:01:00"})
        assert "error" in data
        assert data["field"] == "playback"

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        data = await call_and_parse(app, "seek", {"room": "Living Room", "position": "0:01:00"})
        assert "error" in data
        assert data["field"] == "sonos_network"

    def test_has_control_annotations(self) -> None:
        app, _ = make_app()
        tool = get_tool(app, "seek")
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False

    def test_disabled_when_in_tools_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["seek"])
        assert get_tool(app, "seek") is None


# ── Get Sleep Timer ────────────────────────────────────────────────────────────


class TestGetSleepTimerTool:
    @pytest.mark.anyio
    async def test_success_returns_timer_state(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "get_sleep_timer", {"room": "Living Room"})
        assert data["active"] is True
        assert data["remaining_seconds"] == 600
        assert data["remaining_minutes"] == 10
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "get_sleep_timer", {"room": "X"})
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_playback_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        data = await call_and_parse(app, "get_sleep_timer", {"room": "Living Room"})
        assert "error" in data

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        data = await call_and_parse(app, "get_sleep_timer", {"room": "Living Room"})
        assert "error" in data

    def test_has_read_only_annotations(self) -> None:
        app, _ = make_app()
        tool = get_tool(app, "get_sleep_timer")
        assert tool.annotations.readOnlyHint is True

    def test_disabled_when_in_tools_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["get_sleep_timer"])
        assert get_tool(app, "get_sleep_timer") is None


# ── Set Sleep Timer ────────────────────────────────────────────────────────────


class TestSetSleepTimerTool:
    @pytest.mark.anyio
    async def test_success_returns_timer_state(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "set_sleep_timer", {"room": "Living Room", "minutes": 30})
        assert data["active"] is True
        assert data["remaining_seconds"] == 1800
        assert data["remaining_minutes"] == 30
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_zero_minutes_clears_timer(self) -> None:
        app, _ = make_app()
        data = await call_and_parse(app, "set_sleep_timer", {"room": "Living Room", "minutes": 0})
        assert data["active"] is False

    @pytest.mark.anyio
    async def test_room_not_found(self) -> None:
        app, _ = make_app(raise_room_not_found=True)
        data = await call_and_parse(app, "set_sleep_timer", {"room": "X", "minutes": 10})
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_playback_error(self) -> None:
        app, _ = make_app(raise_playback_error=True)
        data = await call_and_parse(app, "set_sleep_timer", {"room": "Living Room", "minutes": 10})
        assert "error" in data
        assert data["field"] == "playback"

    @pytest.mark.anyio
    async def test_discovery_error(self) -> None:
        app, _ = make_app(raise_discovery_error=True)
        data = await call_and_parse(app, "set_sleep_timer", {"room": "Living Room", "minutes": 10})
        assert "error" in data
        assert data["field"] == "sonos_network"

    def test_has_control_annotations(self) -> None:
        app, _ = make_app()
        tool = get_tool(app, "set_sleep_timer")
        assert tool.annotations.readOnlyHint is False
        assert tool.annotations.destructiveHint is False

    def test_disabled_when_in_tools_disabled(self) -> None:
        app, _ = make_app(tools_disabled=["set_sleep_timer"])
        assert get_tool(app, "set_sleep_timer") is None


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
        self.set_sleep_timer_calls: list[tuple[str, str, int]] = []

    def set_sleep_timer(self, ip_address: str, room_name: str, minutes: int) -> SleepTimerState:
        self.set_sleep_timer_calls.append((ip_address, room_name, minutes))
        return SleepTimerState(
            room_name=room_name,
            active=True,
            remaining_seconds=minutes * 60,
            remaining_minutes=minutes,
        )

    def get_sleep_timer(self, ip_address: str, room_name: str) -> SleepTimerState:
        return SleepTimerState(room_name=room_name, active=False)

    def get_playback_state(self, ip_address: str, room_name: str) -> PlaybackState:
        return PlaybackState(transport_state="PLAYING", room_name=room_name)

    def seek(self, ip_address: str, position: str) -> None:
        return None

    def play(self, ip_address: str) -> None: ...
    def pause(self, ip_address: str) -> None: ...
    def stop(self, ip_address: str) -> None: ...
    def next_track(self, ip_address: str) -> None: ...
    def previous_track(self, ip_address: str) -> None: ...
    def get_track_info(self, ip_address: str): ...
    def get_volume(self, ip_address: str) -> int:
        return 50

    def get_mute(self, ip_address: str) -> bool:
        return False


def make_validating_app() -> tuple[FastMCP, _ValidatingAdapter]:
    from soniq_mcp.config.models import SoniqConfig
    from soniq_mcp.services.sonos_service import SonosService

    adapter = _ValidatingAdapter()
    sonos_service = SonosService(_ValidatingRoomService(), adapter, SoniqConfig())
    app = FastMCP("test")
    register(app, SoniqConfig(), PlaybackService(sonos_service=sonos_service))
    return app, adapter


class TestSetSleepTimerRawValidation:
    @pytest.mark.anyio
    async def test_invalid_boolean_minutes_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_sleep_timer", {"room": "Living Room", "minutes": True})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "playback"
        assert "minutes" in data["error"]
        assert adapter.set_sleep_timer_calls == []

    @pytest.mark.anyio
    async def test_invalid_string_minutes_returns_validation_error_without_write(self) -> None:
        app, adapter = make_validating_app()
        result = await app.call_tool("set_sleep_timer", {"room": "Living Room", "minutes": "5"})
        data = json.loads(result[0].text)
        assert data["category"] == "validation"
        assert data["field"] == "playback"
        assert "minutes" in data["error"]
        assert adapter.set_sleep_timer_calls == []
