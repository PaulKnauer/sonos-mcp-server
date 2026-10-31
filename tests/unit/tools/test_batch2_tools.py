"""Unit tests for playlist edit, ramp volume, and stereo pair MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from soniq_mcp.domain.exceptions import (
    GroupError,
    GroupValidationError,
    PlaylistError,
    PlaylistValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
    VolumeCapExceeded,
    VolumeError,
    VolumeValidationError,
)
from soniq_mcp.domain.models import SonosPlaylist, VolumeRampResult


def _register(module_register, service, disabled=None):
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
    module_register(app, config, service)
    return tools


def _playlist_tools(service=None, disabled=None):
    from soniq_mcp.tools.playlists import register

    service = service or MagicMock()
    return _register(register, service, disabled), service


def _volume_tools(service=None, disabled=None):
    from soniq_mcp.tools.volume import register

    service = service or MagicMock()
    return _register(register, service, disabled), service


def _group_tools(service=None, disabled=None):
    from soniq_mcp.tools.groups import register

    service = service or MagicMock()
    return _register(register, service, disabled), service


class TestSaveQueueAsPlaylistTool:
    def test_returns_playlist(self):
        svc = MagicMock()
        svc.save_queue_as_playlist.return_value = SonosPlaylist("Mix", "file:///x#1", "SQ:1")
        tools, _ = _playlist_tools(svc)

        result = tools["save_queue_as_playlist"](room="Kitchen", title="Mix")

        assert result["item_id"] == "SQ:1"
        assert result["title"] == "Mix"

    def test_room_not_found(self):
        svc = MagicMock()
        svc.save_queue_as_playlist.side_effect = RoomNotFoundError("Garage")
        tools, _ = _playlist_tools(svc)

        assert tools["save_queue_as_playlist"](room="Garage", title="Mix")["field"] == "room"

    def test_validation_error(self):
        svc = MagicMock()
        svc.save_queue_as_playlist.side_effect = PlaylistValidationError("blank")
        tools, _ = _playlist_tools(svc)

        result = tools["save_queue_as_playlist"](room="Kitchen", title="")

        assert result["category"] == "validation"
        assert result["field"] == "playlist"


class TestRemoveFromPlaylistTool:
    def test_returns_removed(self):
        svc = MagicMock()
        svc.remove_from_playlist.return_value = {
            "playlist_id": "SQ:1",
            "status": "removed",
            "position": 2,
        }
        tools, _ = _playlist_tools(svc)

        result = tools["remove_from_playlist"](playlist_id="SQ:1", position=2)

        assert result == {"playlist_id": "SQ:1", "status": "removed", "position": 2}

    def test_playlist_error(self):
        svc = MagicMock()
        svc.remove_from_playlist.side_effect = PlaylistError("boom")
        tools, _ = _playlist_tools(svc)

        assert tools["remove_from_playlist"](playlist_id="SQ:1", position=1)["field"] == "playlist"


class TestReorderPlaylistTool:
    def test_returns_reordered(self):
        svc = MagicMock()
        svc.reorder_playlist.return_value = {
            "playlist_id": "SQ:1",
            "status": "reordered",
            "from_position": 3,
            "to_position": 1,
        }
        tools, _ = _playlist_tools(svc)

        result = tools["reorder_playlist"](playlist_id="SQ:1", from_position=3, to_position=1)

        svc.reorder_playlist.assert_called_once_with("SQ:1", 3, 1)
        assert result["status"] == "reordered"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.reorder_playlist.side_effect = SonosDiscoveryError("down")
        tools, _ = _playlist_tools(svc)

        result = tools["reorder_playlist"](playlist_id="SQ:1", from_position=1, to_position=2)

        assert result["category"] == "connectivity"

    def test_rename_still_not_exposed(self):
        tools, _ = _playlist_tools()

        assert "rename_playlist" not in tools


@pytest.mark.parametrize(
    ("tool_name", "kwargs"),
    [
        ("save_queue_as_playlist", {"room": "Kitchen", "title": "Mix"}),
        ("remove_from_playlist", {"playlist_id": "SQ:1", "position": 1}),
        ("reorder_playlist", {"playlist_id": "SQ:1", "from_position": 1, "to_position": 2}),
    ],
)
def test_playlist_edit_unexpected_error_is_internal(tool_name, kwargs):
    svc = MagicMock()
    getattr(svc, tool_name).side_effect = RuntimeError("x")
    tools, _ = _playlist_tools(svc)

    assert tools[tool_name](**kwargs)["category"] == "internal"


class TestRampVolumeTool:
    def test_returns_ramp_result(self):
        svc = MagicMock()
        svc.ramp_volume.return_value = VolumeRampResult("Kitchen", 30, "SLEEP_TIMER_RAMP_TYPE", 8)
        tools, _ = _volume_tools(svc)

        result = tools["ramp_volume"](room="Kitchen", target=30)

        svc.ramp_volume.assert_called_once_with("Kitchen", 30, "SLEEP_TIMER_RAMP_TYPE")
        assert result == {
            "status": "ok",
            "room": "Kitchen",
            "target_volume": 30,
            "ramp_type": "SLEEP_TIMER_RAMP_TYPE",
            "ramp_seconds": 8,
        }

    def test_volume_cap(self):
        svc = MagicMock()
        svc.ramp_volume.side_effect = VolumeCapExceeded(95, 80)
        tools, _ = _volume_tools(svc)

        result = tools["ramp_volume"](room="Kitchen", target=95)

        assert result["field"] == "volume"
        assert result["category"] == "validation"

    @pytest.mark.parametrize(
        "exc", [VolumeValidationError("bad ramp"), VolumeError("boom"), ValueError("range")]
    )
    def test_volume_errors(self, exc):
        svc = MagicMock()
        svc.ramp_volume.side_effect = exc
        tools, _ = _volume_tools(svc)

        assert tools["ramp_volume"](room="Kitchen", target=30)["field"] == "sonos_volume"

    def test_room_not_found(self):
        svc = MagicMock()
        svc.ramp_volume.side_effect = RoomNotFoundError("Garage")
        tools, _ = _volume_tools(svc)

        assert tools["ramp_volume"](room="Garage", target=30)["field"] == "room"

    def test_discovery_error(self):
        svc = MagicMock()
        svc.ramp_volume.side_effect = SonosDiscoveryError("down")
        tools, _ = _volume_tools(svc)

        assert tools["ramp_volume"](room="Kitchen", target=30)["category"] == "connectivity"


class TestStereoPairTools:
    def test_create_returns_ok(self):
        tools, svc = _group_tools()

        result = tools["create_stereo_pair"](room="Left", slave_room="Right")

        svc.create_stereo_pair.assert_called_once_with("Left", "Right")
        assert result == {"status": "ok", "room": "Left", "slave_room": "Right"}

    @pytest.mark.parametrize(
        ("exc", "field"),
        [
            (GroupValidationError("same"), "group"),
            (GroupError("paired"), "group"),
            (RoomNotFoundError("Right"), "room"),
            (SonosDiscoveryError("down"), "sonos_network"),
            (RuntimeError("x"), "group"),
        ],
    )
    def test_create_errors(self, exc, field):
        svc = MagicMock()
        svc.create_stereo_pair.side_effect = exc
        tools, _ = _group_tools(svc)

        assert tools["create_stereo_pair"](room="Left", slave_room="Right")["field"] == field

    def test_separate_returns_ok(self):
        tools, svc = _group_tools()

        assert tools["separate_stereo_pair"](room="Left") == {"status": "ok", "room": "Left"}
        svc.separate_stereo_pair.assert_called_once_with("Left")

    @pytest.mark.parametrize(
        "exc", [GroupError("x"), RoomNotFoundError("Left"), SonosDiscoveryError("d"), KeyError()]
    )
    def test_separate_errors(self, exc):
        svc = MagicMock()
        svc.separate_stereo_pair.side_effect = exc
        tools, _ = _group_tools(svc)

        assert "error" in tools["separate_stereo_pair"](room="Left")


@pytest.mark.parametrize(
    ("factory", "names"),
    [
        (_playlist_tools, ["save_queue_as_playlist", "remove_from_playlist", "reorder_playlist"]),
        (_volume_tools, ["ramp_volume"]),
        (_group_tools, ["create_stereo_pair", "separate_stereo_pair"]),
    ],
)
def test_disabled_tools_not_registered(factory, names):
    tools, _ = factory(disabled=names)

    for name in names:
        assert name not in tools


@pytest.mark.parametrize(
    ("factory", "tool_name", "expected"),
    [
        (_volume_tools, "ramp_volume", ["room", "target", "ramp_type"]),
        (_group_tools, "create_stereo_pair", ["room", "slave_room"]),
        (_group_tools, "separate_stereo_pair", ["room"]),
    ],
)
def test_parameter_names_match_brief(factory, tool_name, expected):
    import inspect

    tools, _ = factory()

    assert list(inspect.signature(tools[tool_name]).parameters) == expected
