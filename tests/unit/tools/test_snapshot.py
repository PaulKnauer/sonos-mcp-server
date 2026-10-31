"""Unit tests for snapshot MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

from soniq_mcp.domain.exceptions import (
    RoomNotFoundError,
    SnapshotError,
    SnapshotNotFoundError,
    SonosDiscoveryError,
)
from soniq_mcp.domain.models import SnapshotRestoreResult, SnapshotToken


def _make_config(disabled=None):
    config = MagicMock()
    config.tools_disabled = disabled or []
    return config


def _make_app():
    app = MagicMock()
    _tools = {}

    def tool_decorator(title=None, annotations=None):
        def decorator(fn):
            _tools[fn.__name__] = fn
            return fn

        return decorator

    app.tool.side_effect = tool_decorator
    app._tools = _tools
    return app


def _register_and_get(tool_name, service=None, disabled=None):
    from soniq_mcp.tools.snapshot import register

    app = _make_app()
    service = service or MagicMock()
    register(app, _make_config(disabled), service)
    return app._tools.get(tool_name), service


class TestSnapshotTool:
    def test_returns_snapshot_id(self):
        svc = MagicMock()
        svc.snapshot.return_value = SnapshotToken("abc", "Kitchen", False)
        fn, _ = _register_and_get("snapshot", svc)

        result = fn(room="Kitchen")

        svc.snapshot.assert_called_once_with("Kitchen", False)
        assert result == {"snapshot_id": "abc", "room": "Kitchen", "include_queue": False}

    def test_room_not_found(self):
        svc = MagicMock()
        svc.snapshot.side_effect = RoomNotFoundError("Garage")
        fn, _ = _register_and_get("snapshot", svc)

        assert fn(room="Garage")["field"] == "room"

    def test_snapshot_error(self):
        svc = MagicMock()
        svc.snapshot.side_effect = SnapshotError("boom")
        fn, _ = _register_and_get("snapshot", svc)

        assert fn(room="Kitchen")["field"] == "snapshot"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.snapshot.side_effect = SonosDiscoveryError("down")
        fn, _ = _register_and_get("snapshot", svc)

        assert fn(room="Kitchen")["category"] == "connectivity"

    def test_unexpected_error_is_internal(self):
        svc = MagicMock()
        svc.snapshot.side_effect = RuntimeError("secret detail")
        fn, _ = _register_and_get("snapshot", svc)

        result = fn(room="Kitchen")

        assert result["category"] == "internal"
        assert "secret" not in result["error"]

    def test_snapshot_in_progress_is_validation_error(self):
        from soniq_mcp.domain.exceptions import SnapshotInProgressError

        svc = MagicMock()
        svc.snapshot.side_effect = SnapshotInProgressError("pending")
        fn, _ = _register_and_get("snapshot", svc)

        result = fn(room="Kitchen")

        assert result["category"] == "validation"
        assert result["field"] == "snapshot"

    def test_disabled_tool_not_registered(self):
        fn, _ = _register_and_get("snapshot", disabled=["snapshot"])

        assert fn is None


class TestRestoreSnapshotTool:
    def test_returns_restored_status(self):
        svc = MagicMock()
        svc.restore_snapshot.return_value = SnapshotRestoreResult("abc", "Kitchen", False, True)
        fn, _ = _register_and_get("restore_snapshot", svc)

        result = fn(room="Kitchen", snapshot_id="abc", fade=True)

        svc.restore_snapshot.assert_called_once_with("Kitchen", "abc", True)
        assert result["status"] == "restored"
        assert result["volume_restored"] is True
        assert result["note"] is None

    def test_volume_not_restored_adds_note(self):
        svc = MagicMock()
        svc.restore_snapshot.return_value = SnapshotRestoreResult("abc", "Kitchen", False, False)
        fn, _ = _register_and_get("restore_snapshot", svc)

        result = fn(room="Kitchen", snapshot_id="abc")

        assert result["volume_restored"] is False
        assert "max_volume_pct" in result["note"]

    def test_unknown_snapshot_is_validation_error(self):
        svc = MagicMock()
        svc.restore_snapshot.side_effect = SnapshotNotFoundError("missing")
        fn, _ = _register_and_get("restore_snapshot", svc)

        result = fn(room="Kitchen", snapshot_id="nope")

        assert result["category"] == "validation"
        assert result["field"] == "snapshot"

    def test_room_not_found(self):
        svc = MagicMock()
        svc.restore_snapshot.side_effect = RoomNotFoundError("Garage")
        fn, _ = _register_and_get("restore_snapshot", svc)

        assert fn(room="Garage", snapshot_id="abc")["field"] == "room"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.restore_snapshot.side_effect = SonosDiscoveryError("down")
        fn, _ = _register_and_get("restore_snapshot", svc)

        assert fn(room="Kitchen", snapshot_id="abc")["category"] == "connectivity"

    def test_unexpected_error_is_internal(self):
        svc = MagicMock()
        svc.restore_snapshot.side_effect = RuntimeError("x")
        fn, _ = _register_and_get("restore_snapshot", svc)

        assert fn(room="Kitchen", snapshot_id="abc")["category"] == "internal"
