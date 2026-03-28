"""Unit tests for queue MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import QueueError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import QueueItem


def _make_config(disabled=None):
    config = MagicMock()
    config.tools_disabled = disabled or []
    return config


def _make_app():
    """Return a minimal FastMCP-like app that collects registered tools."""
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


def _register_and_get(tool_name, queue_service=None, disabled=None):
    """Register queue tools and return the named tool function."""
    from soniq_mcp.tools.queue import register

    app = _make_app()
    config = _make_config(disabled)
    if queue_service is None:
        queue_service = MagicMock()
    register(app, config, queue_service)
    return app._tools.get(tool_name), queue_service, config


class TestGetQueue:
    def test_returns_queue_response_on_success(self):
        items = [QueueItem(position=1, uri="uri:1", title="Song", artist="Band", album="LP")]
        qs = MagicMock()
        qs.get_queue.return_value = items

        fn, _, _ = _register_and_get("get_queue", qs)
        result = fn(room="Kitchen")

        assert result["room"] == "Kitchen"
        assert result["count"] == 1
        assert result["items"][0]["position"] == 1
        assert result["items"][0]["title"] == "Song"

    def test_empty_queue_returns_zero_count(self):
        qs = MagicMock()
        qs.get_queue.return_value = []

        fn, _, _ = _register_and_get("get_queue", qs)
        result = fn(room="Kitchen")

        assert result["count"] == 0
        assert result["items"] == []

    def test_room_not_found_returns_error(self):
        qs = MagicMock()
        qs.get_queue.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("get_queue", qs)
        result = fn(room="Kitchen")

        assert "error" in result
        assert result["field"] == "room"

    def test_queue_error_returns_error(self):
        qs = MagicMock()
        qs.get_queue.side_effect = QueueError("timeout")

        fn, _, _ = _register_and_get("get_queue", qs)
        result = fn(room="Kitchen")

        assert result["field"] == "queue"

    def test_discovery_error_returns_error(self):
        qs = MagicMock()
        qs.get_queue.side_effect = SonosDiscoveryError("no devices")

        fn, _, _ = _register_and_get("get_queue", qs)
        result = fn(room="Kitchen")

        assert result["field"] == "sonos_network"

    def test_tool_disabled_returns_error(self):
        fn, _, _ = _register_and_get("get_queue", disabled=["get_queue"])
        assert fn is None


class TestAddToQueue:
    def test_returns_ok_with_queue_position(self):
        qs = MagicMock()
        qs.add_to_queue.return_value = 4

        fn, _, _ = _register_and_get("add_to_queue", qs)
        result = fn(room="Kitchen", uri="x-sonos:track")

        assert result["status"] == "ok"
        assert result["queue_position"] == 4
        assert result["room"] == "Kitchen"

    def test_room_not_found_returns_error(self):
        qs = MagicMock()
        qs.add_to_queue.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("add_to_queue", qs)
        result = fn(room="Kitchen", uri="uri")

        assert result["field"] == "room"

    def test_queue_error_returns_error(self):
        qs = MagicMock()
        qs.add_to_queue.side_effect = QueueError("upnp")

        fn, _, _ = _register_and_get("add_to_queue", qs)
        result = fn(room="Kitchen", uri="uri")

        assert result["field"] == "queue"

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("add_to_queue", disabled=["add_to_queue"])
        assert fn is None


class TestRemoveFromQueue:
    def test_returns_ok_on_success(self):
        qs = MagicMock()

        fn, _, _ = _register_and_get("remove_from_queue", qs)
        result = fn(room="Kitchen", position=2)

        assert result == {"status": "ok", "room": "Kitchen"}
        qs.remove_from_queue.assert_called_once_with("Kitchen", 2)

    def test_room_not_found_returns_error(self):
        qs = MagicMock()
        qs.remove_from_queue.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("remove_from_queue", qs)
        result = fn(room="Kitchen", position=1)

        assert result["field"] == "room"

    def test_queue_error_returns_error(self):
        qs = MagicMock()
        qs.remove_from_queue.side_effect = QueueError("out of range")

        fn, _, _ = _register_and_get("remove_from_queue", qs)
        result = fn(room="Kitchen", position=99)

        assert result["field"] == "queue"

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("remove_from_queue", disabled=["remove_from_queue"])
        assert fn is None


class TestClearQueue:
    def test_returns_ok_on_success(self):
        qs = MagicMock()

        fn, _, _ = _register_and_get("clear_queue", qs)
        result = fn(room="Kitchen")

        assert result == {"status": "ok", "room": "Kitchen"}
        qs.clear_queue.assert_called_once_with("Kitchen")

    def test_room_not_found_returns_error(self):
        qs = MagicMock()
        qs.clear_queue.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("clear_queue", qs)
        result = fn(room="Kitchen")

        assert result["field"] == "room"

    def test_queue_error_returns_error(self):
        qs = MagicMock()
        qs.clear_queue.side_effect = QueueError("upnp")

        fn, _, _ = _register_and_get("clear_queue", qs)
        result = fn(room="Kitchen")

        assert result["field"] == "queue"

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("clear_queue", disabled=["clear_queue"])
        assert fn is None


class TestPlayFromQueue:
    def test_returns_ok_with_position(self):
        qs = MagicMock()

        fn, _, _ = _register_and_get("play_from_queue", qs)
        result = fn(room="Kitchen", position=3)

        assert result == {"status": "ok", "room": "Kitchen", "position": 3}
        qs.play_from_queue.assert_called_once_with("Kitchen", 3)

    def test_room_not_found_returns_error(self):
        qs = MagicMock()
        qs.play_from_queue.side_effect = RoomNotFoundError("Kitchen")

        fn, _, _ = _register_and_get("play_from_queue", qs)
        result = fn(room="Kitchen", position=1)

        assert result["field"] == "room"

    def test_queue_error_returns_error(self):
        qs = MagicMock()
        qs.play_from_queue.side_effect = QueueError("invalid position")

        fn, _, _ = _register_and_get("play_from_queue", qs)
        result = fn(room="Kitchen", position=0)

        assert result["field"] == "queue"

    def test_discovery_error_returns_error(self):
        qs = MagicMock()
        qs.play_from_queue.side_effect = SonosDiscoveryError("no devices")

        fn, _, _ = _register_and_get("play_from_queue", qs)
        result = fn(room="Kitchen", position=1)

        assert result["field"] == "sonos_network"

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("play_from_queue", disabled=["play_from_queue"])
        assert fn is None
