"""Setup-support tools for SoniqMCP.

Minimal tool surface for local verification and future extension.
Sonos-specific tools are added from Story 2 onward.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig


def register(app: FastMCP, config: SoniqConfig) -> None:
    """Register setup-support tools onto ``app``."""

    @app.tool()
    def ping() -> str:
        """Check whether the SoniqMCP server is responsive."""
        return "pong"

    @app.tool()
    def server_info() -> dict[str, str]:
        """Return non-sensitive server metadata.

        Safe to call during setup and troubleshooting.
        """
        return {
            "name": "soniq-mcp",
            "transport": config.transport.value,
            "exposure": config.exposure.value,
            "log_level": config.log_level.value,
        }
