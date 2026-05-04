"""Unit tests for bearer token verifiers."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import Any

import pytest
from mcp.server.auth.provider import AccessToken, TokenVerifier
from pydantic import SecretStr

from soniq_mcp.auth import build_token_verifier
from soniq_mcp.auth.verifiers import StaticBearerVerifier
from soniq_mcp.config import SoniqConfig
from soniq_mcp.config.models import AuthMode


def config_with_static_token() -> SoniqConfig:
    return SoniqConfig(auth_mode=AuthMode.STATIC, auth_token=SecretStr("shared-secret"))


def run_verify(verifier: TokenVerifier, token: str | None) -> AccessToken | None:
    presented_token: Any = token
    return asyncio.run(verifier.verify_token(presented_token))


def test_build_token_verifier_returns_static_verifier_for_static_auth() -> None:
    verifier = build_token_verifier(config_with_static_token())

    assert isinstance(verifier, StaticBearerVerifier)


def test_matching_token_returns_access_token() -> None:
    verifier = build_token_verifier(config_with_static_token())

    token = run_verify(verifier, "shared-secret")

    assert token == AccessToken(
        token="shared-secret",
        client_id="static-token-client",
        scopes=[],
    )


def test_missing_empty_whitespace_and_incorrect_tokens_return_none() -> None:
    verifier = build_token_verifier(config_with_static_token())

    assert run_verify(verifier, None) is None
    assert run_verify(verifier, "") is None
    assert run_verify(verifier, "   ") is None
    assert run_verify(verifier, "wrong-secret") is None
    assert run_verify(verifier, "é") is None


def test_non_ascii_configured_token_returns_none() -> None:
    cfg = SoniqConfig(auth_mode=AuthMode.STATIC, auth_token=SecretStr("sécret"))
    verifier = build_token_verifier(cfg)

    assert run_verify(verifier, "sécret") is None


def test_static_verifier_uses_compare_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    calls: list[tuple[bytes, bytes]] = []

    def fake_compare_digest(configured: bytes, presented: bytes) -> bool:
        calls.append((configured, presented))
        return True

    monkeypatch.setattr(verifier_mod.secrets, "compare_digest", fake_compare_digest)

    verifier = build_token_verifier(config_with_static_token())

    assert run_verify(verifier, "presented-secret") is not None
    assert calls == [(b"shared-secret", b"presented-secret")]


def test_secret_unwrapping_is_confined_to_static_verify_token() -> None:
    source_root = Path(__file__).parents[3] / "src" / "soniq_mcp"
    secret_attr = "get_secret_value"
    matches: list[tuple[str, str | None]] = []

    for path in source_root.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == secret_attr:
                function_name: str | None = None
                current: ast.AST | None = node
                while current is not None:
                    if isinstance(current, ast.FunctionDef | ast.AsyncFunctionDef):
                        function_name = current.name
                        break
                    current = parents.get(current)
                matches.append((path.relative_to(source_root).as_posix(), function_name))

    assert matches == [("auth/verifiers.py", "verify_token")]
