"""Unit tests for the config loader (env var resolution and normalization)."""

from __future__ import annotations

import pytest

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import ExposurePosture, LogLevel, SoniqConfig, TransportMode


class TestLoadConfigDefaults:
    def test_returns_soniq_config_instance(self) -> None:
        cfg = load_config()
        assert isinstance(cfg, SoniqConfig)

    def test_defaults_without_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for key in ["SONIQ_MCP_TRANSPORT", "SONIQ_MCP_EXPOSURE",
                    "SONIQ_MCP_LOG_LEVEL", "SONIQ_MCP_DEFAULT_ROOM",
                    "SONIQ_MCP_CONFIG_FILE"]:
            monkeypatch.delenv(key, raising=False)
        cfg = load_config()
        assert cfg.transport == TransportMode.STDIO
        assert cfg.exposure == ExposurePosture.LOCAL
        assert cfg.log_level == LogLevel.INFO
        assert cfg.default_room is None
        assert cfg.config_file is None


class TestLoadConfigFromEnv:
    def test_transport_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "stdio")
        assert load_config().transport == TransportMode.STDIO

    def test_log_level_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_LOG_LEVEL", "DEBUG")
        assert load_config().log_level == LogLevel.DEBUG

    def test_default_room_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_DEFAULT_ROOM", "Kitchen")
        assert load_config().default_room == "Kitchen"

    def test_empty_env_var_treated_as_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_DEFAULT_ROOM", "")
        assert load_config().default_room is None

    def test_whitespace_only_env_var_treated_as_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_DEFAULT_ROOM", "   ")
        assert load_config().default_room is None


class TestLoadConfigOverrides:
    def test_override_wins_over_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_LOG_LEVEL", "ERROR")
        cfg = load_config(overrides={"log_level": "DEBUG"})
        assert cfg.log_level == LogLevel.DEBUG

    def test_override_transport(self) -> None:
        cfg = load_config(overrides={"transport": "stdio"})
        assert cfg.transport == TransportMode.STDIO

    def test_invalid_override_raises_validation_error(self) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            load_config(overrides={"transport": "not-a-transport"})
