"""Top-level package for the SoniqMCP server."""


def main() -> None:
    """Console entry point (used by ``soniq-mcp`` CLI script)."""
    from soniq_mcp.__main__ import main as entrypoint
    entrypoint()


__all__ = ["main"]
