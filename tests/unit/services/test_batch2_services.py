"""Unit tests for playlist edits, volume ramp, and stereo pairing in services."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import (
    GroupValidationError,
    PlaylistValidationError,
    RoomNotFoundError,
    VolumeCapExceeded,
    VolumeValidationError,
)
from soniq_mcp.domain.models import Room, SonosPlaylist
from soniq_mcp.services.group_service import GroupService
from soniq_mcp.services.playlist_service import PlaylistService
from soniq_mcp.services.volume_service import VolumeService

COORD = Room(name="Kitchen", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
MEMBER = Room(
    name="Dining",
    uid="UID2",
    ip_address="192.168.1.11",
    is_coordinator=False,
    group_coordinator_uid="UID1",
)
OFFICE = Room(name="Office", uid="UID3", ip_address="192.168.1.12", is_coordinator=True)
PLAYLIST = SonosPlaylist(title="Mix", uri="file:///x#1", item_id="SQ:1")


def _room_service(rooms=(COORD, MEMBER, OFFICE)):
    by_name = {r.name: r for r in rooms}
    rs = MagicMock()

    def get_room(name):
        if name not in by_name:
            raise RoomNotFoundError(name)
        return by_name[name]

    rs.get_room.side_effect = get_room
    rs.list_rooms.return_value = list(rooms)
    return rs


def _playlist_service():
    adapter = MagicMock()
    adapter.get_playlists.return_value = [PLAYLIST]
    adapter.save_queue_as_playlist.return_value = PLAYLIST
    return PlaylistService(_room_service(), adapter), adapter


class TestSaveQueueAsPlaylist:
    def test_saves_coordinator_queue_for_grouped_room(self):
        svc, adapter = _playlist_service()

        result = svc.save_queue_as_playlist("Dining", "  Mix ")

        adapter.save_queue_as_playlist.assert_called_once_with(COORD.ip_address, "Mix")
        assert result == PLAYLIST

    def test_ungrouped_room_uses_own_ip(self):
        svc, adapter = _playlist_service()

        svc.save_queue_as_playlist("Office", "Mix")

        adapter.save_queue_as_playlist.assert_called_once_with(OFFICE.ip_address, "Mix")

    def test_blank_title_rejected(self):
        svc, adapter = _playlist_service()

        with pytest.raises(PlaylistValidationError):
            svc.save_queue_as_playlist("Office", "  ")
        adapter.save_queue_as_playlist.assert_not_called()

    def test_unknown_room(self):
        svc, _ = _playlist_service()

        with pytest.raises(RoomNotFoundError):
            svc.save_queue_as_playlist("Garage", "Mix")


class TestRemoveFromPlaylist:
    def test_delegates_with_position(self):
        svc, adapter = _playlist_service()

        result = svc.remove_from_playlist("SQ:1", 2)

        adapter.remove_from_playlist.assert_called_once_with(COORD.ip_address, "SQ:1", 2)
        assert result == {"playlist_id": "SQ:1", "status": "removed", "position": 2}

    @pytest.mark.parametrize("position", [0, -1, True, "2", 1.5])
    def test_invalid_position_rejected(self, position):
        svc, adapter = _playlist_service()

        with pytest.raises(PlaylistValidationError):
            svc.remove_from_playlist("SQ:1", position)
        adapter.remove_from_playlist.assert_not_called()

    def test_unknown_playlist_rejected(self):
        svc, adapter = _playlist_service()

        with pytest.raises(PlaylistValidationError, match="not found"):
            svc.remove_from_playlist("SQ:404", 1)
        adapter.remove_from_playlist.assert_not_called()


class TestReorderPlaylist:
    def test_delegates_positions(self):
        svc, adapter = _playlist_service()

        result = svc.reorder_playlist("SQ:1", 3, 1)

        adapter.reorder_playlist.assert_called_once_with(COORD.ip_address, "SQ:1", 3, 1)
        assert result["status"] == "reordered"
        assert result["from_position"] == 3
        assert result["to_position"] == 1

    def test_invalid_position_rejected(self):
        svc, adapter = _playlist_service()

        with pytest.raises(PlaylistValidationError, match="to_position"):
            svc.reorder_playlist("SQ:1", 1, 0)
        adapter.reorder_playlist.assert_not_called()


def _volume_service(max_volume_pct=80):
    adapter = MagicMock()
    adapter.ramp_to_volume.return_value = 12
    config = SoniqConfig(max_volume_pct=max_volume_pct)
    return VolumeService(_room_service(), adapter, config), adapter


class TestRampVolume:
    def test_ramps_within_cap(self):
        svc, adapter = _volume_service()

        result = svc.ramp_volume("Kitchen", 40)

        adapter.ramp_to_volume.assert_called_once_with(
            COORD.ip_address, 40, "SLEEP_TIMER_RAMP_TYPE"
        )
        assert result.target_volume == 40
        assert result.ramp_seconds == 12
        assert result.room_name == "Kitchen"

    def test_cap_enforced(self):
        svc, adapter = _volume_service(max_volume_pct=50)

        with pytest.raises(VolumeCapExceeded):
            svc.ramp_volume("Kitchen", 60, "AUTOPLAY_RAMP_TYPE")
        adapter.ramp_to_volume.assert_not_called()

    def test_out_of_range_volume(self):
        svc, adapter = _volume_service()

        with pytest.raises(ValueError):
            svc.ramp_volume("Kitchen", -5)
        adapter.ramp_to_volume.assert_not_called()

    def test_unknown_ramp_type(self):
        svc, adapter = _volume_service()

        with pytest.raises(VolumeValidationError, match="ramp_type"):
            svc.ramp_volume("Kitchen", 30, "FAST")
        adapter.ramp_to_volume.assert_not_called()

    @pytest.mark.parametrize("ramp_type", ["ALARM_RAMP_TYPE", "AUTOPLAY_RAMP_TYPE"])
    def test_other_ramp_types_accepted(self, ramp_type):
        svc, adapter = _volume_service()

        assert svc.ramp_volume("Kitchen", 30, ramp_type).ramp_type == ramp_type


class TestStereoPair:
    def test_create_resolves_both_rooms(self):
        adapter = MagicMock()
        svc = GroupService(_room_service(), adapter)

        svc.create_stereo_pair("Kitchen", "Office")

        adapter.create_stereo_pair.assert_called_once_with(COORD.ip_address, OFFICE.ip_address)

    def test_same_room_rejected(self):
        adapter = MagicMock()
        svc = GroupService(_room_service(), adapter)

        with pytest.raises(GroupValidationError):
            svc.create_stereo_pair("Kitchen", "Kitchen")
        adapter.create_stereo_pair.assert_not_called()

    def test_unknown_right_room(self):
        svc = GroupService(_room_service(), MagicMock())

        with pytest.raises(RoomNotFoundError):
            svc.create_stereo_pair("Kitchen", "Garage")

    def test_separate(self):
        adapter = MagicMock()
        svc = GroupService(_room_service(), adapter)

        svc.separate_stereo_pair("Office")

        adapter.separate_stereo_pair.assert_called_once_with(OFFICE.ip_address)
