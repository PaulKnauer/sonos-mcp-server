"""Unit tests for domain models."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.models import Room, SystemTopology, VolumeState


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = "192.168.1.10",
    is_coordinator: bool = True,
    group_coordinator_uid: str | None = None,
) -> Room:
    return Room(
        name=name,
        uid=uid,
        ip_address=ip_address,
        is_coordinator=is_coordinator,
        group_coordinator_uid=group_coordinator_uid,
    )


class TestRoom:
    def test_room_fields(self) -> None:
        room = make_room()
        assert room.name == "Living Room"
        assert room.uid == "RINCON_001"
        assert room.ip_address == "192.168.1.10"
        assert room.is_coordinator is True
        assert room.group_coordinator_uid is None

    def test_room_with_group_coordinator_uid(self) -> None:
        room = make_room(is_coordinator=False, group_coordinator_uid="RINCON_000")
        assert room.is_coordinator is False
        assert room.group_coordinator_uid == "RINCON_000"

    def test_room_is_frozen(self) -> None:
        room = make_room()
        with pytest.raises(Exception):
            room.name = "Kitchen"  # type: ignore[misc]

    def test_room_equality(self) -> None:
        r1 = make_room(uid="RINCON_001")
        r2 = make_room(uid="RINCON_001")
        assert r1 == r2

    def test_room_inequality_different_uid(self) -> None:
        r1 = make_room(uid="RINCON_001")
        r2 = make_room(uid="RINCON_002")
        assert r1 != r2


class TestSystemTopology:
    def test_from_rooms_empty(self) -> None:
        topo = SystemTopology.from_rooms([])
        assert topo.total_count == 0
        assert topo.coordinator_count == 0
        assert topo.rooms == ()

    def test_from_rooms_single_coordinator(self) -> None:
        room = make_room(is_coordinator=True)
        topo = SystemTopology.from_rooms([room])
        assert topo.total_count == 1
        assert topo.coordinator_count == 1
        assert room in topo.rooms

    def test_from_rooms_mixed(self) -> None:
        coord = make_room(name="Living Room", uid="RINCON_001", is_coordinator=True)
        member = make_room(
            name="Kitchen",
            uid="RINCON_002",
            is_coordinator=False,
            group_coordinator_uid="RINCON_001",
        )
        topo = SystemTopology.from_rooms([coord, member])
        assert topo.total_count == 2
        assert topo.coordinator_count == 1

    def test_topology_is_frozen(self) -> None:
        topo = SystemTopology.from_rooms([])
        with pytest.raises(Exception):
            topo.total_count = 99  # type: ignore[misc]
