"""Unit tests for SoCoAdapter alarm methods."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from soniq_mcp.adapters.soco_adapter import SoCoAdapter
from soniq_mcp.domain.exceptions import AlarmError
from soniq_mcp.domain.models import AlarmRecord

IP = "192.168.1.10"


def _make_fake_alarm(
    alarm_id: str = "101",
    player_name: str = "Living Room",
    start_time: datetime.time = datetime.time(7, 0, 0),
    recurrence: str = "DAILY",
    enabled: bool = True,
    volume: int = 30,
    include_linked_zones: bool = False,
) -> MagicMock:
    alarm = MagicMock()
    alarm.alarm_id = alarm_id
    alarm.zone.player_name = player_name
    alarm.start_time = start_time
    alarm.recurrence = recurrence
    alarm.enabled = enabled
    alarm.volume = volume
    alarm.include_linked_zones = include_linked_zones
    return alarm


def _patch_zone():
    return patch("soco.SoCo", return_value=MagicMock())


class TestGetAlarms:
    def test_returns_empty_list_when_no_alarms(self) -> None:
        adapter = SoCoAdapter()
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value=set()):
                result = adapter.get_alarms(IP)
        assert result == []

    def test_returns_normalized_alarm_records(self) -> None:
        adapter = SoCoAdapter()
        fake = _make_fake_alarm()
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value={fake}):
                result = adapter.get_alarms(IP)
        assert len(result) == 1
        record = result[0]
        assert isinstance(record, AlarmRecord)
        assert record.alarm_id == "101"
        assert record.room_name == "Living Room"
        assert record.start_time == "07:00:00"
        assert record.recurrence == "DAILY"
        assert record.enabled is True
        assert record.volume == 30
        assert record.include_linked_zones is False

    def test_returns_multiple_alarms(self) -> None:
        adapter = SoCoAdapter()
        alarms = {
            _make_fake_alarm(alarm_id="1"),
            _make_fake_alarm(alarm_id="2", player_name="Bedroom"),
        }
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value=alarms):
                result = adapter.get_alarms(IP)
        assert len(result) == 2
        ids = {r.alarm_id for r in result}
        assert ids == {"1", "2"}

    def test_wraps_soco_failure_in_alarm_error(self) -> None:
        adapter = SoCoAdapter()
        with _patch_zone():
            with patch("soco.alarms.get_alarms", side_effect=RuntimeError("network failure")):
                with pytest.raises(AlarmError, match="Failed to get alarms"):
                    adapter.get_alarms(IP)

    def test_time_formatted_correctly_with_minutes_and_seconds(self) -> None:
        adapter = SoCoAdapter()
        fake = _make_fake_alarm(start_time=datetime.time(8, 30, 15))
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value={fake}):
                result = adapter.get_alarms(IP)
        assert result[0].start_time == "08:30:15"

    def test_none_volume_preserved(self) -> None:
        adapter = SoCoAdapter()
        fake = _make_fake_alarm(volume=None)
        fake.volume = None
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value={fake}):
                result = adapter.get_alarms(IP)
        assert result[0].volume is None


class TestCreateAlarm:
    def test_creates_and_saves_alarm(self) -> None:
        adapter = SoCoAdapter()
        fake_zone = MagicMock()
        fake_alarm = _make_fake_alarm(alarm_id="999")
        fake_alarm.save = MagicMock()

        with patch("soco.SoCo", return_value=fake_zone):
            with patch("soco.alarms.Alarm", return_value=fake_alarm):
                with patch("soco.alarms.get_alarms", return_value={fake_alarm}):
                    result = adapter.create_alarm(
                        ip_address=IP,
                        start_time=datetime.time(7, 0, 0),
                        recurrence="DAILY",
                        enabled=True,
                        volume=30,
                        include_linked_zones=False,
                    )

        fake_alarm.save.assert_called_once()
        assert isinstance(result, AlarmRecord)
        assert result.alarm_id == "999"

    def test_wraps_soco_failure_in_alarm_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", return_value=MagicMock()):
            with patch("soco.alarms.Alarm", side_effect=RuntimeError("create failed")):
                with pytest.raises(AlarmError, match="Failed to create alarm"):
                    adapter.create_alarm(
                        ip_address=IP,
                        start_time=datetime.time(7, 0, 0),
                        recurrence="DAILY",
                        enabled=True,
                        volume=30,
                        include_linked_zones=False,
                    )


class TestValidateRecurrence:
    def test_uses_soco_recurrence_validator(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.alarms.is_valid_recurrence", return_value=True) as mock_validate:
            result = adapter.is_valid_recurrence("DAILY")
        assert result is True
        mock_validate.assert_called_once_with("DAILY")

    def test_wraps_validator_failure_in_alarm_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.alarms.is_valid_recurrence", side_effect=RuntimeError("boom")):
            with pytest.raises(AlarmError, match="Failed to validate recurrence"):
                adapter.is_valid_recurrence("DAILY")


class TestUpdateAlarm:
    def test_updates_existing_alarm_and_saves(self) -> None:
        adapter = SoCoAdapter()
        fake_alarm = _make_fake_alarm(alarm_id="101")
        fake_alarm.save = MagicMock()

        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value={fake_alarm}):
                adapter.update_alarm(
                    ip_address=IP,
                    alarm_id="101",
                    start_time=datetime.time(8, 0, 0),
                    recurrence="WEEKDAYS",
                    enabled=False,
                    volume=50,
                    include_linked_zones=True,
                )

        fake_alarm.save.assert_called_once()
        assert fake_alarm.start_time == datetime.time(8, 0, 0)
        assert fake_alarm.recurrence == "WEEKDAYS"
        assert fake_alarm.enabled is False
        assert fake_alarm.volume == 50
        assert fake_alarm.include_linked_zones is True

    def test_raises_alarm_error_when_id_not_found(self) -> None:
        adapter = SoCoAdapter()
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value=set()):
                with pytest.raises(AlarmError, match="Alarm.*not found"):
                    adapter.update_alarm(
                        ip_address=IP,
                        alarm_id="missing",
                        start_time=datetime.time(8, 0, 0),
                        recurrence="DAILY",
                        enabled=True,
                        volume=30,
                        include_linked_zones=False,
                    )

    def test_wraps_soco_failure_in_alarm_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("boom")):
            with pytest.raises(AlarmError, match="Failed to update alarm"):
                adapter.update_alarm(
                    ip_address=IP,
                    alarm_id="101",
                    start_time=datetime.time(8, 0, 0),
                    recurrence="DAILY",
                    enabled=True,
                    volume=30,
                    include_linked_zones=False,
                )


class TestDeleteAlarm:
    def test_deletes_alarm_by_id(self) -> None:
        adapter = SoCoAdapter()
        fake_alarm = _make_fake_alarm(alarm_id="101")
        fake_alarm.remove = MagicMock()

        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value={fake_alarm}):
                adapter.delete_alarm(ip_address=IP, alarm_id="101")

        fake_alarm.remove.assert_called_once()

    def test_raises_alarm_error_when_id_not_found(self) -> None:
        adapter = SoCoAdapter()
        with _patch_zone():
            with patch("soco.alarms.get_alarms", return_value=set()):
                with pytest.raises(AlarmError, match="Alarm.*not found"):
                    adapter.delete_alarm(ip_address=IP, alarm_id="missing")

    def test_wraps_soco_failure_in_alarm_error(self) -> None:
        adapter = SoCoAdapter()
        with patch("soco.SoCo", side_effect=RuntimeError("bang")):
            with pytest.raises(AlarmError, match="Failed to delete alarm"):
                adapter.delete_alarm(ip_address=IP, alarm_id="101")
