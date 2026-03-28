"""Unit tests for system tools using a fake RoomService."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import SonosDiscoveryError
from soniq_mcp.domain.models import Room, Speaker, SystemTopology
from soniq_mcp.tools.system import register


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    is_coordinator: bool = True,
) -> Room:
    return Room(
        name=name,
        uid=uid,
        ip_address="192.168.1.10",
        is_coordinator=is_coordinator,
    )


class FakeRoomService:
    def __init__(
        self,
        rooms: list[Room] | None = None,
        raise_error: bool = False,
    ) -> None:
        self._rooms = rooms or []
        self._raise_error = raise_error

    def list_rooms(self, timeout: float = 5.0) -> list[Room]:
        if self._raise_error:
            raise SonosDiscoveryError("network unreachable")
        return list(self._rooms)

    def get_topology(self, timeout: float = 5.0) -> SystemTopology:
        if self._raise_error:
            raise SonosDiscoveryError("network unreachable")
        speakers = [
            Speaker(
                name=room.name,
                uid=room.uid,
                ip_address=room.ip_address,
                room_name=room.name,
                room_uid=room.uid,
                model_name="Sonos One",
                is_visible=True,
            )
            for room in self._rooms
        ]
        return SystemTopology.from_rooms(self._rooms, speakers=speakers)


def make_app_with_service(
    rooms: list[Room] | None = None,
    raise_error: bool = False,
    tools_disabled: list[str] | None = None,
) -> tuple[FastMCP, FakeRoomService]:
    config = SoniqConfig(tools_disabled=tools_disabled or [])
    svc = FakeRoomService(rooms=rooms, raise_error=raise_error)
    app = FastMCP("test")
    register(app, config, svc)
    return app, svc


def get_tool(app: FastMCP, name: str):
    tools = {t.name: t for t in app._tool_manager.list_tools()}
    return tools.get(name)


class TestListRoomsTool:
    def test_tool_is_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "list_rooms") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["list_rooms"])
        assert get_tool(app, "list_rooms") is None

    @pytest.mark.anyio
    async def test_returns_empty_list(self) -> None:
        app, _ = make_app_with_service(rooms=[])
        result = await app.call_tool("list_rooms", {})
        assert result[0].text  # type: ignore[attr-defined]
        import json
        data = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert data["count"] == 0
        assert data["rooms"] == []

    @pytest.mark.anyio
    async def test_returns_room_list(self) -> None:
        rooms = [make_room("Living Room", "RINCON_001")]
        app, _ = make_app_with_service(rooms=rooms)
        result = await app.call_tool("list_rooms", {})
        import json
        data = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert data["count"] == 1
        assert data["rooms"][0]["name"] == "Living Room"
        assert data["rooms"][0]["uid"] == "RINCON_001"

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_failure(self) -> None:
        app, _ = make_app_with_service(raise_error=True)
        result = await app.call_tool("list_rooms", {})
        import json
        data = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert "error" in data
        assert data["field"] == "sonos_network"


class TestGetSystemTopologyTool:
    def test_tool_is_registered(self) -> None:
        app, _ = make_app_with_service()
        assert get_tool(app, "get_system_topology") is not None

    def test_not_registered_when_disabled(self) -> None:
        app, _ = make_app_with_service(tools_disabled=["get_system_topology"])
        assert get_tool(app, "get_system_topology") is None

    @pytest.mark.anyio
    async def test_returns_topology(self) -> None:
        rooms = [
            make_room("Living Room", "RINCON_001", is_coordinator=True),
            make_room("Kitchen", "RINCON_002", is_coordinator=False),
        ]
        app, _ = make_app_with_service(rooms=rooms)
        result = await app.call_tool("get_system_topology", {})
        import json
        data = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert data["total_count"] == 2
        assert data["coordinator_count"] == 1
        assert data["speaker_count"] == 2
        assert len(data["rooms"]) == 2
        assert len(data["speakers"]) == 2

    @pytest.mark.anyio
    async def test_returns_error_on_discovery_failure(self) -> None:
        app, _ = make_app_with_service(raise_error=True)
        result = await app.call_tool("get_system_topology", {})
        import json
        data = json.loads(result[0].text)  # type: ignore[attr-defined]
        assert "error" in data
        assert data["field"] == "sonos_network"
