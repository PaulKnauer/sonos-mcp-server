"""Unit tests: HTTP transport config fields and env var loading (Story 4.1)."""

from __future__ import annotations

import pytest

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import ExposurePosture, SoniqConfig, TransportMode


class TestTransportModeEnum:
    def test_http_value(self) -> None:
        assert TransportMode.HTTP == "http"

    def test_stdio_value_unchanged(self) -> None:
        assert TransportMode.STDIO == "stdio"

    def test_http_is_valid_transport(self) -> None:
        cfg = SoniqConfig(transport=TransportMode.HTTP)
        assert cfg.transport == TransportMode.HTTP

    def test_invalid_transport_rejected(self) -> None:
        with pytest.raises(Exception):
            SoniqConfig(transport="grpc")  # type: ignore[arg-type]


class TestExposurePostureEnum:
    def test_home_network_value(self) -> None:
        assert ExposurePosture.HOME_NETWORK == "home-network"

    def test_local_value_unchanged(self) -> None:
        assert ExposurePosture.LOCAL == "local"

    def test_home_network_is_valid_posture(self) -> None:
        cfg = SoniqConfig(exposure=ExposurePosture.HOME_NETWORK)
        assert cfg.exposure == ExposurePosture.HOME_NETWORK

    def test_invalid_exposure_rejected(self) -> None:
        with pytest.raises(Exception):
            SoniqConfig(exposure="public")  # type: ignore[arg-type]


class TestHttpHostField:
    def test_default_is_localhost(self) -> None:
        cfg = SoniqConfig()
        assert cfg.http_host == "127.0.0.1"

    def test_custom_host_accepted(self) -> None:
        cfg = SoniqConfig(http_host="0.0.0.0")
        assert cfg.http_host == "0.0.0.0"

    def test_arbitrary_ip_accepted(self) -> None:
        cfg = SoniqConfig(http_host="192.168.1.100")
        assert cfg.http_host == "192.168.1.100"


class TestHttpPortField:
    def test_default_is_8000(self) -> None:
        cfg = SoniqConfig()
        assert cfg.http_port == 8000

    def test_custom_port_accepted(self) -> None:
        cfg = SoniqConfig(http_port=9000)
        assert cfg.http_port == 9000

    def test_port_1_accepted(self) -> None:
        cfg = SoniqConfig(http_port=1)
        assert cfg.http_port == 1

    def test_port_65535_accepted(self) -> None:
        cfg = SoniqConfig(http_port=65535)
        assert cfg.http_port == 65535

    def test_port_0_rejected(self) -> None:
        with pytest.raises(Exception):
            SoniqConfig(http_port=0)

    def test_port_65536_rejected(self) -> None:
        with pytest.raises(Exception):
            SoniqConfig(http_port=65536)


class TestHttpEnvVarLoading:
    def test_http_host_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_HTTP_HOST", "0.0.0.0")
        cfg = load_config()
        assert cfg.http_host == "0.0.0.0"

    def test_http_port_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_HTTP_PORT", "9876")
        cfg = load_config()
        assert cfg.http_port == 9876

    def test_http_port_coerced_from_string(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_HTTP_PORT", "7777")
        cfg = load_config()
        assert isinstance(cfg.http_port, int)
        assert cfg.http_port == 7777

    def test_transport_http_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "http")
        cfg = load_config()
        assert cfg.transport == TransportMode.HTTP

    def test_exposure_home_network_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_EXPOSURE", "home-network")
        cfg = load_config()
        assert cfg.exposure == ExposurePosture.HOME_NETWORK

    def test_defaults_used_when_no_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SONIQ_MCP_HTTP_HOST", raising=False)
        monkeypatch.delenv("SONIQ_MCP_HTTP_PORT", raising=False)
        cfg = load_config()
        assert cfg.http_host == "127.0.0.1"
        assert cfg.http_port == 8000
