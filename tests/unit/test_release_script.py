"""Tests for the release helper script."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tarfile
from pathlib import Path
from zipfile import ZipFile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "release.py"
SPEC = importlib.util.spec_from_file_location("release_script", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
release_script = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release_script)

PUBLISH_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "publish.yml"
COMMAND_REFERENCE = REPO_ROOT / "docs" / "prompts" / "command-reference.md"
PROMPTS_GUIDE = REPO_ROOT / "docs" / "prompts" / "example-uses.md"
OPERATIONS_GUIDE = REPO_ROOT / "docs" / "setup" / "operations.md"
RELEASE_CANONICAL_ASSETS = (
    REPO_ROOT / "README.md",
    COMMAND_REFERENCE,
    PROMPTS_GUIDE,
    OPERATIONS_GUIDE,
    REPO_ROOT / "docs" / "setup" / "troubleshooting.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tracked_repo_paths(paths: tuple[Path, ...]) -> set[str]:
    relative_paths = [path.relative_to(REPO_ROOT).as_posix() for path in paths]
    result = subprocess.run(
        ["git", "ls-files", "--", *relative_paths],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def _contains_ordered_lines(text: str, expected_lines: list[str]) -> bool:
    remaining = iter(expected_lines)
    current = next(remaining, None)
    for line in text.splitlines():
        if current is None:
            return True
        if line.strip() == current:
            current = next(remaining, None)
    return current is None


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


def test_release_canonical_assets_exist_in_tagged_repo_checkout() -> None:
    tracked_paths = _tracked_repo_paths(RELEASE_CANONICAL_ASSETS)
    expected_paths = {path.relative_to(REPO_ROOT).as_posix() for path in RELEASE_CANONICAL_ASSETS}

    assert tracked_paths == expected_paths
    assert COMMAND_REFERENCE.relative_to(REPO_ROOT).as_posix() in tracked_paths
    assert PROMPTS_GUIDE.relative_to(REPO_ROOT).as_posix() in tracked_paths


def test_publish_workflow_releases_from_tagged_repo_checkout() -> None:
    workflow = _read(PUBLISH_WORKFLOW)
    assert _contains_ordered_lines(workflow, ["on:", "push:", "tags:", '- "v*.*.*"'])
    assert "publish-pypi:" in workflow
    assert "publish-docker:" in workflow
    assert "create-github-release:" in workflow
    assert workflow.count("uses: actions/checkout@v4") >= 3
    assert "run: make build-check" in workflow
    assert 'gh release view "$GITHUB_REF_NAME"' in workflow
    assert 'gh release create "$GITHUB_REF_NAME"' in workflow


def test_built_package_artifacts_do_not_include_docs_tree(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    if uv is None:
        pytest.skip("uv is required to inspect built package artifacts")

    dist_dir = tmp_path / "dist"
    subprocess.run(
        [uv, "build", "--out-dir", str(dist_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    wheel_path = next(dist_dir.glob("*.whl"))
    sdist_path = next(dist_dir.glob("*.tar.gz"))

    with ZipFile(wheel_path) as wheel:
        wheel_names = wheel.namelist()

    with tarfile.open(sdist_path) as sdist:
        sdist_names = sdist.getnames()

    assert not any(name.startswith("docs/") for name in wheel_names)
    assert not any("/docs/" in name for name in sdist_names)
