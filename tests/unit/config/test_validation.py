"""Unit tests for startup preflight validation."""

from __future__ import annotations

import pytest

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.config.validation import ConfigValidationError, run_preflight


class TestRunPreflightSuccess:
    def test_valid_defaults_pass(self) -> None:
        cfg = run_preflight()
        assert isinstance(cfg, SoniqConfig)

    def test_valid_overrides_pass(self) -> None:
        cfg = run_preflight(overrides={"log_level": "DEBUG"})
        assert cfg.log_level.value == "DEBUG"


class TestRunPreflightFailure:
    def test_invalid_transport_raises_config_validation_error(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"transport": "grpc"})
        assert len(exc_info.value.messages) > 0

    def test_invalid_log_level_raises_config_validation_error(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"log_level": "VERBOSE"})
        assert len(exc_info.value.messages) > 0

    def test_error_message_identifies_field(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"transport": "grpc"})
        assert "transport" in exc_info.value.messages[0]

    def test_config_validation_error_is_value_error(self) -> None:
        with pytest.raises(ValueError):
            run_preflight(overrides={"transport": "bad"})

    def test_messages_are_safe_no_internal_detail(self) -> None:
        """Error messages must not leak host, token, or path information."""
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"transport": "grpc"})
        for msg in exc_info.value.messages:
            assert "/workdir" not in msg
            assert "token" not in msg.lower()


class TestRunPreflightAuthValidation:
    def test_unsupported_auth_mode_raises_config_validation_error(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "oauth2"})
        assert len(exc_info.value.messages) > 0

    def test_oidc_without_issuer_raises_config_validation_error(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "oidc", "transport": "http"})
        assert len(exc_info.value.messages) > 0
        assert any("oidc_issuer" in msg for msg in exc_info.value.messages)

    def test_oidc_without_issuer_allowed_for_stdio(self) -> None:
        cfg = run_preflight(overrides={"auth_mode": "oidc", "transport": "stdio"})
        from soniq_mcp.config.models import AuthMode

        assert cfg.auth_mode == AuthMode.OIDC
        assert cfg.oidc_issuer is None

    def test_valid_static_auth_mode_passes(self) -> None:
        cfg = run_preflight(overrides={"auth_mode": "static"})
        from soniq_mcp.config.models import AuthMode

        assert cfg.auth_mode == AuthMode.STATIC

    def test_valid_oidc_auth_mode_with_issuer_passes(self) -> None:
        cfg = run_preflight(
            overrides={"auth_mode": "oidc", "oidc_issuer": "https://issuer.example.com"}
        )
        from soniq_mcp.config.models import AuthMode

        assert cfg.auth_mode == AuthMode.OIDC

    def test_static_http_without_token_raises_config_validation_error(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "static", "transport": "http"})
        assert len(exc_info.value.messages) > 0

    def test_static_http_without_token_message_names_missing_field(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "static", "transport": "http"})
        assert any("auth_token" in msg for msg in exc_info.value.messages)

    def test_static_http_without_token_messages_contain_only_field_names(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "static", "transport": "http"})
        for msg in exc_info.value.messages:
            # Messages must reference field names, not raw secret values
            assert "auth_token" in msg
            # Must be human-readable, not a raw dump or traceback fragment
            assert "Traceback" not in msg
            assert "SecretStr" not in msg

    def test_static_stdio_without_token_does_not_raise(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = run_preflight(overrides={"auth_mode": "static", "transport": "stdio"})
        assert cfg.auth_mode == AuthMode.STATIC

    def test_auth_none_with_http_passes(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = run_preflight(
            overrides={
                "auth_mode": "none",
                "transport": "http",
                "exposure": "home-network",
                "http_host": "0.0.0.0",
            }
        )
        assert cfg.auth_mode == AuthMode.NONE

    def test_static_http_with_token_passes(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = run_preflight(
            overrides={
                "auth_mode": "static",
                "transport": "http",
                "auth_token": "a-valid-token",
                "exposure": "home-network",
                "http_host": "0.0.0.0",
            }
        )
        assert cfg.auth_mode == AuthMode.STATIC
