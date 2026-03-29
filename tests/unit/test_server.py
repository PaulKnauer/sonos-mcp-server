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
