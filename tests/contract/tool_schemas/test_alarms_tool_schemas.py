"""Contract tests for alarm tool schemas.

Validates that tool names, descriptions, parameter schemas, and annotations
remain stable. These tests act as a breaking-change guard for MCP clients
that depend on the alarm tool surface.
"""

from __future__ import annotations

import json

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


def _property_type(prop: dict) -> str | None:
    if "type" in prop:
        return prop["type"]
    any_of = prop.get("anyOf", [])
    types = [entry.get("type") for entry in any_of if "type" in entry]
    if len(types) == 1:
        return types[0]
    return None


class TestAlarmToolSurfaceContract:
    def test_alarm_tool_surface_is_stable(self, registered_app: FastMCP) -> None:
        assert set(get_tools(registered_app)) == {
            "list_alarms",
            "create_alarm",
            "update_alarm",
            "delete_alarm",
        }


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
        assert set(schema.get("required", [])) == {"room", "start_time", "recurrence"}

    def test_has_optional_volume_and_flags(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["create_alarm"].parameters
        props = schema["properties"]
        assert "volume" in props
        assert "enabled" in props
        assert "include_linked_zones" in props
        assert _property_type(props["room"]) == "string"
        assert _property_type(props["start_time"]) == "string"
        assert _property_type(props["recurrence"]) == "string"
        assert _property_type(props["enabled"]) == "boolean"
        assert _property_type(props["include_linked_zones"]) == "boolean"

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["create_alarm"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_shape_is_stable(self, registered_app: FastMCP) -> None:
        result = await registered_app.call_tool(
            "create_alarm",
            {"room": "Living Room", "start_time": "07:00:00", "recurrence": "DAILY"},
        )
        data = json.loads(result[0].text)
        assert data["alarm_id"] == "101"
        assert data["room_name"] == "Living Room"
        assert data["start_time"] == "07:00:00"
        assert data["recurrence"] == "DAILY"

    @pytest.mark.anyio
    async def test_internal_error_shape_is_stable(self) -> None:
        class _InternalService(FakeAlarmService):
            def create_alarm(self, **kwargs) -> AlarmRecord:
                raise RuntimeError("Unexpected alarm failure at /tmp/alarms.log")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _InternalService())
        result = await app.call_tool(
            "create_alarm",
            {"room": "Living Room", "start_time": "07:00:00", "recurrence": "DAILY"},
        )
        data = json.loads(result[0].text)
        assert data["category"] == "internal"
        assert data["field"] == "alarm"


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
        assert set(schema.get("required", [])) == {
            "alarm_id",
            "room",
            "start_time",
            "recurrence",
            "enabled",
        }

    def test_has_expected_identifier_and_boolean_fields(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["update_alarm"].parameters
        props = schema["properties"]
        assert _property_type(props["alarm_id"]) == "string"
        assert _property_type(props["room"]) == "string"
        assert _property_type(props["enabled"]) == "boolean"
        assert _property_type(props["include_linked_zones"]) == "boolean"

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
        assert _property_type(schema["properties"]["alarm_id"]) == "string"

    def test_is_control_tool(self, registered_app: FastMCP) -> None:
        ann = get_tools(registered_app)["delete_alarm"].annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is True
