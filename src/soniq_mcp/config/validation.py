"""Startup preflight validation for SoniqMCP.

Call ``run_preflight()`` before any Sonos or transport initialisation.
Errors identify the specific field that must be corrected and are safe
to surface to the user.
"""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from pydantic import ValidationError

from soniq_mcp.config.loader import load_config
from soniq_mcp.config.models import AuthMode, SoniqConfig, TransportMode


class ConfigValidationError(ValueError):
    """Raised when configuration fails preflight checks."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        super().__init__("\n".join(messages))


def ensure_preflight_ready(config: SoniqConfig) -> SoniqConfig:
    """Apply blocking preflight checks to an already-loaded config object."""
    auth_errors = _validate_auth_preflight(config)
    if auth_errors:
        raise ConfigValidationError(auth_errors)
    return config


def run_preflight(overrides: dict | None = None) -> SoniqConfig:
    """Load and validate configuration; raise before runtime on failure."""
    try:
        config = load_config(overrides=overrides)
    except (ValidationError, ValueError) as exc:
        if isinstance(exc, ValidationError):
            messages = [_fmt(error) for error in exc.errors()]
        else:
            messages = [str(exc)]
        raise ConfigValidationError(messages) from exc

    return ensure_preflight_ready(config)


def _validate_auth_preflight(config: SoniqConfig) -> list[str]:
    """Return user-facing error messages for blocking auth misconfiguration.

    Only HTTP transport failures are blocking.  Stdio with auth fields present
    is allowed; the operator may be testing locally before enabling HTTP.
    Secret values are never included in returned messages.
    """
    if config.transport == TransportMode.STDIO:
        return []

    errors: list[str] = []

    if config.auth_mode == AuthMode.STATIC and config.auth_token is None:
        errors.append(
            "auth_mode=static requires auth_token to be set. "
            "Set SONIQ_MCP_AUTH_TOKEN to a non-empty bearer token value."
        )

    if config.auth_mode == AuthMode.OIDC:
        errors.extend(_validate_oidc_preflight(config))

    return errors


def _validate_oidc_preflight(config: SoniqConfig) -> list[str]:
    """Validate OIDC JWKS reachability at startup. Returns actionable error messages."""
    issuer_error = _validate_oidc_issuer(config.oidc_issuer)  # type: ignore[arg-type]
    if issuer_error is not None:
        return _oidc_error_messages(
            url=config.oidc_issuer or "",
            category="configuration",
            likely_cause=issuer_error,
        )

    resource_error = _validate_optional_resource_url(config.oidc_resource_url)
    if resource_error is not None:
        return _oidc_error_messages(
            url=config.oidc_resource_url or "",
            category="configuration",
            likely_cause=resource_error,
        )

    ssl_context: ssl.SSLContext | None = None
    discovery_url = _build_discovery_url(config.oidc_issuer)  # type: ignore[arg-type]
    preflight_target_url = config.oidc_jwks_uri or discovery_url
    if config.oidc_ca_bundle:
        try:
            ssl_context = ssl.create_default_context(cafile=config.oidc_ca_bundle)
        except (OSError, ValueError, ssl.SSLError):
            return _oidc_error_messages(
                url=preflight_target_url,
                category="configuration",
                likely_cause=(
                    "oidc_ca_bundle file could not be loaded; "
                    "check the path is correct and the file is a valid CA certificate"
                ),
                config_target=config.oidc_ca_bundle,
            )

    jwks_uri = config.oidc_jwks_uri
    if not jwks_uri:
        # config.oidc_issuer is guaranteed non-None here by the model validator
        try:
            raw = _fetch_url(discovery_url, ssl_context)
            data = json.loads(raw)
            discovered = data.get("jwks_uri")
            if not isinstance(discovered, str) or not discovered:
                return _oidc_error_messages(
                    url=discovery_url,
                    category="discovery",
                    likely_cause=(
                        "OIDC discovery document is valid JSON but missing 'jwks_uri' field"
                    ),
                )
            scheme_error = _validate_jwks_uri(discovered)
            if scheme_error is not None:
                return _oidc_error_messages(
                    url=discovered,
                    category="configuration",
                    likely_cause=scheme_error,
                )
            jwks_uri = discovered
            config.oidc_jwks_uri = discovered
        except (urllib.error.URLError, ssl.SSLError) as exc:
            return _oidc_error_messages(
                url=discovery_url,
                category=_classify_error(exc),
                likely_cause=_describe_error(exc),
            )
        except (json.JSONDecodeError, ValueError):
            return _oidc_error_messages(
                url=discovery_url,
                category="discovery",
                likely_cause="OIDC discovery document returned invalid JSON",
            )

    scheme_error = _validate_jwks_uri(jwks_uri)
    if scheme_error is not None:
        return _oidc_error_messages(
            url=jwks_uri,
            category="configuration",
            likely_cause=scheme_error,
        )

    try:
        raw = _fetch_url(jwks_uri, ssl_context)
        _validate_jwks_document(raw)
        return []
    except (urllib.error.URLError, ssl.SSLError) as exc:
        return _oidc_error_messages(
            url=jwks_uri,
            category=_classify_error(exc),
            likely_cause=_describe_error(exc),
        )
    except (json.JSONDecodeError, ValueError):
        return _oidc_error_messages(
            url=jwks_uri,
            category="discovery",
            likely_cause="JWKS endpoint returned invalid JSON or a document without a 'keys' list",
        )


def _build_discovery_url(issuer: str) -> str:
    """Build OpenID Connect Discovery 1.0 well-known URL from issuer."""
    parsed = urlsplit(issuer)
    issuer_path = parsed.path.rstrip("/")
    if issuer_path:
        discovery_path = f"/.well-known/openid-configuration{issuer_path}"
    else:
        discovery_path = "/.well-known/openid-configuration"
    return urlunsplit((parsed.scheme, parsed.netloc, discovery_path, "", ""))


def _fetch_url(url: str, ssl_context: ssl.SSLContext | None) -> bytes:
    """Fetch a URL and return response body bytes."""
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10, context=ssl_context) as resp:
        return resp.read()


def _validate_jwks_uri(jwks_uri: str) -> str | None:
    """Return an actionable message when the JWKS URI is not runtime-safe."""
    parsed = urlsplit(jwks_uri)
    if parsed.scheme != "https" or not parsed.netloc:
        return "JWKS URI must be an absolute https:// URL reachable by the server"
    return None


def _validate_oidc_issuer(issuer: str) -> str | None:
    """Return an actionable message when the issuer is not a usable absolute URL."""
    parsed = urlsplit(issuer)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "OIDC issuer must be an absolute http:// or https:// URL"
    if parsed.query or parsed.fragment:
        return "OIDC issuer must not include a query string or fragment"
    return None


def _validate_optional_resource_url(resource_url: str | None) -> str | None:
    """Validate optional resource URL early so startup failures stay in preflight."""
    if resource_url is None:
        return None
    parsed = urlsplit(resource_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "OIDC resource URL must be an absolute http:// or https:// URL"
    return None


def _validate_jwks_document(raw: bytes) -> None:
    """Reject reachable endpoints that are not valid JWKS documents."""
    data = json.loads(raw)
    keys = data.get("keys")
    if not isinstance(keys, list):
        raise ValueError("JWKS document missing 'keys' list")


def _classify_error(exc: Exception) -> str:
    """Classify a network or TLS error into a preflight category string."""
    if isinstance(exc, ssl.SSLError):
        return "tls"
    if isinstance(exc, urllib.error.URLError):
        if isinstance(exc.reason, ssl.SSLError):
            return "tls"
        return "network"
    return "network"


def _describe_error(exc: Exception) -> str:
    """Return a safe, human-readable cause description for a network/TLS error."""
    if isinstance(exc, ssl.SSLError):
        return (
            "TLS certificate verification failed; "
            "check CA trust configuration or set SONIQ_MCP_OIDC_CA_BUNDLE"
        )
    if isinstance(exc, urllib.error.URLError):
        if isinstance(exc.reason, ssl.SSLError):
            return (
                "TLS certificate verification failed; "
                "check CA trust configuration or set SONIQ_MCP_OIDC_CA_BUNDLE"
            )
        return "Network connection failed; verify the endpoint is reachable and the URL is correct"
    return "Connection failed; verify endpoint reachability"


def _oidc_error_messages(
    url: str,
    category: str,
    likely_cause: str,
    config_target: str | None = None,
) -> list[str]:
    """Build actionable OIDC preflight error messages for __main__.py rendering."""
    messages = [
        "OIDC JWKS preflight failed",
        f"URL: {url}",
        f"Category: {category}",
        f"Likely cause: {likely_cause}",
        "Docs: docs/setup/troubleshooting.md#configuration-errors-at-startup",
    ]
    if config_target is not None:
        messages.insert(2, f"Configuration target: {config_target}")
    return messages


def _fmt(error: Mapping[str, Any]) -> str:
    """Format a single pydantic error dict into a user-facing string."""
    loc = ".".join(str(part) for part in error.get("loc", []))
    msg = error.get("msg", "invalid value").removeprefix("Value error, ")
    return f"{loc}: {msg}" if loc else msg
