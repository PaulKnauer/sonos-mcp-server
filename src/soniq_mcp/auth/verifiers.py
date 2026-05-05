"""Bearer token verifier implementations."""

from __future__ import annotations

import secrets
import ssl
from urllib.parse import urlparse

import jwt
from jwt import PyJWKClient, PyJWTError
from mcp.server.auth.provider import AccessToken
from pydantic import SecretStr

from soniq_mcp.config.models import SoniqConfig

STATIC_TOKEN_CLIENT_ID = "static-token-client"


class StaticBearerVerifier:
    """Validate a shared static bearer token."""

    def __init__(self, config: SoniqConfig) -> None:
        self._auth_token: SecretStr | None = config.auth_token

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return access details only when the presented token matches."""
        if token is None or token.strip() == "" or self._auth_token is None:
            return None

        configured_token = self._auth_token.get_secret_value()
        if configured_token.strip() == "":
            return None

        try:
            tokens_match = secrets.compare_digest(
                configured_token.encode("ascii"),
                token.encode("ascii"),
            )
        except UnicodeEncodeError:
            return None

        if not tokens_match:
            return None

        return AccessToken(
            token=token,
            client_id=STATIC_TOKEN_CLIENT_ID,
            scopes=[],
        )


class OIDCVerifier:
    """Validate JWT bearer tokens against a configured JWKS endpoint."""

    def __init__(self, config: SoniqConfig) -> None:
        self._issuer = config.oidc_issuer
        self._audience = config.oidc_audience
        self._resource = config.oidc_resource_url
        self._jwk_client = self._build_jwk_client(config)

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return access details for a valid OIDC JWT, else fail closed."""
        if (
            token is None
            or token.strip() == ""
            or not self._issuer
            or not self._audience
            or self._jwk_client is None
        ):
            return None

        try:
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
            )
        except PyJWTError:
            return None
        except Exception:
            return None

        client_id = claims.get("client_id") or claims.get("sub")
        if not isinstance(client_id, str) or client_id.strip() == "":
            return None

        scopes = _extract_scopes(claims)
        expires_at = claims.get("exp")
        if expires_at is not None and not isinstance(expires_at, int):
            return None

        access_token = AccessToken(
            token=token,
            client_id=client_id,
            scopes=scopes,
            expires_at=expires_at,
            resource=self._resource,
        )
        return access_token

    @staticmethod
    def _build_jwk_client(config: SoniqConfig) -> PyJWKClient | None:
        """Build a JWKS client only for valid HTTPS endpoints."""
        jwks_uri = config.oidc_jwks_uri
        if not jwks_uri:
            return None

        parsed = urlparse(jwks_uri)
        if parsed.scheme != "https" or not parsed.netloc:
            return None

        if config.oidc_ca_bundle:
            try:
                ssl_context = ssl.create_default_context(cafile=config.oidc_ca_bundle)
            except (OSError, ValueError, ssl.SSLError):
                return None
            return PyJWKClient(jwks_uri, ssl_context=ssl_context)

        return PyJWKClient(jwks_uri)


def _extract_scopes(claims: dict[str, object]) -> list[str]:
    """Normalize scope claims from either `scp` or `scope`."""
    scp = claims.get("scp")
    if isinstance(scp, list) and all(isinstance(scope, str) for scope in scp):
        return scp
    if isinstance(scp, str):
        return scp.split()

    scope = claims.get("scope")
    if isinstance(scope, str):
        return scope.split()

    return []
