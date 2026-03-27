"""Unit tests for response schemas."""

from __future__ import annotations

from soniq_mcp.domain.models import Room, SystemTopology
from soniq_mcp.schemas.responses import (
    RoomListResponse,
    RoomResponse,
    SystemTopologyResponse,
)


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
    is_coordinator: bool = True,
) -> Room:
    return Room(name=name, uid=uid, ip_address=ip_address, is_coordinator=is_coordinator)


class TestRoomResponse:
    def test_from_domain(self) -> None:
        room = make_room()
        resp = RoomResponse.from_domain(room)
        assert resp.name == "Living Room"
        assert resp.uid == "RINCON_001"
        assert resp.ip_address == "192.168.1.10"
        assert resp.is_coordinator is True

    def test_model_dump_is_snake_case(self) -> None:
        resp = RoomResponse.from_domain(make_room())
        d = resp.model_dump()
        assert "is_coordinator" in d
        assert "ip_address" in d


class TestRoomListResponse:
    def test_empty(self) -> None:
        resp = RoomListResponse.from_domain([])
        assert resp.count == 0
        assert resp.rooms == []

    def test_from_domain_sets_count(self) -> None:
        rooms = [make_room("R1", "UID1"), make_room("R2", "UID2")]
        resp = RoomListResponse.from_domain(rooms)
        assert resp.count == 2
        assert len(resp.rooms) == 2

    def test_model_dump_serialisable(self) -> None:
        resp = RoomListResponse.from_domain([make_room()])
        d = resp.model_dump()
        assert isinstance(d, dict)
        assert d["count"] == 1
        assert isinstance(d["rooms"], list)
        assert d["rooms"][0]["name"] == "Living Room"


class TestSystemTopologyResponse:
    def test_from_empty_topology(self) -> None:
        topo = SystemTopology.from_rooms([])
        resp = SystemTopologyResponse.from_domain(topo)
        assert resp.total_count == 0
        assert resp.coordinator_count == 0
        assert resp.rooms == []

    def test_from_topology_with_rooms(self) -> None:
        rooms = [
            make_room("Living Room", "RINCON_001", is_coordinator=True),
            make_room("Kitchen", "RINCON_002", is_coordinator=False),
        ]
        topo = SystemTopology.from_rooms(rooms)
        resp = SystemTopologyResponse.from_domain(topo)
        assert resp.total_count == 2
        assert resp.coordinator_count == 1
        assert len(resp.rooms) == 2

    def test_model_dump_serialisable(self) -> None:
        topo = SystemTopology.from_rooms([make_room()])
        resp = SystemTopologyResponse.from_domain(topo)
        d = resp.model_dump()
        assert isinstance(d, dict)
        assert "total_count" in d
        assert "coordinator_count" in d
        assert "rooms" in d
