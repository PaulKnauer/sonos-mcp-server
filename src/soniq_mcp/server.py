"""Application composition boundary for the SoniqMCP scaffold."""

from collections.abc import Mapping

from soniq_mcp.transports.bootstrap import bootstrap_transport


def create_application() -> Mapping[str, str]:
    """Return the minimal application metadata needed by the scaffold."""
    return {
        "name": "soniq_mcp",
        "transport": bootstrap_transport(),
    }
