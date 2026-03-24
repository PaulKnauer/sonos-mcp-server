"""CLI entry point for the SoniqMCP server."""

import sys

from soniq_mcp.config.validation import ConfigValidationError, run_preflight
from soniq_mcp.server import create_application


def main() -> None:
    """Bootstrap the application."""
    try:
        run_preflight()
    except ConfigValidationError as exc:
        for msg in exc.messages:
            print(f"config error: {msg}", file=sys.stderr)
        sys.exit(1)
    app = create_application()
    print(f"{app['name']} scaffold ready via {app['transport']}")


if __name__ == "__main__":
    main()
