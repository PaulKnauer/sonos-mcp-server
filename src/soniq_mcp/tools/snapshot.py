"""Snapshot MCP tools for SoniqMCP.

Exposes snapshot and restore_snapshot as thin handlers that delegate to
``SnapshotService``. Use them to wrap one-shot announcements: snapshot,
play the announcement with ``play_uri``, then restore_snapshot.
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.exceptions import RoomNotFoundError, SnapshotError, SonosDiscoveryError
from soniq_mcp.domain.safety import assert_tool_permitted
from soniq_mcp.schemas.errors import ErrorResponse
from soniq_mcp.schemas.responses import SnapshotResponse, SnapshotRestoreResponse

log = logging.getLogger(__name__)

_CAPTURE_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)

_CONTROL_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


def register(app: FastMCP, config: SoniqConfig, snapshot_service: object) -> None:
    """Register snapshot tools onto the FastMCP application.

    Args:
        app: The FastMCP application instance.
        config: Active server configuration (used for permission checks).
        snapshot_service: A ``SnapshotService`` instance (or compatible fake).
    """

    if "snapshot" not in config.tools_disabled:

        @app.tool(
            title="Snapshot Playback",
            annotations=_CAPTURE_TOOL_HINTS,
        )
        def snapshot(room: str, include_queue: bool = False) -> dict:
            """Capture the current playback state of a room so it can be restored later.

            Returns a snapshot_id for restore_snapshot. Snapshots are held in server
            memory only and are lost if the server restarts. Set include_queue=true
            only when the queue itself will be replaced; restoring a large queue is slow.
            """
            assert_tool_permitted("snapshot", config)
            try:
                token = snapshot_service.snapshot(room, include_queue)
                return SnapshotResponse.from_domain(token).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SnapshotError as exc:
                log.warning("Snapshot error in snapshot: %s", exc)
                return ErrorResponse.from_snapshot_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in snapshot: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in snapshot")
                return ErrorResponse.from_internal_error(exc, field="snapshot").model_dump()

    if "restore_snapshot" not in config.tools_disabled:

        @app.tool(
            title="Restore Snapshot",
            annotations=_CONTROL_TOOL_HINTS,
        )
        def restore_snapshot(room: str, snapshot_id: str, fade: bool = False) -> dict:
            """Restore playback captured by snapshot for the same room.

            A room that was stopped or paused stays stopped or paused. Set fade=true
            to ramp the volume back up instead of jumping. The snapshot is consumed.
            """
            assert_tool_permitted("restore_snapshot", config)
            try:
                result = snapshot_service.restore_snapshot(room, snapshot_id, fade)
                return SnapshotRestoreResponse.from_domain(result).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SnapshotError as exc:
                log.warning("Snapshot error in restore_snapshot: %s", exc)
                return ErrorResponse.from_snapshot_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                log.warning("Discovery error in restore_snapshot: %s", exc)
                return ErrorResponse.from_discovery_error(exc).model_dump()
            except Exception as exc:
                log.exception("Internal error in restore_snapshot")
                return ErrorResponse.from_internal_error(exc, field="snapshot").model_dump()
