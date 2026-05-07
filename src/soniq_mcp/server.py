"""Application composition boundary for SoniqMCP.

``create_server()`` is the single place where the MCP application is
assembled. Transport concerns stay in ``transports/``. Sonos service
wiring arrives in Story 2+.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import AnyHttpUrl, TypeAdapter

from soniq_mcp.config import SoniqConfig, run_preflight
from soniq_mcp.config.models import AuthMode, TransportMode
from soniq_mcp.config.validation import ensure_preflight_ready
from soniq_mcp.domain.safety import validate_exposure_posture
from soniq_mcp.tools import register_all
from soniq_mcp.transports.bootstrap import bootstrap_transport

log = logging.getLogger(__name__)

_http_url: TypeAdapter[AnyHttpUrl] = TypeAdapter(AnyHttpUrl)


def _build_auth_kwargs(config: SoniqConfig) -> dict[str, Any]:
    """Build FastMCP auth constructor kwargs for enabled auth modes.

    Only called when HTTP auth is enabled — the guard in create_server() ensures that.
    OIDC uses oidc_issuer as issuer_url; static auth derives issuer from http_host:http_port.
    """
    from mcp.server.auth.settings import AuthSettings

    from soniq_mcp.auth import build_token_verifier

    if config.auth_mode == AuthMode.OIDC:
        issuer: AnyHttpUrl = _http_url.validate_python(config.oidc_issuer)
    else:
        issuer = _http_url.validate_python(
            f"http://{_format_url_host(config.http_host)}:{config.http_port}"
        )

    resource: AnyHttpUrl | None = (
        _http_url.validate_python(config.oidc_resource_url)
        if config.oidc_resource_url is not None
        else None
    )
    auth_settings = AuthSettings(
        issuer_url=issuer,
        resource_server_url=resource,
        required_scopes=None,
    )
    return {"auth": auth_settings, "token_verifier": build_token_verifier(config)}


def _format_url_host(host: str) -> str:
    """Return host formatted for use in a URL authority."""
    if ":" in host and not host.startswith("["):
        return f"[{host}]"
    return host


def create_server(config: SoniqConfig | None = None) -> FastMCP:
    """Create and configure the MCP application."""
    if config is None:
        config = run_preflight()
    else:
        config = ensure_preflight_ready(config)

    warnings = validate_exposure_posture(config)
    for warning in warnings:
        log.warning("Exposure posture: %s", warning)

    auth_kwargs: dict[str, Any] = {}
    _http_auth_modes = (AuthMode.STATIC, AuthMode.OIDC)
    if config.transport == TransportMode.HTTP and config.auth_mode in _http_auth_modes:
        auth_kwargs = _build_auth_kwargs(config)

    app = FastMCP("soniq-mcp", host=config.http_host, port=config.http_port, **auth_kwargs)
    register_all(app, config)

    log.info(
        "SoniqMCP server created transport=%s exposure=%s max_volume=%s%%",
        config.transport.value,
        config.exposure.value,
        config.max_volume_pct,
    )
    return app


def create_application() -> Mapping[str, str]:
    """Return minimal app metadata for backward-compatible smoke tests."""
    return {
        "name": "soniq_mcp",
        "transport": bootstrap_transport(),
    }
