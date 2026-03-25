"""Unit tests for the __main__ entry point."""

from __future__ import annotations

import pytest

from soniq_mcp.__main__ import main

_ALL_ENV_KEYS = [
    "SONIQ_MCP_TRANSPORT",
    "SONIQ_MCP_EXPOSURE",
    "SONIQ_MCP_LOG_LEVEL",
    "SONIQ_MCP_DEFAULT_ROOM",
]


@pytest.fixture(autouse=True)
def _clear_soniq_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _ALL_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_main_exits_on_bad_config(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    """Bad env config must cause sys.exit(1) with human-readable diagnostics."""
    monkeypatch.setenv("SONIQ_MCP_TRANSPORT", "websocket")
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "configuration error" in captured.err
    assert "transport" in captured.err


def test_main_bootstraps_server_on_valid_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid config must create the server and dispatch the selected transport."""
    from soniq_mcp import server as server_module
    from soniq_mcp.transports import bootstrap as bootstrap_module

    app = object()
    called: dict[str, object] = {}

    def fake_create_server(config: object) -> object:
        called["create_server_config"] = config
        return app

    def fake_run_transport(app_arg: object, config_arg: object) -> None:
        called["run_transport_app"] = app_arg
        called["run_transport_config"] = config_arg

    monkeypatch.setattr(server_module, "create_server", fake_create_server)
    monkeypatch.setattr(bootstrap_module, "run_transport", fake_run_transport)

    main()

    assert called["run_transport_app"] is app
    assert called["create_server_config"] is called["run_transport_config"]
