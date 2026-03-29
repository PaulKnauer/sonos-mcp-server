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
        result = subprocess.run(
            ["helm", "template", "soniq", str(_CHART_PATH)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"helm template failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert result.stdout.strip(), "helm template produced no output"
