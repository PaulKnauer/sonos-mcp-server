# Story 4.1: Run SoniqMCP over Streamable HTTP

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to run the server remotely over `Streamable HTTP`,
so that I can use it from trusted devices and deployed MCP clients on my home network.

## Acceptance Criteria

1. Given a valid deployment configuration, when the user starts the server with `SONIQ_MCP_TRANSPORT=http`, then the server exposes the MCP tool surface over `Streamable HTTP`.
2. Given the server is running in HTTP mode, when a client invokes tools, the remote mode uses the same underlying tool and service boundaries as `stdio` — no tool logic changes are required.
3. Given the server is started in HTTP mode, then the transport-specific bootstrap remains isolated from domain logic (tools and services are unaware of transport).
4. Given the server is configured with `SONIQ_MCP_EXPOSURE=home-network`, then the remote startup path supports the documented home-network trust model and emits appropriate posture guidance.

## Tasks / Subtasks

- [ ] Extend `TransportMode` and `ExposurePosture` enums in `config/models.py` (AC: 1, 4)
  - [ ] Add `HTTP = "http"` to `TransportMode` enum
  - [ ] Add `HOME_NETWORK = "home-network"` to `ExposurePosture` enum
  - [ ] Add `http_host: str = Field(default="127.0.0.1", ...)` to `SoniqConfig`
  - [ ] Add `http_port: int = Field(default=8000, ge=1, le=65535, ...)` to `SoniqConfig`

- [ ] Update `config/defaults.py` with HTTP defaults (AC: 1, 4)
  - [ ] Add `"http_host": "127.0.0.1"` and `"http_port": 8000` to `DEFAULTS`

- [ ] Update `config/loader.py` to read HTTP env vars (AC: 1, 4)
  - [ ] Add `"SONIQ_MCP_HTTP_HOST": "http_host"` to `_ENV_MAP`
  - [ ] Add `"SONIQ_MCP_HTTP_PORT": "http_port"` to `_ENV_MAP`

- [ ] Create `transports/streamable_http.py` (AC: 1, 3)
  - [ ] Implement `run_streamable_http(app: FastMCP, config: SoniqConfig) -> None`
  - [ ] Log startup with `host`, `port`, and path before calling `app.run(transport="streamable-http")`
  - [ ] Implement `streamable_http_transport_name() -> str` returning `"streamable-http"` (follows `stdio.py` pattern)

- [ ] Update `transports/bootstrap.py` to dispatch HTTP transport (AC: 1, 3)
  - [ ] Add branch: `if config.transport == TransportMode.HTTP: from soniq_mcp.transports.streamable_http import run_streamable_http; run_streamable_http(app, config)`
  - [ ] Import is lazy (inside the branch) — same pattern as the stdio branch

- [ ] Update `server.py` to pass `host` and `port` to `FastMCP` (AC: 1, 3)
  - [ ] Change `FastMCP("soniq-mcp")` to `FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)`
  - [ ] These values are ignored by the stdio transport but must be set for HTTP transport to bind correctly

- [ ] Update `domain/safety.py` to support `HOME_NETWORK` posture (AC: 4)
  - [ ] In `validate_exposure_posture`, allow `HOME_NETWORK` without the "not yet fully supported" warning
  - [ ] Emit an informational warning when `HOME_NETWORK` is active: "home-network exposure: server is bound to `{config.http_host}:{config.http_port}` — ensure this is only reachable from your trusted home network"
  - [ ] Keep the existing warning for any other unexpected posture values

- [ ] Write automated tests (AC: 1, 2, 3, 4)
  - [ ] `tests/unit/config/test_http_config.py` — unit tests for new `TransportMode.HTTP`, `ExposurePosture.HOME_NETWORK`, `http_host` / `http_port` fields: valid values, env var loading, int coercion for port, out-of-range port rejection
  - [ ] `tests/integration/transports/test_http_bootstrap.py` — integration tests: `create_server` succeeds with HTTP config, tool surface matches stdio, `run_transport` dispatches to HTTP (assert `NotImplementedError` is NOT raised), `TransportMode.HTTP` accepted by config validation
  - [ ] `tests/smoke/streamable_http/__init__.py` — empty init file
  - [ ] `tests/smoke/streamable_http/test_streamable_http_smoke.py` — smoke test that starts the server as a subprocess and connects via `streamable_http_client` (see Dev Notes for subprocess fixture pattern)
  - [ ] Run `make test` and confirm full suite passes with no regressions (597+ tests)

## Dev Notes

### Architecture Constraints (Must Follow)

- `transports/streamable_http.py` must NOT import from `tools/`, `services/`, or `adapters/` — transport modules are isolated at the boundary.
- `server.py` is the only place that creates `FastMCP`; transport modules receive the pre-built app.
- `config/models.py` comment already anticipates this change: "Later stories add HTTP transport and expanded exposure posture values."
- Tool handlers, services, and adapters are UNCHANGED by this story — the same 29 tools registered via `register_all` are served over HTTP without modification.
  [Source: `_bmad-output/planning-artifacts/architecture.md#API-Boundaries`]

### MCP SDK HTTP Transport API (v1.26.0)

`app.run(transport="streamable-http")` calls `anyio.run(self.run_streamable_http_async)` which starts uvicorn internally:

```python
# Internally (do not copy this):
config = uvicorn.Config(
    starlette_app,
    host=self.settings.host,    # comes from FastMCP constructor arg
    port=self.settings.port,    # comes from FastMCP constructor arg
    log_level=self.settings.log_level.lower(),
)
```

**Key FastMCP constructor args for HTTP:**

```python
FastMCP(
    "soniq-mcp",
    host="127.0.0.1",          # bind address — use config.http_host
    port=8000,                  # bind port — use config.http_port
    streamable_http_path="/mcp",  # default, do not change
)
```

**Default MCP endpoint path:** `/mcp` — this is where clients connect.

**DNS rebinding protection:** FastMCP auto-enables it when `host` is `127.0.0.1`, `localhost`, or `::1`. For `0.0.0.0` (home-network mode), it is NOT auto-enabled — which is correct since trusted-home-network clients need to connect.

`uvicorn` is available via `mcp[cli]` (no separate dependency needed). Current version: 0.42.0.

### `transports/streamable_http.py` — Complete Implementation

```python
"""Streamable HTTP transport for SoniqMCP.

Runs the MCP server over HTTP for cross-device home-network use.
Requires uvicorn (bundled via mcp[cli]).
"""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from soniq_mcp.config.models import SoniqConfig

log = logging.getLogger(__name__)


def run_streamable_http(app: FastMCP, config: SoniqConfig) -> None:
    """Start the MCP server using the Streamable HTTP transport."""
    log.info(
        "Starting SoniqMCP over Streamable HTTP transport host=%s port=%s path=/mcp",
        config.http_host,
        config.http_port,
    )
    app.run(transport="streamable-http")


def streamable_http_transport_name() -> str:
    """Return the canonical transport identifier."""
    return "streamable-http"
```

### `config/models.py` — Minimal Changes Required

Only two additions to the enums and two new fields on `SoniqConfig`. The `extra = "forbid"` model config is already in place — adding named fields is the correct pattern (do not break this constraint):

```python
class TransportMode(str, Enum):
    STDIO = "stdio"
    HTTP = "http"          # NEW


class ExposurePosture(str, Enum):
    LOCAL = "local"
    HOME_NETWORK = "home-network"  # NEW
```

Add to `SoniqConfig`:
```python
http_host: str = Field(
    default="127.0.0.1",
    description="Bind address for HTTP transport. Use '0.0.0.0' for home-network access.",
)
http_port: int = Field(
    default=8000,
    ge=1,
    le=65535,
    description="Bind port for HTTP transport.",
)
```

### `server.py` — Passing host/port to FastMCP

The ONLY change to `server.py` is passing `host` and `port` from config to `FastMCP`:

```python
app = FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)
```

These are silently ignored by the stdio transport, so this change has no stdio regression risk.

### `domain/safety.py` — Updated `validate_exposure_posture`

```python
def validate_exposure_posture(config: SoniqConfig) -> list[str]:
    warnings: list[str] = []
    from soniq_mcp.config.models import ExposurePosture
    if config.exposure == ExposurePosture.HOME_NETWORK:
        warnings.append(
            f"home-network exposure: server will bind to {config.http_host}:{config.http_port} — "
            "ensure this host is reachable only from your trusted home network."
        )
    elif config.exposure != ExposurePosture.LOCAL:
        warnings.append(
            f"exposure '{config.exposure.value}' is not yet fully supported; "
            "defaulting to local-only behaviour."
        )
    return warnings
```

### `transports/bootstrap.py` — Adding HTTP Branch

```python
from soniq_mcp.config import SoniqConfig, TransportMode

def run_transport(app: FastMCP, config: SoniqConfig) -> None:
    if config.transport == TransportMode.STDIO:
        from soniq_mcp.transports.stdio import run_stdio
        run_stdio(app)
    elif config.transport == TransportMode.HTTP:
        from soniq_mcp.transports.streamable_http import run_streamable_http
        run_streamable_http(app, config)
    else:
        raise NotImplementedError(
            f"Transport '{config.transport.value}' is not yet implemented"
        )
```

### Smoke Test — Starting the HTTP Server as a Subprocess

The HTTP smoke test must start the server in a subprocess (uvicorn blocks the process). Use `subprocess.Popen` with a fixed test port, wait briefly for readiness, then connect:

```python
import os
import subprocess
import sys
import time

import anyio
import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

_TEST_PORT = 18431  # use a high port unlikely to conflict


@pytest.fixture(scope="module")
def http_server_proc():
    env = {
        **os.environ,
        "SONIQ_MCP_TRANSPORT": "http",
        "SONIQ_MCP_HTTP_HOST": "127.0.0.1",
        "SONIQ_MCP_HTTP_PORT": str(_TEST_PORT),
        "SONIQ_MCP_EXPOSURE": "local",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "soniq_mcp"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)  # allow uvicorn to start
    yield proc
    proc.terminate()
    proc.wait(timeout=5)


class TestStreamableHTTPSmoke:
    def test_client_can_initialize_and_call_ping(self, http_server_proc) -> None:
        async def run_session() -> None:
            url = f"http://127.0.0.1:{_TEST_PORT}/mcp"
            async with streamable_http_client(url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    tools = await session.list_tools()
                    tool_names = [tool.name for tool in tools.tools]
                    assert "ping" in tool_names

                    result = await session.call_tool("ping")
                    assert result.isError is False
                    assert [item.text for item in result.content] == ["pong"]

        anyio.run(run_session)
```

**Important:** `streamable_http_client` yields 3 values: `(read_stream, write_stream, get_session_id_callback)` — the `_` unpacks the session ID callback. Do NOT use 2-value unpacking (this is different from `stdio_client`).

### Integration Test — HTTP Bootstrap (No uvicorn Required)

The integration test validates config + dispatch logic without actually starting uvicorn:

```python
from unittest.mock import patch

from soniq_mcp.config.models import SoniqConfig, TransportMode, ExposurePosture
from soniq_mcp.server import create_server
from soniq_mcp.transports.bootstrap import run_transport


def test_create_server_with_http_config():
    cfg = SoniqConfig(transport=TransportMode.HTTP, http_host="127.0.0.1", http_port=9999)
    app = create_server(config=cfg)
    assert isinstance(app, FastMCP)
    # verify host/port were passed through
    assert app.settings.host == "127.0.0.1"
    assert app.settings.port == 9999


def test_http_server_exposes_same_tool_surface():
    http_cfg = SoniqConfig(transport=TransportMode.HTTP)
    stdio_cfg = SoniqConfig(transport=TransportMode.STDIO)
    http_app = create_server(config=http_cfg)
    stdio_app = create_server(config=stdio_cfg)
    http_tools = {t.name for t in http_app._tool_manager.list_tools()}
    stdio_tools = {t.name for t in stdio_app._tool_manager.list_tools()}
    assert http_tools == stdio_tools


def test_run_transport_dispatches_to_http():
    cfg = SoniqConfig(transport=TransportMode.HTTP)
    app = create_server(config=cfg)
    with patch("soniq_mcp.transports.streamable_http.run_streamable_http") as mock_run:
        run_transport(app, cfg)
        mock_run.assert_called_once_with(app, cfg)


def test_home_network_exposure_emits_warning():
    from soniq_mcp.domain.safety import validate_exposure_posture
    cfg = SoniqConfig(exposure=ExposurePosture.HOME_NETWORK)
    warnings = validate_exposure_posture(cfg)
    assert len(warnings) == 1
    assert "home-network" in warnings[0]
```

### Configuration Reference for HTTP Mode

| Env Var | Default | Description |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `stdio` | Set to `http` to enable Streamable HTTP |
| `SONIQ_MCP_HTTP_HOST` | `127.0.0.1` | Bind address — use `0.0.0.0` for home-network access |
| `SONIQ_MCP_HTTP_PORT` | `8000` | Bind port |
| `SONIQ_MCP_EXPOSURE` | `local` | Set to `home-network` when binding to `0.0.0.0` |

**MCP endpoint URL:** `http://<host>:<port>/mcp`

**Typical home-network launch:**
```bash
SONIQ_MCP_TRANSPORT=http SONIQ_MCP_HTTP_HOST=0.0.0.0 SONIQ_MCP_HTTP_PORT=8000 SONIQ_MCP_EXPOSURE=home-network soniq-mcp
```

### Existing Test That References TransportMode

`tests/smoke/stdio/test_entrypoint_smoke.py::TestEntrypointBadConfig::test_bad_transport_exits_nonzero` currently sets `SONIQ_MCP_TRANSPORT=not-a-transport` and expects a `SystemExit`. This still works because `"not-a-transport"` is not `"http"` or `"stdio"`. No changes needed to the stdio smoke tests.

`tests/integration/transports/test_server_bootstrap.py::test_run_transport_raises_for_unsupported` uses a `MagicMock` transport. This continues to hit the `else: raise NotImplementedError` branch. No changes needed.

### Files to Create

```text
src/soniq_mcp/transports/streamable_http.py
tests/smoke/streamable_http/__init__.py
tests/smoke/streamable_http/test_streamable_http_smoke.py
tests/integration/transports/test_http_bootstrap.py
tests/unit/config/test_http_config.py
```

### Files to Modify

```text
src/soniq_mcp/config/models.py       (add HTTP + HOME_NETWORK enums, http_host + http_port fields)
src/soniq_mcp/config/defaults.py     (add http_host + http_port defaults)
src/soniq_mcp/config/loader.py       (add SONIQ_MCP_HTTP_HOST + SONIQ_MCP_HTTP_PORT to _ENV_MAP)
src/soniq_mcp/transports/bootstrap.py  (add HTTP branch to run_transport)
src/soniq_mcp/server.py              (pass host + port to FastMCP constructor)
src/soniq_mcp/domain/safety.py       (support HOME_NETWORK in validate_exposure_posture)
```

### Previous Story Intelligence

- Story 3.3 completed with 597 tests passing. Full test run via `make test` must still pass.
- The `create_server` test in `test_server_bootstrap.py` uses `SoniqConfig(transport=TransportMode.STDIO)` — adding `HTTP` to the enum does not break this.
- All tools are wired via `register_all` in `tools/__init__.py` — no changes needed to tools for HTTP support.
- Do NOT add new MCP tool names to `KNOWN_TOOL_NAMES` in this story — no new tools are introduced.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
