"""Unit tests for SoCoAdapter playlist lifecycle methods."""

from __future__ import annotations

from unittest.mock import MagicMock, call, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import (
    PlaylistError,
    PlaylistUnsupportedOperationError,
    PlaylistValidationError,
)
from soniq_mcp.domain.models import SonosPlaylist

IP = "192.168.1.10"
SOURCE_IP = "192.168.1.20"


def _patch_soco(zone: MagicMock):
    return patch("soco.SoCo", return_value=zone)


def _patch_soco_multi(zones: dict[str, MagicMock]):
    """Patch soco.SoCo to return different zones by IP."""
    return patch("soco.SoCo", side_effect=lambda ip: zones[ip])


def make_fake_playlist(
    title: str = "My Playlist", uri: str = "x-rincon-playlist://pl", item_id: str = "SQ:1"
) -> MagicMock:
    item = MagicMock()
    item.title = title
    item.uri = uri
    item.item_id = item_id
    return item


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
        zone.music_library.get_music_library_information.assert_called_once_with(
            "sonos_playlists",
            complete_result=True,
        )

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

    def test_returns_empty_list_when_no_playlists(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.return_value = []
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.get_playlists(IP)
        assert result == []

    def test_wraps_soco_error_as_playlist_error(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.side_effect = RuntimeError("oops")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistError, match="Failed to get playlists"):
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

    def test_wraps_soco_error_as_playlist_error(self) -> None:
        zone = MagicMock()
        zone.clear_queue.side_effect = RuntimeError("zone unreachable")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistError, match="Failed to play playlist"):
                adapter.play_playlist(IP, "x-rincon-playlist://pl1")


class TestCreatePlaylist:
    def test_creates_playlist_and_returns_domain_object(self) -> None:
        zone = MagicMock()
        new_pl = make_fake_playlist(
            title="New Playlist", uri="x-rincon-playlist://new", item_id="SQ:5"
        )
        zone.create_sonos_playlist.return_value = new_pl
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.create_playlist(IP, "New Playlist")
        zone.create_sonos_playlist.assert_called_once_with("New Playlist")
        assert isinstance(result, SonosPlaylist)
        assert result.title == "New Playlist"
        assert result.uri == "x-rincon-playlist://new"
        assert result.item_id == "SQ:5"

    def test_item_id_is_none_when_absent(self) -> None:
        zone = MagicMock()
        result_obj = MagicMock(spec=["title", "uri"])
        result_obj.title = "Test"
        result_obj.uri = "x-rincon-playlist://t"
        zone.create_sonos_playlist.return_value = result_obj
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            result = adapter.create_playlist(IP, "Test")
        assert result.item_id is None

    def test_wraps_soco_error_as_playlist_error(self) -> None:
        zone = MagicMock()
        zone.create_sonos_playlist.side_effect = RuntimeError("SoCo failure")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistError, match="Failed to create playlist"):
                adapter.create_playlist(IP, "Test")


class TestRenamePlaylist:
    def test_raises_unsupported_operation_error(self) -> None:
        adapter = SoCoAdapter()
        with pytest.raises(PlaylistUnsupportedOperationError, match="not supported"):
            adapter.rename_playlist(IP, "SQ:1", "New Name")

    def test_does_not_call_soco(self) -> None:
        zone = MagicMock()
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistUnsupportedOperationError):
                adapter.rename_playlist(IP, "SQ:1", "New Name")
        zone.assert_not_called()


class TestUpdatePlaylist:
    def test_clears_and_refills_playlist_from_queue(self) -> None:
        playlist_zone = MagicMock()
        source_zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        updated_pl = make_fake_playlist(item_id="SQ:1", title="My Playlist")
        playlist_zone.music_library.get_music_library_information.side_effect = [[pl], [updated_pl]]
        playlist_zone.music_library.browse.return_value = []
        queue_item = MagicMock()
        source_zone.get_queue.return_value = [queue_item]
        adapter = SoCoAdapter()
        with _patch_soco_multi({IP: playlist_zone, SOURCE_IP: source_zone}):
            result = adapter.update_playlist(IP, "SQ:1", SOURCE_IP)
        playlist_zone.clear_sonos_playlist.assert_called_once_with(pl, update_id=0)
        playlist_zone.add_item_to_sonos_playlist.assert_called_once_with(queue_item, pl)
        assert isinstance(result, SonosPlaylist)

    def test_raises_validation_error_when_playlist_not_found(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.return_value = []
        source_zone = MagicMock()
        adapter = SoCoAdapter()
        with _patch_soco_multi({IP: zone, SOURCE_IP: source_zone}):
            with pytest.raises(PlaylistValidationError, match="not found"):
                adapter.update_playlist(IP, "SQ:99", SOURCE_IP)

    def test_raises_validation_error_when_queue_is_empty(self) -> None:
        zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        zone.music_library.get_music_library_information.return_value = [pl]
        zone.music_library.browse.return_value = []
        source_zone = MagicMock()
        source_zone.get_queue.return_value = []
        adapter = SoCoAdapter()
        with _patch_soco_multi({IP: zone, SOURCE_IP: source_zone}):
            with pytest.raises(PlaylistValidationError, match="empty"):
                adapter.update_playlist(IP, "SQ:1", SOURCE_IP)

    def test_adds_multiple_queue_items(self) -> None:
        playlist_zone = MagicMock()
        source_zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        playlist_zone.music_library.get_music_library_information.side_effect = [[pl], [pl]]
        playlist_zone.music_library.browse.return_value = []
        first_batch = [MagicMock() for _ in range(100)]
        second_batch = [MagicMock() for _ in range(50)]
        source_zone.get_queue.side_effect = [first_batch, second_batch]
        source_zone.queue_size = 150
        adapter = SoCoAdapter()
        with _patch_soco_multi({IP: playlist_zone, SOURCE_IP: source_zone}):
            adapter.update_playlist(IP, "SQ:1", SOURCE_IP)
        assert playlist_zone.add_item_to_sonos_playlist.call_count == 150
        assert source_zone.get_queue.call_args_list == [
            call(start=0, max_items=100),
            call(start=100, max_items=100),
        ]

    def test_restores_original_contents_when_copy_fails(self) -> None:
        playlist_zone = MagicMock()
        source_zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        original_items = [MagicMock(), MagicMock()]
        playlist_zone.music_library.get_music_library_information.return_value = [pl]
        playlist_zone.music_library.browse.return_value = original_items
        source_zone.get_queue.return_value = [MagicMock(), MagicMock()]
        playlist_zone.add_item_to_sonos_playlist.side_effect = [
            None,
            RuntimeError("copy failed"),
            None,
            None,
        ]
        adapter = SoCoAdapter()
        with _patch_soco_multi({IP: playlist_zone, SOURCE_IP: source_zone}):
            with pytest.raises(PlaylistError, match="Failed to update playlist"):
                adapter.update_playlist(IP, "SQ:1", SOURCE_IP)
        assert playlist_zone.clear_sonos_playlist.call_count == 2
        assert playlist_zone.add_item_to_sonos_playlist.call_count == 4

    def test_wraps_soco_error_as_playlist_error(self) -> None:
        zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        zone.music_library.get_music_library_information.return_value = [pl]
        zone.music_library.browse.return_value = []
        source_zone = MagicMock()
        source_zone.get_queue.return_value = [MagicMock()]
        zone.clear_sonos_playlist.side_effect = RuntimeError("SoCo failure")
        adapter = SoCoAdapter()
        with _patch_soco_multi({IP: zone, SOURCE_IP: source_zone}):
            with pytest.raises(PlaylistError, match="Failed to update playlist"):
                adapter.update_playlist(IP, "SQ:1", SOURCE_IP)

    def test_uses_title_fallback_when_playlist_has_no_item_id(self) -> None:
        zone = MagicMock()
        legacy = make_fake_playlist(title="Legacy Playlist", item_id=None)
        zone.music_library.get_music_library_information.return_value = [legacy]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.delete_playlist(IP, "Legacy Playlist")
        zone.remove_sonos_playlist.assert_called_once_with(legacy)

    def test_lookup_errors_propagate_as_playlist_errors(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.side_effect = RuntimeError("library down")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistError, match="Failed to get playlists"):
                adapter.delete_playlist(IP, "SQ:1")


class TestDeletePlaylist:
    def test_removes_playlist_by_item_id(self) -> None:
        zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        zone.music_library.get_music_library_information.return_value = [pl]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.delete_playlist(IP, "SQ:1")
        zone.remove_sonos_playlist.assert_called_once_with(pl)

    def test_raises_validation_error_when_not_found(self) -> None:
        zone = MagicMock()
        zone.music_library.get_music_library_information.return_value = []
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistValidationError, match="not found"):
                adapter.delete_playlist(IP, "SQ:99")

    def test_wraps_soco_error_as_playlist_error(self) -> None:
        zone = MagicMock()
        pl = make_fake_playlist(item_id="SQ:1")
        zone.music_library.get_music_library_information.return_value = [pl]
        zone.remove_sonos_playlist.side_effect = RuntimeError("removal failed")
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            with pytest.raises(PlaylistError, match="Failed to delete playlist"):
                adapter.delete_playlist(IP, "SQ:1")

    def test_does_not_remove_wrong_playlist(self) -> None:
        zone = MagicMock()
        pl1 = make_fake_playlist(item_id="SQ:1", title="Playlist 1")
        pl2 = make_fake_playlist(item_id="SQ:2", title="Playlist 2")
        zone.music_library.get_music_library_information.return_value = [pl1, pl2]
        adapter = SoCoAdapter()
        with _patch_soco(zone):
            adapter.delete_playlist(IP, "SQ:2")
        zone.remove_sonos_playlist.assert_called_once_with(pl2)
