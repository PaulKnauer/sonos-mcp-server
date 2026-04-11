# Story 3.1: Add alarm discovery and lifecycle operations

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to view, create, update, and delete Sonos alarms,
so that I can automate repeatable listening behavior through the MCP server.

## Acceptance Criteria

1. Given a reachable household with alarm support, when the client requests the alarm list, then the service returns normalized alarm records for supported rooms.
2. Given a valid alarm payload, when the client creates or updates an alarm, then the service validates the request through the alarm-service boundary and returns the resulting normalized alarm record.
3. Given an existing alarm identifier, when the client deletes the alarm, then the service removes it successfully and returns a structured confirmation response.

## Tasks / Subtasks

- [x] Add alarm domain primitives and MCP-facing schemas (AC: 1, 2, 3)
  - [x] Add `AlarmError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [x] Add `AlarmValidationError(AlarmError)` for malformed alarm payloads, unsupported room targeting, and missing alarm-id paths
  - [x] Add a frozen `AlarmRecord` dataclass to `src/soniq_mcp/domain/models.py`
  - [x] Normalize at least these fields in `AlarmRecord`:
    - [x] `alarm_id: str`
    - [x] `room_name: str`
    - [x] `start_time: str`
    - [x] `recurrence: str`
    - [x] `enabled: bool`
    - [x] `volume: int | None`
    - [x] `include_linked_zones: bool`
  - [x] Add `AlarmResponse`, `AlarmsListResponse`, and a structured delete confirmation response to `src/soniq_mcp/schemas/responses.py`
  - [x] Add `ErrorResponse.from_alarm_error(exc)` to `src/soniq_mcp/schemas/errors.py`
  - [x] Extend `tests/unit/schemas/test_responses.py` for the new response shapes

- [x] Extend `SoCoAdapter` with alarm operations using the current SoCo alarm API (AC: 1, 2, 3)
  - [x] Add adapter methods for:
    - [x] `get_alarms(ip_address: str) -> list[AlarmRecord]`
    - [x] `create_alarm(...) -> AlarmRecord`
    - [x] `update_alarm(alarm_id: str, ...) -> AlarmRecord`
    - [x] `delete_alarm(ip_address: str, alarm_id: str) -> None`
  - [x] Keep all `soco` imports inside `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Use the current SoCo alarm API rather than inventing wrappers:
    - [x] `soco.alarms.get_alarms(zone=...)`
    - [x] `soco.alarms.Alarm(...).save()`
    - [x] existing-alarm mutation plus `save()` for updates
    - [x] `soco.alarms.remove_alarm_by_id(zone, alarm_id)` or equivalent supported removal path
    - [x] `soco.alarms.is_valid_recurrence(text)` for recurrence validation support
  - [x] Wrap all SoCo failures in `AlarmError`
  - [x] Never leak raw `Alarm` objects outside the adapter boundary

- [x] Create `AlarmService` with request validation and room-scoped orchestration (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/services/alarm_service.py`
  - [x] Constructor: `AlarmService(room_service: object, adapter: SoCoAdapter)`
  - [x] Implement:
    - [x] `list_alarms() -> list[AlarmRecord]`
    - [x] `create_alarm(...) -> AlarmRecord`
    - [x] `update_alarm(alarm_id: str, ...) -> AlarmRecord`
    - [x] `delete_alarm(alarm_id: str) -> str | dict`
  - [x] Resolve room names through `room_service`; do not trust raw room strings from tools
  - [x] Validate recurrence strings before adapter writes
  - [x] Validate `start_time` in a deterministic, user-correctable format before adapter writes
  - [x] Validate `volume` in the Sonos-safe range before adapter writes
  - [x] Return `AlarmValidationError` for malformed payloads or unknown alarm ids instead of generic operational failures
  - [x] Keep eligibility checks and normalization in the service, not in tool handlers

- [x] Decide and implement the public alarm MCP tool surface (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/tools/alarms.py`
  - [x] Register stable tool names:
    - [x] `list_alarms()`
    - [x] `create_alarm(...)`
    - [x] `update_alarm(...)`
    - [x] `delete_alarm(alarm_id: str)`
  - [x] Use `_READ_ONLY_TOOL_HINTS` for listing and `_CONTROL_TOOL_HINTS` for lifecycle mutations
  - [x] Keep tool handlers thin: permission guard first, service call second, schema/error translation only
  - [x] Return `model_dump()` from response schemas on success
  - [x] Catch `AlarmError`, `AlarmValidationError`, `RoomNotFoundError`, and `SonosDiscoveryError` and map them through `ErrorResponse`

- [x] Wire the alarm capability into registration and config validation (AC: 2, 3)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to construct and register `AlarmService`
  - [x] Add the new alarm tool names to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [x] Preserve stable registration order and transport parity across `stdio` and HTTP
  - [x] Do not collapse alarm logic into `FavouritesService`, `SonosService`, or `tools/playlists.py`

- [x] Add automated regression coverage for alarm lifecycle behavior (AC: 1, 2, 3)
  - [x] Add `tests/unit/adapters/test_soco_adapter_alarms.py`
  - [x] Add `tests/unit/services/test_alarm_service.py`
  - [x] Add `tests/unit/tools/test_alarms.py`
  - [x] Add `tests/contract/tool_schemas/test_alarms_tool_schemas.py`
  - [x] Extend `tests/contract/error_mapping/test_error_schemas.py` for alarm errors
  - [x] Cover at least:
    - [x] empty alarm inventory
    - [x] normalized alarm list output
    - [x] valid create/update/delete flows
    - [x] malformed recurrence validation
    - [x] invalid time format validation
    - [x] room-not-found handling
    - [x] missing alarm-id handling
    - [x] SoCo failure mapping without leaking library details
  - [x] Run the targeted alarm suites plus `make test` and confirm the full suite still passes

## Dev Notes

### Story intent

- This is the first story in Epic 3 and it establishes the new `alarms` capability family.
- The goal is to add alarm discovery and lifecycle operations without disturbing existing playback, queue, favourites, or playlist-playback behavior.
- This story does not add playlist CRUD. That belongs to Story 3.2.
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-3-Alarm-and-Playlist-Lifecycle-Management`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-31-Add-alarm-discovery-and-lifecycle-operations`]

### Current repo state to build on

- There is currently no alarm capability family in `src/` or `tests/`; this story creates it from scratch within the established project patterns.
- Playlist playback already exists and currently routes through `tools/playlists.py` and `FavouritesService`. Do not use this story to refactor playlist lifecycle ownership beyond what is needed to avoid future conflicts.
- `tools/__init__.py` currently registers playback, volume, favourites, playlists, queue, groups, play modes, audio, and inputs, but not alarms.
  [Source: `src/soniq_mcp/tools/__init__.py`]
  [Source: `src/soniq_mcp/tools/playlists.py`]
  [Source: `src/soniq_mcp/services/favourites_service.py`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- `tools/alarms.py` owns MCP registration, permission checks, and success/error translation only.
- `services/alarm_service.py` owns room resolution, recurrence validation, payload validation, lookup/update/delete orchestration, and normalization.
- `src/soniq_mcp/adapters/soco_adapter.py` remains the only direct `SoCo` integration boundary.
- Do not call `SoCo` directly from tools, transports, or config/bootstrap code.
- Do not add alarm logic to `tools/playback.py`, `tools/playlists.py`, `services/sonos_service.py`, or `services/favourites_service.py`.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]

### SoCo and library requirements

- The project currently depends on `soco>=0.30.14`; implement against that version family unless the dependency is intentionally changed in this story.
- The locked SoCo alarm interface available to this repo includes:
  - `soco.alarms.get_alarms(zone=None)`
  - `soco.alarms.Alarm(zone, start_time=None, duration=None, recurrence='DAILY', enabled=True, program_uri=None, program_metadata='', play_mode='NORMAL', volume=20, include_linked_zones=False)`
  - `Alarm.save()`, `Alarm.remove()`
  - `soco.alarms.remove_alarm_by_id(zone, alarm_id)`
  - `soco.alarms.is_valid_recurrence(text)`
- Use those APIs directly inside the adapter rather than inventing speculative abstractions.
- If SoCo returns richer alarm fields than the initial MCP contract needs, normalize only the stable subset required by this story and keep the mapping deterministic.
  [Source: `pyproject.toml`]
  [Source: external SoCo API inspection against the project environment]

### Response and error-shape requirements

- Preserve `snake_case` in tool parameters, response fields, config fields, and internal models.
- Return structured alarm responses rather than ad hoc dicts for lifecycle operations.
- Use typed alarm-domain errors for:
  - malformed recurrence values
  - malformed time values
  - missing/unknown alarm ids
  - unsupported or unreachable room targets
  - Sonos/SoCo operational failures
- Never leak raw SoCo alarm objects, IP addresses, URLs, or filesystem paths through user-facing error text.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Format-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]
  [Source: `src/soniq_mcp/schemas/errors.py`]

### Implementation guidance

- Reuse `RoomService` to resolve target rooms and household reachability rather than building a second discovery path.
- Follow the established pattern used by `InputService`, `GroupService`, and existing tool modules:
  - thin tool handlers
  - service-owned validation
  - adapter-owned SoCo interaction
  - Pydantic response models returned via `.model_dump()`
- Prefer a normalized alarm contract that is easy for MCP clients to consume over mirroring every SoCo field.
- Keep the first cut bounded. Alarm listing plus create/update/delete is in scope; playlist CRUD, library browsing, and transport changes are not.
  [Source: `src/soniq_mcp/tools/inputs.py`]
  [Source: `src/soniq_mcp/tools/groups.py`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-32-Introduce-Sonos-playlist-CRUD-operations`]

### Testing requirements

- Add unit coverage for service-level validation and adapter-level alarm translation separately.
- Add contract tests that lock the new tool names, parameters, annotations, and normalized response shapes.
- Keep default automated validation hardware-independent by using fakes/mocks around the adapter boundary.
- Re-run the full regression suite after the targeted alarm tests pass.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/unit/tools/test_playlists.py`]
  [Source: `tests/contract/tool_schemas/test_playlists_tool_schemas.py`]

### Project Structure Notes

- New source files expected:
  - `src/soniq_mcp/tools/alarms.py`
  - `src/soniq_mcp/services/alarm_service.py`
  - alarm-related extensions in `src/soniq_mcp/domain/exceptions.py`
  - alarm-related extensions in `src/soniq_mcp/domain/models.py`
  - alarm-related extensions in `src/soniq_mcp/schemas/responses.py`
  - alarm-related extensions in `src/soniq_mcp/schemas/errors.py`
  - registration/config updates in `src/soniq_mcp/tools/__init__.py` and `src/soniq_mcp/config/models.py`
- New test files expected:
  - `tests/unit/adapters/test_soco_adapter_alarms.py`
  - `tests/unit/services/test_alarm_service.py`
  - `tests/unit/tools/test_alarms.py`
  - `tests/contract/tool_schemas/test_alarms_tool_schemas.py`
- No dedicated UX document exists for this project; use PRD + architecture guidance for user-facing clarity and error semantics.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
  [Source: `_bmad-output/planning-artifacts/epics.md#UX-Design-Requirements`]

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-3-Alarm-and-Playlist-Lifecycle-Management`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-31-Add-alarm-discovery-and-lifecycle-operations`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `src/soniq_mcp/tools/__init__.py`]
- [Source: `src/soniq_mcp/tools/playlists.py`]
- [Source: `src/soniq_mcp/services/favourites_service.py`]
- [Source: `src/soniq_mcp/schemas/errors.py`]
- [Source: `pyproject.toml`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Story created from BMAD planning artifacts and current repo structure.
- Alarm API guidance verified against the current SoCo interface expected by this repo.
- Implemented using `alarm.remove()` rather than `remove_alarm_by_id` (equivalent supported removal path per story guidance).
- Follow-up implementation aligned recurrence validation with `soco.alarms.is_valid_recurrence()` through the adapter boundary.
- Follow-up implementation moved missing/blank `alarm_id` handling to `AlarmValidationError` paths in the service layer.
- Follow-up implementation marked `delete_alarm` as destructive in MCP tool annotations and added regression coverage for the corrected metadata.
- Follow-up implementation corrected `list_alarms()` to treat an empty discovery snapshot as a `SonosDiscoveryError` instead of an empty alarm inventory.
- Follow-up implementation added regression coverage for the fixed household-query path used by `list_alarms()` and `update_alarm()`.

### Completion Notes List

- Story scoped to the new alarm capability family only; playlist CRUD remains reserved for Story 3.2.
- Added `AlarmError` + `AlarmValidationError` to domain exceptions following existing pattern.
- Added `AlarmRecord` frozen dataclass to domain models with all 7 required fields.
- Added `AlarmResponse`, `AlarmsListResponse`, `AlarmDeleteResponse` to response schemas.
- Added `ErrorResponse.from_alarm_error()` to error schemas.
- Extended `SoCoAdapter` with `get_alarms`, `create_alarm`, `update_alarm`, `delete_alarm` and private `_normalize_alarm` — all soco imports deferred inside methods.
- Created `AlarmService` with full validation: HH:MM:SS time format, recurrence whitelist, volume 0-100 range.
- Created `tools/alarms.py` with 4 tools: thin handlers, permission guards, schema translation.
- Wired `AlarmService` into `tools/__init__.py` and added 4 tool names to `KNOWN_TOOL_NAMES`.
- Updated integration transport test (`test_http_bootstrap.py`) to include 4 new alarm tools (47 → 51).
- Corrected review follow-ups in the alarm stack: SoCo-backed recurrence validation, validation-category handling for missing/unknown alarm IDs, and deterministic delete failure when no rooms are discoverable.
- Added targeted regression coverage for recurrence validator delegation, validation-category alarm ID failures, and destructive delete tool metadata.
- Corrected the remaining review finding in `AlarmService`: household alarm listing now fails with discovery semantics when no rooms are reachable, avoiding false empty inventories and downstream validation misclassification.
- Added service-level regression coverage for no-room alarm listing and for update flows where room lookup succeeds but the household alarm query has no reachable rooms.
- Validation: `uv run pytest -q tests/unit/services/test_alarm_service.py` passed (33 tests).
- Validation: `make test` passed (1229 passed, 3 skipped). `make lint` passed.

### File List

- src/soniq_mcp/domain/exceptions.py (modified — added AlarmError, AlarmValidationError)
- src/soniq_mcp/domain/models.py (modified — added AlarmRecord)
- src/soniq_mcp/schemas/responses.py (modified — added AlarmResponse, AlarmsListResponse, AlarmDeleteResponse)
- src/soniq_mcp/schemas/errors.py (modified — added from_alarm_error)
- src/soniq_mcp/adapters/soco_adapter.py (modified — added alarm adapter methods)
- src/soniq_mcp/services/alarm_service.py (new)
- src/soniq_mcp/tools/alarms.py (new)
- src/soniq_mcp/tools/__init__.py (modified — wired AlarmService and register_alarms)
- src/soniq_mcp/config/models.py (modified — added 4 alarm tool names to KNOWN_TOOL_NAMES)
- tests/unit/schemas/test_responses.py (modified — added alarm response schema tests)
- tests/unit/adapters/test_soco_adapter_alarms.py (new)
- tests/unit/services/test_alarm_service.py (new)
- tests/unit/tools/test_alarms.py (new)
- tests/contract/tool_schemas/test_alarms_tool_schemas.py (new)
- tests/contract/error_mapping/test_error_schemas.py (modified — added alarm error tests)
- tests/integration/transports/test_http_bootstrap.py (modified — updated expected tool set to 51)
- _bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md (this file)

### Change Log

- 2026-04-11: Implemented Story 3.1 — alarm discovery and lifecycle (list, create, update, delete). Added 4 MCP tools, AlarmService, SoCoAdapter alarm methods, domain primitives, response schemas, and full test coverage (unit + contract). 1221 tests pass.
- 2026-04-11: Addressed review follow-ups for Story 3.1 — aligned recurrence validation with SoCo, corrected missing/unknown alarm-id failures to use validation-category responses, fixed delete metadata to be destructive, and re-ran targeted plus full regression validation.
- 2026-04-11: Addressed final review finding for Story 3.1 — `list_alarms()` now reports no-room discovery as a connectivity failure rather than an empty inventory, with regression coverage and full-suite validation.
