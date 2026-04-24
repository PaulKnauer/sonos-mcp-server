"""Unit tests for server composition boundary."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
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
