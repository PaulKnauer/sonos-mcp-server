"""Alarm management MCP tools for SoniqMCP."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import (
    AlarmError,
    RoomNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import AlarmDeleteResponse, AlarmResponse, AlarmsListResponse

log = logging.getLogger(__name__)

_READ_ONLY_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_CONTROL_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)

_DELETE_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=True,
    idempotentHint=False,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, alarm_service: object) -> None:
    """Register alarm lifecycle tools onto the FastMCP application."""

    if "list_alarms" not in config.tools_disabled:

        @app.tool(title="List Alarms", annotations=_READ_ONLY_TOOL_HINTS)
        def list_alarms() -> dict:
            """List all Sonos alarms in the household."""
            assert_tool_permitted("list_alarms", config)
            try:
                records = alarm_service.list_alarms()
                return AlarmsListResponse.from_domain(records).model_dump()
            except AlarmError as exc:
                return ErrorResponse.from_alarm_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in list_alarms: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "create_alarm" not in config.tools_disabled:

        @app.tool(title="Create Alarm", annotations=_CONTROL_TOOL_HINTS)
        def create_alarm(
            room: str,
            start_time: str,
            recurrence: str,
            enabled: bool = True,
            volume: int | None = None,
            include_linked_zones: bool = False,
        ) -> dict:
            """Create a new Sonos alarm.

            Args:
                room: Target room name.
                start_time: Alarm start time in HH:MM:SS format (e.g. "07:00:00").
                recurrence: Recurrence rule — DAILY, WEEKDAYS, WEEKENDS, or ON_<day>[_<day>...]
                    where day is 0 (Sunday) through 6 (Saturday).
                enabled: True to activate immediately (default: True).
                volume: Alarm volume 0-100, or omit to use the zone default.
                include_linked_zones: True to play on all grouped rooms (default: False).
            """
            assert_tool_permitted("create_alarm", config)
            try:
                record = alarm_service.create_alarm(
                    room_name=room,
                    start_time=start_time,
                    recurrence=recurrence,
                    enabled=enabled,
                    volume=volume,
                    include_linked_zones=include_linked_zones,
                )
                return AlarmResponse.from_domain(record).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except AlarmError as exc:
                return ErrorResponse.from_alarm_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in create_alarm: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "update_alarm" not in config.tools_disabled:

        @app.tool(title="Update Alarm", annotations=_CONTROL_TOOL_HINTS)
        def update_alarm(
            alarm_id: str,
            room: str,
            start_time: str,
            recurrence: str,
            enabled: bool,
            include_linked_zones: bool = False,
            volume: int | None = None,
        ) -> dict:
            """Update an existing Sonos alarm.

            Args:
                alarm_id: ID of the alarm to update (from list_alarms).
                room: Room name used for Sonos discovery.
                start_time: New start time in HH:MM:SS format.
                recurrence: New recurrence rule (DAILY, WEEKDAYS, WEEKENDS, or ON_<day>[_<day>...]).
                enabled: True to keep the alarm active, False to disable.
                include_linked_zones: True to play on all grouped rooms (default: False).
                volume: New alarm volume 0-100, or omit to use the zone default.
            """
            assert_tool_permitted("update_alarm", config)
            try:
                record = alarm_service.update_alarm(
                    alarm_id=alarm_id,
                    room_name=room,
                    start_time=start_time,
                    recurrence=recurrence,
                    enabled=enabled,
                    volume=volume,
                    include_linked_zones=include_linked_zones,
                )
                return AlarmResponse.from_domain(record).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except AlarmError as exc:
                return ErrorResponse.from_alarm_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in update_alarm: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "delete_alarm" not in config.tools_disabled:

        @app.tool(title="Delete Alarm", annotations=_DELETE_TOOL_HINTS)
        def delete_alarm(alarm_id: str) -> dict:
            """Delete a Sonos alarm by ID.

            Args:
                alarm_id: ID of the alarm to delete (from list_alarms).
            """
            assert_tool_permitted("delete_alarm", config)
            try:
                result = alarm_service.delete_alarm(alarm_id=alarm_id)
                return AlarmDeleteResponse(
                    alarm_id=result["alarm_id"],
                    status=result["status"],
                ).model_dump()
            except AlarmError as exc:
                return ErrorResponse.from_alarm_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery failed in delete_alarm: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
