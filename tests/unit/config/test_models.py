"""Unit tests for SoniqConfig typed models and defaults."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from soniq_mcp.config.models import (
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
        assert cfg.config_file is None

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

    def test_optional_config_file_accepts_path(self) -> None:
        cfg = SoniqConfig(config_file="/etc/soniq/config.toml")
        assert cfg.config_file == "/etc/soniq/config.toml"


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
