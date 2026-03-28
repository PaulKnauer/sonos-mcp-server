"""Integration tests: HTTP transport bootstrap and tool surface parity (Story 4.1)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from mcp.server.fastmcp import FastMCP

from soniq_mcp.config.models import ExposurePosture, SoniqConfig, TransportMode
from soniq_mcp.domain.safety import validate_exposure_posture
from soniq_mcp.server import create_server
from soniq_mcp.transports.bootstrap import run_transport
from soniq_mcp.transports.streamable_http import streamable_http_transport_name


class TestCreateServerWithHttpConfig:
    def test_create_server_http_transport_succeeds(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_create_server_passes_host_to_fastmcp(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP, http_host="0.0.0.0", http_port=9001)
        app = create_server(config=cfg)
        assert app.settings.host == "0.0.0.0"
        assert app.settings.port == 9001

    def test_create_server_localhost_host_and_port(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP, http_host="127.0.0.1", http_port=9999)
        app = create_server(config=cfg)
        assert app.settings.host == "127.0.0.1"
        assert app.settings.port == 9999

    def test_stdio_server_also_receives_host_port(self) -> None:
        """server.py always passes host/port; stdio transport ignores them."""
        cfg = SoniqConfig(transport=TransportMode.STDIO, http_host="127.0.0.1", http_port=8080)
        app = create_server(config=cfg)
        assert app.settings.host == "127.0.0.1"
        assert app.settings.port == 8080


class TestHttpToolSurfaceParity:
    def test_http_exposes_same_tools_as_stdio(self) -> None:
        http_cfg = SoniqConfig(transport=TransportMode.HTTP)
        stdio_cfg = SoniqConfig(transport=TransportMode.STDIO)
        http_app = create_server(config=http_cfg)
        stdio_app = create_server(config=stdio_cfg)
        http_tools = {t.name for t in http_app._tool_manager.list_tools()}
        stdio_tools = {t.name for t in stdio_app._tool_manager.list_tools()}
        assert http_tools == stdio_tools

    def test_http_server_exposes_ping(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        tool_names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" in tool_names

    def test_http_server_exposes_all_29_tools(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        tool_names = {t.name for t in app._tool_manager.list_tools()}
        # Spot-check key tools from all capability areas
        expected = {
            "ping", "server_info", "list_rooms",
            "play", "pause", "stop", "get_playback_state",
            "get_volume", "set_volume", "mute",
            "get_queue", "add_to_queue", "clear_queue",
            "list_favourites", "play_favourite",
            "get_group_topology", "join_group", "party_mode",
        }
        assert expected.issubset(tool_names)


class TestRunTransportHttpDispatch:
    def test_run_transport_dispatches_to_http(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        with patch("soniq_mcp.transports.streamable_http.run_streamable_http") as mock_run:
            run_transport(app, cfg)
            mock_run.assert_called_once_with(app, cfg)

    def test_run_transport_does_not_raise_for_http(self) -> None:
        """HTTP transport must not hit the NotImplementedError branch."""
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        with patch("soniq_mcp.transports.streamable_http.run_streamable_http"):
            # Should not raise NotImplementedError
            run_transport(app, cfg)

    def test_run_transport_still_raises_for_unknown(self) -> None:
        from unittest.mock import MagicMock
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        bad_cfg = MagicMock()
        bad_cfg.transport.__eq__ = lambda self, other: False
        with pytest.raises(NotImplementedError):
            run_transport(app, bad_cfg)


class TestStreamableHttpTransportName:
    def test_transport_name_is_streamable_http(self) -> None:
        assert streamable_http_transport_name() == "streamable-http"


class TestHomeNetworkExposurePosture:
    def test_home_network_emits_warning(self) -> None:
        cfg = SoniqConfig(exposure=ExposurePosture.HOME_NETWORK, http_host="0.0.0.0", http_port=8000)
        warnings = validate_exposure_posture(cfg)
        assert len(warnings) == 1
        assert "home-network" in warnings[0]
        assert "0.0.0.0" in warnings[0]
        assert "8000" in warnings[0]

    def test_local_exposure_no_warning(self) -> None:
        cfg = SoniqConfig(exposure=ExposurePosture.LOCAL)
        warnings = validate_exposure_posture(cfg)
        assert warnings == []

    def test_unknown_exposure_emits_unsupported_warning(self) -> None:
        """Simulates a future posture value not yet fully supported."""
        cfg = SoniqConfig(exposure=ExposurePosture.LOCAL)
        # Bypass pydantic to test the safety function with a fake posture
        object.__setattr__(cfg, "exposure", type("FakePosture", (), {"value": "public"})())
        warnings = validate_exposure_posture(cfg)
        assert len(warnings) == 1
        assert "not yet fully supported" in warnings[0]

    def test_home_network_warning_mentions_host_and_port(self) -> None:
        cfg = SoniqConfig(
            exposure=ExposurePosture.HOME_NETWORK,
            http_host="192.168.1.50",
            http_port=8765,
        )
        warnings = validate_exposure_posture(cfg)
        assert "192.168.1.50" in warnings[0]
        assert "8765" in warnings[0]
