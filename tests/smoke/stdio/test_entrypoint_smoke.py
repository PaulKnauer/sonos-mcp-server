"""Smoke tests: entry point startup behaviour (AC 1, 3, 4).

Tests call main() directly (no subprocess) for reliability in all
container environments.  The key properties under test are:
  - bad config → clean sys.exit(1), not a traceback
  - stderr messages identify the offending field
  - modules import without side-effects
  - a same-machine MCP client can connect over stdio and call `ping`
"""

from __future__ import annotations

import sys
from pathlib import Path

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


class TestModuleImportSmoke:
    """Packages must be importable without side-effects."""

    def test_main_package_importable(self) -> None:
        import soniq_mcp  # noqa: F401

    def test_main_module_importable(self) -> None:
        import soniq_mcp.__main__  # noqa: F401

    def test_server_module_importable(self) -> None:
        import soniq_mcp.server  # noqa: F401


class TestEntrypointBadConfig:
    """Invalid config must cause exit(1) with field-level diagnostics (AC 2, 4)."""

    def test_bad_transport_exits_nonzero(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "not-a-transport")
        from soniq_mcp.__main__ import main

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    def test_bad_transport_stderr_names_field(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "grpc")
        from soniq_mcp.__main__ import main

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "transport" in captured.err
        assert "configuration error" in captured.err

    def test_bad_config_no_traceback_in_stderr(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """Error output must be human-readable, not a Python traceback (AC 4)."""
        monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "bad")
        from soniq_mcp.__main__ import main

        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "Traceback" not in captured.err
        assert "fix the above errors" in captured.err


class TestStdioConnectivity:
    """A same-machine MCP client must be able to connect and call tools (AC 3)."""

    def test_client_can_initialize_and_call_ping(self) -> None:
        async def run_session() -> None:
            params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "soniq_mcp"],
                cwd=str(Path.cwd()),
                env={"SONIQ_MCP_TRANSPORT": "stdio"},
            )

            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]
                    assert "ping" in tool_names

                    result = await session.call_tool("ping")

                    assert result.isError is False
                    assert [item.text for item in result.content] == ["pong"]

        anyio.run(run_session)
