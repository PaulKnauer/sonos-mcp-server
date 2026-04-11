"""Unit tests for PlaylistService."""

from __future__ import annotations

import pytest

from soniq_mcp.domain.exceptions import (
    PlaylistError,
    PlaylistUnsupportedOperationError,
    PlaylistValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import Room, SonosPlaylist
from soniq_mcp.services.playlist_service import PlaylistService

IP = "192.168.1.10"
ROOM_IP = "192.168.1.20"
ROOM_NAME = "Living Room"
ROOM = Room(name=ROOM_NAME, uid="RINCON_123", ip_address=ROOM_IP, is_coordinator=True)
HOUSEHOLD_ROOM = Room(name="Household", uid="RINCON_001", ip_address=IP, is_coordinator=True)

PLAYLIST = SonosPlaylist(title="Party Mix", uri="x-rincon-playlist://pl1", item_id="SQ:1")


class FakeRoomService:
    def __init__(
        self,
        rooms: list[Room] | None = None,
        raise_not_found: bool = False,
        raise_discovery: bool = False,
    ) -> None:
        self._rooms = rooms if rooms is not None else [HOUSEHOLD_ROOM, ROOM]
        self._raise_not_found = raise_not_found
        self._raise_discovery = raise_discovery

    def list_rooms(self) -> list[Room]:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        return self._rooms

    def get_room(self, room_name: str) -> Room:
        if self._raise_not_found:
            raise RoomNotFoundError(room_name)
        for room in self._rooms:
            if room.name == room_name:
                return room
        raise RoomNotFoundError(room_name)


class FakeAdapter:
    def __init__(
        self,
        playlists: list[SonosPlaylist] | None = None,
        raise_playlist_error: bool = False,
        raise_unsupported: bool = False,
        created_playlist: SonosPlaylist | None = None,
        updated_playlist: SonosPlaylist | None = None,
    ) -> None:
        self._playlists = playlists if playlists is not None else [PLAYLIST]
        self._raise_playlist_error = raise_playlist_error
        self._raise_unsupported = raise_unsupported
        self._created_playlist = created_playlist or SonosPlaylist(
            title="New", uri="x-rincon-playlist://new", item_id="SQ:99"
        )
        self._updated_playlist = updated_playlist or PLAYLIST
        self.get_playlists_calls: list[str] = []
        self.play_playlist_calls: list[tuple] = []
        self.create_playlist_calls: list[tuple] = []
        self.rename_playlist_calls: list[tuple] = []
        self.update_playlist_calls: list[tuple] = []
        self.delete_playlist_calls: list[tuple] = []

    def get_playlists(self, ip_address: str) -> list[SonosPlaylist]:
        if self._raise_playlist_error:
            raise PlaylistError("adapter error")
        self.get_playlists_calls.append(ip_address)
        return self._playlists

    def play_playlist(self, ip_address: str, uri: str) -> None:
        if self._raise_playlist_error:
            raise PlaylistError("adapter error")
        self.play_playlist_calls.append((ip_address, uri))

    def create_playlist(self, ip_address: str, title: str) -> SonosPlaylist:
        if self._raise_playlist_error:
            raise PlaylistError("adapter error")
        self.create_playlist_calls.append((ip_address, title))
        return self._created_playlist

    def rename_playlist(self, ip_address: str, item_id: str, title: str) -> SonosPlaylist:
        if self._raise_unsupported:
            raise PlaylistUnsupportedOperationError("rename not supported")
        if self._raise_playlist_error:
            raise PlaylistError("adapter error")
        self.rename_playlist_calls.append((ip_address, item_id, title))
        return SonosPlaylist(title=title, uri=PLAYLIST.uri, item_id=item_id)

    def update_playlist(self, ip_address: str, item_id: str, source_ip: str) -> SonosPlaylist:
        if self._raise_playlist_error:
            raise PlaylistError("adapter error")
        self.update_playlist_calls.append((ip_address, item_id, source_ip))
        return self._updated_playlist

    def delete_playlist(self, ip_address: str, item_id: str) -> None:
        if self._raise_playlist_error:
            raise PlaylistError("adapter error")
        self.delete_playlist_calls.append((ip_address, item_id))
        self._playlists = [playlist for playlist in self._playlists if playlist.item_id != item_id]


class TestListPlaylists:
    def test_returns_playlists_from_adapter(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(playlists=[PLAYLIST]))
        result = svc.list_playlists()
        assert result == [PLAYLIST]

    def test_uses_first_room_ip(self) -> None:
        adapter = FakeAdapter()
        svc = PlaylistService(FakeRoomService(), adapter)
        svc.list_playlists()
        assert adapter.get_playlists_calls == [IP]

    def test_returns_empty_list_when_no_playlists(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(playlists=[]))
        result = svc.list_playlists()
        assert result == []

    def test_raises_discovery_error_when_no_rooms(self) -> None:
        svc = PlaylistService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(SonosDiscoveryError):
            svc.list_playlists()

    def test_propagates_playlist_error_from_adapter(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(raise_playlist_error=True))
        with pytest.raises(PlaylistError):
            svc.list_playlists()


class TestPlayPlaylist:
    def test_resolves_room_and_calls_adapter(self) -> None:
        adapter = FakeAdapter()
        svc = PlaylistService(FakeRoomService(), adapter)
        svc.play_playlist(ROOM_NAME, PLAYLIST.uri)
        assert adapter.play_playlist_calls == [(ROOM_IP, PLAYLIST.uri)]

    def test_propagates_room_not_found(self) -> None:
        svc = PlaylistService(FakeRoomService(raise_not_found=True), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.play_playlist("Unknown Room", PLAYLIST.uri)

    def test_propagates_playlist_error_from_adapter(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(raise_playlist_error=True))
        with pytest.raises(PlaylistError):
            svc.play_playlist(ROOM_NAME, PLAYLIST.uri)


class TestCreatePlaylist:
    def test_creates_playlist_with_valid_title(self) -> None:
        new_pl = SonosPlaylist(title="Summer Jams", uri="x-rincon://new", item_id="SQ:5")
        adapter = FakeAdapter(created_playlist=new_pl)
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.create_playlist("  Summer Jams  ")
        assert result == new_pl
        assert adapter.create_playlist_calls == [(IP, "Summer Jams")]

    def test_raises_validation_error_on_empty_title(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="title"):
            svc.create_playlist("")

    def test_raises_validation_error_on_whitespace_title(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="title"):
            svc.create_playlist("   ")

    def test_raises_discovery_error_when_no_rooms(self) -> None:
        svc = PlaylistService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(SonosDiscoveryError):
            svc.create_playlist("Test")

    def test_propagates_playlist_error_from_adapter(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(raise_playlist_error=True))
        with pytest.raises(PlaylistError):
            svc.create_playlist("Test")


class TestRenamePlaylist:
    def test_renames_playlist_with_valid_inputs(self) -> None:
        adapter = FakeAdapter(playlists=[PLAYLIST])
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.rename_playlist("SQ:1", "  New Name  ")
        assert result.title == "New Name"
        assert result.item_id == "SQ:1"
        assert adapter.rename_playlist_calls == [(IP, "SQ:1", "New Name")]

    def test_allows_bounded_title_fallback_for_missing_item_id(self) -> None:
        legacy = SonosPlaylist(
            title="Legacy Playlist", uri="x-rincon-playlist://legacy", item_id=None
        )
        adapter = FakeAdapter(playlists=[legacy])
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.rename_playlist("Legacy Playlist", "Renamed")
        assert result.item_id == "Legacy Playlist"
        assert adapter.rename_playlist_calls == [(IP, "Legacy Playlist", "Renamed")]

    def test_raises_validation_error_on_blank_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="playlist_id"):
            svc.rename_playlist("", "New Name")

    def test_raises_validation_error_on_blank_title(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="title"):
            svc.rename_playlist("SQ:1", "")

    def test_raises_validation_error_on_unknown_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(playlists=[PLAYLIST]))
        with pytest.raises(PlaylistValidationError, match="not found"):
            svc.rename_playlist("SQ:99", "New Name")

    def test_propagates_unsupported_operation_error(self) -> None:
        svc = PlaylistService(
            FakeRoomService(), FakeAdapter(playlists=[PLAYLIST], raise_unsupported=True)
        )
        with pytest.raises(PlaylistUnsupportedOperationError):
            svc.rename_playlist("SQ:1", "New Name")


class TestUpdatePlaylist:
    def test_updates_playlist_from_room_queue(self) -> None:
        updated = SonosPlaylist(title="Party Mix", uri="x-rincon://updated", item_id="SQ:1")
        adapter = FakeAdapter(playlists=[PLAYLIST], updated_playlist=updated)
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.update_playlist("SQ:1", ROOM_NAME)
        assert result == updated
        assert adapter.update_playlist_calls == [(IP, "SQ:1", ROOM_IP)]

    def test_raises_validation_error_on_blank_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="playlist_id"):
            svc.update_playlist("", ROOM_NAME)

    def test_raises_validation_error_on_unknown_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(playlists=[PLAYLIST]))
        with pytest.raises(PlaylistValidationError, match="not found"):
            svc.update_playlist("SQ:99", ROOM_NAME)

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        svc = PlaylistService(FakeRoomService(raise_not_found=True), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            svc.update_playlist("SQ:1", "Unknown Room")

    def test_propagates_playlist_error_from_adapter(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(raise_playlist_error=True))
        with pytest.raises(PlaylistError):
            svc.update_playlist("SQ:1", ROOM_NAME)


class TestPlaylistLifecycleInteroperability:
    """Verify that lifecycle-created/updated playlists work through play_playlist."""

    def test_created_playlist_uri_is_playable(self) -> None:
        """A URI returned by create_playlist can be passed directly to play_playlist."""
        new_pl = SonosPlaylist(title="Summer Jams", uri="x-rincon-playlist://new", item_id="SQ:5")
        adapter = FakeAdapter(created_playlist=new_pl)
        svc = PlaylistService(FakeRoomService(), adapter)
        created = svc.create_playlist("Summer Jams")
        svc.play_playlist(ROOM_NAME, created.uri)
        assert adapter.play_playlist_calls == [(ROOM_IP, "x-rincon-playlist://new")]

    def test_updated_playlist_uri_is_playable(self) -> None:
        """A URI returned by update_playlist can be passed directly to play_playlist."""
        updated = SonosPlaylist(
            title="Party Mix", uri="x-rincon-playlist://updated", item_id="SQ:1"
        )
        adapter = FakeAdapter(playlists=[PLAYLIST], updated_playlist=updated)
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.update_playlist("SQ:1", ROOM_NAME)
        svc.play_playlist(ROOM_NAME, result.uri)
        assert adapter.play_playlist_calls == [(ROOM_IP, "x-rincon-playlist://updated")]

    def test_created_playlist_has_required_playback_fields(self) -> None:
        """A SonosPlaylist from create_playlist always has title, uri, and item_id."""
        new_pl = SonosPlaylist(title="Road Trip", uri="x-rincon-playlist://rt", item_id="SQ:7")
        adapter = FakeAdapter(created_playlist=new_pl)
        svc = PlaylistService(FakeRoomService(), adapter)
        created = svc.create_playlist("Road Trip")
        assert created.title == "Road Trip"
        assert created.uri == "x-rincon-playlist://rt"
        assert created.item_id == "SQ:7"

    def test_updated_playlist_preserves_item_id_for_re_identification(self) -> None:
        """update_playlist preserves item_id so the playlist can still be found."""
        updated = SonosPlaylist(
            title="Party Mix", uri="x-rincon-playlist://updated", item_id="SQ:1"
        )
        adapter = FakeAdapter(playlists=[PLAYLIST], updated_playlist=updated)
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.update_playlist("SQ:1", ROOM_NAME)
        assert result.item_id == "SQ:1"
        assert result.uri is not None

    def test_delete_removes_playlist_from_subsequent_list_results(self) -> None:
        """After delete, the removed playlist no longer appears in list_playlists."""
        adapter = FakeAdapter(playlists=[PLAYLIST])
        svc = PlaylistService(FakeRoomService(), adapter)
        svc.delete_playlist("SQ:1")
        remaining = svc.list_playlists()
        assert remaining == []


class TestDeletePlaylist:
    def test_deletes_playlist_and_returns_confirmation(self) -> None:
        adapter = FakeAdapter(playlists=[PLAYLIST])
        svc = PlaylistService(FakeRoomService(), adapter)
        result = svc.delete_playlist("SQ:1")
        assert result == {"playlist_id": "SQ:1", "status": "deleted"}
        assert adapter.delete_playlist_calls == [(IP, "SQ:1")]

    def test_raises_validation_error_on_blank_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="playlist_id"):
            svc.delete_playlist("")

    def test_raises_validation_error_on_whitespace_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter())
        with pytest.raises(PlaylistValidationError, match="playlist_id"):
            svc.delete_playlist("  ")

    def test_raises_validation_error_on_unknown_id(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(playlists=[PLAYLIST]))
        with pytest.raises(PlaylistValidationError, match="not found"):
            svc.delete_playlist("SQ:99")

    def test_raises_discovery_error_when_no_rooms(self) -> None:
        svc = PlaylistService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(SonosDiscoveryError):
            svc.delete_playlist("SQ:1")

    def test_propagates_playlist_error_from_adapter(self) -> None:
        svc = PlaylistService(FakeRoomService(), FakeAdapter(raise_playlist_error=True))
        with pytest.raises(PlaylistError):
            svc.delete_playlist("SQ:1")
