# Story 2.4: Apply Reliable Sonos Service and Adapter Boundaries

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want the core playback and volume features implemented through stable service and adapter layers,
so that tool logic remains thin and transport-agnostic.

## Acceptance Criteria

1. Given the playback and volume capabilities are implemented, when the code is reviewed against the architecture, then MCP tool handlers do not call `SoCo` directly.
2. Given the playback and volume capabilities are implemented, when the code is reviewed against the architecture, then Sonos operations are mediated through the agreed service and adapter boundaries.
3. Given domain and adapter errors are raised during playback or volume operations, when tool handlers return responses, then domain exceptions are translated consistently into MCP-safe responses using the shared error model.
4. Given the playback and volume stack is reviewed for structure, when files and modules are compared to the architecture, then the code organization follows the agreed structure and naming conventions.

## Tasks / Subtasks

- [x] Introduce the shared Sonos orchestration boundary and shared SoCo adapter (AC: 1, 2, 4)
  - [x] Create `src/soniq_mcp/adapters/soco_adapter.py` as the common Sonos integration boundary for playback and volume operations
  - [x] Create `src/soniq_mcp/services/sonos_service.py` as the main orchestration service for core playback and volume operations
  - [x] Keep `soco` imports isolated to `adapters/` only; tool and service layers must not import `soco`
  - [x] Preserve the existing by-IP interaction pattern already established in Stories 2.2 and 2.3

- [x] Refactor playback capability to use the shared boundaries without changing tool behavior (AC: 1, 2, 3, 4)
  - [x] Update `src/soniq_mcp/services/playback_service.py` to delegate shared Sonos operations through the new shared boundary, or reduce it to a thin capability wrapper if needed
  - [x] Update `src/soniq_mcp/adapters/playback_adapter.py` to delegate common SoCo interaction to `soco_adapter.py`, or remove it if the shared adapter fully supersedes it
  - [x] Keep grouped-room `get_track_info()` coordinator-routing behavior from Story 2.2 intact
  - [x] Ensure playback tools continue to expose the same tool names, parameters, annotations, success payloads, and error mapping

- [x] Refactor volume capability to use the shared boundaries without changing tool behavior (AC: 1, 2, 3, 4)
  - [x] Update `src/soniq_mcp/services/volume_service.py` to delegate shared Sonos operations through the new shared boundary, or reduce it to a thin capability wrapper if needed
  - [x] Update `src/soniq_mcp/adapters/volume_adapter.py` to delegate common SoCo interaction to `soco_adapter.py`, or remove it if the shared adapter fully supersedes it
  - [x] Preserve `check_volume()` and `VolumeCapExceeded` safety behavior exactly as implemented in Story 2.3
  - [x] Ensure volume tools continue to expose the same tool names, parameters, annotations, success payloads, and error mapping

- [x] Wire registration and module structure to match the architecture direction (AC: 2, 4)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to construct and inject the shared adapter/service boundary cleanly
  - [x] Reuse the existing `room_service` instance; do not create parallel discovery or room-lookup logic
  - [x] Keep capability-area tool modules (`tools/playback.py`, `tools/volume.py`) thin and transport-agnostic
  - [x] Remove any redundant module wiring created by earlier story-by-story implementation if the shared boundary makes it obsolete

- [x] Expand regression coverage around architectural boundaries (AC: 1, 2, 3, 4)
  - [x] Add or update unit tests in `tests/unit/services/` to verify orchestration and delegation boundaries
  - [x] Add or update unit tests in `tests/unit/adapters/` to verify the shared SoCo adapter behavior and error wrapping
  - [x] Add or update unit tests in `tests/unit/tools/` to verify tools still translate domain exceptions to MCP-safe responses unchanged
  - [x] Add or update contract tests in `tests/contract/tool_schemas/` if needed to prove no external tool surface regressions
  - [x] Run `make test` and confirm the full suite still passes

## Dev Notes

### Story Intent

- Story 2.4 is primarily a boundary and structure refactor, not a feature expansion.
- The external MCP tool surface for playback and volume must remain stable while the internal architecture is aligned to the documented target shape.
- The current codebase already satisfies much of the transport separation, but playback and volume are implemented as parallel capability stacks (`playback_service.py`, `volume_service.py`, `playback_adapter.py`, `volume_adapter.py`) rather than the architecture’s preferred shared orchestration boundary. This story should close that gap without regressing behavior. [Source: `_bmad-output/planning-artifacts/epics.md#Story-24-Apply-Reliable-Sonos-Service-and-Adapter-Boundaries`]

### Architecture Constraints (Must Follow)

- `tools/` handles MCP-facing inputs and outputs only.
- `services/` owns business logic and orchestration.
- `adapters/` owns external library integration with `SoCo`.
- No transport or tool module may call `SoCo` directly.
- The architecture explicitly identifies `services/sonos_service.py` as the main orchestration boundary for core Sonos operations and `adapters/soco_adapter.py` as the corresponding integration boundary. [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries`] [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- Capability-specific services may still exist, but they must not create parallel transport logic, config logic, or conflicting patterns. [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]

### Current Codebase Reality

- Current tool wiring lives in `src/soniq_mcp/tools/__init__.py` and constructs:
  - `RoomService(DiscoveryAdapter())`
  - `PlaybackService(room_service, PlaybackAdapter())`
  - `VolumeService(room_service, VolumeAdapter(), config)`
- Current playback and volume tools are already thin and correctly keep `SoCo` out of `tools/`.
- Current playback and volume services directly own orchestration against room lookup plus capability adapters.
- Current playback and volume adapters each instantiate `soco.SoCo(ip_address)` independently.
- Story 2.4 should refactor toward the architecture target while preserving the established behavior from Stories 2.2 and 2.3.

### Required Behavioral Preservation

- Do not change tool names or parameter shapes for:
  - `play`, `pause`, `stop`, `next_track`, `previous_track`, `get_playback_state`, `get_track_info`
  - `get_volume`, `set_volume`, `adjust_volume`, `mute`, `unmute`, `get_mute`
- Do not change success payload shapes returned by existing tools.
- Do not change error mapping behavior already established:
  - Playback tools map `RoomNotFoundError`, `PlaybackError`, and `SonosDiscoveryError` through `ErrorResponse`
  - Volume tools map `VolumeCapExceeded`, `VolumeError`, `RoomNotFoundError`, and `SonosDiscoveryError` through `ErrorResponse`
- Preserve grouped-room `get_track_info()` coordinator routing from Story 2.2.
- Preserve `check_volume()` safety enforcement and `adjust_volume()` clamping semantics from Story 2.3.

### Recommended Implementation Direction

- Introduce `src/soniq_mcp/adapters/soco_adapter.py` as the shared low-level SoCo boundary for by-IP operations used by playback and volume.
- Introduce `src/soniq_mcp/services/sonos_service.py` as the main orchestration service for playback and volume actions that require room lookup plus SoCo interaction.
- Keep `RoomService` and `DiscoveryAdapter` separate; story 2.1 established discovery/topology responsibilities there.
- Keep capability tool modules separate by area (`tools/playback.py`, `tools/volume.py`) even if they now share one orchestrating service.
- If `playback_service.py` and `volume_service.py` remain, they should become thin facades over `SonosService`, not alternate orchestration centers.
- If a simpler refactor is cleaner, removing one or both capability-specific services/adapters is acceptable, but only if:
  - the architecture direction is improved,
  - the external tool surface is unchanged,
  - all tests are updated,
  - the resulting structure is easier for future stories 3.1-3.3 to build on.

### File Structure Requirements

Expected files to create:

```text
src/soniq_mcp/services/sonos_service.py
src/soniq_mcp/adapters/soco_adapter.py
```

Expected files likely to modify:

```text
src/soniq_mcp/tools/__init__.py
src/soniq_mcp/tools/playback.py
src/soniq_mcp/tools/volume.py
src/soniq_mcp/services/playback_service.py
src/soniq_mcp/services/volume_service.py
src/soniq_mcp/adapters/playback_adapter.py
src/soniq_mcp/adapters/volume_adapter.py
tests/unit/services/test_playback_service.py
tests/unit/services/test_volume_service.py
tests/unit/adapters/test_playback_adapter.py
tests/unit/adapters/test_volume_adapter.py
tests/unit/tools/test_playback.py
tests/unit/tools/test_volume.py
tests/contract/tool_schemas/test_playback_tool_schemas.py
tests/contract/tool_schemas/test_volume_tool_schemas.py
```

Potential cleanup targets if they become redundant:

```text
src/soniq_mcp/services/playback_service.py
src/soniq_mcp/services/volume_service.py
src/soniq_mcp/adapters/playback_adapter.py
src/soniq_mcp/adapters/volume_adapter.py
```

Only remove these if the replacement structure is clearly better and fully covered by tests.

### Testing Requirements

- Unit tests must verify the new shared orchestration boundary and shared SoCo adapter behavior directly.
- Unit tests must keep using fakes or local test doubles; do not require real Sonos hardware.
- Tool tests must verify that responses and error translation remain unchanged across the refactor.
- Contract tests must continue to validate stable tool names and parameters for playback and volume tools.
- Run the full suite with `make test` before marking the story complete. [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`] [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries`]

### Previous Story Intelligence

- Story 2.2 established:
  - grouped-room coordinator-aware track info behavior,
  - stable playback tool schemas,
  - review-driven fixes around queue position normalization and grouped-room track metadata.
- Story 2.3 established:
  - `VolumeService` must reuse `check_volume()` and `VolumeCapExceeded`,
  - stable volume and mute tool schemas,
  - `make test` as the required validation command,
  - all tool handlers return `.model_dump()` for schema responses and structured dicts for simple success responses.
- Story 2.3 Dev Agent Record reports `282 tests pass (3 skipped)` at implementation time; the merge commit for story 2.3 reported `375 tests pass`. Use the current repo baseline at execution time rather than assuming either number is still exact.

### Project Structure Notes

- The architecture’s target structure includes `services/sonos_service.py` and `adapters/soco_adapter.py`, but the current repository does not yet contain them.
- The current codebase is already aligned on the higher-level boundary rule `tools -> services -> adapters`, so this story should be an architectural consolidation rather than a wholesale rewrite.
- Do not introduce a monolithic utility module or move business logic into `tools/`.

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-24-Apply-Reliable-Sonos-Service-and-Adapter-Boundaries`
- Architecture patterns and enforcement: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries`
- Architectural boundaries and target mapping: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`
- Product context for SoCo-based Sonos control: `_bmad-output/planning-artifacts/prd.md`
- Previous story context: `_bmad-output/implementation-artifacts/2-2-control-core-playback-in-a-target-room.md`
- Previous story context: `_bmad-output/implementation-artifacts/2-3-control-volume-and-mute-safely.md`

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Added `SoCoAdapter` and `SonosService` as shared playback/volume boundaries, then kept `PlaybackService`, `VolumeService`, `PlaybackAdapter`, and `VolumeAdapter` as compatibility facades over the shared boundary.
- Preserved production tool behavior by changing only `tools/__init__.py` wiring; tool modules and MCP schemas remained unchanged.
- Added explicit unit coverage for the new shared boundary and kept the existing playback/volume suites green.
- Fixed the review follow-up constructor regressions by restoring legacy keyword injection support for `VolumeService`, making `sonos_service` explicit for shared-service injection, and updating tool wiring to use the explicit keyword path.

### Completion Notes List

- Implemented `src/soniq_mcp/adapters/soco_adapter.py` as the shared by-IP SoCo boundary for playback state, track info, volume, and mute operations.
- Implemented `src/soniq_mcp/services/sonos_service.py` as the shared orchestration service for room lookup, grouped-room coordinator routing, playback control, volume control, and mute control.
- Refactored `src/soniq_mcp/adapters/playback_adapter.py` and `src/soniq_mcp/adapters/volume_adapter.py` into thin compatibility facades over `SoCoAdapter`.
- Refactored `src/soniq_mcp/services/playback_service.py` and `src/soniq_mcp/services/volume_service.py` into thin compatibility facades over `SonosService`, while preserving constructor compatibility used by existing tests.
- Updated `src/soniq_mcp/tools/__init__.py` to construct one shared `SonosService` instance from `RoomService` plus `SoCoAdapter`, then inject it into playback and volume capability wrappers.
- Preserved Story 2.2 grouped-room coordinator routing for `get_track_info()` and Story 2.3 volume safety behavior using `check_volume()` and `VolumeCapExceeded`.
- Added `tests/unit/adapters/test_soco_adapter.py` and `tests/unit/services/test_sonos_service.py` to verify the new shared boundary directly.
- Restored constructor compatibility for `VolumeService(room_service=..., adapter=..., config=...)` and tightened `PlaybackService` so `room_service` without an adapter is rejected early instead of failing later with `AttributeError`.
- Added regression coverage for explicit `sonos_service=` injection and for rejecting invalid wrapper construction paths.
- Validation:
  - `uv run pytest tests/unit/adapters/test_soco_adapter.py tests/unit/services/test_sonos_service.py`
  - `uv run pytest tests/unit/adapters/test_playback_adapter.py tests/unit/adapters/test_volume_adapter.py tests/unit/services/test_playback_service.py tests/unit/services/test_volume_service.py tests/unit/tools/test_playback.py tests/unit/tools/test_volume.py tests/contract/tool_schemas/test_playback_tool_schemas.py tests/contract/tool_schemas/test_volume_tool_schemas.py`
  - `uv run pytest tests/unit/services/test_playback_service.py tests/unit/services/test_volume_service.py`
  - `uv run pytest tests/unit/tools/test_playback.py tests/unit/tools/test_volume.py tests/contract/tool_schemas/test_playback_tool_schemas.py tests/contract/tool_schemas/test_volume_tool_schemas.py`
  - `make test` → `391 passed, 3 skipped`

### File List

- `src/soniq_mcp/adapters/soco_adapter.py`
- `src/soniq_mcp/services/sonos_service.py`
- `src/soniq_mcp/adapters/playback_adapter.py`
- `src/soniq_mcp/adapters/volume_adapter.py`
- `src/soniq_mcp/services/playback_service.py`
- `src/soniq_mcp/services/volume_service.py`
- `src/soniq_mcp/tools/__init__.py`
- `tests/unit/services/test_playback_service.py`
- `tests/unit/services/test_volume_service.py`
- `tests/unit/adapters/test_soco_adapter.py`
- `tests/unit/services/test_sonos_service.py`
- `_bmad-output/implementation-artifacts/2-4-apply-reliable-sonos-service-and-adapter-boundaries.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

## Change Log

| Date | Change |
|------|--------|
| 2026-03-28 | Story 2.4 implemented. Added shared `SoCoAdapter` and `SonosService` boundaries, refactored playback/volume wrappers to delegate through them, and expanded unit coverage for the new shared architecture. |
| 2026-03-28 | Addressed code review findings by restoring compatibility constructor handling in the playback/volume facades, updating shared-service injection to use explicit `sonos_service=` wiring, and adding regression tests for those paths. |
