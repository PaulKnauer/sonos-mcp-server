"""Unit tests for QueueService."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import QueueError, RoomNotFoundError
from soniq_mcp.domain.models import QueueItem, Room
from soniq_mcp.services.queue_service import QueueService

ROOM = Room(name="Kitchen", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
IP = ROOM.ip_address


def _make_service(room=ROOM, adapter=None):
    room_service = MagicMock()
    room_service.get_room.return_value = room
    if adapter is None:
        adapter = MagicMock()
    return QueueService(room_service, adapter), room_service, adapter


class TestGetQueue:
    def test_resolves_room_and_delegates(self):
        items = [QueueItem(position=1, uri="uri:1", title="T1")]
        svc, rs, adapter = _make_service()
        adapter.get_queue.return_value = items

        result = svc.get_queue("Kitchen")

        rs.get_room.assert_called_once_with("Kitchen")
        adapter.get_queue.assert_called_once_with(IP)
        assert result == items

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Kitchen")

        with pytest.raises(RoomNotFoundError):
            svc.get_queue("Kitchen")

    def test_propagates_queue_error(self):
        svc, _, adapter = _make_service()
        adapter.get_queue.side_effect = QueueError("network")

        with pytest.raises(QueueError):
            svc.get_queue("Kitchen")


class TestAddToQueue:
    def test_resolves_room_and_delegates(self):
        svc, rs, adapter = _make_service()
        adapter.add_to_queue.return_value = 5

        result = svc.add_to_queue("Kitchen", "x-sonos:track")

        adapter.add_to_queue.assert_called_once_with(IP, "x-sonos:track")
        assert result == 5

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Kitchen")

        with pytest.raises(RoomNotFoundError):
            svc.add_to_queue("Kitchen", "uri")

    def test_propagates_queue_error(self):
        svc, _, adapter = _make_service()
        adapter.add_to_queue.side_effect = QueueError("upnp")

        with pytest.raises(QueueError):
            svc.add_to_queue("Kitchen", "uri")


class TestRemoveFromQueue:
    def test_resolves_room_and_delegates(self):
        svc, rs, adapter = _make_service()

        svc.remove_from_queue("Kitchen", 2)

        adapter.remove_from_queue.assert_called_once_with(IP, 2)

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Kitchen")

        with pytest.raises(RoomNotFoundError):
            svc.remove_from_queue("Kitchen", 1)

    def test_propagates_queue_error(self):
        svc, _, adapter = _make_service()
        adapter.remove_from_queue.side_effect = QueueError("out of range")

        with pytest.raises(QueueError):
            svc.remove_from_queue("Kitchen", 99)


class TestClearQueue:
    def test_resolves_room_and_delegates(self):
        svc, rs, adapter = _make_service()

        svc.clear_queue("Kitchen")

        rs.get_room.assert_called_once_with("Kitchen")
        adapter.clear_queue.assert_called_once_with(IP)

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Kitchen")

        with pytest.raises(RoomNotFoundError):
            svc.clear_queue("Kitchen")

    def test_propagates_queue_error(self):
        svc, _, adapter = _make_service()
        adapter.clear_queue.side_effect = QueueError("upnp")

        with pytest.raises(QueueError):
            svc.clear_queue("Kitchen")


class TestPlayFromQueue:
    def test_resolves_room_and_delegates(self):
        svc, rs, adapter = _make_service()

        svc.play_from_queue("Kitchen", 3)

        adapter.play_from_queue.assert_called_once_with(IP, 3)

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Kitchen")

        with pytest.raises(RoomNotFoundError):
            svc.play_from_queue("Kitchen", 1)

    def test_propagates_queue_error(self):
        svc, _, adapter = _make_service()
        adapter.play_from_queue.side_effect = QueueError("invalid position")

        with pytest.raises(QueueError):
            svc.play_from_queue("Kitchen", 0)
