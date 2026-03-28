"""Unit tests for SoCoAdapter favourites and playlists methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import FavouritesError
from soniq_mcp.domain.models import Favourite, SonosPlaylist

IP = "192.168.1.10"


def _patch_soco(zone: MagicMock):
    return patch("soco.SoCo", return_value=zone)


def make_fake_favourite(title: str = "My Fav", uri: str = "x-sonos://fav", didl: str = "<DIDL/>") -> MagicMock:
    item = MagicMock()
    item.title = title
    item.uri = uri
    item.to_didl_string.return_value = didl
    return item


def make_fake_playlist(title: str = "My Playlist", uri: str = "x-rincon-playlist://pl", item_id: str = "SQ:1") -> MagicMock:
    item = MagicMock()
    item.title = title
    item.uri = uri
    item.item_id = item_id
    return item


class TestGetFavourites:
    def test_returns_list_of_favourites(self) -> None:
        zone = MagicMock()
        fav = make_fake_favourite(title="Radio", uri="x-sonosapi://radio", didl="<DIDL>radio</DIDL>")
        zone.music_library.get_sonos_favorites.return_value = [fav]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.get_favourites(IP)
        assert len(result) == 1
        assert isinstance(result[0], Favourite)
        assert result[0].title == "Radio"
        assert result[0].uri == "x-sonosapi://radio"
        assert result[0].meta == "<DIDL>radio</DIDL>"

    def test_empty_didl_becomes_none(self) -> None:
        zone = MagicMock()
        fav = make_fake_favourite(didl="")
        zone.music_library.get_sonos_favorites.return_value = [fav]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.get_favourites(IP)
        assert result[0].meta is None

    def test_returns_empty_list_when_no_favourites(self) -> None:
        zone = MagicMock()
        zone.music_library.get_sonos_favorites.return_value = []
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.get_favourites(IP)
        assert result == []

    def test_wraps_soco_error_as_favourites_error(self) -> None:
        zone = MagicMock()
        zone.music_library.get_sonos_favorites.side_effect = RuntimeError("network error")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(FavouritesError, match="Failed to get favourites"):
                adapter.get_favourites(IP)


class TestPlayFavourite:
    def test_calls_play_uri_with_meta(self) -> None:
        zone = MagicMock()
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.play_favourite(IP, "x-sonos://fav", "<DIDL/>")
        zone.play_uri.assert_called_once_with(uri="x-sonos://fav", meta="<DIDL/>")

    def test_uses_empty_string_when_meta_is_none(self) -> None:
        zone = MagicMock()
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.play_favourite(IP, "x-sonos://fav", None)
        zone.play_uri.assert_called_once_with(uri="x-sonos://fav", meta="")

    def test_wraps_soco_error_as_favourites_error(self) -> None:
        zone = MagicMock()
        zone.play_uri.side_effect = RuntimeError("UPnP failure")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(FavouritesError, match="Failed to play favourite"):
                adapter.play_favourite(IP, "x-sonos://fav", None)


class TestGetPlaylists:
    def test_returns_list_of_playlists(self) -> None:
        zone = MagicMock()
        pl = make_fake_playlist(title="Party Mix", uri="x-rincon-playlist://pl1", item_id="SQ:1")
        zone.music_library.get_music_library_information.return_value = [pl]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.get_playlists(IP)
        assert len(result) == 1
        assert isinstance(result[0], SonosPlaylist)
        assert result[0].title == "Party Mix"
        assert result[0].uri == "x-rincon-playlist://pl1"
        assert result[0].item_id == "SQ:1"

    def test_calls_correct_music_library_category(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.return_value = []
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.get_playlists(IP)
        zone.music_library.get_music_library_information.assert_called_once_with("sonos_playlists")

    def test_item_id_defaults_to_none_when_absent(self) -> None:
        zone = MagicMock()
        pl = MagicMock(spec=["title", "uri"])
        pl.title = "No ID Playlist"
        pl.uri = "x-rincon-playlist://pl2"
        zone.music_library.get_music_library_information.return_value = [pl]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.get_playlists(IP)
        assert result[0].item_id is None

    def test_wraps_soco_error_as_favourites_error(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.side_effect = RuntimeError("oops")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(FavouritesError, match="Failed to get playlists"):
                adapter.get_playlists(IP)


class TestPlayPlaylist:
    def test_clears_queue_adds_uri_and_plays(self) -> None:
        zone = MagicMock()
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.play_playlist(IP, "x-rincon-playlist://pl1")
        zone.clear_queue.assert_called_once()
        zone.add_uri_to_queue.assert_called_once_with("x-rincon-playlist://pl1")
        zone.play_from_queue.assert_called_once_with(0)

    def test_wraps_soco_error_as_favourites_error(self) -> None:
        zone = MagicMock()
        zone.clear_queue.side_effect = RuntimeError("zone unreachable")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(FavouritesError, match="Failed to play playlist"):
                adapter.play_playlist(IP, "x-rincon-playlist://pl1")
