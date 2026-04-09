# Story 1.3: Add room-level audio EQ controls

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to view and change bass, treble, and loudness for a room,
so that I can tune the listening experience from the same AI control surface.

## Acceptance Criteria

1. **Get EQ settings:** Given a reachable target room, when the client requests current bass, treble, and loudness settings, then the service returns the normalized audio-setting values for that room.

2. **Set EQ settings:** Given a reachable target room, when the client updates bass, treble, or loudness, then the service validates the request against supported ranges and types and applies the change through the dedicated audio-settings service boundary.

3. **Reject invalid EQ requests:** Given an invalid audio-setting request, when the client invokes the tool, then the service returns a typed validation error and the room state remains unchanged.

## Tasks / Subtasks

- [x] Add audio EQ domain and response models (AC: 1, 2)
  - [x] Add `AudioSettingsState` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields `room_name: str`, `bass: int`, `treble: int`, `loudness: bool`
  - [x] Add `AudioSettingsResponse` Pydantic model to `src/soniq_mcp/schemas/responses.py` with `from_domain(state: AudioSettingsState)` factory

- [x] Add dedicated audio EQ error handling (AC: 2, 3)
  - [x] Add `AudioSettingsError` to `src/soniq_mcp/domain/exceptions.py` for EQ operation and validation failures
  - [x] Add `ErrorResponse.from_audio_settings_error()` to `src/soniq_mcp/schemas/errors.py` with a stable `field` for audio-setting failures
  - [x] Keep invalid-range/type failures in the validation category rather than returning raw `ValueError` text directly from tool handlers

- [x] Extend `SoCoAdapter` with audio EQ methods (AC: 1, 2, 3)
  - [x] Add `get_audio_settings(ip_address: str, room_name: str) -> AudioSettingsState` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Add `set_bass(ip_address: str, level: int) -> None` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Add `set_treble(ip_address: str, level: int) -> None` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Add `set_loudness(ip_address: str, enabled: bool) -> None` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Normalize SoCo property reads into `AudioSettingsState` and wrap all SoCo failures as `AudioSettingsError`

- [x] Create dedicated audio settings service boundary (AC: 1, 2, 3)
  - [x] Add `src/soniq_mcp/services/audio_settings_service.py`
  - [x] `get_audio_settings(room_name: str) -> AudioSettingsState`
  - [x] `set_bass(room_name: str, level: int) -> AudioSettingsState`
  - [x] `set_treble(room_name: str, level: int) -> AudioSettingsState`
  - [x] `set_loudness(room_name: str, enabled: bool) -> AudioSettingsState`
  - [x] Validate `bass` and `treble` as integers in the inclusive range `-10..10`
  - [x] Validate `loudness` as boolean and return the resulting normalized EQ state after each write

- [x] Add MCP audio tool module (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/tools/audio.py`
  - [x] Add `get_eq_settings(room)` with `_READ_ONLY_TOOL_HINTS`
  - [x] Add `set_bass(room, level)`, `set_treble(room, level)`, and `set_loudness(room, enabled)` with `_CONTROL_TOOL_HINTS`
  - [x] Map `RoomNotFoundError`, `AudioSettingsError`, and `SonosDiscoveryError` to structured `ErrorResponse` values
  - [x] Return `AudioSettingsResponse` from all successful audio-EQ tools so the client always gets the resulting normalized state

- [x] Wire audio tools into registration and config (AC: 1, 2)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to instantiate `AudioSettingsService` and register `tools/audio.py`
  - [x] Add `get_eq_settings`, `set_bass`, `set_treble`, and `set_loudness` to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [x] Update transport parity expectations in `tests/integration/transports/test_http_bootstrap.py`

- [x] Add regression coverage across adapter, service, tools, schemas, and contract boundaries (AC: 1, 2, 3)
  - [x] Add adapter tests in `tests/unit/adapters/test_soco_adapter_audio_settings.py`
  - [x] Add service tests in `tests/unit/services/test_audio_settings_service.py`
  - [x] Add tool tests in `tests/unit/tools/test_audio.py`
  - [x] Add response-schema tests in `tests/unit/schemas/test_responses.py`
  - [x] Add contract tests in `tests/contract/tool_schemas/test_audio_tool_schemas.py`

### Review Findings

- [x] [Review][Patch] Setter tool schemas no longer declare argument types [src/soniq_mcp/tools/audio.py:71]

## Dev Notes

### Story intent and architectural boundary

- Unlike Story 1.2, this story must use a dedicated audio-settings boundary.
- The architecture explicitly assigns bass, treble, and loudness to `tools/audio.py` and `services/audio_settings_service.py`.
- Do not add EQ operations to `tools/playback.py`, `services/playback_service.py`, or `services/sonos_service.py` beyond any truly shared helper reuse that already exists.

### Tool surface

- Implement these MCP tools:
  - `get_eq_settings(room)`
  - `set_bass(room, level)`
  - `set_treble(room, level)`
  - `set_loudness(room, enabled)`
- Keep names stable and `snake_case`.
- All successful tool responses should return the same normalized EQ payload: `room_name`, `bass`, `treble`, `loudness`.

### Validation requirements

- `bass` and `treble` must be validated as integers in the range `-10..10` before adapter writes.
- `loudness` must be validated as boolean at the service boundary.
- Invalid inputs must return a typed validation error through the new audio-settings error path.
- Do not allow raw `ValueError`, SoCo exceptions, or free-form Python type errors to reach the tool layer.

### SoCo capability details

- Use these SoCo properties:
  - `zone.bass`
  - `zone.treble`
  - `zone.loudness`
- `balance` and `trueplay` are explicitly out of scope for this story.

### Service behavior

- `AudioSettingsService` owns: request validation, room lookup, orchestration of adapter calls, returning normalized resulting state after writes.
- Write flow: validate → resolve room → write via adapter → re-read authoritative state.

### Error taxonomy guidance

- `AudioSettingsError` keeps EQ-specific failures separate from `VolumeError` / `PlaybackError`.
- `RoomNotFoundError` and `SonosDiscoveryError` use the existing shared mappings.

### References

- Story definition and acceptance criteria: [epics.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/epics.md)
- Phase-2 feature intent: [prd.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd.md)
- Architecture boundaries: [architecture.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/architecture.md)
- SoCo EQ capability notes: [technical-soco-capability-gap-research-2026-04-02.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/research/technical-soco-capability-gap-research-2026-04-02.md)
- Previous story learnings: [1-2-support-seek-and-sleep-timer-operations.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/1-2-support-seek-and-sleep-timer-operations.md)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Environment created from last committed state; sprint-status.yaml and story file were uncommitted and handled outside the environment.
- All 901 unit/contract/integration tests pass with 0 failures.
- `bool` is a subclass of `int` in Python — `_validate_eq_level` explicitly rejects `bool` values to prevent `True`/`False` being silently accepted as integer EQ levels.
- Follow-up fix validated the real FastMCP boundary: invalid EQ inputs now reach the service unchanged and return structured validation errors instead of being coerced or rejected as raw `ToolError`s.
- Full regression rerun after the follow-up fix: `921 passed, 3 skipped`; `make lint` passes.
- Review follow-up fix restored explicit MCP schema types for EQ setter parameters while preserving raw runtime inputs for service-level validation; verified with live FastMCP schema dumps.
- Full regression rerun after the schema-contract fix: `924 passed, 3 skipped`; `make lint` passes.

### Completion Notes List

- Implemented `AudioSettingsState` frozen dataclass and `AudioSettingsResponse` with `from_domain()` factory following Story 1.2 patterns.
- Added `AudioSettingsError` (ErrorCategory.OPERATION) and `ErrorResponse.from_audio_settings_error()` with stable `field="audio_settings"`.
- Extended `SoCoAdapter` with 4 EQ methods; all SoCo failures wrapped as `AudioSettingsError`; loudness normalized to `bool` on read.
- `AudioSettingsService` validates bass/treble as integers in `[-10, 10]` (explicitly rejecting `bool` subclass) and loudness as `bool`; re-reads adapter for authoritative post-write state.
- `tools/audio.py` registers all four tools with correct read-only/control annotations; all setters return `AudioSettingsResponse`.
- `KNOWN_TOOL_NAMES` extended with 4 new tools; transport parity test updated from 34 to 38 tools.
- 901 total tests pass (0 regressions). ~102 new tests across adapter, service, tool, schema, and contract layers.
- Added `AudioSettingsValidationError` so invalid EQ requests map to `ErrorCategory.VALIDATION` while adapter/device failures remain operational.
- Preserved raw invalid EQ inputs at the FastMCP boundary using `Annotated[object, Field(...)]` so values like `"5"`, `true`, `"true"`, and `2` still reach the dedicated audio-settings validation path unchanged.
- Restored explicit MCP setter parameter schema types (`integer` for bass/treble, `boolean` for loudness) to keep the client-visible contract aligned with the story and acceptance criteria.
- Added contract assertions for EQ setter parameter types to prevent future schema regressions, alongside the existing invalid-input and error-category coverage.

### File List

- `_bmad-output/implementation-artifacts/1-3-add-room-level-audio-eq-controls.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `src/soniq_mcp/domain/models.py`
- `src/soniq_mcp/domain/exceptions.py`
- `src/soniq_mcp/schemas/responses.py`
- `src/soniq_mcp/schemas/errors.py`
- `src/soniq_mcp/adapters/soco_adapter.py`
- `src/soniq_mcp/services/audio_settings_service.py`
- `src/soniq_mcp/tools/audio.py`
- `src/soniq_mcp/tools/__init__.py`
- `src/soniq_mcp/config/models.py`
- `tests/unit/adapters/test_soco_adapter_audio_settings.py`
- `tests/unit/services/test_audio_settings_service.py`
- `tests/unit/tools/test_audio.py`
- `tests/unit/schemas/test_responses.py`
- `tests/contract/error_mapping/test_error_schemas.py`
- `tests/contract/tool_schemas/test_audio_tool_schemas.py`
- `tests/integration/transports/test_http_bootstrap.py`

### Change Log

- Story 1.3 implementation: Add room-level audio EQ controls (`get_eq_settings`, `set_bass`, `set_treble`, `set_loudness`) — 4 new MCP tools, dedicated service and adapter layer, full test coverage (Date: 2026-04-09)
- Story 1.3 follow-up fix: restore typed validation errors for invalid EQ tool inputs and split validation vs operational audio-setting failures (Date: 2026-04-09)
- Story 1.3 review follow-up: restore EQ setter schema types without reintroducing FastMCP coercion; add schema contract assertions (Date: 2026-04-09)
