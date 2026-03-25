"""Smoke tests: entry point startup behaviour (AC 1, 3, 4).

Tests call main() directly (no subprocess) for reliability in all
container environments.  The key properties under test are:
  - bad config → clean sys.exit(1), not a traceback
  - stderr messages identify the offending field
  - modules import without side-effects
"""

from __future__ import annotations

import sys
from io import StringIO

import pytest


class TestModuleImportSmoke:
    """Packages must be importable without side-effects."""

    def test_main_package_importable(self) -> None:
        import soniq_mcp  # noqa: F401

    def test_main_module_importable(self) -> None:
        import soniq_mcp.__main__  # noqa: F401

    def test_server_module_importable(self) -> None:
        import soniq_mcp.server  # noqa: F401


class TestEntrypointBadConfig:
    """Invalid config must cause exit(1) with field-level diagnostics (AC 2, 4)."""

    def test_bad_transport_exits_nonzero(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "not-a-transport")
        from soniq_mcp.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_bad_transport_stderr_names_field(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "grpc")
        from soniq_mcp.__main__ import main

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "transport" in captured.err
        assert "configuration error" in captured.err

    def test_bad_config_no_traceback_in_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """Error output must be human-readable, not a Python traceback (AC 4)."""
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "bad")
        from soniq_mcp.__main__ import main

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "Traceback" not in captured.err
        assert "fix the above errors" in captured.err
