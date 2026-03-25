"""Top-level package for the SoniqMCP server."""


def main() -> None:
    from soniq_mcp.__main__ import main as entrypoint
    entrypoint()


__all__ = ["main"]
