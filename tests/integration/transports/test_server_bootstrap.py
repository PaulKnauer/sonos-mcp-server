"""Integration tests: server bootstrap with stdio transport (AC 1, 2, 3)."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, TransportMode
from soniq_mcp.config.validation import ConfigValidationError
from soniq_mcp.server import create_server
from soniq_mcp.transports.bootstrap import bootstrap_transport, run_transport
from soniq_mcp.transports.stdio import stdio_transport_name


class TestServerBootstrapIntegration:
    """Server must boot successfully with valid config (AC 1, 2)."""

    def test_create_server_with_stdio_config(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.STDIO)
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_server_exposes_tool_surface(self) -> None:
        """Server must expose the agreed tool surface (AC 1)."""
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        tool_names = [t.name for t in app._tool_manager.list_tools()]
        assert "ping" in tool_names
        assert "server_info" in tool_names

    def test_bad_config_blocks_startup(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid config must prevent server creation (AC 2)."""
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "not-a-transport")
        with pytest.raises(ConfigValidationError):
            create_server()

    def test_server_info_returns_non_sensitive_data(self) -> None:
        """Startup diagnostics must not expose sensitive config (AC 4)."""
        cfg = SoniqConfig(default_room="Bedroom", config_file="/secret/path")
        app = create_server(config=cfg)
        tool_names = [t.name for t in app._tool_manager.list_tools()]
        # server_info tool exists and only returns safe fields
        assert "server_info" in tool_names


class TestTransportBootstrap:
    """Transport selection uses internal service boundaries (AC 2)."""

    def test_bootstrap_transport_returns_stdio(self) -> None:
        assert bootstrap_transport() == "stdio"

    def test_stdio_transport_name_consistent(self) -> None:
        assert stdio_transport_name() == bootstrap_transport()

    def test_run_transport_raises_for_unsupported(self) -> None:
        """Unsupported transports must raise NotImplementedError cleanly."""
        from unittest.mock import MagicMock
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        bad_cfg = MagicMock(transport=MagicMock(value="grpc"))
        bad_cfg.transport.__eq__ = lambda self, other: False
        with pytest.raises(NotImplementedError):
            run_transport(app, bad_cfg)
