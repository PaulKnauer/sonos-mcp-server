"""Unit tests for RoomService using a fake adapter."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import Room
from soniq_mcp.services.room_service import RoomService


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


class FakeAdapter:
    """Fake DiscoveryAdapter that returns a pre-configured list of rooms."""

    def __init__(self, rooms: list[Room], raise_error: bool = False) -> None:
        self._rooms = rooms
        self._raise_error = raise_error
        self.discover_calls: list[float] = []

    def discover_rooms(self, timeout: float = 5.0) -> list[Room]:
        self.discover_calls.append(timeout)
        if self._raise_error:
            raise SonosDiscoveryError("network unreachable")
        return list(self._rooms)


class TestRoomServiceListRooms:
    def test_returns_empty_list(self) -> None:
        svc = RoomService(FakeAdapter([]))
        assert svc.list_rooms() == []

    def test_returns_rooms_sorted_by_name(self) -> None:
        rooms = [
            make_room("Zebra Room", "RINCON_003"),
            make_room("Apple Room", "RINCON_001"),
            make_room("Middle Room", "RINCON_002"),
        ]
        svc = RoomService(FakeAdapter(rooms))
        names = [r.name for r in svc.list_rooms()]
        assert names == ["Apple Room", "Middle Room", "Zebra Room"]

    def test_sorting_is_case_insensitive(self) -> None:
        rooms = [
            make_room("zebra", "RINCON_002"),
            make_room("Apple", "RINCON_001"),
        ]
        svc = RoomService(FakeAdapter(rooms))
        names = [r.name for r in svc.list_rooms()]
        assert names == ["Apple", "zebra"]

    def test_passes_timeout_to_adapter(self) -> None:
        adapter = FakeAdapter([])
        svc = RoomService(adapter)
        svc.list_rooms(timeout=3.0)
        assert adapter.discover_calls == [3.0]

    def test_propagates_discovery_error(self) -> None:
        svc = RoomService(FakeAdapter([], raise_error=True))
        with pytest.raises(SonosDiscoveryError):
            svc.list_rooms()


class TestRoomServiceGetTopology:
    def test_empty_topology(self) -> None:
        svc = RoomService(FakeAdapter([]))
        topo = svc.get_topology()
        assert topo.total_count == 0
        assert topo.coordinator_count == 0

    def test_topology_counts(self) -> None:
        rooms = [
            make_room("Living Room", "RINCON_001", is_coordinator=True),
            make_room("Kitchen", "RINCON_002", is_coordinator=False),
        ]
        svc = RoomService(FakeAdapter(rooms))
        topo = svc.get_topology()
        assert topo.total_count == 2
        assert topo.coordinator_count == 1

    def test_topology_rooms_match_list_rooms_order(self) -> None:
        rooms = [
            make_room("Zebra", "RINCON_002"),
            make_room("Apple", "RINCON_001"),
        ]
        svc = RoomService(FakeAdapter(rooms))
        topo = svc.get_topology()
        assert topo.rooms[0].name == "Apple"
        assert topo.rooms[1].name == "Zebra"


class TestRoomServiceGetRoom:
    def test_finds_room_by_name(self) -> None:
        rooms = [make_room("Living Room", "RINCON_001")]
        svc = RoomService(FakeAdapter(rooms))
        room = svc.get_room("Living Room")
        assert room.uid == "RINCON_001"

    def test_lookup_is_case_insensitive(self) -> None:
        rooms = [make_room("Living Room", "RINCON_001")]
        svc = RoomService(FakeAdapter(rooms))
        room = svc.get_room("living room")
        assert room.name == "Living Room"

    def test_lookup_strips_whitespace(self) -> None:
        rooms = [make_room("Living Room", "RINCON_001")]
        svc = RoomService(FakeAdapter(rooms))
        room = svc.get_room("  Living Room  ")
        assert room.uid == "RINCON_001"

    def test_raises_room_not_found(self) -> None:
        svc = RoomService(FakeAdapter([make_room("Kitchen", "RINCON_001")]))
        with pytest.raises(RoomNotFoundError, match="Bathroom"):
            svc.get_room("Bathroom")

    def test_propagates_discovery_error(self) -> None:
        svc = RoomService(FakeAdapter([], raise_error=True))
        with pytest.raises(SonosDiscoveryError):
            svc.get_room("Living Room")
