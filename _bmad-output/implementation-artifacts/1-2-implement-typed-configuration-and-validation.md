# Story 1.2: Implement Typed Configuration and Validation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want the server configuration validated before runtime,
so that setup mistakes are caught early and explained clearly.

## Acceptance Criteria

1. Given the server is started with configuration inputs, when configuration is loaded, then typed configuration models validate required fields, formats, and defaults.
2. Given invalid configuration, when startup begins, then normal runtime does not start.
3. Given invalid configuration, when validation fails, then errors identify the specific field or setting that must be corrected.
4. Given a supported setup, when configuration is evaluated, then it supports a single-household Sonos environment.

## Tasks / Subtasks

- [x] Build the configuration schema layer under `src/soniq_mcp/config/` (AC: 1, 4)
  - [x] Define typed config models in `models.py`
  - [x] Define sensible defaults in `defaults.py`
  - [x] Keep the config model aligned to single-household home use
- [x] Implement config loading and normalization (AC: 1)
  - [x] Support environment variables and file-based config inputs if both are part of the chosen design
  - [x] Normalize raw input before runtime use
  - [x] Keep the loader independent from transports and Sonos operations
- [x] Implement validation and preflight behavior (AC: 1, 2, 3, 4)
  - [x] Fail startup before normal runtime if required configuration is invalid
  - [x] Return actionable field-level validation messages
  - [x] Validate safe defaults and exposure posture inputs needed later by Story 1.4
- [x] Add example config artifacts (AC: 1, 3)
  - [x] Create or update `.env.example`
  - [x] Add minimal config examples or docs hooks that Story 1.5 can extend
- [x] Test the configuration boundary thoroughly (AC: 1, 2, 3, 4)
  - [x] Add unit tests for valid and invalid config permutations
  - [x] Add integration coverage for startup preflight failure behavior
  - [x] Use fixtures and fakes rather than real Sonos hardware

## Dev Notes

- Depends on Story 1.1 being complete. Reuse the scaffolded package layout rather than introducing new config locations.
- The architecture requires typed configuration models, startup preflight checks, and a stateless service with no database.
- Configuration is authoritative only for app setup. Runtime Sonos state still comes from Sonos devices, not persisted app state.
- Optimize for a single-home, single-household setup. Multi-tenant or multi-household concerns are explicitly out of scope.
- Support sensible defaults and clear error reporting. The product promise here is smooth setup, not maximum configurability on day 0.
- Design config shapes so later stories can add:
  - `stdio` and `Streamable HTTP` runtime mode selection
  - local or trusted-home-network exposure posture
  - tool restriction and safety controls
- Validation errors should be deterministic and safe for user-facing diagnostics. Avoid leaking unnecessary host, token, or local network detail.

### Project Structure Notes

- Primary implementation paths:
  - `src/soniq_mcp/config/models.py`
  - `src/soniq_mcp/config/defaults.py`
  - `src/soniq_mcp/config/loader.py`
  - `src/soniq_mcp/config/validation.py`
  - `tests/unit/config/`
  - `tests/integration/config/`
  - `tests/fixtures/configs/`
- Do not place config parsing in transport modules, tool handlers, or `server.py`.
- If environment parsing helpers are needed, keep them close to `config/` rather than scattering utility code.

### References

- Story source and acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#story-12-implement-typed-configuration-and-validation]
- Data architecture and startup validation expectations: [Source: _bmad-output/planning-artifacts/architecture.md#data-architecture]
- Process patterns for config validation and errors: [Source: _bmad-output/planning-artifacts/architecture.md#process-patterns]
- Config structure and test organization: [Source: _bmad-output/planning-artifacts/architecture.md#project-structure--boundaries]
- Setup and onboarding requirements FR39-F43: [Source: _bmad-output/planning-artifacts/prd.md#setup-configuration-and-onboarding]
- Reliability and security NFRs around setup feedback: [Source: _bmad-output/planning-artifacts/prd.md#reliability] [Source: _bmad-output/planning-artifacts/prd.md#security]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Restored Story 1.1 source files missing from environment before implementing Story 1.2.
- Confirmed pydantic 2.12.5 available as transitive dep of `mcp[cli]` — no new dependency required.

### Completion Notes List

- Implemented `SoniqConfig` pydantic v2 model with `TransportMode`, `ExposurePosture`, `LogLevel` enums — all with safe defaults for single-household use.
- `load_config()` reads `SONIQ_MCP_*` env vars, applies defaults, normalises empty strings to None, accepts programmatic overrides.
- `run_preflight()` wraps load_config and converts pydantic `ValidationError` into `ConfigValidationError` with field-named, user-safe messages.
- `ExposurePosture.LOCAL` and enum stubs in place for Story 1.4 to extend.
- 42 tests pass (34 unit + 8 integration); zero regressions against Story 1.1 smoke tests.
- Post-review fixes verified in `master`; full suite now passes with 73/73 tests.

### File List

- `src/soniq_mcp/config/__init__.py`
- `src/soniq_mcp/config/models.py`
- `src/soniq_mcp/config/defaults.py`
- `src/soniq_mcp/config/loader.py`
- `src/soniq_mcp/config/validation.py`
- `src/soniq_mcp/__init__.py` (restored from Story 1.1)
- `src/soniq_mcp/__main__.py` (restored from Story 1.1)
- `src/soniq_mcp/server.py` (restored from Story 1.1)
- `src/soniq_mcp/transports/bootstrap.py` (restored from Story 1.1)
- `src/soniq_mcp/transports/stdio.py` (restored from Story 1.1)
- `tests/unit/config/__init__.py`
- `tests/unit/config/test_models.py`
- `tests/unit/config/test_loader.py`
- `tests/unit/config/test_validation.py`
- `tests/unit/test_scaffold_smoke.py` (restored from Story 1.1)
- `tests/integration/config/__init__.py`
- `tests/integration/config/test_preflight_startup.py`
- `tests/fixtures/configs/valid_defaults.env`
- `.env.example`

## Change Log

- 2026-03-24: Story 1.2 implemented. Added typed config models (`SoniqConfig`, enums), `load_config()` loader (env vars + overrides), `run_preflight()` validation with `ConfigValidationError`. 42 tests (34 unit, 8 integration) all passing. Status → review.
- 2026-03-25: Review fixes verified on `master`. Full test suite passes (73/73). Status → done.
