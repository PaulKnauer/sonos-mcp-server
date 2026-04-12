"""Unit tests for SoCoAdapter local music-library browse methods."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from requests import exceptions as requests_exceptions

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import LibraryError, SonosDiscoveryError
from soniq_mcp.domain.models import LibraryItem

IP = "192.168.1.10"


def _patch_soco(zone: MagicMock):
    return patch("soco.SoCo", return_value=zone)


class _BrowseResult(list):
    def __init__(self, items: list[object], total_matches: int | None = None) -> None:
        super().__init__(items)
        self.total_matches = total_matches


def make_raw_item(
    *,
    title: str = "Test Item",
    item_id: str | None = "A:ALBUM/1",
    uri: str | None = "x-file-cifs://track.mp3",
    item_class: str = "object.container.album.musicAlbum",
    can_play: bool | None = False,
    can_browse: bool | None = True,
    album_art_uri: str | None = "/getaa?s=1",
) -> MagicMock:
    item = MagicMock()
    item.title = title
    item.item_id = item_id
    item.uri = uri
    item.item_class = item_class
    item.can_play = can_play
    item.can_browse = can_browse
    item.album_art_uri = album_art_uri
    return item


class TestBrowseLibrary:
    def test_top_level_browse_calls_music_library_information(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.return_value = _BrowseResult([])
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            items, total_matches = adapter.browse_library(
                IP, "artists", start=10, limit=25, parent_id=None
            )

        zone.music_library.get_music_library_information.assert_called_once_with(
            "artists",
            start=10,
            max_items=25,
            full_album_art_uri=False,
            complete_result=False,
        )
        assert items == []
        assert total_matches is None

    def test_child_browse_calls_browse_by_idstring(self) -> None:
        zone = MagicMock()
        zone.music_library.browse_by_idstring.return_value = _BrowseResult([])
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            adapter.browse_library(IP, "albums", start=0, limit=50, parent_id="A:ARTIST/1")

        zone.music_library.browse_by_idstring.assert_called_once_with(
            "albums",
            "A:ARTIST/1",
            start=0,
            max_items=50,
            full_album_art_uri=False,
        )

    def test_returns_normalized_library_items(self) -> None:
        zone = MagicMock()
        raw = make_raw_item(title="Album", can_play=False, can_browse=True)
        zone.music_library.get_music_library_information.return_value = _BrowseResult(
            [raw], total_matches=250
        )
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            items, total_matches = adapter.browse_library(IP, "albums", start=0, limit=100)

        assert total_matches == 250
        assert items == [
            LibraryItem(
                title="Album",
                item_type="object.container.album.musicAlbum",
                item_id="A:ALBUM/1",
                uri="x-file-cifs://track.mp3",
                album_art_uri="/getaa?s=1",
                is_browsable=True,
                is_playable=False,
            )
        ]

    def test_infers_browsable_from_item_id_when_capability_flag_missing(self) -> None:
        zone = MagicMock()
        raw = make_raw_item(can_play=None, can_browse=None, uri=None)
        zone.music_library.get_music_library_information.return_value = _BrowseResult([raw])
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            items, _ = adapter.browse_library(IP, "artists", start=0, limit=100)

        assert items[0].is_browsable is True
        assert items[0].is_playable is False

    def test_wraps_soco_error_as_library_error(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.side_effect = RuntimeError("boom")
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            with pytest.raises(LibraryError, match="Failed to browse local music library"):
                adapter.browse_library(IP, "tracks", start=0, limit=100)

    def test_wraps_network_error_as_discovery_error(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.side_effect = (
            requests_exceptions.ConnectionError("network down")
        )
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            with pytest.raises(SonosDiscoveryError, match="Failed to reach Sonos music library"):
                adapter.browse_library(IP, "tracks", start=0, limit=100)


class TestPlayLibraryItem:
    def test_uses_queue_oriented_playback_pattern(self) -> None:
        zone = MagicMock()
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            adapter.play_library_item(IP, "x-file-cifs://track.mp3")

        zone.clear_queue.assert_called_once_with()
        zone.add_uri_to_queue.assert_called_once_with("x-file-cifs://track.mp3")
        zone.play_from_queue.assert_called_once_with(0)

    def test_wraps_failures_as_library_error(self) -> None:
        zone = MagicMock()
        zone.add_uri_to_queue.side_effect = RuntimeError("boom")
        adapter = SoCoAdapter()

        with _patch_soco(zone):
            with pytest.raises(LibraryError, match="Failed to play library item"):
                adapter.play_library_item(IP, "x-file-cifs://track.mp3")
