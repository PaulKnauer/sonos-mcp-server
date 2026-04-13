"""Unit tests for SoniqConfig typed models and defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from soniq_mcp.config.models import (
    KNOWN_TOOL_NAMES,
    ExposurePosture,
    LogLevel,
    SoniqConfig,
    TransportMode,
)


class TestSoniqConfigDefaults:
    def test_all_defaults_are_safe(self) -> None:
        cfg = SoniqConfig()
        assert cfg.transport == TransportMode.STDIO
        assert cfg.exposure == ExposurePosture.LOCAL
        assert cfg.log_level == LogLevel.INFO
        assert cfg.default_room is None

    def test_transport_default_is_stdio(self) -> None:
        assert SoniqConfig().transport == TransportMode.STDIO

    def test_exposure_default_is_local(self) -> None:
        assert SoniqConfig().exposure == ExposurePosture.LOCAL


class TestSoniqConfigValidValues:
    def test_valid_transport_stdio(self) -> None:
        cfg = SoniqConfig(transport="stdio")
        assert cfg.transport == TransportMode.STDIO

    def test_valid_exposure_local(self) -> None:
        cfg = SoniqConfig(exposure="local")
        assert cfg.exposure == ExposurePosture.LOCAL

    @pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR"])
    def test_valid_log_levels(self, level: str) -> None:
        cfg = SoniqConfig(log_level=level)
        assert cfg.log_level.value == level

    def test_optional_default_room_accepts_string(self) -> None:
        cfg = SoniqConfig(default_room="Living Room")
        assert cfg.default_room == "Living Room"


class TestSoniqConfigInvalidValues:
    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(transport="grpc")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("transport",) for e in errors)

    def test_invalid_exposure_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(exposure="public")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("exposure",) for e in errors)

    def test_invalid_log_level_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(log_level="VERBOSE")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("log_level",) for e in errors)

    def test_whitespace_stripped_from_optional_string(self) -> None:
        cfg = SoniqConfig(default_room="  Bedroom  ")
        assert cfg.default_room == "Bedroom"

    def test_config_file_is_supported(self) -> None:
        cfg = SoniqConfig(config_file="/etc/soniq/config.toml")
        assert cfg.config_file == "/etc/soniq/config.toml"

    def test_unknown_field_raises(self) -> None:
        with pytest.raises(ValidationError):
            SoniqConfig(not_a_real_field="value")


class TestKnownToolNames:
    def test_phase_two_tool_names_are_present(self) -> None:
        expected_phase_two_tools = {
            "get_play_mode",
            "set_play_mode",
            "seek",
            "get_sleep_timer",
            "set_sleep_timer",
            "get_eq_settings",
            "set_bass",
            "set_treble",
            "set_loudness",
            "switch_to_line_in",
            "switch_to_tv",
            "get_group_volume",
            "set_group_volume",
            "adjust_group_volume",
            "group_mute",
            "group_unmute",
            "group_rooms",
            "list_alarms",
            "create_alarm",
            "update_alarm",
            "delete_alarm",
            "create_playlist",
            "update_playlist",
            "delete_playlist",
            "browse_library",
            "play_library_item",
        }
        assert expected_phase_two_tools <= KNOWN_TOOL_NAMES
