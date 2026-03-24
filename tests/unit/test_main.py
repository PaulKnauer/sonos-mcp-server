"""Unit tests for the __main__ entry point."""

from __future__ import annotations

import sys

import pytest

from soniq_mcp.__main__ import main
from soniq_mcp.config.validation import ConfigValidationError


def test_main_exits_on_bad_config(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Bad env config must cause sys.exit(1) before scaffold message is printed."""
    monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "websocket")
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "config error" in captured.err


def test_main_prints_scaffold_on_valid_config(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Valid config must reach the scaffold print without raising."""
    for key in ["SONIQ_MCP_TRANSPORT", "SONIQ_MCP_EXPOSURE", "SONIQ_MCP_LOG_LEVEL", "SONIQ_MCP_DEFAULT_ROOM"]:
        monkeypatch.delenv(key, raising=False)
    main()
    captured = capsys.readouterr()
    assert "scaffold ready" in captured.out
