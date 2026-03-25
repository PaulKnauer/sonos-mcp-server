# Story 1.3: Run SoniqMCP Locally over stdio

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to run the server locally with `stdio`,
so that I can use it directly from an MCP-capable AI client on the same machine.

## Acceptance Criteria

1. Given a valid local configuration, when the user starts the server in `stdio` mode, then the MCP server boots successfully and exposes the agreed tool surface.
2. Given the local runtime is started, when the implementation is reviewed, then it uses the same internal tool and service boundaries defined by the architecture.
3. Given the server is running locally, when a same-machine MCP-compatible AI client connects, then the client can connect successfully.
4. Given startup occurs, when diagnostics are emitted, then they are useful without exposing sensitive configuration.

## Tasks / Subtasks

- [x] Implement `stdio` transport bootstrap (AC: 1, 2)
  - [x] Add transport bootstrap code under `src/soniq_mcp/transports/stdio.py`
  - [x] Keep `server.py` and `transports/bootstrap.py` as the composition boundary
  - [x] Avoid direct `SoCo` calls from transport code
- [x] Establish the initial MCP server entry point (AC: 1, 2, 3)
  - [x] Create the base server initialization using the official MCP Python SDK
  - [x] Register a minimal initial tool surface appropriate for local setup and future extension
  - [x] Wire config loading and preflight into startup
- [x] Implement startup diagnostics and safe logging behavior (AC: 4)
  - [x] Add structured logging configuration
  - [x] Emit clear startup mode, validation, and failure messages
  - [x] Avoid leaking sensitive configuration values
- [x] Add local execution paths (AC: 1, 3)
  - [x] Ensure `__main__.py` or the configured CLI entry point can run local `stdio`
  - [x] Add `Makefile` targets or commands for local start/test paths
- [x] Test local `stdio` behavior (AC: 1, 2, 3, 4)
  - [x] Add integration tests for server bootstrap in `stdio` mode
  - [x] Add smoke coverage for process start and basic response behavior
  - [x] Keep tests independent of real Sonos hardware

## Dev Notes

- Depends on Stories 1.1 and 1.2. It should not start until the scaffold and configuration layer exist.
- The architecture explicitly sets `stdio` as the primary local transport. `Streamable HTTP` is a later story and should not distort this implementation.
- Keep transport-specific concerns at the boundary. Tool handlers remain thin and service-oriented even if early tools are placeholders.
- This story is about a viable local MCP endpoint and safe startup experience, not about full Sonos feature delivery.
- Logging and diagnostics are part of the user experience. Startup should be readable, deterministic, and free of sensitive config disclosure.
- The local path should be easy to call from future docs for Claude Desktop and similar MCP clients.

### Project Structure Notes

- Primary implementation paths:
  - `src/soniq_mcp/__main__.py`
  - `src/soniq_mcp/server.py`
  - `src/soniq_mcp/logging_config.py`
  - `src/soniq_mcp/transports/bootstrap.py`
  - `src/soniq_mcp/transports/stdio.py`
  - `src/soniq_mcp/tools/`
  - `tests/integration/transports/`
  - `tests/smoke/stdio/`
- Do not implement local transport inside docs, config, or service modules.
- If a temporary setup-support tool is needed for local verification, place it in `tools/setup_support.py`.

### References

- Story source and acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#story-13-run-soniqmcp-locally-over-stdio]
- API and communication decisions for `stdio`: [Source: _bmad-output/planning-artifacts/architecture.md#api--communication-patterns]
- Transport, logging, and error-boundary rules: [Source: _bmad-output/planning-artifacts/architecture.md#communication-patterns] [Source: _bmad-output/planning-artifacts/architecture.md#format-patterns]
- Project structure and smoke test expectations: [Source: _bmad-output/planning-artifacts/architecture.md#project-structure--boundaries]
- FR30, FR35, FR50 and related NFRs: [Source: _bmad-output/planning-artifacts/prd.md#mcp-client-and-agent-integration] [Source: _bmad-output/planning-artifacts/prd.md#documentation-examples-and-troubleshooting] [Source: _bmad-output/planning-artifacts/prd.md#integration]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (container-use environment: mighty-lacewing)

### Debug Log References

- Environment had no Python/uv — installed python3.12 via apt and uv via pip.
- Subprocess-based smoke tests timed out in slow ARM64 container; replaced with direct main() calls.
- Follow-up review fix added a real MCP stdio client/session smoke test to prove same-machine connectivity and `ping` tool invocation.

### Completion Notes List

- FastMCP server created via `create_server(config)` in `server.py` — composition boundary preserved.
- `tools/setup_support.py` provides `ping` and `server_info` tools for local verification.
- `logging_config.py` configures stderr logging without leaking config values.
- `__main__.py` catches `ConfigValidationError`, prints field-level messages, and exits 1 cleanly.
- `transports/bootstrap.py` dispatches to `run_stdio()` based on config; extensible for Story 4.1.
- `Makefile` gains `run-stdio` target.
- 26 tests passing (unit + integration + smoke).
- Review follow-up: `tests/smoke/stdio/test_entrypoint_smoke.py` now spawns `python -m soniq_mcp`, initializes an MCP `ClientSession` over stdio, lists tools, and calls `ping` to close the AC3 proof gap.
- Full suite after review fix: 114 tests passing.

### File List

- `src/soniq_mcp/__init__.py`
- `src/soniq_mcp/__main__.py`
- `src/soniq_mcp/server.py`
- `src/soniq_mcp/logging_config.py`
- `src/soniq_mcp/tools/__init__.py`
- `src/soniq_mcp/tools/setup_support.py`
- `src/soniq_mcp/transports/__init__.py`
- `src/soniq_mcp/transports/stdio.py`
- `src/soniq_mcp/transports/bootstrap.py`
- `tests/unit/test_server.py`
- `tests/unit/test_logging_config.py`
- `tests/unit/transports/__init__.py`
- `tests/unit/transports/test_bootstrap.py`
- `tests/unit/transports/test_stdio.py`
- `tests/integration/transports/__init__.py`
- `tests/integration/transports/test_server_bootstrap.py`
- `tests/smoke/stdio/__init__.py`
- `tests/smoke/stdio/test_entrypoint_smoke.py`
- `Makefile`

## Change Log

- 2026-03-25: Story 1.3 implemented. FastMCP stdio server with `ping`/`server_info` tools, safe logging, clean error handling. 26 tests passing. Status → review.
- 2026-03-25: Review follow-up implemented. Added end-to-end stdio MCP connectivity smoke coverage for client initialize/list_tools/call_tool(`ping`). Full suite: 114 passing.
