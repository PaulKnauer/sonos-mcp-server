"""CLI entry point for the SoniqMCP server."""

from __future__ import annotations

import sys


def main() -> None:
    """Bootstrap SoniqMCP with full preflight and safe error reporting."""
    from soniq_mcp.config import run_preflight
    from soniq_mcp.config.validation import ConfigValidationError
    from soniq_mcp.logging_config import setup_logging

    # Preflight first, before imports that may depend on config.
    try:
        config = run_preflight()
    except ConfigValidationError as exc:
        print(
            "[soniq-mcp] setup error: configuration validation blocked startup.",
            file=sys.stderr,
        )
        for msg in exc.messages:
            print(f"[soniq-mcp] configuration error: {msg}", file=sys.stderr)
        print(
            "[soniq-mcp] next step: fix the above errors and restart. "
            "See docs/setup/troubleshooting.md#configuration-errors-at-startup",
            file=sys.stderr,
        )
        sys.exit(1)

    setup_logging(config.log_level.value)

    import logging

    log = logging.getLogger(__name__)
    log.info(
        "SoniqMCP starting transport=%s exposure=%s max_volume=%s%%",
        config.transport.value,
        config.exposure.value,
        config.max_volume_pct,
    )

    from soniq_mcp.server import create_server
    from soniq_mcp.transports.bootstrap import run_transport

    try:
        app = create_server(config)
        run_transport(app, config)
    except Exception:
        if log.isEnabledFor(logging.DEBUG):
            log.exception("Runtime startup failure during service initialization.")
        else:
            log.error("Runtime startup failure during service initialization.")
        print(
            "[soniq-mcp] runtime error: startup completed configuration validation "
            "but failed during transport or service initialization.",
            file=sys.stderr,
        )
        print(
            "[soniq-mcp] next step: review stderr logs for developer details and "
            "see docs/setup/troubleshooting.md#remote-deployment-troubleshooting",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
