# Story 1.3: Run SoniqMCP Locally over stdio

Status: ready-for-dev

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

- [ ] Implement `stdio` transport bootstrap (AC: 1, 2)
  - [ ] Add transport bootstrap code under `src/soniq_mcp/transports/stdio.py`
  - [ ] Keep `server.py` and `transports/bootstrap.py` as the composition boundary
  - [ ] Avoid direct `SoCo` calls from transport code
- [ ] Establish the initial MCP server entry point (AC: 1, 2, 3)
  - [ ] Create the base server initialization using the official MCP Python SDK
  - [ ] Register a minimal initial tool surface appropriate for local setup and future extension
  - [ ] Wire config loading and preflight into startup
- [ ] Implement startup diagnostics and safe logging behavior (AC: 4)
  - [ ] Add structured logging configuration
  - [ ] Emit clear startup mode, validation, and failure messages
  - [ ] Avoid leaking sensitive configuration values
- [ ] Add local execution paths (AC: 1, 3)
  - [ ] Ensure `__main__.py` or the configured CLI entry point can run local `stdio`
  - [ ] Add `Makefile` targets or commands for local start/test paths
- [ ] Test local `stdio` behavior (AC: 1, 2, 3, 4)
  - [ ] Add integration tests for server bootstrap in `stdio` mode
  - [ ] Add smoke coverage for process start and basic response behavior
  - [ ] Keep tests independent of real Sonos hardware

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

gpt-5-codex

### Debug Log References

### Completion Notes List

### File List
