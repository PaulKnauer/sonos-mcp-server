"""Logging configuration for SoniqMCP.

Sets up structured, stderr-directed logging.  Never logs raw config
values to avoid leaking sensitive information in startup output.
"""

from __future__ import annotations

import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging.

    Args:
        log_level: One of DEBUG, INFO, WARNING, ERROR.
    """
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
