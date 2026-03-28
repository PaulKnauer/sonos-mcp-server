# Story 4.1: Run SoniqMCP over Streamable HTTP

Status: done

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

- [x] Extend `TransportMode` and `ExposurePosture` enums in `config/models.py` (AC: 1, 4)
  - [x] Add `HTTP = "http"` to `TransportMode` enum
  - [x] Add `HOME_NETWORK = "home-network"` to `ExposurePosture` enum
  - [x] Add `http_host: str = Field(default="127.0.0.1", ...)` to `SoniqConfig`
  - [x] Add `http_port: int = Field(default=8000, ge=1, le=65535, ...)` to `SoniqConfig`

- [x] Update `config/defaults.py` with HTTP defaults (AC: 1, 4)
  - [x] Add `"http_host": "127.0.0.1"` and `"http_port": 8000` to `DEFAULTS`

- [x] Update `config/loader.py` to read HTTP env vars (AC: 1, 4)
  - [x] Add `"SONIQ_MCP_HTTP_HOST": "http_host"` to `_ENV_MAP`
  - [x] Add `"SONIQ_MCP_HTTP_PORT": "http_port"` to `_ENV_MAP`

- [x] Create `transports/streamable_http.py` (AC: 1, 3)
  - [x] Implement `run_streamable_http(app: FastMCP, config: SoniqConfig) -> None`
  - [x] Log startup with `host`, `port`, and path before calling `app.run(transport="streamable-http")`
  - [x] Implement `streamable_http_transport_name() -> str` returning `"streamable-http"` (follows `stdio.py` pattern)

- [x] Update `transports/bootstrap.py` to dispatch HTTP transport (AC: 1, 3)
  - [x] Add branch: `if config.transport == TransportMode.HTTP: from soniq_mcp.transports.streamable_http import run_streamable_http; run_streamable_http(app, config)`
  - [x] Import is lazy (inside the branch) — same pattern as the stdio branch

- [x] Update `server.py` to pass `host` and `port` to `FastMCP` (AC: 1, 3)
  - [x] Change `FastMCP("soniq-mcp")` to `FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)`
  - [x] These values are ignored by the stdio transport but must be set for HTTP transport to bind correctly

- [x] Update `domain/safety.py` to support `HOME_NETWORK` posture (AC: 4)
  - [x] In `validate_exposure_posture`, allow `HOME_NETWORK` without the "not yet fully supported" warning
  - [x] Emit an informational warning when `HOME_NETWORK` is active: "home-network exposure: server is bound to `{config.http_host}:{config.http_port}` — ensure this is only reachable from your trusted home network"
  - [x] Keep the existing warning for any other unexpected posture values

- [x] Write automated tests (AC: 1, 2, 3, 4)
  - [x] `tests/unit/config/test_http_config.py` — unit tests for new `TransportMode.HTTP`, `ExposurePosture.HOME_NETWORK`, `http_host` / `http_port` fields: valid values, env var loading, int coercion for port, out-of-range port rejection
  - [x] `tests/integration/transports/test_http_bootstrap.py` — integration tests: `create_server` succeeds with HTTP config, tool surface matches stdio, `run_transport` dispatches to HTTP (assert `NotImplementedError` is NOT raised), `TransportMode.HTTP` accepted by config validation
  - [x] `tests/smoke/streamable_http/__init__.py` — empty init file
  - [x] `tests/smoke/streamable_http/test_streamable_http_smoke.py` — smoke test that starts the server as a subprocess and connects via `streamable_http_client`
  - [x] Run `make test` and confirm full suite passes with no regressions (635 passed, 3 skipped)

## Dev Notes

### Architecture Constraints (Must Follow)

- `transports/streamable_http.py` must NOT import from `tools/`, `services/`, or `adapters/` — transport modules are isolated at the boundary.
- `server.py` is the only place that creates `FastMCP`; transport modules receive the pre-built app.
- `config/models.py` comment already anticipates this change: "Later stories add HTTP transport and expanded exposure posture values."
- Tool handlers, services, and adapters are UNCHANGED by this story — the same 29 tools registered via `register_all` are served over HTTP without modification.
  [Source: `_bmad-output/planning-artifacts/architecture.md#API-Boundaries`]

### MCP SDK HTTP Transport API (v1.26.0)

`app.run(transport="streamable-http")` calls `anyio.run(self.run_streamable_http_async)` which starts uvicorn internally.

**Default MCP endpoint path:** `/mcp` — this is where clients connect.

**DNS rebinding protection:** FastMCP auto-enables it when `host` is `127.0.0.1`, `localhost`, or `::1`. For `0.0.0.0` (home-network mode), it is NOT auto-enabled — which is correct since trusted-home-network clients need to connect.

`uvicorn` is available via `mcp[cli]` (no separate dependency needed). Current version: 0.42.0.

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

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes List

- Added `TransportMode.HTTP = "http"` and `ExposurePosture.HOME_NETWORK = "home-network"` to config enums in `config/models.py`.
- Added `http_host: str` (default `"127.0.0.1"`) and `http_port: int` (default `8000`, range 1-65535) to `SoniqConfig`.
- Added `http_host` and `http_port` to `config/defaults.py` and wired `SONIQ_MCP_HTTP_HOST`/`SONIQ_MCP_HTTP_PORT` env vars in `config/loader.py`.
- Created `transports/streamable_http.py` with `run_streamable_http()` (calls `app.run(transport="streamable-http")`) and `streamable_http_transport_name()`.
- Updated `transports/bootstrap.py` with a lazy HTTP branch — same pattern as stdio.
- Updated `server.py` to pass `host=config.http_host, port=config.http_port` to `FastMCP` constructor; silently ignored by stdio transport.
- Updated `domain/safety.py`: `HOME_NETWORK` posture emits a trust-model reminder warning; `LOCAL` emits none; other unknown postures still emit "not yet fully supported".
- 38 new tests added across 3 new test files. Full suite: 635 passed, 3 skipped (pre-existing), zero regressions.
- HTTP smoke test starts the server as a subprocess bound to `127.0.0.1:18431`, connects via `streamable_http_client`, verifies `ping` returns `"pong"` and the tool surface is populated. Both smoke tests pass.
- `streamable_http_client` yields 3 values `(read_stream, write_stream, get_session_id_callback)` — unpack the third as `_`.
- Post-review hardening added config-level enforcement for HTTP exposure/bind combinations: `LOCAL` requires loopback bind, `HOME_NETWORK` requires non-loopback bind.
- Tightened HTTP parity verification from subset matching to exact tool-surface matching for all 30 registered tools.
- Reworked the HTTP smoke fixture to use dynamic port allocation, active readiness probing, and stderr capture on startup failure.
- Post-review validation: `uv run pytest tests/unit/config/test_http_config.py tests/integration/transports/test_http_bootstrap.py tests/smoke/streamable_http/test_streamable_http_smoke.py` → 45 passed; `uv run pytest` → 642 passed, 3 skipped.

### File List

- `src/soniq_mcp/config/models.py` (modified — added HTTP/HOME_NETWORK enums, http_host, http_port)
- `src/soniq_mcp/config/defaults.py` (modified — added http_host, http_port defaults)
- `src/soniq_mcp/config/loader.py` (modified — added SONIQ_MCP_HTTP_HOST, SONIQ_MCP_HTTP_PORT env mappings)
- `src/soniq_mcp/transports/streamable_http.py` (created)
- `src/soniq_mcp/transports/bootstrap.py` (modified — added HTTP dispatch branch)
- `src/soniq_mcp/server.py` (modified — pass host/port to FastMCP)
- `src/soniq_mcp/domain/safety.py` (modified — HOME_NETWORK posture support)
- `tests/unit/config/test_http_config.py` (created — 22 unit tests)
- `tests/integration/transports/test_http_bootstrap.py` (created — 16 integration tests)
- `tests/smoke/streamable_http/__init__.py` (created)
- `tests/smoke/streamable_http/test_streamable_http_smoke.py` (created — 2 smoke tests)
- `_bmad-output/implementation-artifacts/4-1-run-soniqmcp-over-streamable-http.md` (this file — status updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)
- `src/soniq_mcp/config/models.py` (modified — added HTTP exposure/bind consistency validator)
- `src/soniq_mcp/domain/safety.py` (modified — added explicit local/non-loopback unsafe warning path)
- `tests/unit/config/test_http_config.py` (modified — added validation coverage for local vs home-network bind rules)
- `tests/integration/transports/test_http_bootstrap.py` (modified — exact tool-surface assertion, unsafe local bind warning coverage)
- `tests/smoke/streamable_http/test_streamable_http_smoke.py` (modified — dynamic port allocation, readiness probing, stderr capture)

## Change Log

- 2026-03-28: Story closed — all tasks complete, all ACs satisfied, 635 tests passing. Status set to done.
- 2026-03-28: Post-review hardening applied. Enforced safe HTTP exposure/bind combinations, upgraded HTTP parity assertions to exact tool matching, and made the streamable HTTP smoke test deterministic. Full suite passes: 642 passed, 3 skipped.
