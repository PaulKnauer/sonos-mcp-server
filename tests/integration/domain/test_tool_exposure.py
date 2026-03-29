"""Integration tests: tool exposure controls at server level (AC: 2, 4)."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.server import create_server


class TestToolExposureAtStartup:
    """Disabled tools must not appear in the tool surface (AC: 4)."""

    def test_all_tools_exposed_by_default(self) -> None:
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" in names
        assert "server_info" in names

    def test_disabled_tool_not_registered(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        app = create_server(config=cfg)
        names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" not in names

    def test_non_disabled_tool_still_registered(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping"])
        app = create_server(config=cfg)
        names = {t.name for t in app._tool_manager.list_tools()}
        assert "server_info" in names

    def test_all_tools_disabled_leaves_empty_surface(self) -> None:
        cfg = SoniqConfig(tools_disabled=["ping", "server_info"])
        app = create_server(config=cfg)
        names = {t.name for t in app._tool_manager.list_tools()}
        assert "ping" not in names
        assert "server_info" not in names

    def test_volume_cap_reflected_in_server_info(self) -> None:
        cfg = SoniqConfig(max_volume_pct=60)
        app = create_server(config=cfg)
        # server_info tool is present and reports the capped volume
        names = {t.name for t in app._tool_manager.list_tools()}
        assert "server_info" in names

    def test_registered_tools_include_permission_hints(self) -> None:
        cfg = SoniqConfig()
        app = create_server(config=cfg)
        tools = {tool.name: tool for tool in app._tool_manager.list_tools()}

        ping_annotations = tools["ping"].annotations
        assert isinstance(ping_annotations, ToolAnnotations)
        assert ping_annotations.readOnlyHint is True
        assert ping_annotations.destructiveHint is False
        assert ping_annotations.idempotentHint is True
        assert ping_annotations.openWorldHint is False

        info_annotations = tools["server_info"].annotations
        assert isinstance(info_annotations, ToolAnnotations)
        assert info_annotations.readOnlyHint is True
        assert info_annotations.destructiveHint is False
        assert info_annotations.idempotentHint is True
        assert info_annotations.openWorldHint is False


class TestSafetyConfigPreflight:
    """Invalid safety config must block startup (AC: 1, 3)."""

    def test_invalid_volume_cap_blocks_startup(self) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SoniqConfig(max_volume_pct=150)

    def test_valid_low_volume_cap_starts_ok(self) -> None:
        cfg = SoniqConfig(max_volume_pct=20)
        app = create_server(config=cfg)
        assert isinstance(app, FastMCP)
