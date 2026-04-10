# Story 2.1: Support capability-aware input switching

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to switch a supported room to line-in or TV input,
so that I can control external sources from the same AI workflow.

## Acceptance Criteria

1. Given a room that supports line-in or TV input, when the client requests an input switch, then the service validates device capability support before invoking the adapter and returns the resulting normalized input state.
2. Given a room that does not support the requested input, when the client invokes the input-switching tool, then the service returns a typed unsupported-capability error and no playback state is changed.
3. Given an invalid room name or Sonos communication failure, when an input-switching tool is invoked, then the tool returns a typed MCP-safe error response and never leaks raw SoCo objects or exceptions.

## Tasks / Subtasks

- [x] Add input domain and error primitives (AC: 1, 2, 3)
  - [x] Add `InputError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [x] Add `InputValidationError(InputError)` for local validation and unsupported-capability paths
  - [x] Add `InputState` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields:
    - [x] `room_name: str`
    - [x] `input_source: Literal["line_in", "tv"]`
    - [x] `coordinator_room_name: str | None`

- [x] Add input response and error schemas (AC: 1, 2, 3)
  - [x] Add `InputStateResponse` to `src/soniq_mcp/schemas/responses.py`
  - [x] Add `ErrorResponse.from_input_error(exc)` to `src/soniq_mcp/schemas/errors.py`
  - [x] Extend `tests/unit/schemas/test_responses.py` with input-response coverage

- [x] Extend `SoCoAdapter` with input switching operations (AC: 1, 2, 3)
  - [x] Add `switch_to_line_in(ip_address: str) -> None`
  - [x] Add `switch_to_tv(ip_address: str) -> None`
  - [x] Add `get_music_source(ip_address: str) -> str`
  - [x] Implement adapter methods with the current SoCo API:
    - [x] `zone.switch_to_line_in()`
    - [x] `zone.switch_to_tv()`
    - [x] `zone.music_source`
  - [x] Keep all `soco` imports inside `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Wrap all SoCo exceptions in `InputError`

- [x] Create `InputService` with capability guards and orchestration (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/services/input_service.py`
  - [x] Constructor: `InputService(room_service: object, adapter: SoCoAdapter)`
  - [x] Implement `switch_to_line_in(room_name: str) -> InputState`
  - [x] Implement `switch_to_tv(room_name: str) -> InputState`
  - [x] Resolve the room via `room_service.get_room(room_name)`
  - [x] Add explicit capability guards before adapter calls:
    - [x] line-in support must be validated before `switch_to_line_in`
    - [x] TV support must be validated before `switch_to_tv`
  - [x] Raise `InputValidationError` with user-correctable messages for unsupported devices instead of relying on raw SoCo failures
  - [x] Normalize the resulting state into `InputState`

- [x] Decide and implement the capability-detection rule in service code (AC: 1, 2)
  - [x] Use the smallest reliable guard that fits the existing repo architecture and current discovery data
  - [x] If current `Room`/topology data is insufficient to determine support, extend discovery/system topology carefully rather than bypassing validation
  - [x] Preserve transport-neutral behavior and keep capability checks in the service layer, not the tool layer

- [x] Create MCP input tools (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/tools/inputs.py`
  - [x] Register `switch_to_line_in(room: str)`
  - [x] Register `switch_to_tv(room: str)`
  - [x] Use `_CONTROL_TOOL_HINTS`
  - [x] Keep tool handlers thin: permission guard first, service call second, schema/error translation only
  - [x] Return `InputStateResponse.model_dump()` on success
  - [x] Catch `InputError`, `RoomNotFoundError`, and `SonosDiscoveryError` and map them to `ErrorResponse`

- [x] Wire input tools into the server and config registry (AC: 1, 2, 3)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to construct `InputService(room_service, SoCoAdapter())`
  - [x] Register inputs after existing playback/audio capability modules in a stable order
  - [x] Add `"switch_to_line_in"` and `"switch_to_tv"` to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`

- [x] Add automated regression coverage (AC: 1, 2, 3)
  - [x] Add `tests/unit/adapters/test_soco_adapter_inputs.py`
  - [x] Add `tests/unit/services/test_input_service.py`
  - [x] Add `tests/unit/tools/test_inputs.py`
  - [x] Add `tests/contract/tool_schemas/test_input_tool_schemas.py`
  - [x] Cover unsupported-capability failures, room-not-found, discovery failures, and stable schema output
  - [x] Run `make test` and confirm the full suite still passes

## Dev Notes

### Story intent

- This is the first story in Phase 2 Epic 2 and it is specifically about capability-aware input switching.
- It is not a topology-discovery story and it is not a group-audio story.
- The implementation should establish the dedicated input-switching capability boundary that later Epic 2 stories can build on.

### Architecture guardrails

- Add a dedicated `src/soniq_mcp/tools/inputs.py` and `src/soniq_mcp/services/input_service.py`; do not fold input switching into `tools/playback.py`, `tools/groups.py`, or `services/sonos_service.py`.
- `SoCoAdapter` remains the only direct `soco` integration boundary.
- Services own:
  - room resolution,
  - capability support checks,
  - validation,
  - normalized output shaping.
- Tools own:
  - MCP registration,
  - permission checks,
  - success payload formatting,
  - error translation only.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]

### Existing repo patterns to reuse

- Current capability modules already follow the desired shape:
  - `src/soniq_mcp/tools/playback.py` + `src/soniq_mcp/services/playback_service.py`
  - `src/soniq_mcp/tools/audio.py` + `src/soniq_mcp/services/audio_settings_service.py`
  - `src/soniq_mcp/tools/groups.py` + `src/soniq_mcp/services/group_service.py`
- Keep the same conventions:
  - module-local `_READ_ONLY_TOOL_HINTS` / `_CONTROL_TOOL_HINTS`
  - `assert_tool_permitted(tool_name, config)` at invocation time
  - `ErrorResponse.model_dump()` on failure
  - Pydantic response models with `snake_case` fields
  [Source: `src/soniq_mcp/tools/playback.py`]
  [Source: `src/soniq_mcp/tools/audio.py`]
  [Source: `src/soniq_mcp/tools/groups.py`]

### Previous story intelligence

- Phase 2 Story `1.4` hardened contracts and regression tests after schema-drift issues in earlier playback/audio work.
- Carry that lesson forward here:
  - lock tool schemas with contract tests,
  - keep validation in the service layer,
  - do not allow raw SoCo behavior to define the external MCP contract.
- The current repo baseline after Story `1.4` is a heavily tested capability-oriented structure, so Story `2.1` should extend that shape instead of introducing a one-off shortcut.
  [Source: `_bmad-output/implementation-artifacts/1-4-harden-advanced-playback-contracts-and-regression-coverage.md`]

### SoCo input-switching API

- The repo currently pins `soco>=0.30.14`.
- Current SoCo supports:
  - `zone.switch_to_line_in([source])`
  - `zone.switch_to_tv()`
  - `zone.music_source`
  - `zone.is_playing_line_in`
  - `zone.is_playing_tv`
- `switch_to_line_in` is intended for speakers that support line-in.
- `switch_to_tv` is intended for soundbar / TV-capable devices.
- SoCo raises UPnP or Sonos exceptions on unsupported or invalid operations; these must be wrapped and normalized rather than leaked directly.
  [Source: `pyproject.toml`]
  [Source: official SoCo `soco.core` documentation for current input-switching APIs]

### Capability detection guidance

- The architecture explicitly requires capability-aware validation before invoking the adapter.
- Do not blindly call `switch_to_line_in` / `switch_to_tv` and treat a SoCo exception as the primary eligibility check.
- If current discovery data does not expose enough information to make a clean support decision, extend topology/discovery in a focused way that benefits future Epic 2 stories rather than burying the logic in the tool layer.
- Keep the guard implementation pragmatic:
  - enough to reject clearly unsupported devices,
  - simple enough to remain hardware-independent in default tests.

### Suggested public tool surface

- `switch_to_line_in(room: str) -> InputStateResponse`
- `switch_to_tv(room: str) -> InputStateResponse`

Suggested normalized response shape:

```python
{
    "room_name": "Living Room",
    "input_source": "tv",
    "coordinator_room_name": "Living Room",
}
```

If coordinator context is not practical yet, `coordinator_room_name` may be `None`, but keep the field in the domain/response shape for consistency with future Epic 2 work.

### Files likely to change

```text
src/soniq_mcp/domain/exceptions.py
src/soniq_mcp/domain/models.py
src/soniq_mcp/adapters/soco_adapter.py
src/soniq_mcp/schemas/errors.py
src/soniq_mcp/schemas/responses.py
src/soniq_mcp/services/input_service.py
src/soniq_mcp/tools/inputs.py
src/soniq_mcp/tools/__init__.py
src/soniq_mcp/config/models.py
tests/unit/schemas/test_responses.py
tests/unit/adapters/test_soco_adapter_inputs.py
tests/unit/services/test_input_service.py
tests/unit/tools/test_inputs.py
tests/contract/tool_schemas/test_input_tool_schemas.py
```

### Testing requirements

- Adapter tests must verify correct SoCo method selection and exception wrapping.
- Service tests must verify:
  - valid line-in switching,
  - valid TV switching,
  - unsupported capability errors,
  - room-not-found propagation,
  - discovery failures.
- Tool tests must verify:
  - disabled-tool registration,
  - response shape stability,
  - `InputError` translation,
  - `RoomNotFoundError` translation,
  - `SonosDiscoveryError` translation.
- Contract tests must lock tool names and parameter names for:
  - `switch_to_line_in`
  - `switch_to_tv`

### Project structure notes

- The architecture already names `inputs.py` / `input_service.py` as the intended ownership boundary for this capability family.
- This story is a clean match for the documented structure and should be implemented as the first dedicated input-switching slice.
- Do not introduce a database, transport-specific branching, or an overgrown `SonosService` extension for this work.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-21-Support-capability-aware-input-switching`
- Epic context: `_bmad-output/planning-artifacts/epics.md#Epic-2-Input-and-Group-Audio-Expansion`
- Phase intent: `_bmad-output/planning-artifacts/prd.md#Post-MVP-Features`
- Architecture patterns: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`
- Boundary mapping: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`
- Previous story context: `_bmad-output/implementation-artifacts/1-4-harden-advanced-playback-contracts-and-regression-coverage.md`
- Existing tool pattern: `src/soniq_mcp/tools/playback.py`
- Existing capability pattern: `src/soniq_mcp/tools/audio.py`
- Existing group pattern: `src/soniq_mcp/tools/groups.py`
- Dependency baseline: `pyproject.toml`
- External reference: official SoCo `soco.core` input-switching documentation

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest tests/unit/adapters/test_soco_adapter_inputs.py tests/unit/services/test_input_service.py tests/unit/tools/test_inputs.py tests/contract/tool_schemas/test_input_tool_schemas.py tests/unit/adapters/test_discovery_adapter.py tests/unit/services/test_room_service.py tests/unit/domain/test_models.py tests/unit/schemas/test_responses.py tests/unit/test_server.py -q` -> `117 passed`
- `make test` -> `974 passed, 3 skipped`

### Completion Notes List

- Added dedicated input-switching domain, service, adapter, and tool boundaries for `line_in` and `tv`.
- Extended discovery-derived speaker metadata with `supports_line_in` and `supports_tv`, then enforced capability validation in `InputService` before any adapter call.
- Normalized successful input-switch results to `InputStateResponse` and added typed MCP-safe translation for unsupported capability and adapter failures.
- Added unit, contract, and integration coverage for new tools plus bootstrap exposure updates so the new tool surface is locked down.

### File List

_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md
_bmad-output/implementation-artifacts/sprint-status.yaml
_bmad-output/phase-index.yaml
src/soniq_mcp/domain/exceptions.py
src/soniq_mcp/domain/models.py
src/soniq_mcp/adapters/discovery_adapter.py
src/soniq_mcp/services/room_service.py
src/soniq_mcp/schemas/errors.py
src/soniq_mcp/schemas/responses.py
src/soniq_mcp/services/input_service.py
src/soniq_mcp/tools/inputs.py
src/soniq_mcp/adapters/soco_adapter.py
src/soniq_mcp/tools/__init__.py
src/soniq_mcp/config/models.py
tests/unit/adapters/test_soco_adapter_inputs.py
tests/unit/services/test_input_service.py
tests/unit/tools/test_inputs.py
tests/contract/tool_schemas/test_input_tool_schemas.py
tests/unit/adapters/test_discovery_adapter.py
tests/unit/domain/test_models.py
tests/unit/services/test_room_service.py
tests/unit/schemas/test_responses.py
tests/integration/transports/test_http_bootstrap.py

### Review Findings

- [x] [Review][Patch] Double discovery — refactor `_ensure_support` to accept pre-resolved speakers: `switch_to_line_in`/`switch_to_tv` should call `get_speakers_for_room` once (which resolves the Room internally), then pass both to `_ensure_support`, eliminating the redundant second `get_room` call. [`input_service.py`, `room_service.py`]
- [x] [Review][Patch] Fail with `InputError` when music_source unrecognized after switch — `_normalize_source` returns `None` for unrecognized SoCo values; `_build_input_state` should raise `InputError` instead of silently substituting `expected_source`. [`input_service.py:51-54`]
- [x] [Review][Patch] `endswith()` model matching allows false positives — changed to substring `in` check with frozensets; also handles "Sonos Beam Gen 2" style names that `endswith` would miss. [`discovery_adapter.py:_infer_input_capabilities`]
- [x] [Review][Patch] `coordinator_room_name` stays as `room.name` when coordinator UID is set but not found — fixed to initialize `None` when `coordinator_uid` is set, only overwrite if coordinator found. [`input_service.py:_build_input_state`]
- [x] [Review][Patch] Tool annotation test only covers `switch_to_tv` — added `TestInputToolAnnotations::test_switch_to_line_in_annotations_are_control`. [`tests/unit/tools/test_inputs.py`]
- [x] [Review][Patch] Service tests missing `SonosDiscoveryError` from `discover_speakers` — added `test_discovery_error_in_speakers_propagates`. [`tests/unit/services/test_input_service.py`]
- [x] [Review][Patch] Contract tests don't lock `idempotentHint`/`openWorldHint` — expanded to `test_tool_annotations_are_stable` asserting all four annotation fields for both tools. [`tests/contract/tool_schemas/test_input_tool_schemas.py`]
- [x] [Review][Defer] Full network discovery on every capability check [`room_service.py:get_speakers_for_room`] — deferred, pre-existing no-caching architecture; address when caching/topology snapshots are introduced
- [x] [Review][Defer] Invisible speakers matched by `room_name` fallback in `get_speakers_for_room` [`room_service.py`] — deferred, pre-existing; OR condition is likely intentional for bonded satellites/subs that have `room_uid=None`
- [x] [Review][Defer] `Literal` type not enforced at runtime in `InputState.input_source` [`domain/models.py`] — deferred, pre-existing pattern across all domain dataclasses; Python does not enforce Literal at runtime

### Change Log

- 2026-04-09: Implemented capability-aware input switching, added tool/service/adapter/schema coverage, and moved story to review.
