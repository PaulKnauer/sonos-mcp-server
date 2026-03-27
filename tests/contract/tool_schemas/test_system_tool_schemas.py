"""Contract tests for system tool schemas.

Validates that ``list_rooms`` and ``get_system_topology`` tool names,
descriptions, and parameter schemas remain stable. These tests act as
a breaking-change guard for MCP clients that depend on the tool surface.
"""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.models import Room, SystemTopology
from soniq_mcp.tools.system import register


class _StubRoomService:
    def list_rooms(self, timeout: float = 5.0) -> list[Room]:
        return []

    def get_topology(self, timeout: float = 5.0) -> SystemTopology:
        return SystemTopology.from_rooms([])


@pytest.fixture()
def registered_app() -> FastMCP:
    app = FastMCP("contract-test")
    config = SoniqConfig()
    register(app, config, _StubRoomService())
    return app


def get_tools(app: FastMCP) -> dict:
    return {t.name: t for t in app._tool_manager.list_tools()}


class TestListRoomsContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        assert "list_rooms" in tools

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        desc = tools["list_rooms"].description
        assert desc and len(desc) > 0

    def test_tool_has_no_required_parameters(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        schema = tools["list_rooms"].parameters
        required = schema.get("required", [])
        assert required == [], f"list_rooms should require no params, got: {required}"

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        annotations = tools["list_rooms"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False


class TestGetSystemTopologyContract:
    def test_tool_name_is_stable(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        assert "get_system_topology" in tools

    def test_tool_description_is_present(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        desc = tools["get_system_topology"].description
        assert desc and len(desc) > 0

    def test_tool_has_no_required_parameters(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        schema = tools["get_system_topology"].parameters
        required = schema.get("required", [])
        assert required == [], f"get_system_topology should require no params, got: {required}"

    def test_tool_is_read_only(self, registered_app: FastMCP) -> None:
        tools = get_tools(registered_app)
        annotations = tools["get_system_topology"].annotations
        assert annotations is not None
        assert annotations.readOnlyHint is True
        assert annotations.destructiveHint is False
