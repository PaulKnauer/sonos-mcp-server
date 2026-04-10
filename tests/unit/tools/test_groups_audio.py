"""Unit tests for group-audio MCP tool handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

from soniq_mcp.domain.exceptions import (
    GroupError,
    GroupValidationError,
    RoomNotFoundError,
    SonosDiscoveryError,
    VolumeCapExceeded,
)
from soniq_mcp.domain.models import GroupAudioState


def _make_group_audio_state(
    room_name: str = "Living Room",
    coordinator: str = "Living Room",
    members: tuple = ("Living Room", "Kitchen"),
    volume: int = 40,
    is_muted: bool = False,
) -> GroupAudioState:
    return GroupAudioState(
        room_name=room_name,
        coordinator_room_name=coordinator,
        member_room_names=members,
        volume=volume,
        is_muted=is_muted,
    )


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


def _register_and_get(tool_name, group_service=None, disabled=None):
    from soniq_mcp.tools.groups import register

    app = _make_app()
    config = _make_config(disabled)
    if group_service is None:
        group_service = MagicMock()
    register(app, config, group_service)
    return app._tools.get(tool_name), group_service, config


class TestGetGroupVolumeTool:
    def test_returns_group_audio_state_on_success(self):
        gs = MagicMock()
        gs.get_group_audio_state.return_value = _make_group_audio_state(volume=42)

        fn, _, _ = _register_and_get("get_group_volume", gs)
        result = fn(room="Living Room")

        assert result["volume"] == 42
        assert result["room_name"] == "Living Room"
        assert result["coordinator_room_name"] == "Living Room"
        assert isinstance(result["member_room_names"], list)

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.get_group_audio_state.side_effect = RoomNotFoundError("Living Room")

        fn, _, _ = _register_and_get("get_group_volume", gs)
        result = fn(room="Living Room")

        assert "error" in result
        assert result["field"] == "room"

    def test_group_validation_error_returns_group_error(self):
        gs = MagicMock()
        gs.get_group_audio_state.side_effect = GroupValidationError("not grouped")

        fn, _, _ = _register_and_get("get_group_volume", gs)
        result = fn(room="Office")

        assert "error" in result
        assert result["field"] == "group"

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.get_group_audio_state.side_effect = GroupError("SoCo failure")

        fn, _, _ = _register_and_get("get_group_volume", gs)
        result = fn(room="Living Room")

        assert "error" in result
        assert result["field"] == "group"

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.get_group_audio_state.side_effect = SonosDiscoveryError("no network")

        fn, _, _ = _register_and_get("get_group_volume", gs)
        result = fn(room="Living Room")

        assert "error" in result
        assert result["field"] == "sonos_network"

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("get_group_volume", disabled=["get_group_volume"])
        assert fn is None


class TestSetGroupVolumeTool:
    def test_returns_group_audio_state_on_success(self):
        gs = MagicMock()
        gs.set_group_volume.return_value = _make_group_audio_state(volume=60)

        fn, _, _ = _register_and_get("set_group_volume", gs)
        result = fn(room="Living Room", volume=60)

        gs.set_group_volume.assert_called_once_with("Living Room", 60)
        assert result["volume"] == 60

    def test_volume_cap_exceeded_returns_validation_error(self):
        gs = MagicMock()
        gs.set_group_volume.side_effect = VolumeCapExceeded(requested=90, cap=80)

        fn, _, _ = _register_and_get("set_group_volume", gs)
        result = fn(room="Living Room", volume=90)

        assert "error" in result
        assert result["field"] == "volume"

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.set_group_volume.side_effect = RoomNotFoundError("Living Room")

        fn, _, _ = _register_and_get("set_group_volume", gs)
        result = fn(room="Living Room", volume=50)

        assert "error" in result
        assert result["field"] == "room"

    def test_group_validation_error_returns_group_error(self):
        gs = MagicMock()
        gs.set_group_volume.side_effect = GroupValidationError("not grouped")

        fn, _, _ = _register_and_get("set_group_volume", gs)
        result = fn(room="Office", volume=50)

        assert "error" in result
        assert result["field"] == "group"

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.set_group_volume.side_effect = GroupError("failure")

        fn, _, _ = _register_and_get("set_group_volume", gs)
        result = fn(room="Living Room", volume=50)

        assert "error" in result

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("set_group_volume", disabled=["set_group_volume"])
        assert fn is None


class TestAdjustGroupVolumeTool:
    def test_returns_group_audio_state_on_success(self):
        gs = MagicMock()
        gs.adjust_group_volume.return_value = _make_group_audio_state(volume=45)

        fn, _, _ = _register_and_get("adjust_group_volume", gs)
        result = fn(room="Living Room", delta=5)

        gs.adjust_group_volume.assert_called_once_with("Living Room", 5)
        assert result["volume"] == 45

    def test_volume_cap_exceeded_returns_validation_error(self):
        gs = MagicMock()
        gs.adjust_group_volume.side_effect = VolumeCapExceeded(requested=83, cap=80)

        fn, _, _ = _register_and_get("adjust_group_volume", gs)
        result = fn(room="Living Room", delta=5)

        assert "error" in result
        assert result["field"] == "volume"

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.adjust_group_volume.side_effect = RoomNotFoundError("Living Room")

        fn, _, _ = _register_and_get("adjust_group_volume", gs)
        result = fn(room="Living Room", delta=5)

        assert "error" in result

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("adjust_group_volume", disabled=["adjust_group_volume"])
        assert fn is None


class TestGroupMuteTool:
    def test_returns_group_audio_state_muted_on_success(self):
        gs = MagicMock()
        gs.group_mute.return_value = _make_group_audio_state(is_muted=True)

        fn, _, _ = _register_and_get("group_mute", gs)
        result = fn(room="Living Room")

        gs.group_mute.assert_called_once_with("Living Room")
        assert result["is_muted"] is True

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.group_mute.side_effect = RoomNotFoundError("Living Room")

        fn, _, _ = _register_and_get("group_mute", gs)
        result = fn(room="Living Room")

        assert "error" in result
        assert result["field"] == "room"

    def test_group_validation_error_returns_group_error(self):
        gs = MagicMock()
        gs.group_mute.side_effect = GroupValidationError("not grouped")

        fn, _, _ = _register_and_get("group_mute", gs)
        result = fn(room="Office")

        assert "error" in result
        assert result["field"] == "group"

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.group_mute.side_effect = GroupError("SoCo failure")

        fn, _, _ = _register_and_get("group_mute", gs)
        result = fn(room="Living Room")

        assert "error" in result

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.group_mute.side_effect = SonosDiscoveryError("no network")

        fn, _, _ = _register_and_get("group_mute", gs)
        result = fn(room="Living Room")

        assert "error" in result

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("group_mute", disabled=["group_mute"])
        assert fn is None


class TestGroupUnmuteTool:
    def test_returns_group_audio_state_unmuted_on_success(self):
        gs = MagicMock()
        gs.group_unmute.return_value = _make_group_audio_state(is_muted=False)

        fn, _, _ = _register_and_get("group_unmute", gs)
        result = fn(room="Living Room")

        gs.group_unmute.assert_called_once_with("Living Room")
        assert result["is_muted"] is False

    def test_room_not_found_returns_error(self):
        gs = MagicMock()
        gs.group_unmute.side_effect = RoomNotFoundError("Living Room")

        fn, _, _ = _register_and_get("group_unmute", gs)
        result = fn(room="Living Room")

        assert "error" in result

    def test_group_validation_error_returns_group_error(self):
        gs = MagicMock()
        gs.group_unmute.side_effect = GroupValidationError("not grouped")

        fn, _, _ = _register_and_get("group_unmute", gs)
        result = fn(room="Office")

        assert "error" in result
        assert result["field"] == "group"

    def test_group_error_returns_error_response(self):
        gs = MagicMock()
        gs.group_unmute.side_effect = GroupError("SoCo failure")

        fn, _, _ = _register_and_get("group_unmute", gs)
        result = fn(room="Living Room")

        assert "error" in result

    def test_discovery_error_returns_error_response(self):
        gs = MagicMock()
        gs.group_unmute.side_effect = SonosDiscoveryError("no network")

        fn, _, _ = _register_and_get("group_unmute", gs)
        result = fn(room="Living Room")

        assert "error" in result

    def test_tool_disabled_not_registered(self):
        fn, _, _ = _register_and_get("group_unmute", disabled=["group_unmute"])
        assert fn is None
