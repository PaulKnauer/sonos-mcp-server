"""Unit tests for logging configuration."""

from __future__ import annotations

import logging

from soniq_mcp.logging_config import get_logger, setup_logging


class TestSetupLogging:
    def test_setup_logging_accepts_info(self) -> None:
        setup_logging("INFO")
        assert logging.getLogger().level == logging.INFO

    def test_setup_logging_accepts_debug(self) -> None:
        setup_logging("DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_setup_logging_accepts_warning(self) -> None:
        setup_logging("WARNING")
        assert logging.getLogger().level == logging.WARNING


class TestGetLogger:
    def test_get_logger_returns_named_logger(self) -> None:
        log = get_logger("soniq_mcp.test")
        assert log.name == "soniq_mcp.test"

    def test_get_logger_returns_logger_instance(self) -> None:
        assert isinstance(get_logger("test"), logging.Logger)
