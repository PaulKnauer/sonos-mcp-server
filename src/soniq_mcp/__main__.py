"""CLI entry point for the Story 1.1 scaffold."""

from soniq_mcp.server import create_application


def main() -> None:
    """Bootstrap the placeholder application without invoking Sonos behavior."""
    app = create_application()
    print(f"{app['name']} scaffold ready via {app['transport']}")


if __name__ == "__main__":
    main()
