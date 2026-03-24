"""CLI entry point for SoniqMCP.

Runs preflight validation, configures logging, creates the server, and
starts the selected transport.  Exits with code 1 and human-readable
diagnostics if configuration is invalid — no stack traces.
"""

from __future__ import annotations

import sys


def main() -> None:
    """Bootstrap SoniqMCP with full preflight and safe error reporting."""
    from soniq_mcp.config import run_preflight
    from soniq_mcp.config.validation import ConfigValidationError
    from soniq_mcp.logging_config import setup_logging

    # Preflight first — before any other imports that might use config.
    try:
        config = run_preflight()
    except ConfigValidationError as exc:
        for msg in exc.messages:
            print(f"[soniq-mcp] configuration error: {msg}", file=sys.stderr)
        print(
            "[soniq-mcp] fix the above errors and restart.",
            file=sys.stderr,
        )
        sys.exit(1)

    setup_logging(config.log_level.value)

    import logging
    log = logging.getLogger(__name__)
    log.info(
        "SoniqMCP starting — transport=%s exposure=%s",
        config.transport.value,
        config.exposure.value,
    )

    from soniq_mcp.server import create_server
    from soniq_mcp.transports.bootstrap import run_transport

    app = create_server(config)
    run_transport(app, config)


if __name__ == "__main__":
    main()
