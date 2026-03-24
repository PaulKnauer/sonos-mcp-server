"""CLI entry point for the SoniqMCP server."""

from soniq_mcp.server import create_application


def main() -> None:
    """Bootstrap the application."""
    app = create_application()
    print(f"{app['name']} scaffold ready via {app['transport']}")


if __name__ == "__main__":
    main()
