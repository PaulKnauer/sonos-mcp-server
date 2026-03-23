"""Transport bootstrap boundary for the SoniqMCP scaffold."""

from soniq_mcp.transports.stdio import stdio_transport_name


def bootstrap_transport() -> str:
    """Resolve the placeholder local transport for early scaffold verification."""
    return stdio_transport_name()
