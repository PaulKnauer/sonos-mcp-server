"""Unit tests for bearer token verifiers."""

from __future__ import annotations

import ast
import asyncio
import inspect
import json
import ssl
import time
from pathlib import Path
from typing import Any, get_type_hints

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from jwt import PyJWKClientError, PyJWTError
from jwt.algorithms import RSAAlgorithm
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
        transport=TransportMode.STDIO,
        auth_mode=AuthMode.OIDC,
        oidc_issuer="https://issuer.example.com/",
        oidc_jwks_uri="https://issuer.example.com/jwks.json",
    )


def config_with_oidc_http_jwks() -> SoniqConfig:
    return SoniqConfig(
        transport=TransportMode.HTTP,
        auth_mode=AuthMode.OIDC,
        oidc_issuer="https://issuer.example.com/",
        oidc_audience="soniq-mcp",
        oidc_jwks_uri="http://issuer.example.com/jwks.json",
    )


def config_with_oidc_ca_bundle() -> SoniqConfig:
    return SoniqConfig(
        transport=TransportMode.HTTP,
        auth_mode=AuthMode.OIDC,
        oidc_issuer="https://issuer.example.com/",
        oidc_audience="soniq-mcp",
        oidc_jwks_uri="https://issuer.example.com/jwks.json",
        oidc_ca_bundle="/tmp/homelab-ca.pem",
    )


def config_with_oidc_resource() -> SoniqConfig:
    return SoniqConfig(
        transport=TransportMode.HTTP,
        auth_mode=AuthMode.OIDC,
        oidc_issuer="https://issuer.example.com/",
        oidc_audience="soniq-mcp",
        oidc_jwks_uri="https://issuer.example.com/jwks.json",
        oidc_resource_url="https://resource.example.com",
    )


def run_verify(verifier: TokenVerifier, token: str | None) -> AccessToken | None:
    presented_token: Any = token
    return asyncio.run(verifier.verify_token(presented_token))


# ---------------------------------------------------------------------------
# In-process RSA/JWT helpers — provider-free OIDC verifier fixtures
# ---------------------------------------------------------------------------


def _make_rsa_keypair() -> tuple[RSAPrivateKey, RSAPublicKey]:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    return private_key, private_key.public_key()


def _make_jwks(public_key: RSAPublicKey, kid: str = "test-kid") -> dict[str, Any]:
    """Build a JWKS dict from an in-process public key without network access."""
    jwk_dict = json.loads(RSAAlgorithm.to_jwk(public_key))
    jwk_dict.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk_dict]}


def _make_rs256_jwt(
    private_key: RSAPrivateKey,
    claims: dict[str, Any],
    kid: str = "test-kid",
) -> str:
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": kid})


def _valid_oidc_claims(**extra: Any) -> dict[str, Any]:
    """Minimal valid JWT payload matching config_with_oidc()."""
    return {
        "sub": "user-123",
        "iss": "https://issuer.example.com/",
        "aud": "soniq-mcp",
        "exp": int(time.time()) + 3600,
        **extra,
    }


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
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
            init_calls.append(uri)

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    verifier = OIDCVerifier(config_with_oidc())

    assert init_calls == ["https://issuer.example.com/jwks.json"]
    assert isinstance(verifier, OIDCVerifier)


def test_oidc_verifier_rejects_non_https_jwks_uri(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    init_calls: list[str] = []

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            init_calls.append(uri)

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    verifier = OIDCVerifier(config_with_oidc_http_jwks())

    assert init_calls == []
    assert run_verify(verifier, "good-token") is None


def test_oidc_verifier_uses_custom_ca_bundle_ssl_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    ssl_context = ssl.create_default_context()
    captured_cafiles: list[str] = []
    captured_ssl_contexts: list[ssl.SSLContext | None] = []

    class FakeJWKClient:
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
            assert uri == "https://issuer.example.com/jwks.json"
            captured_ssl_contexts.append(ssl_context)

    def fake_create_default_context(*, cafile: str | None = None) -> ssl.SSLContext:
        captured_cafiles.append(cafile or "")
        return ssl_context

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(verifier_mod.ssl, "create_default_context", fake_create_default_context)

    OIDCVerifier(config_with_oidc_ca_bundle())

    assert captured_cafiles == ["/tmp/homelab-ca.pem"]
    assert captured_ssl_contexts == [ssl_context]


def test_oidc_verifier_leaves_ssl_context_none_without_ca_bundle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    init_calls: list[str] = []

    class FakeJWKClient:
        def __init__(self, uri: str) -> None:
            assert uri == "https://issuer.example.com/jwks.json"
            init_calls.append(uri)

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    OIDCVerifier(config_with_oidc())

    assert init_calls == ["https://issuer.example.com/jwks.json"]


def test_oidc_verifier_returns_none_when_ca_bundle_context_creation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    init_calls: list[str] = []

    class FakeJWKClient:
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
            init_calls.append(uri)

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(
        verifier_mod.ssl,
        "create_default_context",
        lambda *, cafile=None: (_ for _ in ()).throw(OSError("bad ca bundle")),
    )

    verifier = OIDCVerifier(config_with_oidc_ca_bundle())

    assert init_calls == []
    assert run_verify(verifier, "good-token") is None


def test_valid_oidc_token_maps_scope_string_sub_and_exp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    captured_tokens: list[str] = []

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
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


def test_oidc_verifier_reuses_single_jwk_client_for_multiple_verifications(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    init_calls: list[str] = []
    captured_tokens: list[str] = []

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
            init_calls.append(uri)

        def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
            captured_tokens.append(token)
            return FakeSigningKey()

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)
    monkeypatch.setattr(
        verifier_mod.jwt,
        "decode",
        lambda token, key, algorithms, audience, issuer: {
            "sub": token,
            "scope": "play",
            "exp": 1_762_345_678,
        },
    )

    verifier = OIDCVerifier(config_with_oidc())

    first = run_verify(verifier, "token-one")
    second = run_verify(verifier, "token-two")

    assert init_calls == ["https://issuer.example.com/jwks.json"]
    assert captured_tokens == ["token-one", "token-two"]
    assert first == AccessToken(
        token="token-one",
        client_id="token-one",
        scopes=["play"],
        expires_at=1_762_345_678,
    )
    assert second == AccessToken(
        token="token-two",
        client_id="token-two",
        scopes=["play"],
        expires_at=1_762_345_678,
    )


def test_valid_oidc_token_prefers_client_id_and_scp(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeSigningKey:
        key = "public-key"

    class FakeJWKClient:
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
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


def test_oidc_verifier_accepts_key_lookup_success_after_internal_refresh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeSigningKey:
        key = "public-key"
        key_id = "rotated-kid"

    refresh_calls: list[bool] = []
    monkeypatch.setattr(
        verifier_mod.jwt,
        "decode",
        lambda *args, **kwargs: {
            "client_id": "rotated-client",
            "scp": ["playback"],
            "exp": 1_762_345_999,
        },
    )

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None

    def fake_get_signing_keys(refresh: bool = False) -> list[FakeSigningKey]:
        refresh_calls.append(refresh)
        return [FakeSigningKey()] if refresh else []

    def fake_get_signing_key_from_jwt(token: str) -> FakeSigningKey:
        assert token == "rotated-token"
        return verifier._jwk_client.get_signing_key("rotated-kid")

    monkeypatch.setattr(verifier._jwk_client, "get_signing_keys", fake_get_signing_keys)
    monkeypatch.setattr(
        verifier._jwk_client,
        "get_signing_key_from_jwt",
        fake_get_signing_key_from_jwt,
    )

    assert run_verify(verifier, "rotated-token") == AccessToken(
        token="rotated-token",
        client_id="rotated-client",
        scopes=["playback"],
        expires_at=1_762_345_999,
    )
    assert refresh_calls == [False, True]


def test_invalid_oidc_tokens_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    import soniq_mcp.auth.verifiers as verifier_mod

    class FakeJWKClient:
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
            self.uri = uri

        def get_signing_key_from_jwt(self, token: str) -> None:
            raise PyJWTError("bad token")

    monkeypatch.setattr(verifier_mod, "PyJWKClient", FakeJWKClient)

    verifier = OIDCVerifier(config_with_oidc())

    assert run_verify(verifier, None) is None
    assert run_verify(verifier, "") is None
    assert run_verify(verifier, "   ") is None
    assert run_verify(verifier, "bad-token") is None


def test_oidc_verifier_returns_none_when_jwks_refresh_still_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None

    refresh_calls: list[bool] = []

    def fake_get_signing_keys(refresh: bool = False) -> list[object]:
        refresh_calls.append(refresh)
        return []

    def fake_get_signing_key_from_jwt(token: str) -> None:
        assert token == "rotated-token"
        return verifier._jwk_client.get_signing_key("rotated-kid")

    monkeypatch.setattr(verifier._jwk_client, "get_signing_keys", fake_get_signing_keys)
    monkeypatch.setattr(
        verifier._jwk_client,
        "get_signing_key_from_jwt",
        fake_get_signing_key_from_jwt,
    )

    assert run_verify(verifier, "rotated-token") is None
    assert refresh_calls == [False, True]


def test_pyjwkclient_refresh_failure_is_caught_as_invalid_token() -> None:
    assert issubclass(PyJWKClientError, PyJWTError)


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
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
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
        def __init__(self, uri: str, ssl_context: ssl.SSLContext | None = None) -> None:
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


# ---------------------------------------------------------------------------
# Real RS256 path — in-process crypto, no jwt.decode mock, no network
# ---------------------------------------------------------------------------


def test_real_rs256_valid_token_returns_access_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    token = _make_rs256_jwt(private_key, _valid_oidc_claims(scope="read write"))

    verifier = OIDCVerifier(config_with_oidc_resource())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    result = run_verify(verifier, token)

    assert result is not None
    assert result.client_id == "user-123"
    assert result.scopes == ["read", "write"]
    assert isinstance(result.expires_at, int)
    assert result.resource == "https://resource.example.com"


def test_real_rs256_valid_token_prefers_client_id_and_scp_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    token = _make_rs256_jwt(
        private_key,
        _valid_oidc_claims(client_id="cli-abc", scp=["playback", "status"]),
    )

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    result = run_verify(verifier, token)

    assert result is not None
    assert result.client_id == "cli-abc"
    assert result.scopes == ["playback", "status"]


# ---------------------------------------------------------------------------
# Invalid-token matrix — every case must assert None explicitly
# ---------------------------------------------------------------------------


def test_expired_rs256_token_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    expired_claims = {
        "sub": "user-123",
        "iss": "https://issuer.example.com/",
        "aud": "soniq-mcp",
        "exp": int(time.time()) - 3600,
    }
    token = _make_rs256_jwt(private_key, expired_claims)

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    assert run_verify(verifier, token) is None


def test_tampered_rs256_signature_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    token = _make_rs256_jwt(private_key, _valid_oidc_claims())

    header, payload, sig = token.split(".")
    corrupted_sig = sig[:-4] + ("AAAA" if not sig.endswith("AAAA") else "BBBB")
    tampered = f"{header}.{payload}.{corrupted_sig}"

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    assert run_verify(verifier, tampered) is None


def test_wrong_issuer_rs256_token_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    token = _make_rs256_jwt(
        private_key,
        _valid_oidc_claims(iss="https://evil.example.com/"),
    )

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    assert run_verify(verifier, token) is None


def test_wrong_audience_rs256_token_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    token = _make_rs256_jwt(
        private_key,
        _valid_oidc_claims(aud="wrong-audience"),
    )

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    assert run_verify(verifier, token) is None


def test_missing_identity_claim_rs256_token_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, public_key = _make_rsa_keypair()
    jwks = _make_jwks(public_key)
    no_identity_claims: dict[str, Any] = {
        "iss": "https://issuer.example.com/",
        "aud": "soniq-mcp",
        "exp": int(time.time()) + 3600,
        "scope": "read",
    }
    token = _make_rs256_jwt(private_key, no_identity_claims)

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", lambda: jwks)

    assert run_verify(verifier, token) is None


# ---------------------------------------------------------------------------
# JWKS key rotation — real fetch_data boundary, built-in refresh logic
# ---------------------------------------------------------------------------


def test_real_rs256_token_verifies_after_jwks_key_rotation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, public_key = _make_rsa_keypair()
    old_private, old_public = _make_rsa_keypair()

    old_jwks = _make_jwks(old_public, kid="old-kid")
    rotated_jwks = _make_jwks(public_key, kid="new-kid")
    token = _make_rs256_jwt(private_key, _valid_oidc_claims(scope="read"), kid="new-kid")

    fetch_responses = [old_jwks, rotated_jwks]
    call_count: list[int] = [0]

    def fake_fetch_data() -> dict[str, Any]:
        idx = min(call_count[0], len(fetch_responses) - 1)
        call_count[0] += 1
        return fetch_responses[idx]

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", fake_fetch_data)

    result = run_verify(verifier, token)

    assert result is not None
    assert result.client_id == "user-123"
    assert call_count[0] == 2


def test_real_rs256_token_returns_none_when_rotation_key_never_appears(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key, public_key = _make_rsa_keypair()
    wrong_jwks = _make_jwks(public_key, kid="wrong-kid")
    token = _make_rs256_jwt(private_key, _valid_oidc_claims(), kid="expected-kid")

    call_count: list[int] = [0]

    def fake_fetch_data() -> dict[str, Any]:
        call_count[0] += 1
        return wrong_jwks

    verifier = OIDCVerifier(config_with_oidc())
    assert verifier._jwk_client is not None
    monkeypatch.setattr(verifier._jwk_client, "fetch_data", fake_fetch_data)

    assert run_verify(verifier, token) is None
    assert call_count[0] == 2


# ---------------------------------------------------------------------------
# FastMCP TokenVerifier contract compatibility
# ---------------------------------------------------------------------------


def test_oidc_verifier_satisfies_fastmcp_token_verifier_contract() -> None:
    assert inspect.iscoroutinefunction(OIDCVerifier.verify_token)

    expected_hints = get_type_hints(TokenVerifier.verify_token)
    actual_hints = get_type_hints(OIDCVerifier.verify_token)

    assert actual_hints["token"] is expected_hints["token"]
    assert actual_hints["return"] == expected_hints["return"]
