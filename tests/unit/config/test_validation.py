"""Unit tests for startup preflight validation."""

from __future__ import annotations

import pytest

from soniq_mcp.config.models import AuthMode, SoniqConfig
from soniq_mcp.config.validation import (
    ConfigValidationError,
    _build_discovery_url,
    run_preflight,
)


class _MockResponse:
    """Minimal context-manager response for urllib.request.urlopen mocking."""

    def __init__(self, body: bytes = b'{"keys": []}') -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _MockResponse:
        return self

    def __exit__(self, *args: object) -> None:
        pass


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


class TestOIDCPreflightValidation:
    """OIDC startup preflight must validate connectivity and surface actionable errors."""

    def _oidc_http(self, **extra: object) -> dict:
        base: dict = {
            "transport": "http",
            "auth_mode": "oidc",
            "oidc_issuer": "https://issuer.example.com",
            "oidc_audience": "soniq-mcp",
            "oidc_jwks_uri": "https://issuer.example.com/.well-known/jwks.json",
            "exposure": "home-network",
            "http_host": "0.0.0.0",
        }
        base.update(extra)
        return base

    def test_explicit_jwks_uri_success_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 1: reachable explicit JWKS URI must allow startup to succeed."""
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _MockResponse(b'{"keys": []}'),
        )
        cfg = run_preflight(overrides=self._oidc_http())
        assert cfg.auth_mode == AuthMode.OIDC

    def test_discovery_when_jwks_uri_absent_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 4: missing oidc_jwks_uri must trigger discovery from oidc_issuer."""
        call_count = [0]
        responses = [
            b'{"jwks_uri": "https://issuer.example.com/.well-known/jwks.json"}',
            b'{"keys": []}',
        ]

        def mock_urlopen(*args: object, **kwargs: object) -> _MockResponse:
            resp = responses[call_count[0]]
            call_count[0] += 1
            return _MockResponse(resp)

        monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)
        overrides = {k: v for k, v in self._oidc_http().items() if k != "oidc_jwks_uri"}
        cfg = run_preflight(overrides=overrides)
        assert cfg.auth_mode == AuthMode.OIDC
        assert call_count[0] == 2
        assert cfg.oidc_jwks_uri == "https://issuer.example.com/.well-known/jwks.json"

    def test_unreachable_jwks_blocks_startup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 2: unreachable JWKS endpoint must block HTTP startup."""
        import urllib.error

        def raise_network(*args: object, **kwargs: object) -> None:
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr("urllib.request.urlopen", raise_network)
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides=self._oidc_http())
        msgs = exc_info.value.messages
        assert any("OIDC JWKS preflight failed" in m for m in msgs)
        assert any("Category: network" in m for m in msgs)

    def test_tls_failure_has_actionable_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 3: TLS trust failure must include URL, category, likely cause, and docs ref."""
        import ssl
        import urllib.error

        def raise_tls(*args: object, **kwargs: object) -> None:
            raise urllib.error.URLError(ssl.SSLError("CERTIFICATE_VERIFY_FAILED"))

        monkeypatch.setattr("urllib.request.urlopen", raise_tls)
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides=self._oidc_http())
        msgs = exc_info.value.messages
        assert any("URL:" in m for m in msgs)
        assert any("Category: tls" in m for m in msgs)
        assert any("Likely cause:" in m for m in msgs)
        assert any("Docs:" in m for m in msgs)

    def test_invalid_issuer_is_reported_as_configuration_error(self) -> None:
        """Malformed issuer values must fail as config errors, not discovery errors."""
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(
                overrides=self._oidc_http(
                    oidc_jwks_uri=None,
                    oidc_issuer="not-a-url",
                )
            )
        msgs = exc_info.value.messages
        assert any("Category: configuration" in m for m in msgs)
        assert any("OIDC issuer must be an absolute" in m for m in msgs)

    def test_invalid_resource_url_is_reported_during_preflight(self) -> None:
        """Bad oidc_resource_url values must not wait until server wiring to fail."""
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(
                overrides=self._oidc_http(
                    oidc_resource_url="not-a-url",
                )
            )
        msgs = exc_info.value.messages
        assert any("Category: configuration" in m for m in msgs)
        assert any("OIDC resource URL must be an absolute" in m for m in msgs)

    def test_stdio_oidc_does_not_run_network_check(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 1 (stdio): stdio with OIDC config must not fail startup or make network calls."""
        calls: list[object] = []

        def fail_if_called(*args: object, **kwargs: object) -> None:
            calls.append(args)
            raise RuntimeError("urlopen must not be called for stdio")

        monkeypatch.setattr("urllib.request.urlopen", fail_if_called)
        cfg = run_preflight(
            overrides={
                "transport": "stdio",
                "auth_mode": "oidc",
                "oidc_issuer": "https://issuer.example.com",
                "oidc_jwks_uri": "https://issuer.example.com/.well-known/jwks.json",
            }
        )
        assert calls == []
        assert cfg.auth_mode == AuthMode.OIDC

    def test_error_messages_contain_no_secrets(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 7: preflight error messages must never include bearer tokens or secret values."""
        import urllib.error

        def raise_network(*args: object, **kwargs: object) -> None:
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr("urllib.request.urlopen", raise_network)
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides=self._oidc_http())
        for msg in exc_info.value.messages:
            assert "SecretStr" not in msg
            assert "Traceback" not in msg
            assert "supersecret" not in msg

    def test_discovery_unreachable_blocks_startup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """AC 2: unreachable discovery endpoint must block startup with actionable message."""
        import urllib.error

        def raise_network(*args: object, **kwargs: object) -> None:
            raise urllib.error.URLError("Connection refused")

        monkeypatch.setattr("urllib.request.urlopen", raise_network)
        overrides = {k: v for k, v in self._oidc_http().items() if k != "oidc_jwks_uri"}
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides=overrides)
        msgs = exc_info.value.messages
        assert any("OIDC JWKS preflight failed" in m for m in msgs)
        assert any(".well-known/openid-configuration" in m for m in msgs)

    def test_invalid_ca_bundle_reports_explicit_jwks_target(self) -> None:
        """Explicit JWKS validation must keep the reported URL aligned with the target."""
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(
                overrides=self._oidc_http(
                    oidc_jwks_uri="https://issuer.example.com/jwks.json",
                    oidc_ca_bundle="/definitely/missing.pem",
                )
            )
        msgs = exc_info.value.messages
        assert any("URL: https://issuer.example.com/jwks.json" in m for m in msgs)
        assert any("Configuration target: /definitely/missing.pem" in m for m in msgs)

    def test_non_https_jwks_uri_blocks_startup(self) -> None:
        """Runtime-only-safe HTTPS JWKS URIs must be enforced during preflight."""
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(
                overrides=self._oidc_http(
                    oidc_jwks_uri="http://issuer.example.com/.well-known/jwks.json"
                )
            )
        msgs = exc_info.value.messages
        assert any("Category: configuration" in m for m in msgs)
        assert any("https://" in m for m in msgs)

    def test_invalid_jwks_document_blocks_startup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Reachable JWKS endpoints must still return a valid JWKS document."""
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *a, **kw: _MockResponse(b'{"not_keys": []}'),
        )
        with pytest.raises(ConfigValidationError) as exc_info:
            run_preflight(overrides=self._oidc_http())
        msgs = exc_info.value.messages
        assert any("Category: discovery" in m for m in msgs)
        assert any("keys' list" in m for m in msgs)

    def test_discovery_url_uses_well_known_path_rules(self) -> None:
        """Issuer paths must be preserved after the well-known prefix."""
        assert (
            _build_discovery_url("https://issuer.example.com/tenant-a")
            == "https://issuer.example.com/.well-known/openid-configuration/tenant-a"
        )
