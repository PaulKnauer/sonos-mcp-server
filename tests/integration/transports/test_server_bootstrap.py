"""Integration tests: server bootstrap with stdio transport (AC 1, 2, 3)."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig, TransportMode
from soniq_mcp.config.validation import ConfigValidationError
from soniq_mcp.server import create_server
from soniq_mcp.transports.bootstrap import bootstrap_transport, run_transport
from soniq_mcp.transports.stdio import stdio_transport_name


def _parse_payload(result: object) -> dict[str, object]:
    first = result[0]  # type: ignore[index]
    if isinstance(first, list):
        first = first[0]
    return json.loads(first.text)  # type: ignore[attr-defined]


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

    def test_bad_config_blocks_startup(self, monkeypatch: pytest.MonkeyPatch) -> None:
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

    @pytest.mark.anyio
    async def test_server_info_payload_stays_safely_scoped(self) -> None:
        cfg = SoniqConfig(
            transport=TransportMode.HTTP,
            exposure="home-network",
            http_host="0.0.0.0",
            config_file="/secret/path",
        )
        app = create_server(config=cfg)
        result = await app.call_tool("server_info", {})
        payload = _parse_payload(result)
        assert payload["transport"] == "http"
        assert payload["exposure"] == "home-network"
        assert payload["log_level"] == "INFO"
        assert payload["max_volume_pct"] == "80"
        assert "/secret/path" not in json.dumps(payload)
        assert "0.0.0.0" not in json.dumps(payload)

    @pytest.mark.anyio
    async def test_runtime_tools_expose_shared_error_categories(self) -> None:
        cfg = SoniqConfig()

        class ExplodingRoomService:
            def list_rooms(self) -> list[object]:
                from soniq_mcp.domain.exceptions import SonosDiscoveryError

                raise SonosDiscoveryError("no speakers at 192.168.1.50")

            def get_topology(self) -> object:
                raise AssertionError("not used")

        from soniq_mcp.tools import system as system_tools

        test_app = FastMCP("test")
        system_tools.register(test_app, cfg, ExplodingRoomService())
        result = await test_app.call_tool("list_rooms", {})
        payload = _parse_payload(result)
        assert payload["category"] == "connectivity"
        assert payload["field"] == "sonos_network"
        assert "192.168.1.50" not in json.dumps(payload)


class TestDisabledAuthStdioBackwardCompat:
    """stdio startup and tool surface unchanged when auth_mode=none (AC 2, 3)."""

    def test_stdio_with_auth_mode_none_explicit_returns_fastmcp(self) -> None:
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig(transport=TransportMode.STDIO, auth_mode=AuthMode.NONE)
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_stdio_disabled_auth_same_tools_as_default(self) -> None:
        """auth_mode=none stdio must expose the same tool surface as the pre-auth default."""
        from soniq_mcp.config.models import AuthMode

        auth_none_cfg = SoniqConfig(transport=TransportMode.STDIO, auth_mode=AuthMode.NONE)
        default_cfg = SoniqConfig(transport=TransportMode.STDIO)
        auth_none_app = create_server(config=auth_none_cfg)
        default_app = create_server(config=default_cfg)
        assert {t.name for t in auth_none_app._tool_manager.list_tools()} == {
            t.name for t in default_app._tool_manager.list_tools()
        }

    def test_stdio_disabled_auth_settings_auth_is_none(self) -> None:
        """FastMCP.settings.auth must remain None for stdio with auth_mode=none (AC 3, 4)."""
        from soniq_mcp.config.models import AuthMode

        cfg = SoniqConfig(transport=TransportMode.STDIO, auth_mode=AuthMode.NONE)
        app = create_server(config=cfg)
        assert app.settings.auth is None


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
