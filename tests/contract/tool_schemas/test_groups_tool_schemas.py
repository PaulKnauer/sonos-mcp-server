"""Contract tests for grouping tool schemas.

Validates that tool names, descriptions, and parameter schemas remain
stable. These tests act as a breaking-change guard for MCP clients.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import Room
from soniq_mcp.tools.groups import register


class _StubGroupService:
    def get_group_topology(self) -> list[Room]:
        return []

    def join_group(self, room_name: str, coordinator_name: str) -> None:
        pass

    def unjoin_room(self, room_name: str) -> None:
        pass

    def party_mode(self) -> None:
        pass


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubGroupService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestGetGroupTopologyContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "get_group_topology" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["get_group_topology"].description
        assert desc and len(desc) > 0

    def test_tool_has_no_required_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["get_group_topology"].parameters
        assert schema.get("required", []) == [] or "required" not in schema

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["get_group_topology"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_groups_and_counts(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("get_group_topology", {})
        data = json.loads(result[0].text)
        assert "groups" in data
        assert "total_groups" in data
        assert "total_rooms" in data


class TestJoinGroupContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "join_group" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["join_group"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["join_group"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_has_coordinator_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["join_group"].parameters
        assert "coordinator" in schema.get("properties", {})
        assert "coordinator" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["join_group"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_shape_is_stable(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool(
            "join_group", {"room": "Office", "coordinator": "Living Room"}
        )
        data = json.loads(result[0].text)
        assert data == {"status": "ok", "room": "Office", "coordinator": "Living Room"}


class TestUnjoinRoomContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "unjoin_room" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["unjoin_room"].description
        assert desc and len(desc) > 0

    def test_tool_has_room_parameter(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["unjoin_room"].parameters
        assert "room" in schema.get("properties", {})
        assert "room" in schema.get("required", [])

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["unjoin_room"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False


class TestPartyModeContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        assert "party_mode" in get_tools(registered_app)

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        desc = get_tools(registered_app)["party_mode"].description
        assert desc and len(desc) > 0

    def test_tool_has_no_required_parameters(self, registered_app: FastMCP) -> None:
        schema = get_tools(registered_app)["party_mode"].parameters
        assert schema.get("required", []) == [] or "required" not in schema

    def test_tool_is_not_read_only(self, registered_app: FastMCP) -> None:
        annotations = get_tools(registered_app)["party_mode"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is False
        assert annotations.destructiveHint is False

    @pytest.mark.anyio
    async def test_response_includes_status(self, registered_app: FastMCP) -> None:
        import json

        result = await registered_app.call_tool("party_mode", {})
        data = json.loads(result[0].text)
        assert "status" in data
        assert data["status"] == "ok"

    @pytest.mark.anyio
    async def test_internal_error_shape_is_stable(self) -> None:
        import json

        class _InternalService(_StubGroupService):
            def party_mode(self) -> None:
                raise RuntimeError("Unexpected group failure at /tmp/groups.log")

        app = FastMCP("contract-test")
        register(app, SoniqConfig(), _InternalService())
        result = await app.call_tool("party_mode", {})
        data = json.loads(result[0].text)
        assert data["category"] == "internal"
        assert data["field"] == "group"
