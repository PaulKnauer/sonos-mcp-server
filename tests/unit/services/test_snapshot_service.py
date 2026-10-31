"""Unit tests for SnapshotService."""

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.domain.exceptions import (
    RoomNotFoundError,
    SnapshotError,
    SnapshotInProgressError,
    SnapshotNotFoundError,
)
from soniq_mcp.domain.models import Room
from soniq_mcp.services import snapshot_service as snapshot_module
from soniq_mcp.services.snapshot_service import SnapshotService

KITCHEN = Room(name="Kitchen", uid="UID1", ip_address="192.168.1.10", is_coordinator=True)
OFFICE = Room(name="Office", uid="UID2", ip_address="192.168.1.11", is_coordinator=True)
DINING = Room(
    name="Dining",
    uid="UID3",
    ip_address="192.168.1.12",
    is_coordinator=False,
    group_coordinator_uid="UID1",
)


class FakeSnapshotAdapter:
    def __init__(self, state=None):
        self.state = state if state is not None else {"volume": 30, "transport_state": "PLAYING"}
        self.captured: list[tuple[str, bool]] = []
        self.restored: list[tuple[str, dict, bool, bool]] = []

    def capture(self, ip_address, include_queue):
        self.captured.append((ip_address, include_queue))
        return dict(self.state)

    def restore(self, ip_address, state, fade, restore_volume=True):
        self.restored.append((ip_address, state, fade, restore_volume))


class FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _make_service(adapter=None, max_volume_pct=80, clock=None):
    rooms = {"Kitchen": KITCHEN, "Office": OFFICE, "Dining": DINING}
    room_service = MagicMock()

    def get_room(name):
        if name not in rooms:
            raise RoomNotFoundError(name)
        return rooms[name]

    room_service.get_room.side_effect = get_room
    room_service.list_rooms.return_value = list(rooms.values())
    adapter = adapter or FakeSnapshotAdapter()
    config = SoniqConfig(max_volume_pct=max_volume_pct)
    return SnapshotService(room_service, adapter, config, clock=clock or FakeClock()), adapter


class TestSnapshot:
    def test_returns_opaque_token_for_room(self):
        svc, adapter = _make_service()

        token = svc.snapshot("Kitchen")

        assert token.room_name == "Kitchen"
        assert token.include_queue is False
        assert len(token.snapshot_id) >= 16
        assert adapter.captured == [(KITCHEN.ip_address, False)]

    def test_tokens_are_unique(self):
        svc, _ = _make_service()

        assert svc.snapshot("Kitchen").snapshot_id != svc.snapshot("Office").snapshot_id

    def test_passes_include_queue(self):
        svc, adapter = _make_service()

        token = svc.snapshot("Kitchen", include_queue=True)

        assert token.include_queue is True
        assert adapter.captured == [(KITCHEN.ip_address, True)]

    def test_propagates_room_not_found(self):
        svc, _ = _make_service()

        with pytest.raises(RoomNotFoundError):
            svc.snapshot("Garage")

    def test_propagates_adapter_error(self):
        adapter = MagicMock()
        adapter.capture.side_effect = SnapshotError("boom")
        svc, _ = _make_service(adapter=adapter)

        with pytest.raises(SnapshotError):
            svc.snapshot("Kitchen")

    def test_registry_is_bounded(self, monkeypatch):
        monkeypatch.setattr(snapshot_module, "MAX_SNAPSHOTS", 2)
        clock = FakeClock()
        svc, _ = _make_service(clock=clock)

        first = svc.snapshot("Kitchen")
        clock.now += snapshot_module.PENDING_LOCK_SECONDS + 1
        svc.snapshot("Kitchen")
        clock.now += snapshot_module.PENDING_LOCK_SECONDS + 1
        svc.snapshot("Kitchen")

        with pytest.raises(SnapshotNotFoundError):
            svc.restore_snapshot("Kitchen", first.snapshot_id)


class TestRestoreSnapshot:
    def test_restores_and_consumes_snapshot(self):
        svc, adapter = _make_service()
        token = svc.snapshot("Kitchen")

        result = svc.restore_snapshot("Kitchen", token.snapshot_id, fade=True)

        assert result.room_name == "Kitchen"
        assert result.volume_restored is True
        assert result.queue_restored is False
        ip, state, fade, restore_volume = adapter.restored[0]
        assert ip == KITCHEN.ip_address
        assert state["volume"] == 30
        assert fade is True
        assert restore_volume is True
        with pytest.raises(SnapshotNotFoundError):
            svc.restore_snapshot("Kitchen", token.snapshot_id)

    def test_queue_restored_only_when_captured(self):
        svc, _ = _make_service()
        token = svc.snapshot("Kitchen", include_queue=True)

        assert svc.restore_snapshot("Kitchen", token.snapshot_id).queue_restored is True

    def test_unknown_id_raises_not_found(self):
        svc, _ = _make_service()

        with pytest.raises(SnapshotNotFoundError):
            svc.restore_snapshot("Kitchen", "nope")

    def test_snapshot_bound_to_room(self):
        svc, adapter = _make_service()
        token = svc.snapshot("Kitchen")

        with pytest.raises(SnapshotNotFoundError):
            svc.restore_snapshot("Office", token.snapshot_id)
        assert adapter.restored == []

    def test_volume_above_cap_is_not_restored(self):
        svc, adapter = _make_service(FakeSnapshotAdapter({"volume": 95}), max_volume_pct=80)
        token = svc.snapshot("Kitchen")

        result = svc.restore_snapshot("Kitchen", token.snapshot_id, fade=True)

        assert result.volume_restored is False
        assert adapter.restored[0][3] is False

    def test_failed_restore_keeps_snapshot_for_retry(self):
        adapter = FakeSnapshotAdapter()
        svc, _ = _make_service(adapter=adapter)
        token = svc.snapshot("Kitchen")
        adapter.restore = MagicMock(side_effect=[SnapshotError("boom"), None])

        with pytest.raises(SnapshotError):
            svc.restore_snapshot("Kitchen", token.snapshot_id)
        assert svc.restore_snapshot("Kitchen", token.snapshot_id).room_name == "Kitchen"


class TestGroupedRooms:
    def test_group_member_is_captured_and_restored_on_coordinator(self):
        svc, adapter = _make_service()

        token = svc.snapshot("Dining")
        result = svc.restore_snapshot("Dining", token.snapshot_id)

        assert token.room_name == "Dining"
        assert adapter.captured == [(KITCHEN.ip_address, False)]
        assert adapter.restored[0][0] == KITCHEN.ip_address
        assert result.room_name == "Dining"


class TestOverlappingSnapshots:
    def test_second_snapshot_of_same_room_is_rejected(self):
        svc, adapter = _make_service()
        svc.snapshot("Kitchen")

        with pytest.raises(SnapshotInProgressError, match="restore_snapshot"):
            svc.snapshot("Kitchen")
        assert len(adapter.captured) == 1

    def test_group_member_blocked_by_pending_coordinator_snapshot(self):
        svc, adapter = _make_service()
        svc.snapshot("Kitchen")

        with pytest.raises(SnapshotInProgressError):
            svc.snapshot("Dining")
        assert len(adapter.captured) == 1

    def test_other_rooms_are_not_blocked(self):
        svc, _ = _make_service()
        svc.snapshot("Kitchen")

        assert svc.snapshot("Office").room_name == "Office"

    def test_restore_releases_the_room(self):
        svc, _ = _make_service()
        first = svc.snapshot("Kitchen")
        svc.restore_snapshot("Kitchen", first.snapshot_id)

        assert svc.snapshot("Kitchen").snapshot_id != first.snapshot_id

    def test_failed_restore_keeps_room_blocked(self):
        adapter = FakeSnapshotAdapter()
        svc, _ = _make_service(adapter=adapter)
        token = svc.snapshot("Kitchen")
        adapter.restore = MagicMock(side_effect=SnapshotError("boom"))

        with pytest.raises(SnapshotError):
            svc.restore_snapshot("Kitchen", token.snapshot_id)
        with pytest.raises(SnapshotInProgressError):
            svc.snapshot("Kitchen")

    def test_abandoned_snapshot_stops_blocking_after_timeout(self):
        clock = FakeClock()
        svc, _ = _make_service(clock=clock)
        first = svc.snapshot("Kitchen")

        clock.now += snapshot_module.PENDING_LOCK_SECONDS + 1
        second = svc.snapshot("Kitchen")

        assert second.snapshot_id != first.snapshot_id
        # The abandoned snapshot can still be restored explicitly.
        assert svc.restore_snapshot("Kitchen", first.snapshot_id).room_name == "Kitchen"

    def test_failed_capture_does_not_block(self):
        adapter = FakeSnapshotAdapter()
        svc, _ = _make_service(adapter=adapter)
        original_capture = adapter.capture
        adapter.capture = MagicMock(side_effect=SnapshotError("timeout"))

        with pytest.raises(SnapshotError):
            svc.snapshot("Kitchen")
        adapter.capture = original_capture
        assert svc.snapshot("Kitchen").room_name == "Kitchen"

    def test_concurrent_capture_is_rejected(self):
        started = threading.Event()
        release = threading.Event()
        adapter = FakeSnapshotAdapter()
        original_capture = adapter.capture

        def slow_capture(ip_address, include_queue):
            started.set()
            release.wait(timeout=5)
            return original_capture(ip_address, include_queue)

        adapter.capture = slow_capture
        svc, _ = _make_service(adapter=adapter)
        results: list[object] = []
        worker = threading.Thread(target=lambda: results.append(svc.snapshot("Kitchen")))
        worker.start()
        assert started.wait(timeout=5)

        try:
            with pytest.raises(SnapshotInProgressError, match="already being captured"):
                svc.snapshot("Dining")
        finally:
            release.set()
            worker.join(timeout=5)
        assert len(results) == 1
