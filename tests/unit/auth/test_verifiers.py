"""Unit tests for bearer token verifiers."""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path
from typing import Any

import pytest
from jwt import PyJWTError
from mcp.server.auth.provider import AccessToken, TokenVerifier
from pydantic import SecretStr

from soniq_mcp.auth import build_token_verifier
from soniq_mcp.auth.verifiers import OIDCVerifier, StaticBearerVerifier
from soniq_mcp.config import SoniqConfig
from soniq_mcp.config.models import AuthMode, TransportMode


def config_with_static_token() -> SoniqConfig:
    return SoniqConfig(auth_mode=AuthMode.STATIC, auth_token=SecretStr("shared-secret"))


def config_with_oidc() -> SoniqConfig:
    return SoniqConfig(
        transport=TransportMode.HTTP,
        auth_mode=AuthMode.OIDC,
        oidc_issuer="https://issuer.example.com/",
        oidc_audience="soniq-mcp",
        oidc_jwks_uri="https://issuer.example.com/jwks.json",
    )


def config_with_oidc_missing_claim_enforcement() -> SoniqConfig:
    return SoniqConfig(
        transport=TransportMode.HTTP,
        auth_mode=AuthMode.OIDC,
        oidc_issuer="https://issuer.example.com/",
        oidc_jwks_uri="https://issuer.example.com/jwks.json",
    )


def run_verify(verifier: TokenVerifier, token: str | None) -> AccessToken | None:
    presented_token: Any = token
    return asyncio.run(verifier.verify_token(presented_token))


def test_build_token_verifier_returns_static_verifier_for_static_auth() -> None:
    verifier = build_token_verifier(config_with_static_token())

    assert isinstance(verifier, StaticBearerVerifier)


def test_build_token_verifier_returns_oidc_verifier_for_oidc_auth() -> None:
    verifier = build_token_verifier(config_with_oidc())

    assert isinstance(verifier, OIDCVerifier)


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


def test_build_token_verifier_raises_for_none_auth_mode() -> None:
    cfg = SoniqConfig(auth_mode=AuthMode.NONE)
    with pytest.raises(NotImplementedError):
        build_token_verifier(cfg)


def test_unconfigured_auth_token_returns_none_for_any_presented_token() -> None:
    cfg = SoniqConfig(auth_mode=AuthMode.STATIC)  # auth_token=None, bypassing preflight
    verifier = StaticBearerVerifier(cfg)

    assert run_verify(verifier, "any-token") is None
    assert run_verify(verifier, "shared-secret") is None
    assert run_verify(verifier, "") is None


def test_presented_token_with_surrounding_whitespace_is_rejected() -> None:
    # compare_digest uses raw bytes; no strip means "  shared-secret  " != "shared-secret"
    verifier = build_token_verifier(config_with_static_token())

    assert run_verify(verifier, "  shared-secret  ") is None
    assert run_verify(verifier, " shared-secret") is None
    assert run_verify(verifier, "shared-secret ") is None


def test_whitespace_only_configured_token_always_returns_none() -> None:
    cfg = SoniqConfig(auth_mode=AuthMode.STATIC, auth_token=SecretStr("   "))
    verifier = StaticBearerVerifier(cfg)

    assert run_verify(verifier, "   ") is None
    assert run_verify(verifier, "anything") is None


def test_oidc_verifier_constructs_jwk_client_once(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    init_calls: list[str] = []

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            init_calls.append(uri)

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    verifier = OIDCVerifier(config_with_oidc())

    assert init_calls == ["https://issuer.example.com/jwks.json"]
    assert isinstance(verifier, OIDCVerifier)


def test_valid_oidc_token_maps_scope_string_sub_and_exp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    captured_tokens: list[str] = []

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            captured_tokens.append(token)
            return FakeSigningKey()

    def fake_decode(
        token: str,
        key: str,
        algorithms: list[str],
        audience: str | None,
        issuer: str | None,
    ) -> dict[str, Any]:
        assert token == "good-token"
        assert key == "public-key"
        assert algorithms == ["RS256"]
        assert audience == "soniq-mcp"
        assert issuer == "https://issuer.example.com/"
        return {
            "sub": "user-123",
            "scope": "read write",
            "exp": 1_762_345_678,
        }

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(verifier_mod.jwt, "decode", fake_decode)

    verifier = OIDCVerifier(config_with_oidc())

    assert run_verify(verifier, "good-token") == AccessToken(
        token="good-token",
        client_id="user-123",
        scopes=["read", "write"],
        expires_at=1_762_345_678,
    )
    assert captured_tokens == ["good-token"]


def test_valid_oidc_token_prefers_client_id_and_scp(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            return FakeSigningKey()

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(
        verifier_mod.jwt,
        "decode",
        lambda *args, **kwargs: {
            "client_id": "cli-789",
            "sub": "user-123",
            "scp": ["playback", "zones"],
            "exp": 1_762_345_999,
        },
    )

    verifier = OIDCVerifier(config_with_oidc())

    assert run_verify(verifier, "good-token") == AccessToken(
        token="good-token",
        client_id="cli-789",
        scopes=["playback", "zones"],
        expires_at=1_762_345_999,
    )


def test_invalid_oidc_tokens_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def get_signing_key_from_jwt(self, token: str) -> None:
            raise PyJWTError("bad token")

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    verifier = OIDCVerifier(config_with_oidc())

    assert run_verify(verifier, None) is None
    assert run_verify(verifier, "") is None
    assert run_verify(verifier, "   ") is None
    assert run_verify(verifier, "bad-token") is None


def test_oidc_verifier_fails_closed_without_audience_or_issuer() -> None:
    missing_audience = OIDCVerifier(config_with_oidc_missing_claim_enforcement())
    missing_issuer = OIDCVerifier(
        SoniqConfig(
            transport=TransportMode.STDIO,
            auth_mode=AuthMode.OIDC,
            oidc_audience="soniq-mcp",
            oidc_jwks_uri="https://issuer.example.com/jwks.json",
        )
    )

    assert run_verify(missing_audience, "good-token") is None
    assert run_verify(missing_issuer, "good-token") is None


def test_oidc_decode_exceptions_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            return FakeSigningKey()

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    verifier = OIDCVerifier(config_with_oidc())

    monkeypatch.setattr(
        verifier_mod.jwt,
        "decode",
        lambda *args, **kwargs: (_ for _ in ()).throw(PyJWTError("expired")),
    )
    assert run_verify(verifier, "expired-token") is None

    monkeypatch.setattr(
        verifier_mod.jwt,
        "decode",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert run_verify(verifier, "broken-token") is None


def test_valid_oidc_token_accepts_string_scp(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            self.uri = uri

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            return FakeSigningKey()

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(
        verifier_mod.jwt,
        "decode",
        lambda *args, **kwargs: {
            "client_id": "cli-789",
            "scp": "playback zones",
            "exp": 1_762_345_999,
        },
    )

    verifier = OIDCVerifier(config_with_oidc())

    assert run_verify(verifier, "good-token") == AccessToken(
        token="good-token",
        client_id="cli-789",
        scopes=["playback", "zones"],
        expires_at=1_762_345_999,
    )


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
