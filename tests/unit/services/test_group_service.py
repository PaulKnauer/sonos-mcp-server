"""Unit tests for GroupService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import GroupError, RoomNotFoundError
from soniq_mcp.domain.models import Room
from soniq_mcp.services.group_service import GroupService

ROOM = Room(name="Living Room", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
COORDINATOR = Room(name="Kitchen", uid="UID2", ip_address="192.168.1.20", is_coordinator=True)


def _make_service(rooms=None, get_room_fn=None, adapter=None):
    room_service = MagicMock()
    if rooms is not None:
        room_service.list_rooms.return_value = rooms
    else:
        room_service.list_rooms.return_value = [ROOM]
    if get_room_fn is not None:
        room_service.get_room.side_effect = get_room_fn
    else:
        room_service.get_room.return_value = ROOM
    if adapter is None:
        adapter = MagicMock()
    return GroupService(room_service, adapter), room_service, adapter


class TestGetGroupTopology:
    def test_returns_all_rooms_from_room_service(self):
        rooms = [ROOM, COORDINATOR]
        svc, rs, _ = _make_service(rooms=rooms)

        result = svc.get_group_topology()

        rs.list_rooms.assert_called_once()
        assert result == rooms

    def test_returns_empty_list_when_no_rooms(self):
        svc, rs, _ = _make_service(rooms=[])

        result = svc.get_group_topology()

        assert result == []


class TestJoinGroup:
    def test_resolves_both_rooms_and_delegates(self):
        def get_room(name):
            return ROOM if name == "Living Room" else COORDINATOR

        svc, rs, adapter = _make_service(get_room_fn=get_room)
        svc.join_group("Living Room", "Kitchen")

        adapter.join_group.assert_called_once_with(ROOM.ip_address, COORDINATOR.ip_address)

    def test_propagates_room_not_found_for_room(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Living Room")

        with pytest.raises(RoomNotFoundError):
            svc.join_group("Living Room", "Kitchen")

    def test_propagates_room_not_found_for_coordinator(self):
        call_count = [0]

        def get_room(name):
            call_count[0] += 1
            if call_count[0] == 1:
                return ROOM
            raise RoomNotFoundError(name)

        svc, _, _ = _make_service(get_room_fn=get_room)

        with pytest.raises(RoomNotFoundError):
            svc.join_group("Living Room", "Nonexistent")

    def test_propagates_group_error(self):
        def get_room(name):
            return ROOM if name == "Living Room" else COORDINATOR

        svc, _, adapter = _make_service(get_room_fn=get_room)
        adapter.join_group.side_effect = GroupError("join failed")

        with pytest.raises(GroupError):
            svc.join_group("Living Room", "Kitchen")


class TestUnjoinRoom:
    def test_resolves_room_and_delegates(self):
        svc, rs, adapter = _make_service()
        svc.unjoin_room("Living Room")

        rs.get_room.assert_called_once_with("Living Room")
        adapter.unjoin_room.assert_called_once_with(ROOM.ip_address)

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Living Room")

        with pytest.raises(RoomNotFoundError):
            svc.unjoin_room("Living Room")

    def test_propagates_group_error(self):
        svc, _, adapter = _make_service()
        adapter.unjoin_room.side_effect = GroupError("unjoin failed")

        with pytest.raises(GroupError):
            svc.unjoin_room("Living Room")


class TestPartyMode:
    def test_calls_adapter_with_first_room_ip(self):
        rooms = [ROOM, COORDINATOR]
        svc, _, adapter = _make_service(rooms=rooms)
        svc.party_mode()

        adapter.party_mode.assert_called_once_with(ROOM.ip_address)

    def test_raises_group_error_when_no_rooms(self):
        svc, _, _ = _make_service(rooms=[])

        with pytest.raises(GroupError, match="No Sonos rooms found"):
            svc.party_mode()

    def test_propagates_group_error_from_adapter(self):
        svc, _, adapter = _make_service()
        adapter.party_mode.side_effect = GroupError("network failure")

        with pytest.raises(GroupError):
            svc.party_mode()
