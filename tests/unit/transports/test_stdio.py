"""Unit tests for stdio transport module."""

from __future__ import annotations

from soniq_mcp.transports.stdio import stdio_transport_name


def test_stdio_transport_name_returns_stdio() -> None:
    assert stdio_transport_name() == "stdio"
