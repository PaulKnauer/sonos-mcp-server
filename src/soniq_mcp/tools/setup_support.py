"""Setup-support tools for SoniqMCP.

Minimal tool surface for local verification and future extension.
Sonos-specific tools are added from Story 2 onward.

Each tool checks its own permission at invocation time so dynamic
disablement works correctly.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config import SoniqConfig
from soniq_mcp.domain.safety import assert_tool_permitted


def register(app: FastMCP, config: SoniqConfig) -> None:
    """Register setup-support tools, skipping any in tools_disabled."""

    if "ping" not in config.tools_disabled:

        @app.tool()
        def ping() -> str:
            """Check whether the SoniqMCP server is responsive."""
            assert_tool_permitted("ping", config)
            return "pong"

    if "server_info" not in config.tools_disabled:

        @app.tool()
        def server_info() -> dict[str, str]:
            """Return non-sensitive server metadata."""
            assert_tool_permitted("server_info", config)
            return {
                "name": "soniq-mcp",
                "transport": config.transport.value,
                "exposure": config.exposure.value,
                "log_level": config.log_level.value,
                "max_volume_pct": str(config.max_volume_pct),
            }
