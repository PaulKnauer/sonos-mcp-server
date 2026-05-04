"""Bearer token verifier implementations."""

from __future__ import annotations

import secrets

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
