"""Top-level package for the SoniqMCP server scaffold."""


def main() -> None:
    """Backward-compatible console entry point for the package."""
    from soniq_mcp.__main__ import main as entrypoint

    entrypoint()


__all__ = ["main"]
