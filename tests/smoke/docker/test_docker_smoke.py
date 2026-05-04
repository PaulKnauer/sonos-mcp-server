"""Smoke tests: Docker image build and container runtime (Story 4.2, AC 1, 2, 3).

Builds the Docker image from the project root, starts a container, and verifies
the MCP endpoint is reachable and the tool surface is populated.

These tests are skipped automatically when Docker is not available
(e.g., CI environments without Docker-in-Docker or local machines where the
daemon is stopped).
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

_IMAGE = "soniq-mcp-test:smoke"
_HOST = "127.0.0.1"
_PROJECT_ROOT = Path(__file__).parents[3]


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False

    try:
        result = subprocess.run(
            ["docker", "info"],
            check=False,
            capture_output=True,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False

    return result.returncode == 0


def _free_tcp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((_HOST, 0))
        return int(sock.getsockname()[1])


pytestmark = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker CLI or daemon not available - skipping Docker smoke tests",
)


@pytest.fixture(scope="module")
def docker_image():
    """Build the Docker image from the project root."""
    subprocess.run(
        ["docker", "build", "-t", _IMAGE, str(_PROJECT_ROOT)],
        check=True,
    )
    yield _IMAGE
    subprocess.run(
        ["docker", "rmi", _IMAGE, "--force"],
        check=False,
    )


@pytest.fixture(scope="module")
def docker_container(docker_image):
    """Start a container from the built image and wait for it to be ready."""
    host_port = _free_tcp_port()
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-d",
            "-p",
            f"{host_port}:8000",
            "-e",
            "SONIQ_MCP_TRANSPORT=http",
            "-e",
            "SONIQ_MCP_HTTP_HOST=0.0.0.0",
            "-e",
            "SONIQ_MCP_HTTP_PORT=8000",
            "-e",
            "SONIQ_MCP_EXPOSURE=home-network",
            "-e",
            "SONIQ_MCP_LOG_LEVEL=WARNING",
            docker_image,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    container_id = result.stdout.strip()
    time.sleep(3.0)  # allow uvicorn to bind and become ready
    yield f"http://{_HOST}:{host_port}/mcp"
    subprocess.run(["docker", "rm", "-f", container_id], check=False)


class TestDockerSmoke:
    """Container must serve the MCP endpoint and expose the tool surface (AC 1, 2, 3)."""

    def test_docker_mcp_endpoint_responds(self, docker_container: str) -> None:
        async def run_session() -> None:
            async with streamable_http_client(docker_container) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool("ping")
                    assert result.isError is False
                    assert [item.text for item in result.content] == ["pong"]

        anyio.run(run_session)

    def test_docker_tool_surface_populated(self, docker_container: str) -> None:
        async def run_session() -> None:
            async with streamable_http_client(docker_container) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    assert len(tools.tools) > 0

        anyio.run(run_session)
