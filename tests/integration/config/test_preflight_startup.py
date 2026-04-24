"""Integration tests: startup preflight blocks bad config before runtime."""

from __future__ import annotations

import pytest

from soniq_mcp.config.validation import ConfigValidationError, run_preflight

_ALL_ENV_KEYS = [
    "SONIQ_MCP_TRANSPORT",
    "SONIQ_MCP_EXPOSURE",
    "SONIQ_MCP_LOG_LEVEL",
    "SONIQ_MCP_DEFAULT_ROOM",
    "SONIQ_MCP_AUTH_MODE",
    "SONIQ_MCP_AUTH_TOKEN",
    "SONIQ_MCP_OIDC_ISSUER",
]


@pytest.fixture(autouse=True)
def _clear_soniq_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no pre-existing SONIQ_MCP_* vars bleed into any test."""
    for key in _ALL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


class TestPreflightBlocksBadStartup:
    """Invalid config must prevent normal runtime from proceeding (AC 2, 3)."""

    def test_bad_transport_blocks_startup(self) -> None:
        """Normal runtime must not start when transport is unrecognised."""
        with pytest.raises(ConfigValidationError):
            run_preflight(overrides={"transport": "websocket"})

    def test_bad_log_level_blocks_startup(self) -> None:
        with pytest.raises(ConfigValidationError):
            run_preflight(overrides={"log_level": "TRACE"})

    def test_bad_exposure_blocks_startup(self) -> None:
        with pytest.raises(ConfigValidationError):
            run_preflight(overrides={"exposure": "internet"})

    def test_error_names_the_bad_field(self) -> None:
        """Field-level error messages must identify the offending field (AC 3)."""
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"log_level": "TRACE"})
        assert any("log_level" in m for m in exc_info.value.messages)

    def test_valid_env_config_does_not_block_startup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Happy-path: good env vars must not raise."""
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "stdio")
        monkeypatch.setenv("SONIQ_MCP_LOG_LEVEL", "WARNING")
        cfg = run_preflight()
        assert cfg.transport.value == "stdio"


class TestPreflightAuthBlocking:
    """Auth preflight must block bad config and allow clean config (AC 1, 2, 3, 4)."""

    def test_static_http_without_token_blocks_startup(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "static", "transport": "http"})
        assert len(exc_info.value.messages) > 0
        assert any("auth_token" in m for m in exc_info.value.messages)

    def test_oidc_http_without_issuer_blocks_startup(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "oidc", "transport": "http"})
        assert any("oidc_issuer" in m for m in exc_info.value.messages)

    def test_auth_none_http_does_not_block_startup(self) -> None:
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

    def test_static_stdio_does_not_block_startup(self) -> None:
        cfg = run_preflight(overrides={"auth_mode": "static", "transport": "stdio"})
        assert cfg is not None

    def test_auth_error_messages_reference_field_names_not_secrets(self) -> None:
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides={"auth_mode": "static", "transport": "http"})
        for msg in exc_info.value.messages:
            assert "auth_token" in msg
            assert "SecretStr" not in msg
            assert "Traceback" not in msg


class TestSingleHouseholdScope:
    """Config must be scoped to single-household use (AC 4)."""

    def test_exposure_is_local_by_default(self) -> None:
        cfg = run_preflight()
        assert cfg.exposure.value == "local"

    def test_default_room_is_optional(self) -> None:
        cfg = run_preflight()
        assert cfg.default_room is None

    def test_single_room_override_accepted(self) -> None:
        cfg = run_preflight(overrides={"default_room": "Lounge"})
        assert cfg.default_room == "Lounge"
