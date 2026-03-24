"""Smoke tests: process start and basic response behaviour (AC 1, 3, 4)."""

from __future__ import annotations

import subprocess
import sys

import pytest


class TestEntrypointSmoke:
    """__main__ entry point must be reachable and fail-safe (AC 1, 3)."""

    def test_module_is_importable(self) -> None:
        """Package must import without side-effects."""
        import soniq_mcp  # noqa: F401

    def test_main_module_is_importable(self) -> None:
        import soniq_mcp.__main__  # noqa: F401

    def test_bad_config_exits_nonzero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Invalid config must cause a clean exit(1), not a traceback (AC 4)."""
        result = subprocess.run(
            [sys.executable, "-m", "soniq_mcp"],
            env={
                **__import__("os").environ,
                "SONIQ_MCP_TRANSPORT": "not-a-transport",
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        # Error output must name the bad field
        assert "transport" in result.stderr
        # Must not expose internal paths or stack traces
        assert "Traceback" not in result.stderr

    def test_bad_config_stderr_contains_guidance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "soniq_mcp"],
            env={
                **__import__("os").environ,
                "SONIQ_MCP_TRANSPORT": "grpc",
            },
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "configuration error" in result.stderr
