"""Contract tests for alarm tool schemas.

Validates that tool names, descriptions, parameter schemas, and annotations
remain stable. These tests act as a breaking-change guard for MCP clients
that depend on the alarm tool surface.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import AlarmRecord
from soniq_mcp.tools.alarms import register


def make_alarm_record(alarm_id: str = "101") -> AlarmRecord:
    return AlarmRecord(
        alarm_id=alarm_id,
        room_name="Living Room",
        start_time="07:00:00",
        recurrence="DAILY",
        enabled=True,
        volume=30,
        include_linked_zones=False,
    )


class FakeAlarmService:
    def list_alarms(self) -> list[AlarmRecord]:
        return []

    def create_alarm(self, **kwargs) -> AlarmRecord:
        return make_alarm_record()

    def update_alarm(self, **kwargs) -> AlarmRecord:
        return make_alarm_record()

    def delete_alarm(self, alarm_id: str) -> dict:
        return {"alarm_id": alarm_id, "status": "deleted"}


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, FakeAlarmService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestListAlarmsContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "list_alarms" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["list_alarms"].description
        assert desc and len(desc) > 0

    def test_has_no_required_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["list_alarms"].parameters
        assert schema.get("required", []) == []

    def test_is_read_only(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["list_alarms"].annotations
        assert ann.readOnlyHint is True
        assert ann.destructiveHint is False


class TestCreateAlarmContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "create_alarm" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["create_alarm"].description
        assert desc and len(desc) > 0

    def test_requires_room_start_time_and_recurrence(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["create_alarm"].parameters
        required = set(schema.get("required", []))
        assert "room" in required
        assert "start_time" in required
        assert "recurrence" in required

    def test_has_optional_volume_and_flags(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["create_alarm"].parameters
        props = schema["properties"]
        assert "volume" in props
        assert "enabled" in props
        assert "include_linked_zones" in props

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["create_alarm"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False


class TestUpdateAlarmContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "update_alarm" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["update_alarm"].description
        assert desc and len(desc) > 0

    def test_requires_alarm_id_room_start_time_recurrence_and_enabled(
        self, registered_app: FastMCP
    ) -> None:
        schema = get_tools(registered_app)["update_alarm"].parameters
        required = set(schema.get("required", []))
        assert "alarm_id" in required
        assert "room" in required
        assert "start_time" in required
        assert "recurrence" in required
        assert "enabled" in required

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["update_alarm"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False


class TestDeleteAlarmContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "delete_alarm" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["delete_alarm"].description
        assert desc and len(desc) > 0

    def test_requires_alarm_id(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["delete_alarm"].parameters
        required = set(schema.get("required", []))
        assert "alarm_id" in required

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["delete_alarm"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is True
