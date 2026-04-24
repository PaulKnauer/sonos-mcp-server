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


class TestAuthModeEnum:
    def test_auth_mode_none_value(self) -> None:
        from soniq_mcp.config.models import AuthMode

        assert AuthMode.NONE == "none"

    def test_auth_mode_static_value(self) -> None:
        from soniq_mcp.config.models import AuthMode

        assert AuthMode.STATIC == "static"

    def test_auth_mode_oidc_value(self) -> None:
        from soniq_mcp.config.models import AuthMode

        assert AuthMode.OIDC == "oidc"


class TestSoniqConfigAuthDefaults:
    def test_auth_mode_defaults_to_none(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig()
        assert cfg.auth_mode == AuthMode.NONE

    def test_auth_token_defaults_to_none(self) -> None:
        cfg = SoniqConfig()
        assert cfg.auth_token is None

    def test_oidc_fields_default_to_none(self) -> None:
        cfg = SoniqConfig()
        assert cfg.oidc_issuer is None
        assert cfg.oidc_audience is None
        assert cfg.oidc_jwks_uri is None
        assert cfg.oidc_ca_bundle is None
        assert cfg.oidc_resource_url is None


class TestSoniqConfigAuthParsing:
    def test_auth_mode_none_string_accepted(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig(auth_mode="none")
        assert cfg.auth_mode == AuthMode.NONE

    def test_auth_mode_static_string_accepted(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig(auth_mode="static")
        assert cfg.auth_mode == AuthMode.STATIC

    def test_auth_mode_oidc_with_issuer_accepted(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig(auth_mode="oidc", oidc_issuer="https://issuer.example.com")
        assert cfg.auth_mode == AuthMode.OIDC
        assert cfg.oidc_issuer == "https://issuer.example.com"

    def test_invalid_auth_mode_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(auth_mode="bearer")
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("auth_mode",) for e in errors)

    def test_auth_mode_oidc_without_issuer_raises(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(auth_mode="oidc", transport="http")
        error_msg = str(exc_info.value)
        assert "oidc_issuer" in error_msg

    def test_auth_mode_oidc_without_issuer_allowed_for_stdio(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig(auth_mode="oidc", transport="stdio")
        assert cfg.auth_mode == AuthMode.OIDC
        assert cfg.oidc_issuer is None


class TestSoniqConfigAuthTokenMasking:
    def test_auth_token_secret_str_masked_in_repr(self) -> None:
        cfg = SoniqConfig(auth_mode="static", auth_token="super-secret-token")
        assert "super-secret-token" not in repr(cfg)

    def test_auth_token_secret_str_masked_in_model_dump(self) -> None:
        cfg = SoniqConfig(auth_mode="static", auth_token="super-secret-token")
        dumped = cfg.model_dump()
        # SecretStr serializes as the SecretStr object, not raw string
        # The raw value should not appear when converted to string
        assert "super-secret-token" not in str(dumped)

    def test_auth_token_none_accepted(self) -> None:
        cfg = SoniqConfig(auth_mode="static", auth_token=None)
        assert cfg.auth_token is None


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
