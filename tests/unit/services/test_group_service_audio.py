"""Unit tests for GroupService group-audio operations."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import (
    GroupError,
    GroupValidationError,
    RoomNotFoundError,
    VolumeCapExceeded,
)
from soniq_mcp.domain.models import GroupAudioState, Room
from soniq_mcp.services.group_service import GroupService

COORDINATOR = Room(
    name="Living Room",
    uid="UID_COORD",
    ip_address="192.168.1.10",
    is_coordinator=True,
)
MEMBER = Room(
    name="Kitchen",
    uid="UID_MEMBER",
    ip_address="192.168.1.20",
    is_coordinator=False,
    group_coordinator_uid="UID_COORD",
)
SOLO = Room(
    name="Office",
    uid="UID_SOLO",
    ip_address="192.168.1.30",
    is_coordinator=True,
    # no group_coordinator_uid -> single-room coordinator, no grouped peers
)


def _make_service(
    rooms=None,
    adapter=None,
    max_volume_pct: int = 80,
):
    room_service = MagicMock()
    if rooms is None:
        rooms = [COORDINATOR, MEMBER]
    room_service.list_rooms.return_value = rooms
    if adapter is None:
        adapter = MagicMock()
        adapter.get_group_volume.return_value = 40
        adapter.get_group_mute.return_value = False
        adapter.adjust_group_volume.return_value = 45
    config = MagicMock()
    config.max_volume_pct = max_volume_pct
    return GroupService(room_service, adapter, config), room_service, adapter


class TestGetGroupAudioState:
    def test_room_lookup_is_case_insensitive(self):
        svc, _, adapter = _make_service()
        adapter.get_group_volume.return_value = 35

        result = svc.get_group_audio_state("living room")

        assert result.room_name == "Living Room"
        assert result.coordinator_room_name == "Living Room"

    def test_returns_group_audio_state_for_coordinator(self):
        svc, _, adapter = _make_service()
        adapter.get_group_volume.return_value = 35
        adapter.get_group_mute.return_value = False

        result = svc.get_group_audio_state("Living Room")

        assert isinstance(result, GroupAudioState)
        assert result.room_name == "Living Room"
        assert result.coordinator_room_name == "Living Room"
        assert "Living Room" in result.member_room_names
        assert "Kitchen" in result.member_room_names
        assert result.volume == 35
        assert result.is_muted is False

    def test_returns_group_audio_state_for_member(self):
        svc, _, adapter = _make_service()
        adapter.get_group_volume.return_value = 50

        result = svc.get_group_audio_state("Kitchen")

        assert result.room_name == "Kitchen"
        assert result.coordinator_room_name == "Living Room"
        assert result.volume == 50

    def test_calls_adapter_with_coordinator_ip(self):
        svc, _, adapter = _make_service()

        svc.get_group_audio_state("Kitchen")

        adapter.get_group_volume.assert_called_once_with(COORDINATOR.ip_address)
        adapter.get_group_mute.assert_called_once_with(COORDINATOR.ip_address)

    def test_raises_room_not_found_for_unknown_room(self):
        svc, _, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.get_group_audio_state("Nonexistent")

    def test_raises_group_validation_error_for_ungrouped_room(self):
        svc, _, _ = _make_service(rooms=[SOLO])

        with pytest.raises(GroupValidationError):
            svc.get_group_audio_state("Office")

    def test_propagates_group_error_from_adapter(self):
        svc, _, adapter = _make_service()
        adapter.get_group_volume.side_effect = GroupError("SoCo failure")

        with pytest.raises(GroupError):
            svc.get_group_audio_state("Living Room")


class TestSetGroupVolume:
    def test_sets_volume_and_returns_state(self):
        svc, _, adapter = _make_service(max_volume_pct=80)
        adapter.get_group_mute.return_value = False

        result = svc.set_group_volume("Living Room", 50)

        adapter.set_group_volume.assert_called_once_with(COORDINATOR.ip_address, 50)
        assert result.volume == 50
        assert result.coordinator_room_name == "Living Room"

    def test_raises_volume_cap_exceeded_when_over_limit(self):
        svc, _, _ = _make_service(max_volume_pct=70)

        with pytest.raises(VolumeCapExceeded) as exc_info:
            svc.set_group_volume("Living Room", 75)

        assert exc_info.value.requested == 75
        assert exc_info.value.cap == 70

    def test_raises_group_validation_error_for_negative_volume(self):
        svc, _, adapter = _make_service(max_volume_pct=80)

        with pytest.raises(GroupValidationError, match="0-100"):
            svc.set_group_volume("Living Room", -1)

        adapter.set_group_volume.assert_not_called()

    def test_allows_volume_equal_to_cap(self):
        svc, _, adapter = _make_service(max_volume_pct=80)
        adapter.get_group_mute.return_value = False

        result = svc.set_group_volume("Living Room", 80)

        adapter.set_group_volume.assert_called_once()
        assert result.volume == 80

    def test_raises_room_not_found(self):
        svc, _, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.set_group_volume("Nonexistent", 40)

    def test_raises_group_validation_error_for_ungrouped_room(self):
        svc, _, _ = _make_service(rooms=[SOLO])

        with pytest.raises(GroupValidationError):
            svc.set_group_volume("Office", 40)


class TestAdjustGroupVolume:
    def test_adjusts_volume_and_returns_state(self):
        svc, _, adapter = _make_service(max_volume_pct=80)
        adapter.get_group_volume.return_value = 40
        adapter.adjust_group_volume.return_value = 45
        adapter.get_group_mute.return_value = False

        result = svc.adjust_group_volume("Living Room", 5)

        adapter.adjust_group_volume.assert_called_once_with(COORDINATOR.ip_address, 5)
        assert result.volume == 45

    def test_raises_volume_cap_exceeded_when_intended_exceeds_cap(self):
        svc, _, adapter = _make_service(max_volume_pct=80)
        adapter.get_group_volume.return_value = 78

        with pytest.raises(VolumeCapExceeded):
            svc.adjust_group_volume("Living Room", 5)  # 78+5=83 > 80

    def test_raises_group_validation_when_intended_goes_negative(self):
        svc, _, adapter = _make_service(max_volume_pct=80)
        adapter.get_group_volume.return_value = 3

        with pytest.raises(GroupValidationError, match="invalid level -7"):
            svc.adjust_group_volume("Living Room", -10)

        adapter.adjust_group_volume.assert_not_called()

    def test_raises_room_not_found(self):
        svc, _, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.adjust_group_volume("Nonexistent", 5)

    def test_raises_group_validation_for_ungrouped_room(self):
        svc, _, _ = _make_service(rooms=[SOLO])

        with pytest.raises(GroupValidationError):
            svc.adjust_group_volume("Office", 5)


class TestGroupMute:
    def test_sets_group_mute_true_and_returns_state(self):
        svc, _, adapter = _make_service()
        adapter.get_group_volume.return_value = 40

        result = svc.group_mute("Living Room")

        adapter.set_group_mute.assert_called_once_with(COORDINATOR.ip_address, True)
        assert result.is_muted is True
        assert result.volume == 40

    def test_raises_room_not_found(self):
        svc, _, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.group_mute("Nonexistent")

    def test_raises_group_validation_for_ungrouped_room(self):
        svc, _, _ = _make_service(rooms=[SOLO])

        with pytest.raises(GroupValidationError):
            svc.group_mute("Office")


class TestGroupUnmute:
    def test_sets_group_mute_false_and_returns_state(self):
        svc, _, adapter = _make_service()
        adapter.get_group_volume.return_value = 40

        result = svc.group_unmute("Living Room")

        adapter.set_group_mute.assert_called_once_with(COORDINATOR.ip_address, False)
        assert result.is_muted is False
        assert result.volume == 40

    def test_raises_room_not_found(self):
        svc, _, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.group_unmute("Nonexistent")

    def test_raises_group_validation_for_ungrouped_room(self):
        svc, _, _ = _make_service(rooms=[SOLO])

        with pytest.raises(GroupValidationError):
            svc.group_unmute("Office")
