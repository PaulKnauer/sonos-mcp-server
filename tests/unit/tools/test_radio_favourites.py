"""Unit tests for radio favourites MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

from soniq_mcp.domain.exceptions import FavouritesError, RoomNotFoundError, SonosDiscoveryError
from soniq_mcp.domain.models import RadioFavourite


def _register_and_get(tool_name, service=None, disabled=None):
    from soniq_mcp.tools.favourites import register

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
    return tools.get(tool_name), service


class TestListRadioFavouritesTool:
    def test_returns_items_without_meta(self):
        svc = MagicMock()
        svc.list_radio_favourites.return_value = [
            RadioFavourite("Radio 1", "x-sonosapi-stream:s1", "station", "<meta/>")
        ]
        fn, _ = _register_and_get("list_radio_favourites", svc)

        result = fn(room="Kitchen")

        assert result["room"] == "Kitchen"
        assert result["count"] == 1
        assert result["items"][0] == {
            "title": "Radio 1",
            "uri": "x-sonosapi-stream:s1",
            "kind": "station",
        }

    def test_favourites_error(self):
        svc = MagicMock()
        svc.list_radio_favourites.side_effect = FavouritesError("boom")
        fn, _ = _register_and_get("list_radio_favourites", svc)

        assert fn(room="Kitchen")["field"] == "favourites"

    def test_room_not_found(self):
        svc = MagicMock()
        svc.list_radio_favourites.side_effect = RoomNotFoundError("Garage")
        fn, _ = _register_and_get("list_radio_favourites", svc)

        assert fn(room="Garage")["field"] == "room"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.list_radio_favourites.side_effect = SonosDiscoveryError("down")
        fn, _ = _register_and_get("list_radio_favourites", svc)

        assert fn(room="Kitchen")["category"] == "connectivity"


class TestPlayRadioFavouriteTool:
    def test_returns_ok(self):
        fn, svc = _register_and_get("play_radio_favourite")

        result = fn(room="Kitchen", uri="x-sonosapi-stream:s1")

        svc.play_radio_favourite.assert_called_once_with("Kitchen", "x-sonosapi-stream:s1")
        assert result["status"] == "ok"

    def test_favourites_error(self):
        svc = MagicMock()
        svc.play_radio_favourite.side_effect = FavouritesError("boom")
        fn, _ = _register_and_get("play_radio_favourite", svc)

        assert fn(room="Kitchen", uri="x")["field"] == "favourites"

    def test_room_not_found(self):
        svc = MagicMock()
        svc.play_radio_favourite.side_effect = RoomNotFoundError("Garage")
        fn, _ = _register_and_get("play_radio_favourite", svc)

        assert fn(room="Garage", uri="x")["field"] == "room"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.play_radio_favourite.side_effect = SonosDiscoveryError("down")
        fn, _ = _register_and_get("play_radio_favourite", svc)

        assert fn(room="Kitchen", uri="x")["category"] == "connectivity"

    def test_disabled_tools_not_registered(self):
        disabled = ["list_radio_favourites", "play_radio_favourite"]
        for name in disabled:
            fn, _ = _register_and_get(name, disabled=disabled)
            assert fn is None
