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

EXPECTED_TOOL_NAMES = {
    "add_to_queue",
    "adjust_volume",
    "clear_queue",
    "get_group_topology",
    "get_mute",
    "get_playback_state",
    "get_queue",
    "get_system_topology",
    "get_track_info",
    "get_volume",
    "join_group",
    "list_favourites",
    "list_playlists",
    "list_rooms",
    "mute",
    "next_track",
    "party_mode",
    "pause",
    "ping",
    "play",
    "play_favourite",
    "play_from_queue",
    "play_playlist",
    "previous_track",
    "remove_from_queue",
    "server_info",
    "set_volume",
    "set_play_mode",
    "get_play_mode",
    "seek",
    "get_sleep_timer",
    "set_sleep_timer",
    "get_eq_settings",
    "set_bass",
    "set_treble",
    "set_loudness",
    "stop",
    "unjoin_room",
    "unmute",
}

REPRESENTATIVE_TOOL_NAMES = (
    "ping",
    "server_info",
    "list_rooms",
    "play",
    "set_volume",
    "party_mode",
)


def _tool_index(app: FastMCP) -> dict[str, object]:
    return {tool.name: tool for tool in app._tool_manager.list_tools()}


class TestCreateServerWithHttpConfig:
    def test_create_server_http_transport_succeeds(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)

    def test_create_server_passes_host_to_fastmcp(self) -> None:
        cfg = SoniqConfig(
            transport=TransportMode.HTTP,
            exposure=ExposurePosture.HOME_NETWORK,
            http_host="0.0.0.0",
            http_port=9001,
        )
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

    def test_http_server_exposes_all_34_tools(self) -> None:
        """Verify exact tool-surface parity for Story 4.1 + Story 1.1 play mode + Story 1.2 seek/sleep timer."""
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        app = create_server(config=cfg)
        tool_names = {t.name for t in app._tool_manager.list_tools()}
        assert tool_names == EXPECTED_TOOL_NAMES

    def test_representative_tool_metadata_matches_stdio(self) -> None:
        """Representative tools should keep stable metadata across transports."""
        http_tools = _tool_index(create_server(config=SoniqConfig(transport=TransportMode.HTTP)))
        stdio_tools = _tool_index(create_server(config=SoniqConfig(transport=TransportMode.STDIO)))

        for name in REPRESENTATIVE_TOOL_NAMES:
            http_tool = http_tools[name]
            stdio_tool = stdio_tools[name]
            assert http_tool.annotations == stdio_tool.annotations
            assert http_tool.parameters == stdio_tool.parameters
            assert getattr(http_tool, "output_schema", None) == getattr(
                stdio_tool, "output_schema", None
            )


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
        cfg = SoniqConfig(
            exposure=ExposurePosture.HOME_NETWORK, http_host="0.0.0.0", http_port=8000
        )
        warnings = validate_exposure_posture(cfg)
        assert len(warnings) == 1
        assert "home-network" in warnings[0]
        assert "0.0.0.0" in warnings[0]
        assert "8000" in warnings[0]

    def test_local_exposure_no_warning(self) -> None:
        cfg = SoniqConfig(exposure=ExposurePosture.LOCAL)
        warnings = validate_exposure_posture(cfg)
        assert warnings == []

    def test_local_http_non_loopback_bind_emits_warning(self) -> None:
        cfg = SoniqConfig.model_construct(
            transport=TransportMode.HTTP,
            exposure=ExposurePosture.LOCAL,
            log_level="INFO",
            default_room=None,
            config_file=None,
            max_volume_pct=80,
            tools_disabled=[],
            http_host="0.0.0.0",
            http_port=8000,
        )
        warnings = validate_exposure_posture(cfg)
        assert len(warnings) == 1
        assert "unsafe" in warnings[0]

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
