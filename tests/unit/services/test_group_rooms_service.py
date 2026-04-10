"""Unit tests for GroupService.group_rooms."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from soniq_mcp.domain.exceptions import GroupError, GroupValidationError, SonosDiscoveryError
from soniq_mcp.domain.models import Room
from soniq_mcp.services.group_service import GroupService

LIVING = Room(name="Living Room", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
KITCHEN = Room(name="Kitchen", uid="UID2", ip_address="192.168.1.20", is_coordinator=True)
OFFICE = Room(name="Office", uid="UID3", ip_address="192.168.1.30", is_coordinator=True)
# A room currently grouped under LIVING (stale member)
BEDROOM = Room(
    name="Bedroom",
    uid="UID4",
    ip_address="192.168.1.40",
    is_coordinator=False,
    group_coordinator_uid="UID1",
)
KITCHEN_LOWER = Room(
    name="kitchen",
    uid="UID5",
    ip_address="192.168.1.50",
    is_coordinator=True,
)


def _make_service(rooms=None, adapter=None):
    room_service = MagicMock()
    if rooms is None:
        rooms = [LIVING, KITCHEN, OFFICE]
    room_service.list_rooms.return_value = rooms
    if adapter is None:
        adapter = MagicMock()
    return GroupService(room_service, adapter), adapter


class TestGroupRoomsValidation:
    def test_empty_list_raises_validation_error(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError):
            svc.group_rooms([])

    def test_single_room_raises_validation_error(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError, match="At least 2"):
            svc.group_rooms(["Living Room"])

    def test_duplicate_names_raises_validation_error(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError, match="[Dd]uplicate"):
            svc.group_rooms(["Living Room", "Living Room"])

    def test_case_insensitive_duplicate_raises(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError, match="[Dd]uplicate"):
            svc.group_rooms(["living room", "Living Room"])

    def test_unknown_room_raises_validation_error(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError, match="Unknown"):
            svc.group_rooms(["Living Room", "Nonexistent"])

    def test_ambiguous_normalized_room_name_raises_validation_error(self):
        svc, adapter = _make_service(rooms=[LIVING, KITCHEN, KITCHEN_LOWER])

        with pytest.raises(GroupValidationError, match="[Aa]mbiguous"):
            svc.group_rooms(["Living Room", "Kitchen"])

        adapter.join_group.assert_not_called()
        adapter.unjoin_room.assert_not_called()

    def test_coordinator_not_in_set_raises_validation_error(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError, match="part of the requested room set"):
            svc.group_rooms(["Living Room", "Kitchen"], coordinator_name="Office")

    def test_unknown_coordinator_raises_validation_error(self):
        svc, _ = _make_service()
        with pytest.raises(GroupValidationError, match="not found"):
            svc.group_rooms(["Living Room", "Kitchen"], coordinator_name="Ghost Room")

    def test_no_adapter_calls_on_validation_failure(self):
        svc, adapter = _make_service()
        with pytest.raises(GroupValidationError):
            svc.group_rooms(["Living Room", "Nonexistent"])
        adapter.join_group.assert_not_called()
        adapter.unjoin_room.assert_not_called()


class TestGroupRoomsOrchestration:
    def test_joins_non_coordinator_to_coordinator(self):
        svc, adapter = _make_service()

        svc.group_rooms(["Living Room", "Kitchen"])

        # list_rooms returns rooms as provided: [LIVING, KITCHEN, OFFICE]
        # After normalization: resolved = [LIVING, KITCHEN]
        # Default coordinator = resolved[0] = LIVING
        adapter.join_group.assert_called_once_with(KITCHEN.ip_address, LIVING.ip_address)

    def test_explicit_coordinator_is_respected(self):
        svc, adapter = _make_service()

        svc.group_rooms(["Living Room", "Kitchen"], coordinator_name="Kitchen")

        adapter.join_group.assert_called_once_with(LIVING.ip_address, KITCHEN.ip_address)

    def test_case_insensitive_room_resolution(self):
        svc, adapter = _make_service()

        result = svc.group_rooms(["living room", "kitchen"])

        assert any(r.name == "Living Room" for r in result)
        assert any(r.name == "Kitchen" for r in result)

    def test_three_room_group_joins_two_non_coordinators(self):
        svc, adapter = _make_service()

        svc.group_rooms(["Living Room", "Kitchen", "Office"])

        # LIVING is coordinator (first resolved)
        assert adapter.join_group.call_count == 2
        joined_ips = {c.args[0] for c in adapter.join_group.call_args_list}
        assert KITCHEN.ip_address in joined_ips
        assert OFFICE.ip_address in joined_ips

    def test_returns_updated_coordinator_state(self):
        svc, _ = _make_service()

        result = svc.group_rooms(["Living Room", "Kitchen"])

        room_map = {r.name: r for r in result}
        assert room_map["Living Room"].is_coordinator is True
        assert room_map["Living Room"].group_coordinator_uid is None
        assert room_map["Kitchen"].is_coordinator is False
        assert room_map["Kitchen"].group_coordinator_uid == LIVING.uid

    def test_returns_updated_coordinator_state_with_explicit_coordinator(self):
        svc, _ = _make_service()

        result = svc.group_rooms(["Living Room", "Kitchen"], coordinator_name="Kitchen")

        room_map = {r.name: r for r in result}
        assert room_map["Kitchen"].is_coordinator is True
        assert room_map["Kitchen"].group_coordinator_uid is None
        assert room_map["Living Room"].is_coordinator is False
        assert room_map["Living Room"].group_coordinator_uid == KITCHEN.uid

    def test_unjoins_stale_member_not_in_requested_set(self):
        # BEDROOM is currently in LIVING's group but NOT in the requested set
        svc, adapter = _make_service(rooms=[LIVING, KITCHEN, OFFICE, BEDROOM])

        svc.group_rooms(["Living Room", "Kitchen"])

        adapter.unjoin_room.assert_called_once_with(BEDROOM.ip_address)

    def test_no_unjoin_when_no_stale_members(self):
        svc, adapter = _make_service(rooms=[LIVING, KITCHEN, OFFICE])

        svc.group_rooms(["Living Room", "Kitchen"])

        adapter.unjoin_room.assert_not_called()

    def test_unjoins_requested_member_before_joining_new_coordinator(self):
        kitchen_member = Room(
            name="Kitchen",
            uid="UID2",
            ip_address="192.168.1.20",
            is_coordinator=False,
            group_coordinator_uid=LIVING.uid,
        )
        svc, adapter = _make_service(rooms=[LIVING, kitchen_member, OFFICE])

        svc.group_rooms(["Kitchen", "Office"], coordinator_name="Office")

        assert adapter.unjoin_room.call_args_list == [call(kitchen_member.ip_address)]
        adapter.join_group.assert_called_once_with(kitchen_member.ip_address, OFFICE.ip_address)

    def test_unjoins_nonrequested_followers_of_requested_room_before_joining(self):
        svc, adapter = _make_service(rooms=[LIVING, OFFICE, BEDROOM])

        svc.group_rooms(["Living Room", "Office"], coordinator_name="Office")

        assert adapter.unjoin_room.call_args_list == [call(BEDROOM.ip_address)]
        adapter.join_group.assert_called_once_with(LIVING.ip_address, OFFICE.ip_address)

    def test_propagates_group_error_from_adapter(self):
        svc, adapter = _make_service()
        adapter.join_group.side_effect = GroupError("join failed")

        with pytest.raises(GroupError):
            svc.group_rooms(["Living Room", "Kitchen"])

    def test_propagates_discovery_error_from_room_service(self):
        svc, _ = _make_service()
        svc._room_service.list_rooms.side_effect = SonosDiscoveryError("no network")

        with pytest.raises(SonosDiscoveryError):
            svc.group_rooms(["Living Room", "Kitchen"])

    def test_result_contains_only_requested_rooms(self):
        svc, _ = _make_service(rooms=[LIVING, KITCHEN, OFFICE])

        result = svc.group_rooms(["Living Room", "Kitchen"])

        assert len(result) == 2
        names = {r.name for r in result}
        assert "Living Room" in names
        assert "Kitchen" in names
        assert "Office" not in names
