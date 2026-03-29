"""Smoke tests: Helm chart lint and template rendering (Story 4.3, AC 1, 2, 3).

Validates the Helm chart structure and template rendering using the helm CLI.
These tests are skipped automatically when the `helm` CLI is not available.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parents[3]
_CHART_PATH = _PROJECT_ROOT / "helm" / "soniq"

pytestmark = pytest.mark.skipif(
    shutil.which("helm") is None,
    reason="helm CLI not found — skipping Helm smoke tests",
)


class TestHelmSmoke:
    """Helm chart must lint cleanly and render valid templates (AC 1, 2, 3)."""

    def _run_helm_template(self, *extra_args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["helm", "template", "soniq", str(_CHART_PATH), *extra_args],
            capture_output=True,
            text=True,
        )

    def test_helm_lint_passes(self) -> None:
        result = subprocess.run(
            ["helm", "lint", str(_CHART_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"helm lint failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_helm_template_renders(self) -> None:
        result = self._run_helm_template()
        assert result.returncode == 0, (
            f"helm template failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert result.stdout.strip(), "helm template produced no output"

    def test_helm_template_surfaces_all_supported_env_vars(self) -> None:
        result = self._run_helm_template(
            "--set",
            "config.transport=http",
            "--set",
            "config.httpHost=0.0.0.0",
            "--set",
            "config.httpPort=8010",
            "--set",
            "config.exposure=home-network",
            "--set",
            "config.logLevel=DEBUG",
            "--set",
            "config.maxVolumePct=65",
            "--set-string",
            r"config.toolsDisabled=ping\,server_info",
            "--set-string",
            "config.configFile=/config/soniq.env",
            "--set-string",
            "secret.defaultRoom=Kitchen",
        )
        assert result.returncode == 0, (
            f"helm template failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        for expected in (
            'SONIQ_MCP_TRANSPORT: "http"',
            'SONIQ_MCP_HTTP_HOST: "0.0.0.0"',
            'SONIQ_MCP_HTTP_PORT: "8010"',
            'SONIQ_MCP_EXPOSURE: "home-network"',
            'SONIQ_MCP_LOG_LEVEL: "DEBUG"',
            'SONIQ_MCP_MAX_VOLUME_PCT: "65"',
            'SONIQ_MCP_TOOLS_DISABLED: "ping,server_info"',
            'SONIQ_MCP_CONFIG_FILE: "/config/soniq.env"',
            'SONIQ_MCP_DEFAULT_ROOM: "Kitchen"',
        ):
            assert expected in result.stdout

    def test_helm_template_aligns_container_and_service_ports(self) -> None:
        result = self._run_helm_template(
            "--set",
            "config.httpPort=9000",
            "--set",
            "service.port=9000",
        )
        assert result.returncode == 0, (
            f"helm template failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "containerPort: 9000" in result.stdout
        assert "targetPort: 9000" in result.stdout
        assert "port: 9000" in result.stdout
