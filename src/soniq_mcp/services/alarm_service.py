"""Alarm management service for SoniqMCP."""

from __future__ import annotations

import datetime

from soniq_mcp.domain.exceptions import AlarmValidationError, SonosDiscoveryError
from soniq_mcp.domain.models import AlarmRecord

_TIME_FORMAT = "%H:%M:%S"


def _parse_start_time(value: str) -> datetime.time:
    """Parse and validate a start_time string in HH:MM:SS format.

    Raises:
        AlarmValidationError: If the format is invalid.
    """
    try:
        return datetime.datetime.strptime(value.strip(), _TIME_FORMAT).time()
    except (ValueError, AttributeError) as exc:
        raise AlarmValidationError(
            f"Invalid start_time {value!r}. Expected format: HH:MM:SS (e.g. '07:00:00')."
        ) from exc


def _normalize_alarm_id(value: str) -> str:
    """Return a validated non-empty alarm identifier."""
    if not isinstance(value, str):
        raise AlarmValidationError("Invalid alarm_id. Expected a non-empty string.")
    normalized = value.strip()
    if not normalized:
        raise AlarmValidationError("Invalid alarm_id. Expected a non-empty string.")
    return normalized


def _validate_recurrence(value: str, adapter: object) -> str:
    """Validate that the recurrence string is supported by Sonos.

    Raises:
        AlarmValidationError: If the recurrence string is not valid.
    """
    normalized = value.strip().upper()
    if adapter.is_valid_recurrence(normalized):
        return normalized
    raise AlarmValidationError(f"Invalid recurrence {value!r}.")


def _validate_volume(value: int | None) -> None:
    """Validate that the volume is in the Sonos-safe range 0-100.

    Raises:
        AlarmValidationError: If the volume is out of range.
    """
    if value is None:
        return
    if not isinstance(value, int) or value < 0 or value > 100:
        raise AlarmValidationError(
            f"Invalid volume {value!r}. Alarm volume must be an integer in the range 0-100."
        )


class AlarmService:
    """Service for Sonos alarm discovery and lifecycle operations.

    Owns room resolution, recurrence validation, payload validation,
    and normalization. All SoCo interaction is delegated to the adapter.
    """

    def __init__(self, room_service: object, adapter: object) -> None:
        self._room_service = room_service
        self._adapter = adapter

    def list_alarms(self) -> list[AlarmRecord]:
        """Return all alarms in the household.

        Uses any available room for the discovery call. Does not filter
        by room — returns all household alarms.

        Returns:
            List of normalized ``AlarmRecord`` instances.

        Raises:
            AlarmError: If the adapter call fails.
            SonosDiscoveryError: If no rooms are reachable.
        """
        ip_address = self._get_any_ip_for_alarm_query()
        return self._adapter.get_alarms(ip_address)

    def create_alarm(
        self,
        room_name: str,
        start_time: str,
        recurrence: str,
        enabled: bool,
        volume: int | None,
        include_linked_zones: bool,
    ) -> AlarmRecord:
        """Create a new Sonos alarm.

        Validates all parameters before delegating to the adapter.

        Args:
            room_name: Target room name; resolved through room_service.
            start_time: Start time as ``"HH:MM:SS"`` string.
            recurrence: Recurrence rule (e.g. "DAILY", "WEEKDAYS").
            enabled: True to activate the alarm immediately.
            volume: Alarm volume (0-100), or None.
            include_linked_zones: True to play on all grouped rooms.

        Returns:
            Normalized ``AlarmRecord`` for the newly created alarm.

        Raises:
            AlarmValidationError: If any parameter fails validation.
            RoomNotFoundError: If the room cannot be resolved.
            AlarmError: If the adapter call fails.
        """
        parsed_time = _parse_start_time(start_time)
        normalized_recurrence = _validate_recurrence(recurrence, self._adapter)
        _validate_volume(volume)
        room = self._room_service.get_room(room_name)
        return self._adapter.create_alarm(
            ip_address=room.ip_address,
            start_time=parsed_time,
            recurrence=normalized_recurrence,
            enabled=enabled,
            volume=volume,
            include_linked_zones=include_linked_zones,
        )

    def update_alarm(
        self,
        alarm_id: str,
        room_name: str,
        start_time: str,
        recurrence: str,
        enabled: bool,
        volume: int | None,
        include_linked_zones: bool,
    ) -> AlarmRecord:
        """Update an existing Sonos alarm.

        Validates all parameters before delegating to the adapter.

        Args:
            alarm_id: ID of the alarm to update.
            room_name: Room used for the Sonos discovery call.
            start_time: New start time as ``"HH:MM:SS"`` string.
            recurrence: New recurrence rule.
            enabled: New enabled state.
            volume: New alarm volume (0-100), or None.
            include_linked_zones: New linked-zones setting.

        Returns:
            Normalized ``AlarmRecord`` reflecting the updated state.

        Raises:
            AlarmValidationError: If any parameter fails validation.
            RoomNotFoundError: If the room cannot be resolved.
            AlarmError: If the alarm is not found or the adapter call fails.
        """
        normalized_alarm_id = _normalize_alarm_id(alarm_id)
        parsed_time = _parse_start_time(start_time)
        normalized_recurrence = _validate_recurrence(recurrence, self._adapter)
        _validate_volume(volume)
        room = self._room_service.get_room(room_name)
        self._ensure_alarm_exists(normalized_alarm_id)
        return self._adapter.update_alarm(
            ip_address=room.ip_address,
            alarm_id=normalized_alarm_id,
            start_time=parsed_time,
            recurrence=normalized_recurrence,
            enabled=enabled,
            volume=volume,
            include_linked_zones=include_linked_zones,
        )

    def delete_alarm(self, alarm_id: str) -> dict:
        """Delete a Sonos alarm by ID.

        Uses any available room for the discovery call.

        Args:
            alarm_id: ID of the alarm to delete.

        Returns:
            Structured confirmation dict with ``alarm_id`` and ``status``.

        Raises:
            AlarmError: If the alarm is not found or the adapter call fails.
            SonosDiscoveryError: If no rooms are reachable.
        """
        normalized_alarm_id = _normalize_alarm_id(alarm_id)
        ip_address = self._get_any_ip_for_alarm_mutation()
        self._ensure_alarm_exists(normalized_alarm_id)
        self._adapter.delete_alarm(ip_address=ip_address, alarm_id=normalized_alarm_id)
        return {"alarm_id": normalized_alarm_id, "status": "deleted"}

    def _ensure_alarm_exists(self, alarm_id: str) -> None:
        """Raise a validation error when the alarm identifier is unknown."""
        alarms = self.list_alarms()
        if any(record.alarm_id == alarm_id for record in alarms):
            return
        raise AlarmValidationError(
            f"Alarm '{alarm_id}' was not found. Use 'list_alarms' to see available alarm IDs."
        )

    def _get_any_ip_for_alarm_mutation(self) -> str:
        """Return a reachable room IP for household-wide alarm mutations."""
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise SonosDiscoveryError("No Sonos rooms found — cannot delete alarms.")
        return rooms[0].ip_address

    def _get_any_ip_for_alarm_query(self) -> str:
        """Return a reachable room IP for household-wide alarm queries."""
        rooms = self._room_service.list_rooms()
        if not rooms:
            raise SonosDiscoveryError("No Sonos rooms found — cannot list alarms.")
        return rooms[0].ip_address
