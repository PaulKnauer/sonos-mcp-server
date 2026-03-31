"""Tests for the release helper script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "release.py"
SPEC = importlib.util.spec_from_file_location("release_script", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
release_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_script)


def test_parse_version_accepts_strict_semver() -> None:
    assert release_script.parse_version("1.2.3") == (1, 2, 3)


@pytest.mark.parametrize("version", ["1.2", "1.2.3-rc1", "01.2.3", "a.b.c"])
def test_parse_version_rejects_non_strict_semver(version: str) -> None:
    with pytest.raises(ValueError):
        release_script.parse_version(version)


@pytest.mark.parametrize(
    ("current", "part", "expected"),
    [
        ("0.1.0", "patch", "0.1.1"),
        ("0.1.9", "minor", "0.2.0"),
        ("0.9.9", "major", "1.0.0"),
    ],
)
def test_bump_version_returns_expected_semver(current: str, part: str, expected: str) -> None:
    assert release_script.bump_version(current, part) == expected


def test_read_and_write_version_round_trip(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        '[project]\nname = "soniq-mcp"\nversion = "0.1.0"\ndescription = "test"\n'
    )

    assert release_script.read_version(pyproject_path) == "0.1.0"
    release_script.write_version(pyproject_path, "0.2.0")
    assert release_script.read_version(pyproject_path) == "0.2.0"


def test_replace_version_updates_single_declaration() -> None:
    contents = '[project]\nversion = "0.1.0"\n'
    assert release_script.replace_version(contents, "0.1.1") == '[project]\nversion = "0.1.1"\n'
