"""Unit tests for PlaybackService.play_uri."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import PlaybackError, PlaybackValidationError, RoomNotFoundError
from soniq_mcp.domain.models import Room
from soniq_mcp.services.playback_service import PlaybackService
from soniq_mcp.services.sonos_service import SonosService

COORDINATOR = Room(name="Kitchen", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
MEMBER = Room(
    name="Dining",
    uid="UID2",
    ip_address="192.168.1.11",
    is_coordinator=False,
    group_coordinator_uid="UID1",
)


class FakeAdapter:
    def __init__(self, error: Exception | None = None) -> None:
        self.calls: list[tuple] = []
        self._error = error

    def play_uri(self, ip_address, uri, meta, title, force_radio):
        self.calls.append((ip_address, uri, meta, title, force_radio))
        if self._error:
            raise self._error


def _make_service(adapter=None):
    rooms = {"Kitchen": COORDINATOR, "Dining": MEMBER}
    room_service = MagicMock()

    def get_room(name):
        if name not in rooms:
            raise RoomNotFoundError(name)
        return rooms[name]

    room_service.get_room.side_effect = get_room
    room_service.list_rooms.return_value = list(rooms.values())
    adapter = adapter or FakeAdapter()
    sonos = SonosService(room_service, adapter, SoniqConfig())
    return PlaybackService(sonos_service=sonos), adapter


class TestPlayUri:
    def test_delegates_to_adapter(self):
        svc, adapter = _make_service()

        svc.play_uri("Kitchen", "http://hermes/a.mp3", title="Hi")

        assert adapter.calls == [(COORDINATOR.ip_address, "http://hermes/a.mp3", "", "Hi", False)]

    def test_routes_group_member_to_coordinator(self):
        svc, adapter = _make_service()

        svc.play_uri("Dining", "x-rincon-mp3radio://stream", force_radio=True)

        assert adapter.calls[0][0] == COORDINATOR.ip_address
        assert adapter.calls[0][4] is True

    def test_strips_whitespace(self):
        svc, adapter = _make_service()

        svc.play_uri("Kitchen", "  http://hermes/a.mp3  ")

        assert adapter.calls[0][1] == "http://hermes/a.mp3"

    @pytest.mark.parametrize("uri", ["", "   ", "no-scheme", ":missing", "http:", None, 42])
    def test_invalid_uri_raises_validation_error(self, uri):
        svc, adapter = _make_service()

        with pytest.raises(PlaybackValidationError):
            svc.play_uri("Kitchen", uri)
        assert adapter.calls == []

    def test_propagates_room_not_found(self):
        svc, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.play_uri("Garage", "http://hermes/a.mp3")

    def test_propagates_adapter_error(self):
        svc, _ = _make_service(FakeAdapter(PlaybackError("boom")))

        with pytest.raises(PlaybackError):
            svc.play_uri("Kitchen", "http://hermes/a.mp3")
