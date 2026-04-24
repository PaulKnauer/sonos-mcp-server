# Story 1.3: Preserve Backward Compatibility for Disabled Auth

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an existing SoniqMCP user,
I want upgrading to v0.6.0 to preserve current behavior unless I opt into auth,
so that local and existing HTTP deployments continue working without migration.

## Acceptance Criteria

1. Given `auth_mode=none`, when `create_server()` builds the FastMCP app, then no `auth` or `token_verifier` argument is passed.
2. Given existing env vars from a pre-auth deployment, when the server starts, then startup behavior remains unchanged.
3. Given stdio transport is used, when auth fields are absent, then tool registration and server startup remain unchanged.
4. Given tests inspect the disabled-auth path, when compared to current server construction behavior, then no auth module is imported or invoked.
5. Given the default config is serialized for diagnostics, when diagnostics output is produced, then no auth token field leaks a secret value.

## Tasks / Subtasks

- [x] Prove the `auth_mode=none` server-construction path is a strict no-op in `server.py` (AC: 1, 2, 3, 4)
  - [x] Update [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) so auth wiring is guarded behind `config.auth_mode != AuthMode.NONE`.
  - [x] Keep the disabled path structurally equivalent to the current `FastMCP("soniq-mcp", host=..., port=...)` construction with no `auth=` or `token_verifier=` kwargs added under `auth_mode=none`.
  - [x] If helper imports for future auth wiring are needed, place them inside the guarded branch or a lazy helper so the disabled path does not import or execute auth code.
  - [x] Preserve the existing order of operations: preflight, exposure warnings, `FastMCP` construction, tool registration, then startup logging.

- [x] Preserve startup and tool-surface behavior for current deployments (AC: 2, 3)
  - [x] Confirm [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py) remains unchanged for `AUTH_MODE=none`: same preflight entrypoint, same stderr handling, same logging bootstrap sequence.
  - [x] Keep stdio and HTTP startup behavior unchanged when auth is not configured, including current host/port handling and tool registration.
  - [x] Do not introduce warnings, log noise, or additional config requirements for the default unauthenticated path.

- [x] Add disabled-auth regression tests at the right layers (AC: 1, 2, 3, 4, 5)
  - [x] Extend [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) to assert that `create_server(SoniqConfig(auth_mode="none"))` produces a `FastMCP` instance with `settings.auth is None` and no token verifier attached.
  - [x] Add a unit test that patches or spies on any future auth-builder import path to prove it is not called for `auth_mode=none`.
  - [x] Extend [tests/integration/transports/test_server_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_server_bootstrap.py) and/or [tests/integration/transports/test_http_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_http_bootstrap.py) to confirm stdio and HTTP still expose the same tool surface when auth is disabled.
  - [x] Add or extend a diagnostic-safety test around `SoniqConfig().model_dump()` / repr behavior so the default config does not leak a raw auth token and the field remains masked if present.

- [x] Keep Story 1.3 scoped to backward compatibility only (AC: 1, 2, 3, 4, 5)
  - [x] Do not implement `src/soniq_mcp/auth/verifiers.py` in this story.
  - [x] Do not construct `AuthSettings` or a real `TokenVerifier` for `auth_mode=static` or `auth_mode=oidc` yet.
  - [x] Do not add JWT, JWKS, CA-bundle, or HTTP 401 handling in this story.
  - [x] Do not change tool modules, services, adapters, or transports; the focus is the disabled-auth server/bootstrap path only.

## Dev Notes

### Story Intent

This story is the backward-compatibility guardrail for the optional-auth feature set.

Stories 1.1 and 1.2 already added the auth config surface and preflight validation. Story 1.3 now proves the default path remains unchanged for existing users before Epic 2 and Epic 3 introduce real auth wiring.

The key outcome is architectural, not feature-visible:

- `auth_mode=none` remains the default;
- upgrading without new env vars behaves exactly as before;
- stdio stays untouched;
- HTTP without auth remains untouched;
- auth code is not imported or executed unless the operator opts in later.

If this story starts implementing `AuthSettings`, `TokenVerifier`, or request-time authentication, it has gone too far.

### What Already Exists

Current repo state relevant to this story:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) already defines `AuthMode` and defaults `auth_mode` to `none`.
- [src/soniq_mcp/config/defaults.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/defaults.py) already sets auth defaults to `None` / `"none"`.
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) already blocks bad auth config during preflight but returns cleanly for the default path.
- [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py) still calls `run_preflight()`, then `setup_logging()`, then `create_server(config)`.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) currently constructs `FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)` with no auth kwargs at all.
- Existing unit, integration, and smoke tests already verify startup, transport parity, and safe diagnostics for non-auth flows.

That makes Story 1.3 a regression-proofing story: establish tests and minimal guarded structure now so later auth wiring can land without breaking the common path.

### Previous Story Intelligence

Relevant learnings from Stories 1.1 and 1.2:

- Story 1.1 established `AuthMode` in `config/models.py` and added `SecretStr`-backed `auth_token`; tests were corrected to avoid `get_secret_value()` use outside verifier code.
- Story 1.2 kept auth validation in `run_preflight()` and preserved stdio as a non-blocking path; no auth module or `server.py` wiring was introduced.
- Recent implementation cadence confirms this sequence:
  - `ff3ee53` completed the optional-auth config model story.
  - `c7c04c8` completed the auth preflight validation story.

Use those decisions as constraints. Story 1.3 should prepare for later server wiring without prematurely creating the auth runtime path.

### Architecture Guardrails

- `AUTH_MODE=none` is a hard no-op requirement. The PRD calls backward compatibility a hard constraint and states the default path must remain unchanged for existing deployments.
- Auth is a transport concern only. Do not put auth logic into `tools/`, `services/`, `adapters/`, or `transports/`.
- The architecture requires future auth wiring to happen only in `create_server()` and explicitly says `AUTH_MODE=none` must leave the `FastMCP()` constructor equivalent to current behavior.
- `stdio` must remain unaffected. The architecture and PRD both treat auth as HTTP-only, with stdio staying unchanged for normal local use.
- Secret masking discipline remains in force: use `SecretStr` behavior as-is; do not unwrap `auth_token` in this story.

### Implementation Guidance

Preferred implementation shape:

- Import `AuthMode` in `server.py` if needed and create a guarded branch such as `if config.auth_mode != AuthMode.NONE:`.
- Keep the branch empty of real auth logic for now unless a minimal placeholder is necessary for future-proofing. If you add a placeholder, it must not alter the disabled path and must not require auth imports on module import.
- If you need to reference a future `build_token_verifier()` or `_build_auth_settings()` seam, use tests to lock down that it is not invoked for `auth_mode=none`; do not implement the real auth runtime here.
- Preserve `register_all(app, config)` and the existing startup log message behavior exactly for the disabled path.

For AC 4 specifically:

- The strongest proof is a test that patches the future auth integration seam and asserts it is not called when `auth_mode=none`.
- A secondary proof is inspection of the resulting `FastMCP` instance: `app.settings.auth is None`.
- If the SDK surface exposes a private verifier attribute, it is acceptable for tests to assert it remains `None` because this story is about guarding bootstrap wiring, not public API ergonomics.

For AC 5 specifically:

- The default config should continue to serialize cleanly with `auth_token=None`.
- If a token is present in a non-default config used by tests, serialization/repr must still show masking, not the raw token.
- Do not create a custom serializer that changes current `SecretStr` masking semantics.

### Expected File Touches

Likely to modify:

- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)
- [tests/integration/transports/test_server_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_server_bootstrap.py)
- [tests/integration/transports/test_http_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_http_bootstrap.py)

Potentially inspect but avoid changing unless necessary:

- [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py)
- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [src/soniq_mcp/config/defaults.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/defaults.py)
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [tests/unit/config/test_models.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_models.py)

Do not change in this story:

- `src/soniq_mcp/auth/` runtime implementation
- `tests/unit/auth/test_verifiers.py`
- request-time HTTP auth behavior
- docs, Helm values, Docker examples, or release assets

### Testing Guidance

Minimum test expectations:

- `create_server(config=SoniqConfig(auth_mode="none"))` still returns a `FastMCP`.
- The disabled path still registers the expected tools for both stdio and HTTP.
- `FastMCP.settings.auth` remains `None` for the disabled path.
- No auth integration seam is imported or called when `auth_mode=none`.
- Diagnostics and serialization remain secret-safe.

Recommended test split:

- `tests/unit/test_server.py` for direct constructor assertions and auth-seam non-invocation.
- `tests/integration/transports/test_server_bootstrap.py` for stdio backward-compat checks.
- `tests/integration/transports/test_http_bootstrap.py` for HTTP parity under `auth_mode=none`.

Avoid adding smoke tests in this story unless a current gap cannot be covered elsewhere. The architecture plans static-auth smoke additions later; Story 1.3 should stay focused on no-op verification.

### Anti-Patterns To Avoid

- Do not create `src/soniq_mcp/auth/__init__.py` or `verifiers.py` yet.
- Do not pass `auth=None` or `token_verifier=None` explicitly just to “show intent”; AC 1 requires that no auth kwargs are passed.
- Do not add eager imports from `mcp.server.auth.*` to `server.py` for the disabled path.
- Do not change preflight behavior to emit new warnings for `auth_mode=none`.
- Do not loosen `SecretStr` handling or add custom debug output that might reveal token values.

### Latest Technical Notes

- The installed MCP SDK in this repo exposes `FastMCP.__init__(..., token_verifier: TokenVerifier | None = None, ..., auth: AuthSettings | None = None, ...)`, and the constructor validates that auth settings and verifier configuration must be supplied together when auth is enabled. That makes the `auth_mode=none` branch boundary important and testable.
- The official MCP Python SDK README currently documents v1.x as the stable line and shows auth integration through a `TokenVerifier` plus `AuthSettings` on `FastMCP`, which matches the local package inspection and confirms that auth should remain absent in the disabled path.
- Pydantic `SecretStr` still masks repr/JSON output by default unless a serializer explicitly unwraps it. That supports keeping Story 1.3 focused on regression tests rather than custom secret-handling code.

### Project Structure Notes

- The repo’s composition boundary remains `src/soniq_mcp/server.py`; transport runners live under `src/soniq_mcp/transports/`.
- The current tests already separate unit bootstrap coverage from transport integration coverage; follow that pattern rather than inventing an auth-specific compatibility suite.
- Optional-auth implementation artifacts live under [`_bmad-output/implementation-artifacts/optional-auth`](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth:1); keep this story aligned with that track rather than the legacy Phase 2 tracker.
- No `project-context.md` file was present in this repo during story creation, so the story relies on the PRD, architecture, prior stories, current code, and local package inspection.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-13-Preserve-Backward-Compatibility-for-Disabled-Auth]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Additional-Requirements]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Executive-Summary]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Technical-Success]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Migration-Guide]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- [Source: _bmad-output/implementation-artifacts/optional-auth/1-1-add-optional-auth-configuration-model.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/1-2-validate-auth-configuration-during-preflight.md]
- [Source: src/soniq_mcp/server.py]
- [Source: src/soniq_mcp/__main__.py]
- [Source: src/soniq_mcp/config/models.py]
- [Source: src/soniq_mcp/config/defaults.py]
- [Source: src/soniq_mcp/config/validation.py]
- [Source: tests/unit/test_server.py]
- [Source: tests/integration/transports/test_server_bootstrap.py]
- [Source: tests/integration/transports/test_http_bootstrap.py]
- [Source: tests/smoke/stdio/test_entrypoint_smoke.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/settings.py]
- [Source: https://github.com/modelcontextprotocol/python-sdk]
- [Source: https://docs.pydantic.dev/2.8/examples/secrets/]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (Story 1.3 implementation)

### Debug Log References

- Story created from the optional-auth sprint tracker, Epic 1 story definition, prior optional-auth implementation artifacts, current server/bootstrap code, local MCP SDK package inspection, and current official MCP SDK / Pydantic docs.

### Completion Notes List

- Created a dedicated implementation-ready story for optional-auth Story 1.3 with concrete file targets and regression-focused scope.
- Captured current `server.py` behavior so the dev agent can preserve the exact disabled-auth bootstrap path.
- Pulled forward Story 1.1 and 1.2 learnings to prevent early `auth/` runtime implementation or secret-handling regressions.
- Added explicit guardrails for AC 1 and AC 4: no `auth` / `token_verifier` kwargs on the default path and no auth seam invocation under `auth_mode=none`.
- Included latest technical notes from local package inspection and current official docs for FastMCP auth integration and `SecretStr` masking.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- **Implementation (2026-04-24):** Added `_build_auth_kwargs()` seam to `server.py` and guarded it behind `config.auth_mode != AuthMode.NONE`. The disabled path remains structurally equivalent: `FastMCP("soniq-mcp", host=..., port=...)` with no auth kwargs. Also imported `AuthMode` in `server.py`. No `auth/` runtime was created.
- Added `TestDisabledAuthNoOp` class to `tests/unit/test_server.py` (5 tests): verifies `FastMCP` returned, `settings.auth is None`, `_token_verifier is None`, auth seam not invoked via monkeypatch, and tools registered.
- Added `TestDiagnosticSafety` class to `tests/unit/test_server.py` (3 tests): verifies default config dumps cleanly, `SecretStr` token masked in repr, and masked in `model_dump_json`.
- Added `TestDisabledAuthStdioBackwardCompat` to `tests/integration/transports/test_server_bootstrap.py` (3 tests): confirms stdio with explicit `auth_mode=none` returns `FastMCP`, same tool surface as default, and `settings.auth is None`.
- Added `TestDisabledAuthHttpBackwardCompat` to `tests/integration/transports/test_http_bootstrap.py` (5 tests): confirms HTTP with `auth_mode=none` returns `FastMCP`, same tool surface as default, `settings.auth is None`, `_token_verifier is None`, and exposes all expected tools.
- Full regression: 1490 passed, 3 skipped. Linting clean.

### File List

- `_bmad-output/implementation-artifacts/optional-auth/1-3-preserve-backward-compatibility-for-disabled-auth.md`
- `src/soniq_mcp/server.py`
- `tests/unit/test_server.py`
- `tests/integration/transports/test_server_bootstrap.py`
- `tests/integration/transports/test_http_bootstrap.py`
- `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml`

### Change Log

- **2026-04-24:** Added `_build_auth_kwargs()` seam and `AuthMode` import to `server.py`; guarded future auth wiring behind `config.auth_mode != AuthMode.NONE` in `create_server()`. Added `TestDisabledAuthNoOp` and `TestDiagnosticSafety` unit test classes (8 new tests). Added `TestDisabledAuthStdioBackwardCompat` (3 tests) and `TestDisabledAuthHttpBackwardCompat` (5 tests) integration test classes. Full suite: 1490 passed, 0 regressions.
