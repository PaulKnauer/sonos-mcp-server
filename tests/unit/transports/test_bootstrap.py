"""Unit tests for transport bootstrap module."""

from __future__ import annotations

from soniq_mcp.transports.bootstrap import bootstrap_transport


def test_bootstrap_transport_returns_stdio() -> None:
    assert bootstrap_transport() == "stdio"
