"""Authentication verifier construction."""

from __future__ import annotations

from mcp.server.auth.provider import TokenVerifier

from soniq_mcp.auth.verifiers import OIDCVerifier, StaticBearerVerifier
from soniq_mcp.config.models import AuthMode, SoniqConfig

__all__ = ["OIDCVerifier", "StaticBearerVerifier", "build_token_verifier"]


def build_token_verifier(config: SoniqConfig) -> TokenVerifier:
    """Build the token verifier for the configured auth mode."""
    if config.auth_mode == AuthMode.STATIC:
        return StaticBearerVerifier(config)
    if config.auth_mode == AuthMode.OIDC:
        return OIDCVerifier(config)

    raise NotImplementedError(f"auth_mode={config.auth_mode} has no token verifier")
