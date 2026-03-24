"""Unit tests for startup preflight validation."""

from __future__ import annotations

import pytest

from soniq_mcp.config.models import SoniqConfig, TransportMode
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
