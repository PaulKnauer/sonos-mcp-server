# Story 1.4: Enforce Safe Defaults and Tool Exposure Controls

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want safe default behavior and controllable tool exposure,
so that AI clients cannot cause unnecessary disruption in my home environment.

## Acceptance Criteria

1. Given the server is configured for home use, when a user reviews or applies runtime settings, then the default exposure posture assumes local or trusted-home-network usage.
2. Given a client ecosystem that supports MCP permission-aware tool restriction, when the server is configured, then tool restriction settings are supported.
3. Given risky actions such as volume changes are available, when they are invoked, then they are subject to explicit validation and safety rules.
4. Given the configured trust model, when the server starts, then it does not expose functionality beyond that model by default.

## Tasks / Subtasks

- [x] Extend config and domain models for safety controls (AC: 1, 2, 3, 4)
  - [x] Add explicit safe-default exposure settings
  - [x] Add tool restriction configuration surfaces compatible with MCP client permission models
  - [x] Add safety-oriented settings for risky actions such as volume changes
- [x] Implement safety rule evaluation (AC: 1, 3, 4)
  - [x] Add domain safety helpers in `domain/safety.py`
  - [x] Ensure volume and trust-boundary checks can be reused by later control stories
  - [x] Keep the rule evaluation transport-agnostic
- [x] Wire tool exposure controls into startup and registration flow (AC: 2, 4)
  - [x] Ensure disabled or restricted capabilities are not exposed by default when configuration says so
  - [x] Keep the implementation compatible with local-first operation
- [x] Add diagnostics and validation feedback for safety config (AC: 1, 2, 3, 4)
  - [x] Explain invalid or conflicting safety settings clearly
  - [x] Avoid vague failure modes that force users to reverse engineer behavior
- [x] Test safety and permission behavior (AC: 1, 2, 3, 4)
  - [x] Add unit tests for safety rules and config combinations
  - [x] Add integration coverage for tool exposure behavior
  - [x] Cover malformed, risky, and out-of-range input cases

## Dev Notes

- Depends on Stories 1.1 to 1.3, especially the config model and local bootstrap.
- The PRD makes safe defaults, permission-aware tool restrictions, and non-disruptive home behavior first-class product requirements, not optional hardening.
- MVP has no built-in end-user auth system. Safety in this story is about exposure posture, permission-aware tool restriction compatibility, and domain-level safeguards.
- The system must default to local or trusted home-network use. Public exposure is always an explicit user choice outside this story’s default path.
- This story should prepare reusable safety boundaries for later Sonos features, especially volume-related actions.
- Keep user-facing messaging civil, clear, and corrective. Robustness matters more than configurability here.

### Project Structure Notes

- Primary implementation paths:
  - `src/soniq_mcp/config/models.py`
  - `src/soniq_mcp/config/validation.py`
  - `src/soniq_mcp/domain/safety.py`
  - `src/soniq_mcp/domain/exceptions.py`
  - `src/soniq_mcp/schemas/errors.py`
  - `src/soniq_mcp/server.py`
  - `tests/unit/domain/`
  - `tests/unit/config/`
  - `tests/contract/error_mapping/`
- Do not implement safety rules as ad hoc checks scattered across tool handlers.
- Keep restriction and safety decisions in shared config/domain layers so later stories inherit them.

### References

- Story source and acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#story-14-enforce-safe-defaults-and-tool-exposure-controls]
- Authentication, security, and safe-default architecture decisions: [Source: _bmad-output/planning-artifacts/architecture.md#authentication--security]
- Error handling and safety process patterns: [Source: _bmad-output/planning-artifacts/architecture.md#process-patterns]
- Safety and permission structure mapping: [Source: _bmad-output/planning-artifacts/architecture.md#requirements-to-structure-mapping]
- FR46-F49 and security/reliability NFRs: [Source: _bmad-output/planning-artifacts/prd.md#permission-safety-and-control-boundaries] [Source: _bmad-output/planning-artifacts/prd.md#security] [Source: _bmad-output/planning-artifacts/prd.md#reliability]
- Domain-specific trust and risk constraints: [Source: _bmad-output/planning-artifacts/prd.md#domain-specific-requirements]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (container-use environment: working-warthog)

### Debug Log References

- Environment had no Python — installed python3.12 + uv via apt/pip.
- Review follow-up pass: ran targeted safety tests, then full `pytest` (`118 passed`).

### Completion Notes List

- `SoniqConfig` extended with `max_volume_pct` (default 80, 0-100) and `tools_disabled` (default []).
- `domain/safety.py`: `check_volume()` raises `VolumeCapExceeded` (not silent clamp), `is_tool_permitted()` / `assert_tool_permitted()`, `validate_exposure_posture()` hook for Story 4.
- `domain/exceptions.py`: `SoniqDomainError`, `VolumeCapExceeded`, `ToolNotPermitted` — all with actionable messages.
- `schemas/errors.py`: `ErrorResponse` pydantic model with factory methods for common error types.
- Tool registration in `setup_support.py` skips tools listed in `tools_disabled` at startup time.
- `server.py` calls `validate_exposure_posture()` and logs any warnings before creating the app.
- Loader supports `SONIQ_MCP_MAX_VOLUME_PCT` and `SONIQ_MCP_TOOLS_DISABLED` (comma-separated).
- 40 tests passing (unit domain + config + integration + contract).
- Review findings addressed: `tools_disabled` now rejects unknown tool names with corrective messages.
- Review findings addressed: invalid `SONIQ_MCP_MAX_VOLUME_PCT` values now flow through field-level validation so preflight errors name `max_volume_pct`.
- Review findings addressed: setup-support tools now publish MCP `ToolAnnotations` safety hints for permission-aware clients.
- Full suite currently passing: `118` tests.

### File List

- `src/soniq_mcp/config/models.py`
- `src/soniq_mcp/config/defaults.py`
- `src/soniq_mcp/config/loader.py`
- `src/soniq_mcp/config/validation.py`
- `src/soniq_mcp/domain/exceptions.py`
- `src/soniq_mcp/domain/safety.py`
- `src/soniq_mcp/schemas/errors.py`
- `src/soniq_mcp/tools/setup_support.py`
- `src/soniq_mcp/server.py`
- `tests/unit/domain/__init__.py`
- `tests/unit/domain/test_safety.py`
- `tests/unit/config/test_safety_config.py`
- `tests/integration/domain/__init__.py`
- `tests/integration/domain/test_tool_exposure.py`
- `tests/contract/error_mapping/__init__.py`
- `tests/contract/error_mapping/test_error_schemas.py`

## Change Log

- 2026-03-25: Story 1.4 implemented. Safety controls: volume cap, tool disable list, exposure posture validation, error schemas. 40 tests passing. Status → review.
- 2026-03-25: Review follow-up fixes. Added `tools_disabled` validation, improved `max_volume_pct` env validation messaging, added MCP tool safety annotations, expanded tests. Full suite passing (`118`).
