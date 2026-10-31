"""Device MCP tools for SoniqMCP.

Exposes get_battery_info as a thin handler that delegates to
``DeviceService``.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import DeviceError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import BatteryInfoResponse

log = logging.getLogger(__name__)

_READ_ONLY_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, device_service: object) -> None:
    """Register device tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        device_service: A ``DeviceService`` instance (or compatible fake).
    """

    if "get_battery_info" not in config.tools_disabled:

        @app.tool(title="Get Battery Info", annotations=_READ_ONLY_TOOL_HINTS)
        def get_battery_info(room: str) -> dict:
            """Return battery level and power source for a portable Sonos speaker.

            Rooms without a portable speaker return supported=false instead of an error.
            """
            assert_tool_permitted("get_battery_info", config)
            try:
                info = device_service.get_battery_info(room)
                return BatteryInfoResponse.from_domain(info).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except DeviceError as exc:
                log.warning("Device error in get_battery_info: %s", exc)
                return ErrorResponse.from_device_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_battery_info: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
