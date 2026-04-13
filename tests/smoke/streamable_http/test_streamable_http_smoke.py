"""Smoke tests: Streamable HTTP transport end-to-end (Story 4.1, AC 1, 2).

Starts the server as a subprocess bound to a local test port, connects via
the MCP streamable-http client, and verifies the tool surface and ping tool
work identically to the stdio transport.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

_TEST_HOST = "127.0.0.1"
_MCP_PATH = "/mcp"


def _find_open_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((_TEST_HOST, 0))
        return int(sock.getsockname()[1])


def _wait_for_server(
    proc: subprocess.Popen[bytes], host: str, port: int, timeout: float = 10.0
) -> None:
    deadline = time.monotonic() + timeout
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            stderr = b""
            if proc.stderr is not None:
                stderr = proc.stderr.read()
            raise RuntimeError(
                f"HTTP server exited before becoming ready (exit={proc.returncode}). "
                f"stderr={stderr.decode(errors='replace')}"
            )
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.1)

    raise RuntimeError(f"HTTP server did not become ready on {host}:{port}: {last_error}")


@pytest.fixture(scope="module")
def http_server_proc():
    """Start the SoniqMCP server over Streamable HTTP in a subprocess."""
    test_port = _find_open_port()
    env = {
        **os.environ,
        "SONIQ_MCP_TRANSPORT": "http",
        "SONIQ_MCP_HTTP_HOST": _TEST_HOST,
        "SONIQ_MCP_HTTP_PORT": str(test_port),
        "SONIQ_MCP_EXPOSURE": "local",
        "SONIQ_MCP_LOG_LEVEL": "WARNING",  # reduce noise in test output
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "soniq_mcp"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    _wait_for_server(proc, _TEST_HOST, test_port)
    yield proc, test_port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


class TestStreamableHTTPSmoke:
    """A same-machine MCP client must connect over Streamable HTTP and call tools (AC 1, 2)."""

    def test_client_can_initialize_and_call_ping(self, http_server_proc) -> None:
        _, test_port = http_server_proc

        async def run_session() -> None:
            url = f"http://{_TEST_HOST}:{test_port}{_MCP_PATH}"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()

                    result = await session.call_tool("ping")

                    assert result.isError is False
                    assert [item.text for item in result.content] == ["pong"]

        anyio.run(run_session)

    def test_http_tool_surface_includes_ping(self, http_server_proc) -> None:
        _, test_port = http_server_proc

        async def run_session() -> None:
            url = f"http://{_TEST_HOST}:{test_port}{_MCP_PATH}"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]
                    assert "ping" in tool_names
                    assert "list_rooms" in tool_names
                    assert "play" in tool_names

        anyio.run(run_session)

    def test_phase_two_browse_library_validation_matches_stdio(self, http_server_proc) -> None:
        _, test_port = http_server_proc

        async def call_stdio() -> tuple[bool, dict]:
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "soniq_mcp"],
                cwd=str(Path.cwd()),
                env={"SONIQ_MCP_TRANSPORT": "stdio"},
            )
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool("browse_library", {"category": "invalid"})
                    return result.isError, json.loads(result.content[0].text)

        async def call_http() -> tuple[bool, dict]:
            url = f"http://{_TEST_HOST}:{test_port}{_MCP_PATH}"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool("browse_library", {"category": "invalid"})
                    return result.isError, json.loads(result.content[0].text)

        async def run_comparison() -> None:
            stdio_is_error, stdio_payload = await call_stdio()
            http_is_error, http_payload = await call_http()

            assert http_is_error == stdio_is_error
            assert http_payload == stdio_payload
            assert http_payload["category"] == "validation"
            assert http_payload["field"] == "library"

        anyio.run(run_comparison)

    def test_phase_two_sleep_timer_validation_matches_stdio(self, http_server_proc) -> None:
        _, test_port = http_server_proc

        async def call_stdio() -> tuple[bool, dict]:
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "soniq_mcp"],
                cwd=str(Path.cwd()),
                env={"SONIQ_MCP_TRANSPORT": "stdio"},
            )
            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "set_sleep_timer", {"room": "Living Room", "minutes": True}
                    )
                    return result.isError, json.loads(result.content[0].text)

        async def call_http() -> tuple[bool, dict]:
            url = f"http://{_TEST_HOST}:{test_port}{_MCP_PATH}"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(
                        "set_sleep_timer", {"room": "Living Room", "minutes": True}
                    )
                    return result.isError, json.loads(result.content[0].text)

        async def run_comparison() -> None:
            stdio_is_error, stdio_payload = await call_stdio()
            http_is_error, http_payload = await call_http()

            assert http_is_error == stdio_is_error
            assert http_payload == stdio_payload
            assert http_payload["category"] == "validation"
            assert http_payload["field"] == "playback"
            assert "minutes" in http_payload["error"]

        anyio.run(run_comparison)
