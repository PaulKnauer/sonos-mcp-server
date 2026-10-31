"""Snapshot service — capture and restore playback around announcements.

Snapshots are held in an in-memory registry keyed by an opaque id and
bound to the room they were captured from. Grouped rooms are captured and
restored on their group coordinator, matching where ``play_uri`` plays. They do not survive a server
restart (acceptable for v1): restore promptly after an announcement.
"""

from __future__ import annotations

import logging
import secrets
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import SnapshotNotFoundError, VolumeCapExceeded
from soniq_mcp.domain.models import Room, SnapshotRestoreResult, SnapshotToken
from soniq_mcp.domain.safety import check_volume

log = logging.getLogger(__name__)

# Bound the registry so abandoned snapshots cannot grow memory without limit.
MAX_SNAPSHOTS = 64


@dataclass(frozen=True)
class _StoredSnapshot:
    room_name: str
    include_queue: bool
    state: dict[str, Any]


class SnapshotService:
    """Orchestrates snapshot capture and restore for a single room.

    Args:
        room_service: A ``RoomService`` instance for room/IP resolution.
        adapter: A ``SnapshotAdapter`` instance (or compatible fake).
        config: Active server configuration (volume cap).
    """

    def __init__(self, room_service: object, adapter: object, config: SoniqConfig) -> None:
        self._room_service = room_service
        self._adapter = adapter
        self._config = config
        self._snapshots: OrderedDict[str, _StoredSnapshot] = OrderedDict()
        self._lock = threading.Lock()

    def snapshot(self, room_name: str, include_queue: bool = False) -> SnapshotToken:
        """Capture the current playback state of a room.

        Raises:
            RoomNotFoundError: If the room is not found.
            SnapshotError: If the capture fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._room_service.get_room(room_name)
        target = self._resolve_coordinator(room)
        state = self._adapter.capture(target.ip_address, include_queue)
        snapshot_id = secrets.token_urlsafe(16)
        with self._lock:
            self._snapshots[snapshot_id] = _StoredSnapshot(
                room_name=room.name,
                include_queue=include_queue,
                state=state,
            )
            while len(self._snapshots) > MAX_SNAPSHOTS:
                self._snapshots.popitem(last=False)
        return SnapshotToken(
            snapshot_id=snapshot_id,
            room_name=room.name,
            include_queue=include_queue,
        )

    def restore_snapshot(
        self, room_name: str, snapshot_id: str, fade: bool = False
    ) -> SnapshotRestoreResult:
        """Restore a snapshot previously captured from the same room.

        The snapshot is consumed on success. If the captured volume exceeds
        ``max_volume_pct`` the volume is left unchanged rather than raised
        above the cap, and ``volume_restored`` is False.

        Raises:
            RoomNotFoundError: If the room is not found.
            SnapshotNotFoundError: If the id is unknown or was captured from
                another room.
            SnapshotError: If the restore fails.
            SonosDiscoveryError: If network discovery fails.
        """
        room = self._room_service.get_room(room_name)
        with self._lock:
            stored = self._snapshots.get(snapshot_id)
        if stored is None or stored.room_name != room.name:
            raise SnapshotNotFoundError(
                f"Snapshot '{snapshot_id}' was not found for room {room.name!r}. "
                "Snapshots are in-memory only and are lost when the server restarts."
            )

        restore_volume = self._volume_within_cap(stored.state.get("volume"))
        target = self._resolve_coordinator(room)
        self._adapter.restore(target.ip_address, stored.state, fade, restore_volume)
        with self._lock:
            self._snapshots.pop(snapshot_id, None)
        return SnapshotRestoreResult(
            snapshot_id=snapshot_id,
            room_name=room.name,
            queue_restored=stored.include_queue,
            volume_restored=restore_volume,
        )

    def _resolve_coordinator(self, room: Room) -> Room:
        """Return the group coordinator for a grouped room, else the room itself."""
        coordinator_uid = room.group_coordinator_uid
        if not coordinator_uid:
            return room
        for candidate in self._room_service.list_rooms():
            if candidate.uid == coordinator_uid:
                return candidate
        return room

    def _volume_within_cap(self, volume: object) -> bool:
        if not isinstance(volume, int) or isinstance(volume, bool):
            return True
        try:
            check_volume(volume, self._config)
        except VolumeCapExceeded:
            log.warning(
                "snapshot restore: captured volume %s exceeds cap %s; leaving volume unchanged",
                volume,
                self._config.max_volume_pct,
            )
            return False
        except ValueError:
            return False
        return True
