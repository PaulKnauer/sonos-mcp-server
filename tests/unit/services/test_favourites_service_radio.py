"""Unit tests for FavouritesService radio favourites."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import FavouritesError, RoomNotFoundError
from soniq_mcp.domain.models import RadioFavourite, Room
from soniq_mcp.services.favourites_service import FavouritesService

ROOM = Room(name="Kitchen", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
STATION = RadioFavourite("Radio 1", "x-sonosapi-stream:s1", "station", "<meta/>")


class FakeRadioAdapter:
    def __init__(self, items=None):
        self.items = items if items is not None else [STATION]
        self.played: list[tuple[str, str, str | None]] = []

    def get_radio_favourites(self, ip_address):
        return list(self.items)

    def play_favourite(self, ip_address, uri, meta):
        self.played.append((ip_address, uri, meta))


def _make_service(adapter=None):
    room_service = MagicMock()
    room_service.get_room.return_value = ROOM
    adapter = adapter or FakeRadioAdapter()
    return FavouritesService(room_service, adapter), room_service, adapter


class TestListRadioFavourites:
    def test_returns_adapter_items(self):
        svc, rs, _ = _make_service()

        assert svc.list_radio_favourites("Kitchen") == [STATION]
        rs.get_room.assert_called_once_with("Kitchen")

    def test_propagates_room_not_found(self):
        svc, rs, _ = _make_service()
        rs.get_room.side_effect = RoomNotFoundError("Garage")

        with pytest.raises(RoomNotFoundError):
            svc.list_radio_favourites("Garage")


class TestPlayRadioFavourite:
    def test_plays_with_looked_up_meta(self):
        svc, _, adapter = _make_service()

        svc.play_radio_favourite("Kitchen", "x-sonosapi-stream:s1")

        assert adapter.played == [(ROOM.ip_address, "x-sonosapi-stream:s1", "<meta/>")]

    def test_unknown_uri_plays_without_meta(self):
        svc, _, adapter = _make_service()

        svc.play_radio_favourite("Kitchen", "x-sonosapi-stream:other")

        assert adapter.played == [(ROOM.ip_address, "x-sonosapi-stream:other", None)]

    @pytest.mark.parametrize("uri", ["", "  ", None])
    def test_blank_uri_raises(self, uri):
        svc, _, adapter = _make_service()

        with pytest.raises(FavouritesError):
            svc.play_radio_favourite("Kitchen", uri)
        assert adapter.played == []
