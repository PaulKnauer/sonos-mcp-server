"""Unit tests for the config loader (env var resolution and normalization)."""

from __future__ import annotations

from pathlib import Path

import pytest

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import ExposurePosture, LogLevel, SoniqConfig, TransportMode

_ALL_ENV_KEYS = [
    "SONIQ_MCP_TRANSPORT",
    "SONIQ_MCP_EXPOSURE",
    "SONIQ_MCP_LOG_LEVEL",
    "SONIQ_MCP_DEFAULT_ROOM",
    "SONIQ_MCP_MAX_VOLUME_PCT",
    "SONIQ_MCP_TOOLS_DISABLED",
    "SONIQ_MCP_AUTH_MODE",
    "SONIQ_MCP_AUTH_TOKEN",
    "SONIQ_MCP_OIDC_ISSUER",
    "SONIQ_MCP_OIDC_AUDIENCE",
    "SONIQ_MCP_OIDC_JWKS_URI",
    "SONIQ_MCP_OIDC_CA_BUNDLE",
    "SONIQ_MCP_OIDC_RESOURCE_URL",
]


@pytest.fixture(autouse=True)
def _clear_soniq_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no pre-existing SONIQ_MCP_* vars bleed into any test."""
    for key in _ALL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


class TestLoadConfigDefaults:
    def test_returns_soniq_config_instance(self) -> None:
        cfg = load_config()
        assert isinstance(cfg, SoniqConfig)

    def test_defaults_without_env(self) -> None:
        cfg = load_config()
        assert cfg.transport == TransportMode.STDIO
        assert cfg.exposure == ExposurePosture.LOCAL
        assert cfg.log_level == LogLevel.INFO
        assert cfg.default_room is None


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


class TestLoadConfigFromDotenv:
    def test_loads_values_from_project_dotenv(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text(
            "\n".join(
                [
                    "SONIQ_MCP_LOG_LEVEL=DEBUG",
                    "SONIQ_MCP_DEFAULT_ROOM=Kitchen",
                    "SONIQ_MCP_MAX_VOLUME_PCT=55",
                ]
            )
        )

        cfg = load_config()

        assert cfg.log_level == LogLevel.DEBUG
        assert cfg.default_room == "Kitchen"
        assert cfg.max_volume_pct == 55

    def test_environment_variables_override_project_dotenv(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("SONIQ_MCP_LOG_LEVEL=DEBUG\n")
        monkeypatch.setenv("SONIQ_MCP_LOG_LEVEL", "ERROR")

        cfg = load_config()

        assert cfg.log_level == LogLevel.ERROR


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

    def test_unknown_override_key_raises_validation_error(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            load_config(overrides={"loglevel": "DEBUG"})

    def test_whitespace_only_override_treated_as_none(self) -> None:
        cfg = load_config(overrides={"default_room": "   "})
        assert cfg.default_room is None


class TestLoadConfigAuthEnvVars:
    def test_auth_mode_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from soniq_mcp.config.models import AuthMode

        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "static")
        assert load_config().auth_mode == AuthMode.STATIC

    def test_auth_mode_defaults_to_none_without_env(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = load_config()
        assert cfg.auth_mode == AuthMode.NONE

    def test_auth_token_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "static")
        monkeypatch.setenv("SONIQ_MCP_AUTH_TOKEN", "my-secret-token")
        cfg = load_config()
        assert cfg.auth_token is not None
        assert str(cfg.auth_token) == "**********"
        assert "my-secret-token" not in repr(cfg)

    def test_oidc_issuer_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "oidc")
        monkeypatch.setenv("SONIQ_MCP_OIDC_ISSUER", "https://issuer.example.com")
        cfg = load_config()
        assert cfg.oidc_issuer == "https://issuer.example.com"

    def test_oidc_audience_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "oidc")
        monkeypatch.setenv("SONIQ_MCP_OIDC_ISSUER", "https://issuer.example.com")
        monkeypatch.setenv("SONIQ_MCP_OIDC_AUDIENCE", "my-api")
        cfg = load_config()
        assert cfg.oidc_audience == "my-api"

    def test_oidc_jwks_uri_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "oidc")
        monkeypatch.setenv("SONIQ_MCP_OIDC_ISSUER", "https://issuer.example.com")
        monkeypatch.setenv(
            "SONIQ_MCP_OIDC_JWKS_URI", "https://issuer.example.com/.well-known/jwks.json"
        )
        cfg = load_config()
        assert cfg.oidc_jwks_uri == "https://issuer.example.com/.well-known/jwks.json"

    def test_oidc_ca_bundle_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "oidc")
        monkeypatch.setenv("SONIQ_MCP_OIDC_ISSUER", "https://issuer.example.com")
        monkeypatch.setenv("SONIQ_MCP_OIDC_CA_BUNDLE", "/etc/ssl/certs/ca.pem")
        cfg = load_config()
        assert cfg.oidc_ca_bundle == "/etc/ssl/certs/ca.pem"

    def test_oidc_resource_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_AUTH_MODE", "oidc")
        monkeypatch.setenv("SONIQ_MCP_OIDC_ISSUER", "https://issuer.example.com")
        monkeypatch.setenv("SONIQ_MCP_OIDC_RESOURCE_URL", "https://soniq.example.com")
        cfg = load_config()
        assert cfg.oidc_resource_url == "https://soniq.example.com"

    def test_whitespace_only_oidc_issuer_normalizes_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_OIDC_ISSUER", "   ")
        cfg = load_config()
        assert cfg.oidc_issuer is None

    def test_whitespace_only_oidc_audience_normalizes_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_OIDC_AUDIENCE", "  ")
        cfg = load_config()
        assert cfg.oidc_audience is None

    def test_whitespace_only_oidc_jwks_uri_normalizes_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_OIDC_JWKS_URI", "  ")
        cfg = load_config()
        assert cfg.oidc_jwks_uri is None

    def test_whitespace_only_oidc_ca_bundle_normalizes_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_OIDC_CA_BUNDLE", "  ")
        cfg = load_config()
        assert cfg.oidc_ca_bundle is None

    def test_whitespace_only_oidc_resource_url_normalizes_to_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_OIDC_RESOURCE_URL", "  ")
        cfg = load_config()
        assert cfg.oidc_resource_url is None
