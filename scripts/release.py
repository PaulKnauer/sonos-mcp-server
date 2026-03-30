#!/usr/bin/env python3
"""Release helper for semver bumps, git tags, and GitHub releases."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
PROJECT_VERSION_RE = re.compile(
    r'(?m)^(?P<prefix>version\s*=\s*")(?P<version>\d+\.\d+\.\d+)(?P<suffix>")$'
)


def parse_version(raw: str) -> tuple[int, int, int]:
    """Parse a strict semver version without prerelease/build metadata."""
    match = SEMVER_RE.fullmatch(raw.strip())
    if match is None:
        raise ValueError(
            f"Invalid version '{raw}'. Expected strict semver like 1.2.3."
        )
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def bump_version(version: str, part: str) -> str:
    """Return the next semver for the requested bump part."""
    major, minor, patch = parse_version(version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unsupported bump part '{part}'.")


def read_version(pyproject_path: Path) -> str:
    """Read the project version from pyproject.toml."""
    match = PROJECT_VERSION_RE.search(pyproject_path.read_text())
    if match is None:
        raise ValueError(f"Could not find [project].version in {pyproject_path}.")
    return match.group("version")


def replace_version(contents: str, new_version: str) -> str:
    """Replace the project version line with the requested version."""
    parse_version(new_version)
    updated, count = PROJECT_VERSION_RE.subn(
        rf"\g<prefix>{new_version}\g<suffix>",
        contents,
        count=1,
    )
    if count != 1:
        raise ValueError("Expected exactly one project version declaration to update.")
    return updated


def write_version(pyproject_path: Path, new_version: str) -> None:
    """Persist the new version to pyproject.toml."""
    updated = replace_version(pyproject_path.read_text(), new_version)
    pyproject_path.write_text(updated)


def run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run a subprocess and return captured output."""
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def ensure_clean_worktree(repo_root: Path) -> None:
    """Fail if the working tree has uncommitted changes."""
    result = run(["git", "status", "--porcelain"], cwd=repo_root)
    if result.stdout.strip():
        raise RuntimeError("Refusing release action with a dirty git worktree.")


def ensure_tag_absent(repo_root: Path, tag_name: str) -> None:
    """Fail if the target git tag already exists."""
    result = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag_name}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        raise RuntimeError(f"Git tag '{tag_name}' already exists.")


def create_tag(repo_root: Path, version: str, *, dry_run: bool) -> str:
    """Create an annotated release tag for the provided version."""
    parse_version(version)
    tag_name = f"v{version}"
    ensure_clean_worktree(repo_root)
    ensure_tag_absent(repo_root, tag_name)
    if dry_run:
        return f"git tag -a {tag_name} -m 'Release {tag_name}'"
    run(["git", "tag", "-a", tag_name, "-m", f"Release {tag_name}"], cwd=repo_root)
    return tag_name


def create_release(repo_root: Path, version: str, *, dry_run: bool) -> str:
    """Create a GitHub release with generated notes for the provided version."""
    parse_version(version)
    tag_name = f"v{version}"
    command = [
        "gh",
        "release",
        "create",
        tag_name,
        "--verify-tag",
        "--generate-notes",
        "--title",
        tag_name,
    ]
    if dry_run:
        return " ".join(command)
    run(command, cwd=repo_root)
    return tag_name


def build_parser() -> argparse.ArgumentParser:
    """Construct the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Manage SoniqMCP semver bumps, tags, and GitHub releases."
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to pyproject.toml (default: %(default)s).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root for git and gh commands (default: %(default)s).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("current", help="Print the current project version.")

    bump_parser = subparsers.add_parser("bump", help="Bump the project version.")
    bump_parser.add_argument("part", choices=["major", "minor", "patch"])
    bump_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the next version without writing pyproject.toml.",
    )

    set_parser = subparsers.add_parser(
        "set-version", help="Set the project version explicitly."
    )
    set_parser.add_argument("version")
    set_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print the version without writing pyproject.toml.",
    )

    tag_parser = subparsers.add_parser("tag", help="Create an annotated git tag.")
    tag_parser.add_argument(
        "--version",
        help="Version to tag. Defaults to the current pyproject version.",
    )
    tag_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the git tag command without executing it.",
    )

    release_parser = subparsers.add_parser(
        "release", help="Create a GitHub Release for the current version tag."
    )
    release_parser.add_argument(
        "--version",
        help="Version to release. Defaults to the current pyproject version.",
    )
    release_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the gh release command without executing it.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    pyproject_path = args.pyproject.resolve()
    repo_root = args.repo_root.resolve()

    try:
        current_version = read_version(pyproject_path)
        if args.command == "current":
            print(current_version)
            return 0

        if args.command == "bump":
            next_version = bump_version(current_version, args.part)
            if args.dry_run:
                print(next_version)
                return 0
            write_version(pyproject_path, next_version)
            print(next_version)
            return 0

        if args.command == "set-version":
            parse_version(args.version)
            if args.dry_run:
                print(args.version)
                return 0
            write_version(pyproject_path, args.version)
            print(args.version)
            return 0

        if args.command == "tag":
            version = args.version or current_version
            tag_name = create_tag(repo_root, version, dry_run=args.dry_run)
            print(tag_name)
            return 0

        if args.command == "release":
            version = args.version or current_version
            release_name = create_release(repo_root, version, dry_run=args.dry_run)
            print(release_name)
            return 0
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.error("Unhandled command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
