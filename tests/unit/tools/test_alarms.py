"""Unit tests for alarm tool handlers."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    AlarmError,
    AlarmValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import AlarmRecord
from soniq_mcp.tools.alarms import register


def make_alarm_record(
    alarm_id: str = "101",
    room_name: str = "Living Room",
    start_time: str = "07:00:00",
    recurrence: str = "DAILY",
    enabled: bool = True,
    volume: int | None = 30,
    include_linked_zones: bool = False,
) -> AlarmRecord:
    return AlarmRecord(
        alarm_id=alarm_id,
        room_name=room_name,
        start_time=start_time,
        recurrence=recurrence,
        enabled=enabled,
        volume=volume,
        include_linked_zones=include_linked_zones,
    )


class FakeAlarmService:
    def __init__(
        self,
        alarms: list[AlarmRecord] | None = None,
        *,
        raise_alarm_error: bool = False,
        raise_validation_error: bool = False,
        raise_room_not_found: bool = False,
        raise_discovery_error: bool = False,
        created_alarm: AlarmRecord | None = None,
        updated_alarm: AlarmRecord | None = None,
    ) -> None:
        self._alarms = alarms or []
        self._raise_alarm_error = raise_alarm_error
        self._raise_validation_error = raise_validation_error
        self._raise_room_not_found = raise_room_not_found
        self._raise_discovery_error = raise_discovery_error
        self._created_alarm = created_alarm or make_alarm_record(alarm_id="new-1")
        self._updated_alarm = updated_alarm or make_alarm_record(alarm_id="101")

    def list_alarms(self) -> list[AlarmRecord]:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_alarm_error:
            raise AlarmError("adapter failure")
        return list(self._alarms)

    def create_alarm(self, **kwargs) -> AlarmRecord:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_room_not_found:
            raise RoomNotFoundError(kwargs.get("room_name", "unknown"))
        if self._raise_validation_error:
            raise AlarmValidationError("invalid recurrence")
        if self._raise_alarm_error:
            raise AlarmError("create failed")
        return self._created_alarm

    def update_alarm(self, **kwargs) -> AlarmRecord:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_room_not_found:
            raise RoomNotFoundError(kwargs.get("room_name", "unknown"))
        if self._raise_validation_error:
            raise AlarmValidationError("invalid time format")
        if self._raise_alarm_error:
            raise AlarmError("not found")
        return self._updated_alarm

    def delete_alarm(self, alarm_id: str) -> dict:
        if self._raise_discovery_error:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_validation_error:
            raise AlarmValidationError("invalid alarm_id")
        if self._raise_alarm_error:
            raise AlarmError(f"Alarm '{alarm_id}' not found.")
        return {"alarm_id": alarm_id, "status": "deleted"}


def make_app(
    service: FakeAlarmService | None = None,
    tools_disabled: list[str] | None = None,
) -> FastMCP:
    app = FastMCP("test")
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    register(app, config, service or FakeAlarmService())
    return app


def get_tool(app: FastMCP, name: str):
    return {t.name: t for t in app._tool_manager.list_tools()}.get(name)


def parse(result) -> dict:
    return json.loads(result[0].text)


class TestListAlarmsTool:
    def test_tool_is_registered(self) -> None:
        app = make_app()
        assert get_tool(app, "list_alarms") is not None

    def test_is_read_only(self) -> None:
        tool = get_tool(make_app(), "list_alarms")
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False

    def test_disabled_tool_not_registered(self) -> None:
        app = make_app(tools_disabled=["list_alarms"])
        assert get_tool(app, "list_alarms") is None

    @pytest.mark.anyio
    async def test_returns_empty_list(self) -> None:
        app = make_app(FakeAlarmService(alarms=[]))
        result = await app.call_tool("list_alarms", {})
        data = parse(result)
        assert data["count"] == 0
        assert data["alarms"] == []

    @pytest.mark.anyio
    async def test_returns_alarm_list(self) -> None:
        alarms = [make_alarm_record("1"), make_alarm_record("2")]
        app = make_app(FakeAlarmService(alarms=alarms))
        result = await app.call_tool("list_alarms", {})
        data = parse(result)
        assert data["count"] == 2
        assert len(data["alarms"]) == 2

    @pytest.mark.anyio
    async def test_returns_error_on_alarm_error(self) -> None:
        app = make_app(FakeAlarmService(raise_alarm_error=True))
        result = await app.call_tool("list_alarms", {})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "alarm"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_error(self) -> None:
        app = make_app(FakeAlarmService(raise_discovery_error=True))
        result = await app.call_tool("list_alarms", {})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestCreateAlarmTool:
    def test_tool_is_registered(self) -> None:
        app = make_app()
        assert get_tool(app, "create_alarm") is not None

    def test_is_control_tool(self) -> None:
        tool = get_tool(make_app(), "create_alarm")
        assert tool.annotations.readOnlyHint is False

    def test_disabled_tool_not_registered(self) -> None:
        app = make_app(tools_disabled=["create_alarm"])
        assert get_tool(app, "create_alarm") is None

    @pytest.mark.anyio
    async def test_successful_create_returns_alarm_record(self) -> None:
        app = make_app(FakeAlarmService())
        result = await app.call_tool(
            "create_alarm",
            {
                "room": "Living Room",
                "start_time": "07:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "alarm_id" in data
        assert data["room_name"] == "Living Room"

    @pytest.mark.anyio
    async def test_returns_validation_error(self) -> None:
        app = make_app(FakeAlarmService(raise_validation_error=True))
        result = await app.call_tool(
            "create_alarm",
            {
                "room": "Living Room",
                "start_time": "07:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "alarm"
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_returns_room_not_found_error(self) -> None:
        app = make_app(FakeAlarmService(raise_room_not_found=True))
        result = await app.call_tool(
            "create_alarm",
            {
                "room": "Ghost Room",
                "start_time": "07:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_returns_alarm_error(self) -> None:
        app = make_app(FakeAlarmService(raise_alarm_error=True))
        result = await app.call_tool(
            "create_alarm",
            {
                "room": "Living Room",
                "start_time": "07:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data

    @pytest.mark.anyio
    async def test_returns_discovery_error(self) -> None:
        app = make_app(FakeAlarmService(raise_discovery_error=True))
        result = await app.call_tool(
            "create_alarm",
            {
                "room": "Living Room",
                "start_time": "07:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestUpdateAlarmTool:
    def test_tool_is_registered(self) -> None:
        app = make_app()
        assert get_tool(app, "update_alarm") is not None

    def test_is_control_tool(self) -> None:
        tool = get_tool(make_app(), "update_alarm")
        assert tool.annotations.readOnlyHint is False

    def test_disabled_tool_not_registered(self) -> None:
        app = make_app(tools_disabled=["update_alarm"])
        assert get_tool(app, "update_alarm") is None

    @pytest.mark.anyio
    async def test_successful_update_returns_alarm_record(self) -> None:
        app = make_app(FakeAlarmService())
        result = await app.call_tool(
            "update_alarm",
            {
                "alarm_id": "101",
                "room": "Living Room",
                "start_time": "09:00:00",
                "recurrence": "WEEKDAYS",
                "enabled": False,
                "include_linked_zones": True,
            },
        )
        data = parse(result)
        assert "alarm_id" in data

    @pytest.mark.anyio
    async def test_returns_validation_error(self) -> None:
        app = make_app(FakeAlarmService(raise_validation_error=True))
        result = await app.call_tool(
            "update_alarm",
            {
                "alarm_id": "101",
                "room": "Living Room",
                "start_time": "bad",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_returns_room_not_found_error(self) -> None:
        app = make_app(FakeAlarmService(raise_room_not_found=True))
        result = await app.call_tool(
            "update_alarm",
            {
                "alarm_id": "101",
                "room": "Ghost Room",
                "start_time": "09:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "room"

    @pytest.mark.anyio
    async def test_returns_alarm_error(self) -> None:
        app = make_app(FakeAlarmService(raise_alarm_error=True))
        result = await app.call_tool(
            "update_alarm",
            {
                "alarm_id": "missing",
                "room": "Living Room",
                "start_time": "09:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "alarm"

    @pytest.mark.anyio
    async def test_returns_discovery_error(self) -> None:
        app = make_app(FakeAlarmService(raise_discovery_error=True))
        result = await app.call_tool(
            "update_alarm",
            {
                "alarm_id": "101",
                "room": "Living Room",
                "start_time": "09:00:00",
                "recurrence": "DAILY",
                "enabled": True,
                "include_linked_zones": False,
            },
        )
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestDeleteAlarmTool:
    def test_tool_is_registered(self) -> None:
        app = make_app()
        assert get_tool(app, "delete_alarm") is not None

    def test_is_control_tool(self) -> None:
        tool = get_tool(make_app(), "delete_alarm")
        assert tool.annotations.readOnlyHint is False

    def test_disabled_tool_not_registered(self) -> None:
        app = make_app(tools_disabled=["delete_alarm"])
        assert get_tool(app, "delete_alarm") is None

    @pytest.mark.anyio
    async def test_successful_delete_returns_confirmation(self) -> None:
        app = make_app(FakeAlarmService())
        result = await app.call_tool("delete_alarm", {"alarm_id": "101"})
        data = parse(result)
        assert data["alarm_id"] == "101"
        assert data["status"] == "deleted"

    @pytest.mark.anyio
    async def test_returns_alarm_error_when_not_found(self) -> None:
        app = make_app(FakeAlarmService(raise_alarm_error=True))
        result = await app.call_tool("delete_alarm", {"alarm_id": "missing"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "alarm"

    @pytest.mark.anyio
    async def test_returns_validation_error_for_invalid_alarm_id(self) -> None:
        app = make_app(FakeAlarmService(raise_validation_error=True))
        result = await app.call_tool("delete_alarm", {"alarm_id": ""})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "alarm"
        assert data["category"] == "validation"

    @pytest.mark.anyio
    async def test_returns_discovery_error(self) -> None:
        app = make_app(FakeAlarmService(raise_discovery_error=True))
        result = await app.call_tool("delete_alarm", {"alarm_id": "101"})
        data = parse(result)
        assert "error" in data
        assert data["field"] == "sonos_network"
