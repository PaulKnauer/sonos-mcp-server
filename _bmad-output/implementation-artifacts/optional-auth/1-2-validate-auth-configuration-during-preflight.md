# Story 1.2: Validate Auth Configuration During Preflight

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator,
I want invalid auth configuration to fail before the server accepts requests,
so that setup errors are caught early with actionable feedback.

## Acceptance Criteria

1. Given `auth_mode=static` and no auth token is configured, when preflight runs, then it fails with a clear missing-token error.
2. Given `auth_mode=oidc` and no issuer is configured, when preflight runs, then it fails with a clear missing-issuer error.
3. Given `auth_mode=none`, when preflight runs, then no auth-specific validation failure occurs.
4. Given auth is configured while running stdio transport, when preflight runs, then stdio startup is not blocked.
5. Given a validation failure occurs, when the error is reported, then it does not include the raw static token.

## Tasks / Subtasks

- [x] Extend auth-specific preflight validation in `config/validation.py` (AC: 1, 2, 3, 4, 5)
  - [x] Update [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) so `run_preflight()` explicitly enforces auth preflight rules rather than leaving Story 1.2 behavior implicit.
  - [x] Add a focused auth-validation helper in `config/validation.py` that runs after `load_config()` succeeds and before runtime startup proceeds.
  - [x] Fail preflight for `auth_mode=static` over HTTP when `auth_token` is missing, with a clear, user-facing message that names the missing field but never prints the secret value.
  - [x] Preserve the existing `auth_mode=oidc` missing-issuer failure during `run_preflight()`; if validation ownership is refactored between `models.py` and `validation.py`, keep behavior equivalent and avoid reintroducing stdio blocking.
  - [x] Ensure `auth_mode=none` remains a clean no-op in preflight.

- [x] Preserve stdio behavior as a non-blocking path for auth-configured local use (AC: 4, 5)
  - [x] Ensure `transport=stdio` with auth-related config present does not raise a `ConfigValidationError`.
  - [x] If the implementation emits a warning for stdio+auth, keep it non-secret, human-readable, and compatible with the existing startup flow that calls `run_preflight()` before `setup_logging()`.
  - [x] Do not make stdio behavior depend on any auth verifier, network call, or FastMCP auth wiring in this story.

- [x] Strengthen test coverage at the correct layers (AC: 1, 2, 3, 4, 5)
  - [x] Extend [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py) for missing static token, `auth_mode=none` pass-through, stdio non-blocking behavior, and no-secret-in-message assertions.
  - [x] Extend [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py) so startup-preflight behavior is exercised as an integration boundary, not only via unit tests.
  - [x] Extend [tests/smoke/stdio/test_entrypoint_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/stdio/test_entrypoint_smoke.py) only if needed to prove entrypoint error output stays clean and secret-safe.

- [x] Keep Story 1.2 scoped to preflight only (AC: 1, 2, 3, 4, 5)
  - [x] Do not add `src/soniq_mcp/auth/` in this story.
  - [x] Do not wire `token_verifier` or `AuthSettings` into [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) in this story.
  - [x] Do not add live JWKS connectivity checks yet; those belong to Story 3.3.
  - [x] Do not add docs, Helm values, or HTTP auth request handling here.

## Dev Notes

### Story Intent

This story is the startup-validation layer for the auth config surface introduced in Story 1.1.

The key outcome is operational:

- invalid auth config should fail before normal startup continues;
- valid config should pass cleanly;
- stdio should remain usable even if auth fields are present;
- no secret values should leak into user-facing diagnostics.

This is still a `config/`-only story. Nothing below the preflight boundary should change yet.

### What Already Exists

After Story 1.1, the repo already has:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) with `AuthMode`, auth fields, `SecretStr` masking for `auth_token`, and a model validator that currently enforces missing OIDC issuer for HTTP while allowing stdio.
- [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py) with all auth env-var mappings.
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) that currently wraps `load_config()` and reformats validation errors into `ConfigValidationError`.
- [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py) that calls `run_preflight()` before logging setup and prints user-facing configuration errors to stderr.

That means Story 1.2 should build on the existing `run_preflight()` path rather than creating a second validation entrypoint.

### Previous Story Intelligence

Relevant learnings from Story 1.1:

- The code review uncovered that `auth_mode=oidc` must not hard-fail on stdio before preflight can apply the architecture’s non-blocking stdio rule.
- Tests were corrected so `SecretStr.get_secret_value()` is not used outside verifier code.
- The current codebase already satisfies the missing-issuer case during `run_preflight()` for HTTP because `load_config()` raises a validation error that `run_preflight()` surfaces.

Use that as the baseline. Story 1.2 should not regress the fixed stdio behavior just to “move” the missing-issuer rule around.

### Architecture Guardrails

- Preflight checks belong in [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py), not in verifier constructors and not in `server.py`. [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- Stdio transport with auth config must not be blocked; architecture frames this as warning-not-error behavior. Since `run_preflight()` executes before logging setup, any warning mechanism must work without relying on configured logging. [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- Secret-handling discipline remains in force: do not unwrap `config.auth_token`; rely on `SecretStr` masking and safe message construction. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- No auth logic may enter `tools/`, `services/`, `adapters/`, or runtime transport wiring in this story. [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Additional-Requirements]

### Implementation Guidance

Preferred implementation shape:

- Keep `run_preflight()` as the single public startup-validation function.
- Add a private helper such as `_validate_auth_preflight(config: SoniqConfig) -> list[str]` or equivalent if it improves clarity.
- Raise `ConfigValidationError` only for actual blocking misconfiguration.
- Treat stdio+auth as non-blocking; if you surface a warning, keep it explicit that auth is ignored on stdio and keep the message free of token content.

For missing-token behavior:

- This story is the first place where `auth_mode=static` must require `auth_token`.
- The error should point the operator at the missing config field, not at internal implementation details.

For missing-issuer behavior:

- Current behavior already fails cleanly for HTTP OIDC configs during `run_preflight()`.
- If refactoring that rule from `models.py` into `validation.py` makes the ownership cleaner, do it only if the resulting behavior remains the same for HTTP and still does not block stdio.

### Expected File Touches

Likely to modify:

- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py)
- [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py)
- [tests/smoke/stdio/test_entrypoint_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/stdio/test_entrypoint_smoke.py)

Potentially inspect but avoid changing unless necessary:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py)
- [src/soniq_mcp/logging_config.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/logging_config.py)

Do not change in this story:

- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- `src/soniq_mcp/auth/` (does not exist yet)
- request-time HTTP auth behavior

### Testing Guidance

Minimum test expectations:

- `run_preflight(overrides={"auth_mode": "static", "transport": "http"})` fails if `auth_token` is missing.
- `run_preflight(overrides={"auth_mode": "oidc", "transport": "http"})` fails if `oidc_issuer` is missing.
- `run_preflight(overrides={"auth_mode": "none"})` passes.
- `run_preflight(overrides={"auth_mode": "static", "transport": "stdio"})` does not raise.
- Error messages for auth failures do not include raw token values.
- Entrypoint stderr remains human-readable and non-secret for auth preflight failures.

There is already a solid unit/integration/smoke split in the repo for startup validation. Reuse it instead of inventing a new auth-specific test hierarchy.

### Anti-Patterns To Avoid

- Do not require `auth_token` for `auth_mode=static` on stdio if that would block local use.
- Do not move validation responsibility into future verifier constructors.
- Do not log or print `get_secret_value()` output.
- Do not add OIDC JWKS network checks yet.
- Do not make Story 1.2 depend on PyJWT, FastMCP auth classes, or transport middleware.

### Latest Technical Notes

- Pydantic’s official `SecretStr` docs still confirm masked `repr()`/`str()` behavior and masked JSON serialization by default, which is the right primitive for secret-safe preflight diagnostics.
- The current runtime flow still calls `run_preflight()` before `setup_logging()`, so anything that must be visible at preflight time should not depend on logger configuration.

### Project Structure Notes

- The repo already uses `run_preflight()` as the single startup gate and `ConfigValidationError` as the user-facing failure type.
- The existing `validate_exposure_posture()` pattern returns warnings instead of throwing immediately; that is a useful reference point for the “warning not error” stdio-auth rule, even if Story 1.2 chooses a different implementation detail.
- Story 1.2 should leave the public config surface stable for Stories 1.3, 2.1, and 3.x to consume.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-12-Validate-Auth-Configuration-During-Preflight]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Additional-Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Technical-Success]
- [Source: _bmad-output/implementation-artifacts/optional-auth/1-1-add-optional-auth-configuration-model.md]
- [Source: src/soniq_mcp/config/models.py]
- [Source: src/soniq_mcp/config/loader.py]
- [Source: src/soniq_mcp/config/validation.py]
- [Source: src/soniq_mcp/__main__.py]
- [Source: src/soniq_mcp/logging_config.py]
- [Source: src/soniq_mcp/domain/safety.py]
- [Source: tests/unit/config/test_validation.py]
- [Source: tests/integration/config/test_preflight_startup.py]
- [Source: tests/smoke/stdio/test_entrypoint_smoke.py]
- [Source: https://docs.pydantic.dev/2.2/usage/types/secrets/]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from optional-auth planning artifacts, current config/preflight code, Story 1.1 completion notes, and existing startup validation tests.

### Completion Notes List

- Story created with focused preflight-validation scope, concrete test targets, and explicit guardrails to avoid pulling verifier or server wiring into Story 1.2.
- Added `_validate_auth_preflight(config: SoniqConfig) -> list[str]` private helper to `validation.py`; called in `run_preflight()` after `load_config()` succeeds.
- Static HTTP missing-token check: `auth_mode=static` + `transport=http` + `auth_token is None` → `ConfigValidationError` naming the `auth_token` field.
- OIDC missing-issuer check preserved in `models.py` model validator (transport-aware: stdio allowed, HTTP blocked); `run_preflight()` surfaces this through existing Pydantic error handling.
- Stdio path remains fully non-blocking: `_validate_auth_preflight` short-circuits on `transport=stdio`.
- `SecretStr` masking means raw token values never appear in error messages; tests verify field-name-only message content.
- 13 new tests added: 7 unit (test_validation.py), 5 integration (test_preflight_startup.py), 3 smoke (test_entrypoint_smoke.py); 1154 unit+integration tests pass; lint clean.
- No `auth/` module created; no `server.py` changes; story boundaries preserved.

### File List

- `_bmad-output/implementation-artifacts/optional-auth/1-2-validate-auth-configuration-during-preflight.md`
- `src/soniq_mcp/config/validation.py`
- `tests/unit/config/test_validation.py`
- `tests/integration/config/test_preflight_startup.py`
- `tests/smoke/stdio/test_entrypoint_smoke.py`

### Change Log

- 2026-04-24: Implemented Story 1.2 — added `_validate_auth_preflight` helper to `validation.py`, blocking static-HTTP-no-token misconfiguration while keeping stdio non-blocking. All 5 ACs satisfied.
