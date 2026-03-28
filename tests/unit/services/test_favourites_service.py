"""Unit tests for FavouritesService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import FavouritesError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import Favourite, Room, SonosPlaylist
from soniq_mcp.services.favourites_service import FavouritesService

IP = "192.168.1.10"
ROOM_NAME = "Living Room"
ROOM = Room(name=ROOM_NAME, uid="RINCON_123", ip_address=IP, is_coordinator=True)


class FakeRoomService:
    def __init__(self, rooms: list[Room] | None = None, raise_not_found: bool = False, raise_discovery: bool = False) -> None:
        self._rooms = rooms if rooms is not None else [ROOM]
        self._raise_not_found = raise_not_found
        self._raise_discovery = raise_discovery

    def list_rooms(self) -> list[Room]:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        return self._rooms

    def get_room(self, room_name: str) -> Room:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        if self._raise_not_found:
            raise RoomNotFoundError(room_name)
        for room in self._rooms:
            if room.name == room_name:
                return room
        raise RoomNotFoundError(room_name)


class FakeAdapter:
    def __init__(
        self,
        favourites: list[Favourite] | None = None,
        playlists: list[SonosPlaylist] | None = None,
        raise_favourites_error: bool = False,
    ) -> None:
        self._favourites = favourites or []
        self._playlists = playlists or []
        self._raise_favourites_error = raise_favourites_error
        self.get_favourites_calls: list[str] = []
        self.play_favourite_calls: list[tuple] = []
        self.play_playlist_calls: list[tuple] = []

    def get_favourites(self, ip_address: str) -> list[Favourite]:
        if self._raise_favourites_error:
            raise FavouritesError("adapter error")
        self.get_favourites_calls.append(ip_address)
        return self._favourites

    def play_favourite(self, ip_address: str, uri: str, meta: str | None) -> None:
        if self._raise_favourites_error:
            raise FavouritesError("adapter error")
        self.play_favourite_calls.append((ip_address, uri, meta))

    def get_playlists(self, ip_address: str) -> list[SonosPlaylist]:
        if self._raise_favourites_error:
            raise FavouritesError("adapter error")
        return self._playlists

    def play_playlist(self, ip_address: str, uri: str) -> None:
        if self._raise_favourites_error:
            raise FavouritesError("adapter error")
        self.play_playlist_calls.append((ip_address, uri))


FAV = Favourite(title="Radio", uri="x-sonosapi://radio", meta="<DIDL/>")
PLAYLIST = SonosPlaylist(title="Party Mix", uri="x-rincon-playlist://pl1", item_id="SQ:1")


class TestGetFavourites:
    def test_returns_favourites_from_adapter(self) -> None:
        svc = FavouritesService(FakeRoomService(), FakeAdapter(favourites=[FAV]))
        result = svc.get_favourites()
        assert result == [FAV]

    def test_uses_first_room_ip(self) -> None:
        room2 = Room(name="Bedroom", uid="RINCON_456", ip_address="192.168.1.20", is_coordinator=True)
        adapter = FakeAdapter(favourites=[FAV])
        svc = FavouritesService(FakeRoomService(rooms=[ROOM, room2]), adapter)
        svc.get_favourites()
        assert adapter.get_favourites_calls == [IP]

    def test_raises_favourites_error_when_no_rooms(self) -> None:
        svc = FavouritesService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(FavouritesError, match="No Sonos rooms found"):
            svc.get_favourites()

    def test_propagates_favourites_error_from_adapter(self) -> None:
        svc = FavouritesService(FakeRoomService(), FakeAdapter(raise_favourites_error=True))
        with pytest.raises(FavouritesError):
            svc.get_favourites()

    def test_propagates_discovery_error(self) -> None:
        svc = FavouritesService(FakeRoomService(raise_discovery=True), FakeAdapter())
        with pytest.raises(SonosDiscoveryError):
            svc.get_favourites()


class TestPlayFavourite:
    def test_looks_up_meta_by_uri_when_not_provided(self) -> None:
        adapter = FakeAdapter(favourites=[FAV])
        svc = FavouritesService(FakeRoomService(), adapter)
        svc.play_favourite(ROOM_NAME, FAV.uri, None)
        assert adapter.get_favourites_calls == [IP]
        assert adapter.play_favourite_calls == [(IP, FAV.uri, FAV.meta)]

    def test_prefers_explicit_meta_without_lookup(self) -> None:
        adapter = FakeAdapter(favourites=[FAV])
        svc = FavouritesService(FakeRoomService(), adapter)
        svc.play_favourite(ROOM_NAME, FAV.uri, "<explicit/>")
        assert adapter.get_favourites_calls == []
        assert adapter.play_favourite_calls == [(IP, FAV.uri, "<explicit/>")]

    def test_resolves_room_and_calls_adapter(self) -> None:
        adapter = FakeAdapter()
        svc = FavouritesService(FakeRoomService(), adapter)
        svc.play_favourite(ROOM_NAME, FAV.uri, FAV.meta)
        assert adapter.play_favourite_calls == [(IP, FAV.uri, FAV.meta)]

    def test_propagates_room_not_found(self) -> None:
        svc = FavouritesService(FakeRoomService(raise_not_found=True), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.play_favourite("Unknown Room", FAV.uri, None)

    def test_propagates_favourites_error_from_adapter(self) -> None:
        svc = FavouritesService(FakeRoomService(), FakeAdapter(raise_favourites_error=True))
        with pytest.raises(FavouritesError):
            svc.play_favourite(ROOM_NAME, FAV.uri, None)


class TestGetPlaylists:
    def test_returns_playlists_from_adapter(self) -> None:
        svc = FavouritesService(FakeRoomService(), FakeAdapter(playlists=[PLAYLIST]))
        result = svc.get_playlists()
        assert result == [PLAYLIST]

    def test_raises_favourites_error_when_no_rooms(self) -> None:
        svc = FavouritesService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(FavouritesError, match="No Sonos rooms found"):
            svc.get_playlists()

    def test_propagates_favourites_error_from_adapter(self) -> None:
        svc = FavouritesService(FakeRoomService(), FakeAdapter(raise_favourites_error=True))
        with pytest.raises(FavouritesError):
            svc.get_playlists()


class TestPlayPlaylist:
    def test_resolves_room_and_calls_adapter(self) -> None:
        adapter = FakeAdapter()
        svc = FavouritesService(FakeRoomService(), adapter)
        svc.play_playlist(ROOM_NAME, PLAYLIST.uri)
        assert adapter.play_playlist_calls == [(IP, PLAYLIST.uri)]

    def test_propagates_room_not_found(self) -> None:
        svc = FavouritesService(FakeRoomService(raise_not_found=True), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.play_playlist("Unknown Room", PLAYLIST.uri)

    def test_propagates_favourites_error_from_adapter(self) -> None:
        svc = FavouritesService(FakeRoomService(), FakeAdapter(raise_favourites_error=True))
        with pytest.raises(FavouritesError):
            svc.play_playlist(ROOM_NAME, PLAYLIST.uri)
