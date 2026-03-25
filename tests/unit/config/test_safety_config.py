"""Unit tests for safety-related config fields (AC: 1, 2, 3)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from soniq_mcp.config.models import SoniqConfig


class TestMaxVolumePct:
    def test_default_is_80(self) -> None:
        assert SoniqConfig().max_volume_pct == 80

    def test_custom_cap_accepted(self) -> None:
        assert SoniqConfig(max_volume_pct=50).max_volume_pct == 50

    def test_zero_cap_accepted(self) -> None:
        assert SoniqConfig(max_volume_pct=0).max_volume_pct == 0

    def test_100_cap_accepted(self) -> None:
        assert SoniqConfig(max_volume_pct=100).max_volume_pct == 100

    def test_above_100_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(max_volume_pct=101)
        assert any(e["loc"] == ("max_volume_pct",) for e in exc_info.value.errors())

    def test_negative_rejected(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            SoniqConfig(max_volume_pct=-1)
        assert any(e["loc"] == ("max_volume_pct",) for e in exc_info.value.errors())


class TestToolsDisabled:
    def test_default_is_empty_list(self) -> None:
        assert SoniqConfig().tools_disabled == []

    def test_single_tool_disabled(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        assert cfg.tools_disabled == ["ping"]

    def test_multiple_tools_disabled(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping", "server_info"])
        assert set(cfg.tools_disabled) == {"ping", "server_info"}


class TestLoaderSafetyFields:
    def test_max_volume_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_MAX_VOLUME_PCT", "60")
        from soniq_mcp.config.loader import load_config
        assert load_config().max_volume_pct == 60

    def test_tools_disabled_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SONIQ_MCP_TOOLS_DISABLED", "ping,server_info")
        from soniq_mcp.config.loader import load_config
        cfg = load_config()
        assert set(cfg.tools_disabled) == {"ping", "server_info"}
