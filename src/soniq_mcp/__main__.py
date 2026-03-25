"""CLI entry point for SoniqMCP."""

from __future__ import annotations

import sys


def main() -> None:
    from soniq_mcp.config import run_preflight
    from soniq_mcp.config.validation import ConfigValidationError
    from soniq_mcp.logging_config import setup_logging

    try:
        config = run_preflight()
    except ConfigValidationError as exc:
        for msg in exc.messages:
            print(f"[soniq-mcp] configuration error: {msg}", file=sys.stderr)
        print("[soniq-mcp] fix the above errors and restart.", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.log_level.value)

    import logging
    log = logging.getLogger(__name__)
    log.info(
        "SoniqMCP starting — transport=%s exposure=%s max_volume=%s%%",
        config.transport.value,
        config.exposure.value,
        config.max_volume_pct,
    )

    from soniq_mcp.server import create_server
    from soniq_mcp.transports.bootstrap import run_transport

    app = create_server(config)
    run_transport(app, config)


if __name__ == "__main__":
    main()
