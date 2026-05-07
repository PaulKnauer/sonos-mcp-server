"""Unit tests for server composition boundary."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP
from starlette.routing import Route

from soniq_mcp.config import SoniqConfig
from soniq_mcp.config.validation import ConfigValidationError
from soniq_mcp.server import create_server


class TestCreateServer:
    def test_returns_fastmcp_instance(self) -> None:
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_accepts_injected_config(self) -> None:
        cfg = SoniqConfig(log_level="DEBUG")
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_bad_config_raises_before_server_created(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SoniqConfig(transport="bad-transport")

    def test_preflight_error_propagates_when_no_config_given(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "not-a-transport")
        from soniq_mcp.config.validation import ConfigValidationError

        with pytest.raises(ConfigValidationError):
            create_server()


class TestToolRegistration:
    def test_ping_tool_registered(self) -> None:
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        tool_names = [t.name for t in app._tool_manager.list_tools()]
        assert "ping" in tool_names

    def test_server_info_tool_registered(self) -> None:
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        tool_names = [t.name for t in app._tool_manager.list_tools()]
        assert "server_info" in tool_names


class TestDisabledAuthNoOp:
    """auth_mode=none must be a strict no-op in server construction (AC 1, 2, 3, 4)."""

    def test_disabled_auth_returns_fastmcp(self) -> None:
        cfg = SoniqConfig(auth_mode="none")
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_disabled_auth_settings_auth_is_none(self) -> None:
        """FastMCP.settings.auth must remain None when auth_mode=none (AC 1, 4)."""
        cfg = SoniqConfig(auth_mode="none")
        app = create_server(config=cfg)
        assert app.settings.auth is None

    def test_disabled_auth_token_verifier_is_none(self) -> None:
        """No token verifier must be attached when auth_mode=none (AC 1, 4)."""
        cfg = SoniqConfig(auth_mode="none")
        app = create_server(config=cfg)
        assert app._token_verifier is None

    def test_disabled_auth_seam_not_invoked(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Future auth-builder seam must not be called for auth_mode=none (AC 4).

        Patches the module-level symbol that future auth wiring will call, and
        asserts it is never invoked when auth is disabled.
        """
        called: list[object] = []

        import soniq_mcp.server as server_mod

        monkeypatch.setattr(server_mod, "_build_auth_kwargs", lambda cfg: called.append(cfg) or {})
        cfg = SoniqConfig(auth_mode="none")
        create_server(config=cfg)
        assert called == [], "_build_auth_kwargs must not be called for auth_mode=none"

    def test_disabled_auth_registers_tools(self) -> None:
        """Tool registration must proceed unchanged for auth_mode=none (AC 2, 3)."""
        cfg = SoniqConfig(auth_mode="none")
        app = create_server(config=cfg)
        tool_names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" in tool_names
        assert "server_info" in tool_names

    def test_stdio_static_auth_is_ignored(self) -> None:
        """Stdio must ignore configured static auth instead of wiring FastMCP auth."""
        cfg = SoniqConfig(transport="stdio", auth_mode="static", auth_token="test-token-unit")
        app = create_server(config=cfg)
        assert app.settings.auth is None
        assert app._token_verifier is None

    def test_stdio_oidc_auth_is_ignored(self) -> None:
        """Stdio must ignore configured OIDC auth even when HTTP OIDC is wired."""
        cfg = SoniqConfig(transport="stdio", auth_mode="oidc")
        app = create_server(config=cfg)
        assert app.settings.auth is None
        assert app._token_verifier is None


class TestStaticAuthWiring:
    """auth_mode=static must wire FastMCP auth settings and token verifier (AC 1, 2, 3)."""

    def _static_cfg(self, **kwargs) -> SoniqConfig:  # type: ignore[type-arg]
        values = {"transport": "http", "auth_mode": "static", "auth_token": "test-token-unit"}
        values.update(kwargs)
        return SoniqConfig(**values)

    def test_static_auth_sets_settings_auth(self) -> None:
        """FastMCP.settings.auth must be populated when auth_mode=static (AC 1)."""
        app = create_server(config=self._static_cfg())
        assert app.settings.auth is not None

    def test_static_auth_sets_token_verifier(self) -> None:
        """FastMCP._token_verifier must be set when auth_mode=static (AC 1)."""
        app = create_server(config=self._static_cfg())
        assert app._token_verifier is not None

    def test_static_auth_issuer_url_uses_config_host_and_port(self) -> None:
        """issuer_url must be derived from configured http_host and http_port (AC 2)."""
        app = create_server(config=self._static_cfg(http_host="127.0.0.1", http_port=9123))
        issuer = str(app.settings.auth.issuer_url)
        assert issuer.startswith("http://127.0.0.1:9123")

    def test_static_auth_issuer_url_brackets_ipv6_host(self) -> None:
        """IPv6 hosts must be bracketed before constructing AuthSettings issuer_url."""
        app = create_server(config=self._static_cfg(http_host="::1", http_port=9123))
        issuer = str(app.settings.auth.issuer_url)
        assert issuer.startswith("http://[::1]:9123")

    def test_static_auth_registers_tools(self) -> None:
        """Tool registration must proceed unchanged when auth_mode=static (AC 3)."""
        app = create_server(config=self._static_cfg())
        tool_names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" in tool_names
        assert "server_info" in tool_names


class TestDiagnosticSafety:
    """Serialization and repr must not leak auth secrets (AC 5)."""

    def test_default_config_dumps_cleanly(self) -> None:
        """Default SoniqConfig serializes without errors and auth_token is None."""
        cfg = SoniqConfig()
        dumped = cfg.model_dump()
        assert dumped["auth_token"] is None

    def test_config_with_token_masks_value_in_repr(self) -> None:
        """SecretStr masks the token in repr so secrets don't leak (AC 5)."""
        cfg = SoniqConfig(auth_mode="static", auth_token="supersecret")
        r = repr(cfg)
        assert "supersecret" not in r

    def test_config_with_token_masks_value_in_model_dump_json(self) -> None:
        """model_dump_json uses SecretStr masking semantics by default."""
        cfg = SoniqConfig(auth_mode="static", auth_token="supersecret")
        json_str = cfg.model_dump_json()
        assert "supersecret" not in json_str


class TestOIDCAuthWiring:
    """HTTP OIDC must wire FastMCP auth settings and token verifier (Story 3.3 AC: 1, 5, 6)."""

    def _oidc_cfg(self, **kwargs: object) -> SoniqConfig:
        values: dict = {
            "transport": "http",
            "auth_mode": "oidc",
            "oidc_issuer": "https://issuer.example.com",
            "oidc_audience": "soniq-mcp",
            "oidc_jwks_uri": "https://issuer.example.com/.well-known/jwks.json",
        }
        values.update(kwargs)
        return SoniqConfig(**values)

    def _mock_oidc_preflight_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda *args, **kwargs: _ServerMockResponse(
                b'{"keys": [{"kty": "RSA", "kid": "kid-1", "n": "abc", "e": "AQAB"}]}'
            ),
        )

    def test_http_oidc_sets_settings_auth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTTP OIDC must populate FastMCP.settings.auth (AC 1)."""
        self._mock_oidc_preflight_success(monkeypatch)
        app = create_server(config=self._oidc_cfg())
        assert app.settings.auth is not None

    def test_http_oidc_sets_token_verifier(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """HTTP OIDC must attach a token verifier (AC 1)."""
        self._mock_oidc_preflight_success(monkeypatch)
        app = create_server(config=self._oidc_cfg())
        assert app._token_verifier is not None

    def test_http_oidc_issuer_url_uses_oidc_issuer_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """issuer_url must come from oidc_issuer, not from http_host:http_port (AC 1)."""
        self._mock_oidc_preflight_success(monkeypatch)
        app = create_server(config=self._oidc_cfg())
        issuer = str(app.settings.auth.issuer_url)
        assert "issuer.example.com" in issuer

    def test_http_oidc_resource_server_url_is_none_when_not_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """resource_server_url=None is acceptable when oidc_resource_url is unset (AC 5).

        FastMCP only creates protected-resource metadata routes when a concrete
        resource_server_url is configured, so leaving this as None is a valid
        runtime path rather than a latent startup failure.
        """
        self._mock_oidc_preflight_success(monkeypatch)
        app = create_server(config=self._oidc_cfg())
        assert app.settings.auth.resource_server_url is None
        route_paths = {
            route.path for route in app.streamable_http_app().routes if isinstance(route, Route)
        }
        assert "/.well-known/oauth-protected-resource/mcp" not in route_paths

    def test_http_oidc_resource_server_url_uses_config_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Explicit oidc_resource_url propagates to AuthSettings (AC 6)."""
        self._mock_oidc_preflight_success(monkeypatch)
        app = create_server(config=self._oidc_cfg(oidc_resource_url="https://resource.example.com"))
        assert app.settings.auth.resource_server_url is not None
        route_paths = {
            route.path for route in app.streamable_http_app().routes if isinstance(route, Route)
        }
        assert "/.well-known/oauth-protected-resource" in route_paths

    def test_http_oidc_injected_config_discovers_missing_jwks_uri(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Injected configs must get the same discovery prep as env-loaded configs."""
        cfg = self._oidc_cfg(oidc_jwks_uri=None)

        responses = [
            _ServerMockResponse(b'{"jwks_uri": "https://issuer.example.com/jwks.json"}'),
            _ServerMockResponse(
                b'{"keys": [{"kty": "RSA", "kid": "kid-1", "n": "abc", "e": "AQAB"}]}'
            ),
        ]
        call_count = {"value": 0}

        def mock_urlopen(*args: object, **kwargs: object) -> _ServerMockResponse:
            idx = call_count["value"]
            call_count["value"] += 1
            return responses[idx]

        monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)
        app = create_server(config=cfg)
        assert app._token_verifier is not None
        assert cfg.oidc_jwks_uri == "https://issuer.example.com/jwks.json"

    def test_http_oidc_injected_config_rejects_invalid_resource_url(self) -> None:
        """Injected configs must fail before runtime when resource URL is malformed."""
        cfg = self._oidc_cfg(oidc_resource_url="not-a-url")
        with pytest.raises(ConfigValidationError):
            create_server(config=cfg)

    def test_http_oidc_registers_tools(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Tool registration must proceed unchanged when auth_mode=oidc (AC 1)."""
        self._mock_oidc_preflight_success(monkeypatch)
        app = create_server(config=self._oidc_cfg())
        tool_names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" in tool_names
        assert "server_info" in tool_names

    def test_static_auth_issuer_still_uses_host_and_port(self) -> None:
        """Static auth issuer derivation must remain unchanged after OIDC wiring."""
        cfg = SoniqConfig(
            transport="http",
            auth_mode="static",
            auth_token="t",
            http_host="127.0.0.1",
            http_port=9999,
        )
        app = create_server(config=cfg)
        issuer = str(app.settings.auth.issuer_url)
        assert issuer.startswith("http://127.0.0.1:9999")


class _ServerMockResponse:
    """Minimal context-manager response for urllib.request.urlopen mocking."""

    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _ServerMockResponse:
        return self

    def __exit__(self, *args: object) -> None:
        pass
