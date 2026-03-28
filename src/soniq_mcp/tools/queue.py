"""Queue MCP tools for SoniqMCP.

Exposes get_queue, add_to_queue, remove_from_queue, clear_queue, and
play_from_queue as thin handlers that delegate to ``QueueService``.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import QueueError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import QueueResponse

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


def register(app: FastMCP, config: SoniqConfig, queue_service: object) -> None:
    """Register queue tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        queue_service: A ``QueueService`` instance (or compatible fake).
    """

    if "get_queue" not in config.tools_disabled:

        @app.tool(
            title="Get Queue",
            annotations=_READ_ONLY_TOOL_HINTS,
        )
        def get_queue(room: str) -> dict:
            """Return the current playback queue for the specified Sonos room."""
            assert_tool_permitted("get_queue", config)
            try:
                items = queue_service.get_queue(room)
                return QueueResponse.from_domain(room, items).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except QueueError as exc:
                log.warning("Queue error in get_queue: %s", exc)
                return ErrorResponse.from_queue_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in get_queue: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "add_to_queue" not in config.tools_disabled:

        @app.tool(
            title="Add to Queue",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def add_to_queue(room: str, uri: str) -> dict:
            """Add a URI to the playback queue in the specified Sonos room."""
            assert_tool_permitted("add_to_queue", config)
            try:
                position = queue_service.add_to_queue(room, uri)
                return {"status": "ok", "room": room, "queue_position": position}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except QueueError as exc:
                log.warning("Queue error in add_to_queue: %s", exc)
                return ErrorResponse.from_queue_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in add_to_queue: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "remove_from_queue" not in config.tools_disabled:

        @app.tool(
            title="Remove from Queue",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def remove_from_queue(room: str, position: int) -> dict:
            """Remove the item at the given 1-based position from the queue."""
            assert_tool_permitted("remove_from_queue", config)
            try:
                queue_service.remove_from_queue(room, position)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except QueueError as exc:
                log.warning("Queue error in remove_from_queue: %s", exc)
                return ErrorResponse.from_queue_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in remove_from_queue: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "clear_queue" not in config.tools_disabled:

        @app.tool(
            title="Clear Queue",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def clear_queue(room: str) -> dict:
            """Clear all items from the playback queue in the specified Sonos room."""
            assert_tool_permitted("clear_queue", config)
            try:
                queue_service.clear_queue(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except QueueError as exc:
                log.warning("Queue error in clear_queue: %s", exc)
                return ErrorResponse.from_queue_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in clear_queue: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "play_from_queue" not in config.tools_disabled:

        @app.tool(
            title="Play from Queue",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def play_from_queue(room: str, position: int) -> dict:
            """Start playback from the given 1-based queue position in the specified room."""
            assert_tool_permitted("play_from_queue", config)
            try:
                queue_service.play_from_queue(room, position)
                return {"status": "ok", "room": room, "position": position}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except QueueError as exc:
                log.warning("Queue error in play_from_queue: %s", exc)
                return ErrorResponse.from_queue_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in play_from_queue: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
