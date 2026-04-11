"""Unit tests for AlarmService."""

from __future__ import annotations

import datetime

import pytest

from soniq_mcp.domain.exceptions import (
    AlarmError,
    AlarmValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import AlarmRecord, Room
from soniq_mcp.services.alarm_service import AlarmService

IP = "192.168.1.10"


def make_room(
    name: str = "Living Room",
    uid: str = "RINCON_001",
    ip_address: str = IP,
    is_coordinator: bool = True,
) -> Room:
    return Room(name=name, uid=uid, ip_address=ip_address, is_coordinator=is_coordinator)


def make_alarm_record(
    alarm_id: str = "101",
    room_name: str = "Living Room",
    start_time: str = "07:00:00",
    recurrence: str = "DAILY",
    enabled: bool = True,
    volume: int | None = 30,
    include_linked_zones: bool = False,
) -> AlarmRecord:
    return AlarmRecord(
        alarm_id=alarm_id,
        room_name=room_name,
        start_time=start_time,
        recurrence=recurrence,
        enabled=enabled,
        volume=volume,
        include_linked_zones=include_linked_zones,
    )


class FakeRoomService:
    def __init__(
        self,
        rooms: list[Room] | None = None,
        *,
        raise_discovery: bool = False,
    ) -> None:
        self._rooms = [make_room()] if rooms is None else rooms
        self._raise_discovery = raise_discovery

    def get_room(self, room_name: str) -> Room:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        for room in self._rooms:
            if room.name == room_name:
                return room
        raise RoomNotFoundError(room_name)

    def list_rooms(self) -> list[Room]:
        if self._raise_discovery:
            raise SonosDiscoveryError("network unreachable")
        return list(self._rooms)


class LookupOnlyRoomService(FakeRoomService):
    """Room lookup succeeds, but household-wide list queries return no rooms."""

    def get_room(self, room_name: str) -> Room:
        return make_room(name=room_name)

    def list_rooms(self) -> list[Room]:
        return []


class FakeAdapter:
    def __init__(
        self,
        alarms: list[AlarmRecord] | None = None,
        *,
        raise_alarm_error: bool = False,
        created_alarm: AlarmRecord | None = None,
        valid_recurrence: bool = True,
    ) -> None:
        self._alarms = alarms or []
        self._raise_alarm_error = raise_alarm_error
        self._created_alarm = created_alarm
        self._valid_recurrence = valid_recurrence
        self.create_calls: list[dict] = []
        self.update_calls: list[dict] = []
        self.delete_calls: list[dict] = []
        self.validated_recurrences: list[str] = []

    def get_alarms(self, ip_address: str) -> list[AlarmRecord]:
        if self._raise_alarm_error:
            raise AlarmError("adapter failure")
        return list(self._alarms)

    def is_valid_recurrence(self, recurrence: str) -> bool:
        if self._raise_alarm_error:
            raise AlarmError("validation failed")
        self.validated_recurrences.append(recurrence)
        return self._valid_recurrence

    def create_alarm(
        self,
        ip_address: str,
        start_time: datetime.time,
        recurrence: str,
        enabled: bool,
        volume: int | None,
        include_linked_zones: bool,
    ) -> AlarmRecord:
        if self._raise_alarm_error:
            raise AlarmError("create failed")
        self.create_calls.append(
            {
                "ip_address": ip_address,
                "start_time": start_time,
                "recurrence": recurrence,
                "enabled": enabled,
                "volume": volume,
                "include_linked_zones": include_linked_zones,
            }
        )
        return self._created_alarm or make_alarm_record()

    def update_alarm(
        self,
        ip_address: str,
        alarm_id: str,
        start_time: datetime.time,
        recurrence: str,
        enabled: bool,
        volume: int | None,
        include_linked_zones: bool,
    ) -> AlarmRecord:
        if self._raise_alarm_error:
            raise AlarmError(f"Alarm '{alarm_id}' not found.")
        self.update_calls.append(
            {
                "ip_address": ip_address,
                "alarm_id": alarm_id,
                "start_time": start_time,
                "recurrence": recurrence,
                "enabled": enabled,
                "volume": volume,
                "include_linked_zones": include_linked_zones,
            }
        )
        return make_alarm_record(alarm_id=alarm_id)

    def delete_alarm(self, ip_address: str, alarm_id: str) -> None:
        if self._raise_alarm_error:
            raise AlarmError(f"Alarm '{alarm_id}' not found.")
        self.delete_calls.append({"ip_address": ip_address, "alarm_id": alarm_id})


class TestListAlarms:
    def test_returns_empty_list_when_household_has_no_alarms(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        result = service.list_alarms()
        assert result == []

    def test_returns_all_alarm_records(self) -> None:
        alarms = [make_alarm_record("1"), make_alarm_record("2")]
        service = AlarmService(FakeRoomService(), FakeAdapter(alarms=alarms))
        result = service.list_alarms()
        assert len(result) == 2

    def test_propagates_alarm_error(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter(raise_alarm_error=True))
        with pytest.raises(AlarmError):
            service.list_alarms()

    def test_uses_any_available_room_for_discovery(self) -> None:
        rooms = [make_room("Living Room", ip_address="192.168.1.10")]
        service = AlarmService(FakeRoomService(rooms=rooms), FakeAdapter())
        # Should not raise — simply uses first available room
        service.list_alarms()

    def test_raises_discovery_error_when_no_rooms_available(self) -> None:
        service = AlarmService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(SonosDiscoveryError, match="No Sonos rooms found"):
            service.list_alarms()


class TestCreateAlarm:
    def test_valid_create_returns_record(self) -> None:
        expected = make_alarm_record(alarm_id="new-1")
        service = AlarmService(FakeRoomService(), FakeAdapter(created_alarm=expected))
        result = service.create_alarm(
            room_name="Living Room",
            start_time="07:00:00",
            recurrence="DAILY",
            enabled=True,
            volume=30,
            include_linked_zones=False,
        )
        assert result.alarm_id == "new-1"

    def test_delegates_parsed_time_to_adapter(self) -> None:
        adapter = FakeAdapter(created_alarm=make_alarm_record())
        service = AlarmService(FakeRoomService(), adapter)
        service.create_alarm(
            room_name="Living Room",
            start_time="08:30:00",
            recurrence="DAILY",
            enabled=True,
            volume=30,
            include_linked_zones=False,
        )
        assert adapter.create_calls[0]["start_time"] == datetime.time(8, 30, 0)
        assert adapter.validated_recurrences == ["DAILY"]

    def test_raises_validation_error_for_invalid_time_format(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="start_time"):
            service.create_alarm(
                room_name="Living Room",
                start_time="7am",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_validation_error_for_invalid_recurrence(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter(valid_recurrence=False))
        with pytest.raises(AlarmValidationError, match="recurrence"):
            service.create_alarm(
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="MONTHLY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_validation_error_for_volume_out_of_range(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="volume"):
            service.create_alarm(
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=101,
                include_linked_zones=False,
            )

    def test_raises_validation_error_for_negative_volume(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="volume"):
            service.create_alarm(
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=-1,
                include_linked_zones=False,
            )

    def test_none_volume_is_allowed(self) -> None:
        adapter = FakeAdapter(created_alarm=make_alarm_record(volume=None))
        service = AlarmService(FakeRoomService(), adapter)
        result = service.create_alarm(
            room_name="Living Room",
            start_time="07:00:00",
            recurrence="DAILY",
            enabled=True,
            volume=None,
            include_linked_zones=False,
        )
        assert result.volume is None

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            service.create_alarm(
                room_name="Nonexistent Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    @pytest.mark.parametrize(
        "recurrence",
        [
            "DAILY",
            "WEEKDAYS",
            "WEEKENDS",
            "ON_0",
            "ON_1",
            "ON_0_1",
            "ON_0_1_2_3_4_5_6",
        ],
    )
    def test_valid_recurrence_values_are_accepted(self, recurrence: str) -> None:
        adapter = FakeAdapter(created_alarm=make_alarm_record(recurrence=recurrence))
        service = AlarmService(FakeRoomService(), adapter)
        result = service.create_alarm(
            room_name="Living Room",
            start_time="07:00:00",
            recurrence=recurrence,
            enabled=True,
            volume=30,
            include_linked_zones=False,
        )
        assert result.recurrence == recurrence


class TestUpdateAlarm:
    def test_valid_update_returns_record(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter(alarms=[make_alarm_record("101")]))
        result = service.update_alarm(
            alarm_id="101",
            room_name="Living Room",
            start_time="09:00:00",
            recurrence="WEEKDAYS",
            enabled=False,
            volume=50,
            include_linked_zones=True,
        )
        assert result.alarm_id == "101"

    def test_delegates_parsed_time_to_adapter(self) -> None:
        adapter = FakeAdapter(alarms=[make_alarm_record("101")])
        service = AlarmService(FakeRoomService(), adapter)
        service.update_alarm(
            alarm_id="101",
            room_name="Living Room",
            start_time="09:15:00",
            recurrence="DAILY",
            enabled=True,
            volume=30,
            include_linked_zones=False,
        )
        assert adapter.update_calls[0]["start_time"] == datetime.time(9, 15, 0)

    def test_raises_validation_error_for_invalid_time(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="start_time"):
            service.update_alarm(
                alarm_id="101",
                room_name="Living Room",
                start_time="bad-time",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_validation_error_for_invalid_recurrence(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter(valid_recurrence=False))
        with pytest.raises(AlarmValidationError, match="recurrence"):
            service.update_alarm(
                alarm_id="101",
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="YEARLY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_validation_error_when_alarm_id_is_unknown(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="not found"):
            service.update_alarm(
                alarm_id="missing",
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_discovery_error_when_no_rooms_available(self) -> None:
        service = AlarmService(LookupOnlyRoomService(), FakeAdapter())
        with pytest.raises(SonosDiscoveryError, match="No Sonos rooms found"):
            service.update_alarm(
                alarm_id="101",
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_validation_error_when_alarm_id_is_blank(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="alarm_id"):
            service.update_alarm(
                alarm_id="  ",
                room_name="Living Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )

    def test_raises_room_not_found_for_unknown_room(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(RoomNotFoundError):
            service.update_alarm(
                alarm_id="101",
                room_name="Ghost Room",
                start_time="07:00:00",
                recurrence="DAILY",
                enabled=True,
                volume=30,
                include_linked_zones=False,
            )


class TestDeleteAlarm:
    def test_valid_delete_returns_confirmation(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter(alarms=[make_alarm_record("101")]))
        result = service.delete_alarm(alarm_id="101")
        assert result["alarm_id"] == "101"
        assert result["status"] == "deleted"

    def test_delegates_to_adapter(self) -> None:
        adapter = FakeAdapter(alarms=[make_alarm_record("101")])
        service = AlarmService(FakeRoomService(), adapter)
        service.delete_alarm(alarm_id="101")
        assert len(adapter.delete_calls) == 1
        assert adapter.delete_calls[0]["alarm_id"] == "101"

    def test_raises_validation_error_when_alarm_id_is_unknown(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="not found"):
            service.delete_alarm(alarm_id="missing")

    def test_raises_validation_error_when_alarm_id_is_blank(self) -> None:
        service = AlarmService(FakeRoomService(), FakeAdapter())
        with pytest.raises(AlarmValidationError, match="alarm_id"):
            service.delete_alarm(alarm_id=" ")

    def test_raises_discovery_error_when_no_rooms_available_for_delete(self) -> None:
        service = AlarmService(FakeRoomService(rooms=[]), FakeAdapter())
        with pytest.raises(SonosDiscoveryError, match="No Sonos rooms found"):
            service.delete_alarm(alarm_id="101")
