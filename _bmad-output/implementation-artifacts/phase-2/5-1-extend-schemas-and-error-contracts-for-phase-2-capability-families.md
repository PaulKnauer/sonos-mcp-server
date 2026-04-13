# Story 5.1: Extend schemas and error contracts for phase-2 capability families

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an integrator,
I want the phase-2 tool surface to use stable request, response, and error contracts,
so that I can adopt the new capabilities without reverse engineering behavior.

## Acceptance Criteria

1. Given the new phase-2 tool families are implemented, when request and response schemas are reviewed, then they use consistent `snake_case` naming and normalized structures across the expanded surface.
2. Given a validation, capability, connectivity, or internal failure occurs, when a phase-2 tool returns an error, then the error is mapped into the shared typed error model and raw SoCo objects or unstructured trace strings are not returned.

## Tasks / Subtasks

- [x] Audit the current phase-2 contract surface and lock the intended public shapes (AC: 1, 2)
  - [x] Review phase-2 tool families introduced across Epics 1-4: play modes, seek/sleep timer, audio EQ, input switching, group audio, alarms, playlists, and library access
  - [x] Confirm the current public request surface is expressed consistently through tool signatures, parameter names, and existing schema/domain conversions rather than through ad hoc per-tool dict assembly
  - [x] Identify any response payloads that drift from the normalized naming and structure patterns already established in `src/soniq_mcp/schemas/responses.py`
  - [x] Identify any tool handlers still returning inconsistent or under-specified error payloads for phase-2 capabilities

- [x] Normalize phase-2 response contracts without expanding feature scope (AC: 1)
  - [x] Update `src/soniq_mcp/schemas/responses.py` only where needed to keep phase-2 response models explicit, `snake_case`, and structurally consistent with the rest of the server
  - [x] Prefer reusing existing response schema patterns over introducing parallel one-off dict shapes in tool modules
  - [x] Keep domain-to-schema conversion logic at the schema boundary rather than leaking raw Sonos or SoCo objects through tool handlers
  - [x] Do not introduce new user-facing fields, aliases, or alternate naming conventions unless required to eliminate an inconsistency in the existing public contract

- [x] Harden shared typed error mapping across phase-2 capability families (AC: 2)
  - [x] Extend `src/soniq_mcp/schemas/errors.py` only where needed so validation, capability/operation, connectivity, and configuration failures map into the shared `ErrorResponse` model consistently
  - [x] Ensure sensitive transport and filesystem details remain sanitized in user-facing error strings and suggestions
  - [x] Verify phase-2 tool handlers continue to route expected failures through `ErrorResponse` helpers instead of exposing raw exceptions or unstructured trace text
  - [x] Preserve existing field names like `playback`, `audio_settings`, `input_source`, `group`, `alarm`, `playlist`, and `library` unless a verified inconsistency requires correction

- [x] Expand contract tests to freeze the normalized phase-2 schema surface (AC: 1, 2)
  - [x] Extend the relevant `tests/contract/tool_schemas/test_*_tool_schemas.py` suites for phase-2 families where coverage is missing or too weak to lock the public contract
  - [x] Extend `tests/contract/error_mapping/test_error_schemas.py` to cover any newly standardized error-mapping paths, categories, fields, or sanitization cases
  - [x] Add or refine transport-facing assertions in `tests/integration/transports/test_http_bootstrap.py` only where needed to ensure the phase-2 tool surface remains fully represented across supported transports
  - [x] Keep tests hardware-independent and focused on schema, registration, and contract guarantees rather than live Sonos behavior

- [x] Keep exposure-control and configuration metadata aligned to the contract surface (AC: 1, 2)
  - [x] Verify `src/soniq_mcp/config/models.py` still enumerates the full phase-2 tool surface in `KNOWN_TOOL_NAMES`
  - [x] If any phase-2 tool names or families are missing from validation or registration metadata, correct them without widening scope into Story 5.2 exposure-behavior work
  - [x] Preserve the current transport-neutral naming model so direct and agent-mediated usage continue to reference the same capability names

- [x] Run targeted validation for contract hardening (AC: 1, 2)
  - [x] Run the relevant phase-2 contract test suites
  - [x] Run `tests/contract/error_mapping/test_error_schemas.py`
  - [x] Run `tests/integration/transports/test_http_bootstrap.py`
  - [x] Run lint and format checks on touched Python files

## Dev Notes

### Story intent

- Epic 5 is the rollout-hardening epic for the expanded phase-2 surface. Story 5.1 is the contract-stability slice, not the docs/troubleshooting slice and not the transport/exposure-behavior slice.
- The implementation goal is to make the phase-2 surface easier to adopt by stabilizing its public request, response, and error shapes using the repo's existing schema patterns.
- This story should reduce reverse engineering for integrators, but it should not add new capabilities or reopen already-completed feature stories unless a contract defect requires a minimal correction.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-51-Extend-schemas-and-error-contracts-for-phase-2-capability-families`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]

### Previous story intelligence

- Epic 4 ended with a parity-hardening story rather than new runtime behavior. That pattern is relevant here: prefer regression locking and contract cleanup over speculative refactors.
- The Epic 4 retrospective identified tracker hygiene and earlier parity checks as the main carry-forward lessons. Story 5.1 should continue that discipline by hardening the public contract before broader docs and rollout work in Stories 5.2-5.4.
- Story 4.2 already touched `src/soniq_mcp/schemas/errors.py` for library playback validation and unsupported-operation handling. Story 5.1 should reuse that shared error-model approach instead of creating capability-specific exception payload formats.
  [Source: `_bmad-output/implementation-artifacts/phase-2/4-3-preserve-parity-for-library-access-across-direct-and-agent-mediated-usage.md`]
  [Source: `_bmad-output/implementation-artifacts/epic-4-retro-2026-04-13.md`]
  [Source: `git log --oneline -5`]

### Current repo state to build on

- The server already centralizes public response models in `src/soniq_mcp/schemas/responses.py` and public error payloads in `src/soniq_mcp/schemas/errors.py`.
- There is no central `src/soniq_mcp/schemas/requests.py` in this repository today. Request-contract hardening therefore needs to work with the actual code structure here: tool function signatures, service entry points, and existing validation/domain boundaries.
- Contract coverage already exists by capability family under `tests/contract/tool_schemas/`, and transport registration parity already exists in `tests/integration/transports/test_http_bootstrap.py`.
- `src/soniq_mcp/config/models.py` already uses `KNOWN_TOOL_NAMES` as the validation surface for `tools_disabled`; keep that aligned with the real tool inventory.
  [Source: `src/soniq_mcp/schemas/responses.py`]
  [Source: `src/soniq_mcp/schemas/errors.py`]
  [Source: `src/soniq_mcp/config/models.py`]
  [Source: `tests/contract/tool_schemas/`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- Keep `SoCoAdapter` as the only direct Sonos integration boundary; raw SoCo objects must not escape through tool responses or user-facing errors.
- Maintain transport-neutral tool semantics across `stdio` and `Streamable HTTP`.
- Preserve `snake_case` naming for all user-facing request and response fields.
- Keep capability-aware validation and unsupported-operation handling in service/domain logic, with tool handlers converting those failures into the shared typed error model.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Additional-Requirements`]

### Technical requirements

- Story 5.1 covers the phase-2 capability families added across Epics 1-4:
  - play modes
  - seek and sleep timer
  - audio EQ
  - input switching
  - group audio and topology-related additions
  - alarms
  - playlist lifecycle
  - library browsing and selection/playback
- Request-contract consistency here means stable tool names, parameter names, and validation expectations across these families; do not invent a new request-schema layer unless the code change is genuinely justified.
- Response-contract consistency means the expanded surface should continue to return explicit normalized models instead of ad hoc mixed dict structures.
- Error-contract consistency means phase-2 tools should return `ErrorResponse` payloads with typed `category`, sanitized `error`, and stable `field`/`suggestion` values for expected failures.
- This story explicitly includes validation, capability/operation, connectivity, and internal expected-failure mapping for phase-2 tools, but it does not justify changing transport envelopes or broader documentation flows reserved for later Epic 5 stories.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-51-Extend-schemas-and-error-contracts-for-phase-2-capability-families`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]
  [Source: `src/soniq_mcp/schemas/errors.py`]
  [Source: `src/soniq_mcp/schemas/responses.py`]

### Likely files to inspect or update

- Shared schemas and config:
  - `src/soniq_mcp/schemas/errors.py`
  - `src/soniq_mcp/schemas/responses.py`
  - `src/soniq_mcp/config/models.py`
- Phase-2 tool modules:
  - `src/soniq_mcp/tools/play_modes.py`
  - `src/soniq_mcp/tools/audio_settings.py`
  - `src/soniq_mcp/tools/input.py`
  - `src/soniq_mcp/tools/groups.py`
  - `src/soniq_mcp/tools/group_audio.py`
  - `src/soniq_mcp/tools/alarms.py`
  - `src/soniq_mcp/tools/playlists.py`
  - `src/soniq_mcp/tools/library.py`
  - `src/soniq_mcp/tools/playback.py`
- Contract and transport tests:
  - `tests/contract/error_mapping/test_error_schemas.py`
  - `tests/contract/tool_schemas/test_play_mode_tool_schemas.py`
  - `tests/contract/tool_schemas/test_audio_tool_schemas.py`
  - `tests/contract/tool_schemas/test_input_tool_schemas.py`
  - `tests/contract/tool_schemas/test_groups_audio_tool_schemas.py`
  - `tests/contract/tool_schemas/test_alarms_tool_schemas.py`
  - `tests/contract/tool_schemas/test_playlists_tool_schemas.py`
  - `tests/contract/tool_schemas/test_library_tool_schemas.py`
  - `tests/integration/transports/test_http_bootstrap.py`

### Implementation guidance

- Start by auditing existing response and error patterns before editing code. This story should be driven by observed contract drift, not by generalized cleanup instincts.
- Prefer tightening shared schema helpers over duplicating logic across tool modules.
- If a phase-2 tool already conforms to the normalized contract, leave it alone and enforce the contract through tests instead of refactoring for style.
- Keep new assertions additive and high-signal. The goal is to lock public behavior, not to overfit tests to incidental implementation details.
- Be careful with error wording changes: contract tests should freeze categories, fields, and sanitization guarantees, but avoid brittle assertions on overly specific prose unless the wording itself is a user-facing requirement.

### Testing guidance

- Reuse the capability-specific contract suites already present in `tests/contract/tool_schemas/`.
- Extend `tests/contract/error_mapping/test_error_schemas.py` for any missing phase-2 categories or sanitization coverage.
- Use `tests/integration/transports/test_http_bootstrap.py` only to verify registration/parity metadata, not to duplicate every contract assertion.
- Keep validation hardware-independent. No story work here should require a real Sonos environment.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/contract/error_mapping/test_error_schemas.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]

### Project Structure Notes

- Story files for the active phase live under `_bmad-output/implementation-artifacts/phase-2/`.
- Epic 5 is still in backlog state in the tracker; because this is the first story being created for Epic 5, the tracker should move `epic-5` to `in-progress`.
- This story should not absorb Story 5.2 transport exposure behavior, Story 5.3 broad docs/troubleshooting refresh, or Story 5.4 full regression-suite expansion unless a minimal prerequisite change is unavoidable.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-51-Extend-schemas-and-error-contracts-for-phase-2-capability-families`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Additional-Requirements`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/4-3-preserve-parity-for-library-access-across-direct-and-agent-mediated-usage.md`]
- [Source: `_bmad-output/implementation-artifacts/epic-4-retro-2026-04-13.md`]
- [Source: `src/soniq_mcp/schemas/errors.py`]
- [Source: `src/soniq_mcp/schemas/responses.py`]
- [Source: `src/soniq_mcp/config/models.py`]
- [Source: `tests/contract/error_mapping/test_error_schemas.py`]
- [Source: `tests/integration/transports/test_http_bootstrap.py`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- 2026-04-13: Story created from Epic 5 planning artifacts, the phase tracker, completed Epic 4 story/retro context, recent git history, and the current schema/error/contract surfaces in the repo.
- 2026-04-13: Confirmed the repo already centralizes public response models in `src/soniq_mcp/schemas/responses.py` and typed error payloads in `src/soniq_mcp/schemas/errors.py`.
- 2026-04-13: Confirmed there is no centralized `src/soniq_mcp/schemas/requests.py`; request-contract hardening should therefore target tool signatures and existing validation boundaries rather than forcing a new abstraction by default.
- 2026-04-13: Confirmed capability-specific contract suites already exist for the phase-2 families and should be reused for contract stabilization rather than replaced.
- 2026-04-13: Added failing contract tests for internal-error fallback handling across the phase-2 capability families plus a config guard for phase-2 `KNOWN_TOOL_NAMES`.
- 2026-04-13: Added `ErrorCategory.INTERNAL` and `ErrorResponse.from_internal_error(...)`, then wired unexpected-exception fallback handling through the phase-2 tool handlers so FastMCP does not surface raw tool errors for those paths.
- 2026-04-13: Replaced remaining phase-2 ad hoc success dicts in `groups.py` and `playlists.py` with explicit response models in `src/soniq_mcp/schemas/responses.py`.
- 2026-04-13: Addressed code-review findings by changing `from_internal_error(...)` to emit a fixed user-facing message instead of echoing raw exception text, and by updating troubleshooting/docs coverage to include the new `internal` diagnostic category.
- 2026-04-13: Addressed follow-up review feedback by expanding the troubleshooting matrix so the documented `internal` category lists the full current phase-2 field surface: `playback`, `audio_settings`, `input_source`, `group`, `alarm`, `playlist`, and `library`.
- 2026-04-13: Validation passed:
  - `uv run pytest -q tests/contract/error_mapping/test_error_schemas.py tests/contract/tool_schemas/test_play_mode_tool_schemas.py tests/contract/tool_schemas/test_audio_tool_schemas.py tests/contract/tool_schemas/test_input_tool_schemas.py tests/contract/tool_schemas/test_groups_tool_schemas.py tests/contract/tool_schemas/test_alarms_tool_schemas.py tests/contract/tool_schemas/test_playlists_tool_schemas.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/contract/tool_schemas/test_playback_tool_schemas.py tests/unit/config/test_models.py`
  - `uv run pytest -q tests/contract/error_mapping/test_error_schemas.py tests/contract/tool_schemas/test_play_mode_tool_schemas.py tests/contract/tool_schemas/test_audio_tool_schemas.py tests/contract/tool_schemas/test_input_tool_schemas.py tests/contract/tool_schemas/test_groups_tool_schemas.py tests/contract/tool_schemas/test_alarms_tool_schemas.py tests/contract/tool_schemas/test_playlists_tool_schemas.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/contract/tool_schemas/test_playback_tool_schemas.py tests/integration/transports/test_http_bootstrap.py tests/unit/config/test_models.py`
  - `uv run ruff check src/soniq_mcp/domain/exceptions.py src/soniq_mcp/schemas/errors.py src/soniq_mcp/schemas/responses.py src/soniq_mcp/tools/play_modes.py src/soniq_mcp/tools/audio.py src/soniq_mcp/tools/inputs.py src/soniq_mcp/tools/groups.py src/soniq_mcp/tools/alarms.py src/soniq_mcp/tools/playlists.py src/soniq_mcp/tools/library.py src/soniq_mcp/tools/playback.py tests/contract/error_mapping/test_error_schemas.py tests/contract/tool_schemas/test_play_mode_tool_schemas.py tests/contract/tool_schemas/test_audio_tool_schemas.py tests/contract/tool_schemas/test_input_tool_schemas.py tests/contract/tool_schemas/test_groups_tool_schemas.py tests/contract/tool_schemas/test_alarms_tool_schemas.py tests/contract/tool_schemas/test_playlists_tool_schemas.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/contract/tool_schemas/test_playback_tool_schemas.py tests/unit/config/test_models.py tests/integration/transports/test_http_bootstrap.py`
  - `uv run ruff format --check src/soniq_mcp/domain/exceptions.py src/soniq_mcp/schemas/errors.py src/soniq_mcp/schemas/responses.py src/soniq_mcp/tools/play_modes.py src/soniq_mcp/tools/audio.py src/soniq_mcp/tools/inputs.py src/soniq_mcp/tools/groups.py src/soniq_mcp/tools/alarms.py src/soniq_mcp/tools/playlists.py src/soniq_mcp/tools/library.py src/soniq_mcp/tools/playback.py tests/contract/error_mapping/test_error_schemas.py tests/contract/tool_schemas/test_play_mode_tool_schemas.py tests/contract/tool_schemas/test_audio_tool_schemas.py tests/contract/tool_schemas/test_input_tool_schemas.py tests/contract/tool_schemas/test_groups_tool_schemas.py tests/contract/tool_schemas/test_alarms_tool_schemas.py tests/contract/tool_schemas/test_playlists_tool_schemas.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/contract/tool_schemas/test_playback_tool_schemas.py tests/unit/config/test_models.py tests/integration/transports/test_http_bootstrap.py`
  - `uv run pytest -q`
  - `uv run pytest -q tests/contract/error_mapping/test_error_schemas.py tests/unit/test_integration_docs.py`
  - `uv run pytest -q tests/unit/test_integration_docs.py`
  - `uv run ruff check docs/setup/troubleshooting.md tests/unit/test_integration_docs.py`

### Completion Notes List

- Story scope is contract hardening only; it should stabilize the existing phase-2 request, response, and error surface without introducing new capabilities.
- Shared response and error schema files already exist and should remain the canonical contract boundary.
- The highest-signal implementation path is a targeted audit plus additive contract coverage, with minimal code change where the current surface is already correct.
- Tracker hygiene from Epic 4 should carry forward: this story creation moves Epic 5 into active status and makes `5-1` ready for development.
- Added an `internal` error category and a shared internal-error response helper so unexpected failures in the phase-2 tool families no longer bubble out as FastMCP tool errors.
- Added explicit success response models for `join_group`, `unjoin_room`, `party_mode`, and `play_playlist`, removing the remaining phase-2 ad hoc success dicts without changing their external payload shapes.
- Expanded contract coverage to lock internal-error fallback handling across play modes, seek, audio EQ, input switching, groups, alarms, playlists, and library playback.
- Added a config-level regression guard proving the phase-2 tool names remain enumerated in `KNOWN_TOOL_NAMES`.
- Addressed review feedback by ensuring unexpected internal failures no longer echo raw exception text in public tool responses.
- Updated troubleshooting guidance and its regression test so the documented diagnostic categories now include `internal`.
- Updated the troubleshooting matrix so the documented `internal` category matches the full current phase-2 field surface.
- Full validation passed: `1405 passed, 3 skipped`.

### File List

- _bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- src/soniq_mcp/domain/exceptions.py
- src/soniq_mcp/schemas/errors.py
- src/soniq_mcp/schemas/responses.py
- src/soniq_mcp/tools/alarms.py
- src/soniq_mcp/tools/audio.py
- src/soniq_mcp/tools/groups.py
- src/soniq_mcp/tools/inputs.py
- src/soniq_mcp/tools/library.py
- src/soniq_mcp/tools/play_modes.py
- src/soniq_mcp/tools/playback.py
- src/soniq_mcp/tools/playlists.py
- tests/contract/error_mapping/test_error_schemas.py
- tests/contract/tool_schemas/test_alarms_tool_schemas.py
- tests/contract/tool_schemas/test_audio_tool_schemas.py
- tests/contract/tool_schemas/test_groups_tool_schemas.py
- tests/contract/tool_schemas/test_input_tool_schemas.py
- tests/contract/tool_schemas/test_library_tool_schemas.py
- tests/contract/tool_schemas/test_play_mode_tool_schemas.py
- tests/contract/tool_schemas/test_playback_tool_schemas.py
- tests/contract/tool_schemas/test_playlists_tool_schemas.py
- tests/unit/test_integration_docs.py
- tests/unit/config/test_models.py
- docs/setup/troubleshooting.md

### Change Log

- 2026-04-13: Created Story 5.1 with concrete guidance for response normalization, shared typed error mapping, contract-test hardening, and transport-visible schema parity for the phase-2 capability families.
- 2026-04-13: Marked Story 5.1 done after review closure, full CI validation, and tracker handoff to Story 5.2.
- 2026-04-13: Implemented phase-2 contract hardening by adding typed internal-error fallback handling, normalizing remaining ad hoc success responses in groups/playlists, and expanding contract/config regression coverage.
- 2026-04-13: Addressed review findings by removing raw exception echoing from internal error responses and aligning troubleshooting docs with the public `internal` category.
- 2026-04-13: Addressed follow-up review feedback by expanding the troubleshooting matrix to include all phase-2 `internal` error fields.
