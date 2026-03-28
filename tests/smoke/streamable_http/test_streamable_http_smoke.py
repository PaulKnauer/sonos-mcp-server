"""Smoke tests: Streamable HTTP transport end-to-end (Story 4.1, AC 1, 2).

Starts the server as a subprocess bound to a local test port, connects via
the MCP streamable-http client, and verifies the tool surface and ping tool
work identically to the stdio transport.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

_TEST_PORT = 18431  # high port unlikely to conflict with other services
_TEST_HOST = "127.0.0.1"
_MCP_PATH = "/mcp"


@pytest.fixture(scope="module")
def http_server_proc():
    """Start the SoniqMCP server over Streamable HTTP in a subprocess."""
    env = {
        **os.environ,
        "SONIQ_MCP_TRANSPORT": "http",
        "SONIQ_MCP_HTTP_HOST": _TEST_HOST,
        "SONIQ_MCP_HTTP_PORT": str(_TEST_PORT),
        "SONIQ_MCP_EXPOSURE": "local",
        "SONIQ_MCP_LOG_LEVEL": "WARNING",  # reduce noise in test output
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "soniq_mcp"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)  # allow uvicorn to bind and become ready
    yield proc
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestStreamableHTTPSmoke:
    """A same-machine MCP client must connect over Streamable HTTP and call tools (AC 1, 2)."""

    def test_client_can_initialize_and_call_ping(self, http_server_proc) -> None:
        async def run_session() -> None:
            url = f"http://{_TEST_HOST}:{_TEST_PORT}{_MCP_PATH}"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    result = await session.call_tool("ping")

                    assert result.isError is False
                    assert [item.text for item in result.content] == ["pong"]

        anyio.run(run_session)

    def test_http_tool_surface_includes_ping(self, http_server_proc) -> None:
        async def run_session() -> None:
            url = f"http://{_TEST_HOST}:{_TEST_PORT}{_MCP_PATH}"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]
                    assert "ping" in tool_names
                    assert "list_rooms" in tool_names
                    assert "play" in tool_names

        anyio.run(run_session)
