"""Unit tests for the play_uri MCP tool handler."""

from __future__ import annotations

from unittest.mock import MagicMock

from soniq_mcp.domain.exceptions import (
    PlaybackError,
    PlaybackValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
)


def _register_and_get(service=None, disabled=None):
    from soniq_mcp.tools.playback import register

    tools = {}
    app = MagicMock()

    def tool_decorator(title=None, annotations=None):
        def decorator(fn):
            tools[fn.__name__] = fn
            return fn

        return decorator

    app.tool.side_effect = tool_decorator
    config = MagicMock()
    config.tools_disabled = disabled or []
    service = service or MagicMock()
    register(app, config, service)
    return tools.get("play_uri"), service


class TestPlayUriTool:
    def test_returns_ok(self):
        fn, svc = _register_and_get()

        result = fn(room="Kitchen", uri="http://hermes/a.mp3", title="Hi")

        svc.play_uri.assert_called_once_with("Kitchen", "http://hermes/a.mp3", "", "Hi", False)
        assert result == {"status": "ok", "room": "Kitchen"}

    def test_docstring_warns_about_radio_streams(self):
        fn, _ = _register_and_get()

        assert "snapshot" in fn.__doc__
        assert "radio stream" in fn.__doc__

    def test_validation_error(self):
        svc = MagicMock()
        svc.play_uri.side_effect = PlaybackValidationError("bad uri")
        fn, _ = _register_and_get(svc)

        result = fn(room="Kitchen", uri="nope")

        assert result["category"] == "validation"
        assert result["field"] == "playback"

    def test_playback_error(self):
        svc = MagicMock()
        svc.play_uri.side_effect = PlaybackError("boom")
        fn, _ = _register_and_get(svc)

        assert fn(room="Kitchen", uri="http://x/a.mp3")["category"] == "operation"

    def test_error_text_redacts_urls(self):
        svc = MagicMock()
        svc.play_uri.side_effect = PlaybackError("failed http://10.0.0.5:8080/a.mp3")
        fn, _ = _register_and_get(svc)

        assert "10.0.0.5" not in fn(room="Kitchen", uri="http://x/a.mp3")["error"]

    def test_room_not_found(self):
        svc = MagicMock()
        svc.play_uri.side_effect = RoomNotFoundError("Garage")
        fn, _ = _register_and_get(svc)

        assert fn(room="Garage", uri="http://x/a.mp3")["field"] == "room"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.play_uri.side_effect = SonosDiscoveryError("down")
        fn, _ = _register_and_get(svc)

        assert fn(room="Kitchen", uri="http://x/a.mp3")["category"] == "connectivity"

    def test_unexpected_error_is_internal(self):
        svc = MagicMock()
        svc.play_uri.side_effect = RuntimeError("x")
        fn, _ = _register_and_get(svc)

        assert fn(room="Kitchen", uri="http://x/a.mp3")["category"] == "internal"

    def test_disabled_tool_not_registered(self):
        fn, _ = _register_and_get(disabled=["play_uri"])

        assert fn is None
