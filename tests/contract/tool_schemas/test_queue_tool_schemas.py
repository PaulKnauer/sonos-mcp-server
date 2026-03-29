"""Contract tests for queue tool schemas.

Asserts that tool names and parameter names remain stable across changes.
These tests prevent silent breaking changes to the MCP tool surface.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

import pytest


def _make_config(disabled=None):
    config = MagicMock()
    config.tools_disabled = disabled or []
    return config


def _collect_tools():
    """Register all queue tools and return {name: function} mapping."""
    from soniq_mcp.tools.queue import register

    tools = {}

    app = MagicMock()

    def tool_decorator(title=None, annotations=None):
        def decorator(fn):
            tools[fn.__name__] = fn
            return fn

        return decorator

    app.tool.side_effect = tool_decorator
    register(app, _make_config(), MagicMock())
    return tools


@pytest.fixture(scope="module")
def queue_tools():
    return _collect_tools()


class TestQueueToolNames:
    def test_get_queue_registered(self, queue_tools):
        assert "get_queue" in queue_tools

    def test_add_to_queue_registered(self, queue_tools):
        assert "add_to_queue" in queue_tools

    def test_remove_from_queue_registered(self, queue_tools):
        assert "remove_from_queue" in queue_tools

    def test_clear_queue_registered(self, queue_tools):
        assert "clear_queue" in queue_tools

    def test_play_from_queue_registered(self, queue_tools):
        assert "play_from_queue" in queue_tools


class TestGetQueueParameters:
    def test_has_room_parameter(self, queue_tools):
        params = inspect.signature(queue_tools["get_queue"]).parameters
        assert "room" in params

    def test_room_is_only_parameter(self, queue_tools):
        params = inspect.signature(queue_tools["get_queue"]).parameters
        assert set(params.keys()) == {"room"}


class TestAddToQueueParameters:
    def test_has_room_and_uri_parameters(self, queue_tools):
        params = inspect.signature(queue_tools["add_to_queue"]).parameters
        assert "room" in params
        assert "uri" in params

    def test_has_exactly_two_parameters(self, queue_tools):
        params = inspect.signature(queue_tools["add_to_queue"]).parameters
        assert set(params.keys()) == {"room", "uri"}


class TestRemoveFromQueueParameters:
    def test_has_room_and_position_parameters(self, queue_tools):
        params = inspect.signature(queue_tools["remove_from_queue"]).parameters
        assert "room" in params
        assert "position" in params

    def test_has_exactly_two_parameters(self, queue_tools):
        params = inspect.signature(queue_tools["remove_from_queue"]).parameters
        assert set(params.keys()) == {"room", "position"}


class TestClearQueueParameters:
    def test_has_room_parameter(self, queue_tools):
        params = inspect.signature(queue_tools["clear_queue"]).parameters
        assert "room" in params

    def test_room_is_only_parameter(self, queue_tools):
        params = inspect.signature(queue_tools["clear_queue"]).parameters
        assert set(params.keys()) == {"room"}


class TestPlayFromQueueParameters:
    def test_has_room_and_position_parameters(self, queue_tools):
        params = inspect.signature(queue_tools["play_from_queue"]).parameters
        assert "room" in params
        assert "position" in params

    def test_has_exactly_two_parameters(self, queue_tools):
        params = inspect.signature(queue_tools["play_from_queue"]).parameters
        assert set(params.keys()) == {"room", "position"}


class TestToolsRespectDisabledList:
    @pytest.mark.parametrize(
        "tool_name",
        ["get_queue", "add_to_queue", "remove_from_queue", "clear_queue", "play_from_queue"],
    )
    def test_disabled_tool_not_registered(self, tool_name):
        from soniq_mcp.tools.queue import register

        tools = {}
        app = MagicMock()

        def tool_decorator(title=None, annotations=None):
            def decorator(fn):
                tools[fn.__name__] = fn
                return fn

            return decorator

        app.tool.side_effect = tool_decorator
        register(app, _make_config(disabled=[tool_name]), MagicMock())
        assert tool_name not in tools
