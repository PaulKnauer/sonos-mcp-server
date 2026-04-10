# Story 2.2: Add group-level volume and mute controls

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to control volume and mute for an active group,
so that I can manage multi-room listening without changing rooms one by one.

## Acceptance Criteria

1. Given an active Sonos group with a coordinator, when the client requests group-level volume or mute state, then the service returns the normalized group audio state.
2. Given an active Sonos group with a coordinator, when the client updates group volume or mute, then the service applies the change through the group-service boundary and respects configured safety limits for volume-related actions.
3. Given a request that targets a non-grouped or invalid room state, when the group-audio tool is invoked, then the service returns a typed validation error and does not affect unrelated rooms.

## Tasks / Subtasks

- [ ] Add group-audio domain and schema primitives (AC: 1, 2, 3)
  - [ ] Add `GroupValidationError(GroupError)` to `src/soniq_mcp/domain/exceptions.py` for non-grouped, coordinator-resolution, and invalid-target validation paths
  - [ ] Add `GroupAudioState` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields:
    - [ ] `room_name: str`
    - [ ] `coordinator_room_name: str`
    - [ ] `member_room_names: tuple[str, ...]`
    - [ ] `volume: int`
    - [ ] `is_muted: bool`
  - [ ] Add `GroupAudioStateResponse` to `src/soniq_mcp/schemas/responses.py`
  - [ ] Extend response-schema tests to lock the serialized field set and `snake_case` naming

- [ ] Extend `SoCoAdapter` with group-audio operations (AC: 1, 2, 3)
  - [ ] Add `get_group_volume(ip_address: str) -> int`
  - [ ] Add `set_group_volume(ip_address: str, volume: int) -> None`
  - [ ] Add `adjust_group_volume(ip_address: str, delta: int) -> int`
  - [ ] Add `get_group_mute(ip_address: str) -> bool`
  - [ ] Add `set_group_mute(ip_address: str, muted: bool) -> None`
  - [ ] Implement the adapter methods via `zone.group.volume`, `zone.group.mute`, and `zone.group.set_relative_volume(delta)`
  - [ ] Keep all `soco` imports inside `src/soniq_mcp/adapters/soco_adapter.py`
  - [ ] Wrap all SoCo failures in `GroupError`

- [ ] Extend `GroupService` to own group-audio orchestration (AC: 1, 2, 3)
  - [ ] Update `GroupService` to accept runtime config so it can enforce `max_volume_pct`
  - [ ] Add `get_group_audio_state(room_name: str) -> GroupAudioState`
  - [ ] Add `set_group_volume(room_name: str, volume: int) -> GroupAudioState`
  - [ ] Add `adjust_group_volume(room_name: str, delta: int) -> GroupAudioState`
  - [ ] Add `group_mute(room_name: str) -> GroupAudioState`
  - [ ] Add `group_unmute(room_name: str) -> GroupAudioState`
  - [ ] Reuse a single room/topology snapshot per operation to resolve:
    - [ ] the requested room
    - [ ] the active coordinator
    - [ ] the current member room names
  - [ ] Reject non-grouped targets with `GroupValidationError` instead of silently treating a single room as a group-audio success path
  - [ ] Enforce `config.max_volume_pct` for absolute and relative group-volume operations before adapter writes
  - [ ] Normalize all successful results into `GroupAudioState`

- [ ] Extend MCP grouping tools with group-audio endpoints (AC: 1, 2, 3)
  - [ ] Add tools to `src/soniq_mcp/tools/groups.py`:
    - [ ] `get_group_volume(room: str)`
    - [ ] `set_group_volume(room: str, volume: int)`
    - [ ] `adjust_group_volume(room: str, delta: int)`
    - [ ] `group_mute(room: str)`
    - [ ] `group_unmute(room: str)`
  - [ ] Use existing `_READ_ONLY_TOOL_HINTS` and `_CONTROL_TOOL_HINTS`
  - [ ] Keep tool handlers thin: permission guard first, service call second, schema/error translation only
  - [ ] Return `GroupAudioStateResponse.model_dump()` for state-returning operations
  - [ ] Catch `RoomNotFoundError`, `GroupError`, and `SonosDiscoveryError` and map them through `ErrorResponse`
  - [ ] Catch `VolumeCapExceeded` for volume-changing operations and map it through `ErrorResponse.from_volume_cap(...)`

- [ ] Wire the expanded grouping capability into config and registration (AC: 2, 3)
  - [ ] Update `src/soniq_mcp/tools/__init__.py` so `GroupService` receives config
  - [ ] Add the new tool names to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [ ] Preserve stable registration order and transport parity across `stdio` and HTTP bootstraps

- [ ] Add automated regression coverage for group audio (AC: 1, 2, 3)
  - [ ] Extend `tests/unit/adapters/test_soco_adapter.py` or add focused adapter tests for `zone.group` volume/mute operations
  - [ ] Extend `tests/unit/services/test_group_service.py` with grouped, ungrouped, cap, room-not-found, and adapter-failure coverage
  - [ ] Extend `tests/unit/tools/test_groups.py` with new tool registration, success payloads, and typed error mapping
  - [ ] Extend `tests/contract/tool_schemas/test_groups_tool_schemas.py` to lock the new tool names, parameters, and annotations
  - [ ] Extend `tests/unit/schemas/test_responses.py` for `GroupAudioStateResponse`
  - [ ] Update transport/bootstrap coverage so the new group-audio tools remain exposed consistently
  - [ ] Run `make test` and confirm the full suite still passes

## Dev Notes

### Story intent

- This story adds group-level volume and mute control to the active grouping capability family in Phase 2 Epic 2.
- It is not a room-volume story. Existing `get_volume`, `set_volume`, `adjust_volume`, `mute`, and `unmute` remain room-scoped.
- It is not a topology-discovery story. Reuse existing room/group metadata unless a specific gap blocks normalized group-state output.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-22-Add-group-level-volume-and-mute-controls`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Room-Grouping-and-Household-Topology`]

### Architecture guardrails

- Keep this work inside the existing grouping capability boundary:
  - MCP handlers stay in `src/soniq_mcp/tools/groups.py`
  - orchestration stays in `src/soniq_mcp/services/group_service.py`
  - direct Sonos calls stay in `src/soniq_mcp/adapters/soco_adapter.py`
- Do not add group-audio logic to `tools/volume.py`, `services/volume_service.py`, or `services/sonos_service.py`.
- Services must own:
  - target-room validation
  - active-group/coordinator validation
  - group member normalization
  - safety-cap enforcement
  - typed validation failures
- Tools must own:
  - MCP registration
  - permission checks
  - success payload formatting
  - error translation only
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries-Refresh`]

### Existing repo patterns to reuse

- Current grouping and volume modules already define the shape this story should extend:
  - `src/soniq_mcp/tools/groups.py` + `src/soniq_mcp/services/group_service.py`
  - `src/soniq_mcp/tools/volume.py` + `src/soniq_mcp/services/volume_service.py`
- Reuse the established conventions:
  - module-local `_READ_ONLY_TOOL_HINTS` / `_CONTROL_TOOL_HINTS`
  - `assert_tool_permitted(tool_name, config)` at invocation time
  - structured `ErrorResponse` payloads on expected failures
  - Pydantic response models with `snake_case` fields
  - contract tests that lock tool names, parameters, and annotations
  [Source: `src/soniq_mcp/tools/groups.py`]
  [Source: `src/soniq_mcp/tools/volume.py`]
  [Source: `tests/contract/tool_schemas/test_groups_tool_schemas.py`]
  [Source: `tests/contract/tool_schemas/test_volume_tool_schemas.py`]

### Previous story intelligence

- Story 2.1 established the phase-2 pattern of:
  - adding a dedicated domain state model and response schema,
  - keeping validation in the service layer,
  - keeping SoCo wrapped behind `SoCoAdapter`,
  - adding contract tests to lock the public MCP surface.
- Carry those lessons forward here:
  - do not let raw SoCo `zone.group` behavior define the external contract,
  - do not skip typed validation just because SoCo would raise later,
  - do not duplicate discovery calls unnecessarily inside one service operation.
- Story 2.1 review also fixed a redundant double-discovery path. For group-audio flows, prefer one topology snapshot per service call and derive target room, coordinator, and member list from that same snapshot where practical.
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md#Previous-story-intelligence`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md#Review-findings`]

### Group-audio implementation guidance

- `Room` already carries:
  - `is_coordinator`
  - `group_coordinator_uid`
- `GroupTopologyResponse.from_rooms(...)` already reconstructs coordinator/member relationships from those fields.
- That means this story should not invent a parallel group-membership model at the tool layer.
- A practical service approach is:
  1. load the current room list once,
  2. resolve the requested room from that snapshot,
  3. resolve its effective coordinator UID,
  4. derive the grouped member room names from the same snapshot,
  5. use the target room IP (or resolved coordinator IP) for adapter access to `zone.group`.
- Treat a room with no grouped peers as invalid for these tools. The AC explicitly calls for a typed validation error on non-grouped room state, not an implicit room-volume fallback.
  [Source: `src/soniq_mcp/domain/models.py`]
  [Source: `src/soniq_mcp/schemas/responses.py#GroupTopologyResponse`]
  [Source: `src/soniq_mcp/services/group_service.py`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-22-Add-group-level-volume-and-mute-controls`]

### Safety and error-handling requirements

- Group-volume writes must respect `config.max_volume_pct`, the same runtime safety cap already used for room-volume actions.
- For `set_group_volume`, reject values above the cap before any adapter write.
- For `adjust_group_volume`, calculate the intended target from the current group volume first, then reject cap-violating requests before calling the adapter.
- Preserve deterministic error categories:
  - invalid room name -> `RoomNotFoundError`
  - non-grouped or invalid group target -> `GroupValidationError`
  - cap violation -> `VolumeCapExceeded`
  - Sonos/SoCo failure -> `GroupError`
  - discovery failure -> `SonosDiscoveryError`
- Do not let a failed group operation mutate unrelated rooms through partial fallback logic.
  [Source: `_bmad-output/planning-artifacts/prd.md#Permission-Safety-and-Control-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Non-Functional-Requirements`]
  [Source: `src/soniq_mcp/domain/exceptions.py`]

### SoCo API baseline and latest check

- The repo currently pins `soco>=0.30.14`.
- Current PyPI latest is `0.31.0`, released on April 5, 2026.
- Official SoCo docs still document `ZoneGroup.volume`, `ZoneGroup.mute`, and `ZoneGroup.set_relative_volume(...)`.
- This story should implement against the repo’s pinned baseline and must not bundle a dependency upgrade unless a separate change explicitly requires it.
- Prefer `set_relative_volume(delta)` for relative adjustments because the official docs note it avoids the extra network call pattern of read-modify-write through `group.volume += delta`.
  [Source: `pyproject.toml`]
  [Source: PyPI `soco` project page, latest release metadata]
  [Source: official SoCo `soco.groups.ZoneGroup` documentation]

### Suggested public tool surface

- `get_group_volume(room: str) -> GroupAudioStateResponse`
- `set_group_volume(room: str, volume: int) -> GroupAudioStateResponse`
- `adjust_group_volume(room: str, delta: int) -> GroupAudioStateResponse`
- `group_mute(room: str) -> GroupAudioStateResponse`
- `group_unmute(room: str) -> GroupAudioStateResponse`

Suggested normalized response shape:

```python
{
    "room_name": "Living Room",
    "coordinator_room_name": "Living Room",
    "member_room_names": ("Living Room", "Kitchen"),
    "volume": 32,
    "is_muted": False,
}
```

- `room_name` should identify the requested target room, not a generic label.
- `coordinator_room_name` should always resolve to the active group coordinator.
- `member_room_names` should be stable, human-readable room names from current topology.

### Files likely to change

```text
_bmad-output/implementation-artifacts/phase-2/2-2-add-group-level-volume-and-mute-controls.md
src/soniq_mcp/domain/exceptions.py
src/soniq_mcp/domain/models.py
src/soniq_mcp/adapters/soco_adapter.py
src/soniq_mcp/schemas/responses.py
src/soniq_mcp/services/group_service.py
src/soniq_mcp/tools/groups.py
src/soniq_mcp/tools/__init__.py
src/soniq_mcp/config/models.py
tests/unit/adapters/test_soco_adapter.py
tests/unit/services/test_group_service.py
tests/unit/tools/test_groups.py
tests/unit/schemas/test_responses.py
tests/contract/tool_schemas/test_groups_tool_schemas.py
tests/integration/transports/test_http_bootstrap.py
```

### Testing requirements

- Adapter tests must verify:
  - `zone.group.volume` reads/writes map correctly,
  - `zone.group.mute` reads/writes map correctly,
  - `set_relative_volume(delta)` is used for relative adjustments,
  - SoCo exceptions are wrapped as `GroupError`.
- Service tests must verify:
  - successful grouped-state read,
  - successful grouped absolute-volume write,
  - successful grouped relative-volume write,
  - successful group mute/unmute,
  - non-grouped target rejection,
  - room-not-found propagation,
  - cap enforcement for absolute and relative changes,
  - discovery failure propagation.
- Tool tests must verify:
  - disabled-tool registration behavior,
  - stable success payload shape,
  - `GroupError` translation,
  - `RoomNotFoundError` translation,
  - `SonosDiscoveryError` translation,
  - `VolumeCapExceeded` translation for group-volume writes.
- Contract tests must lock tool names, parameters, and annotations for all five new tools.
- HTTP/bootstrap coverage must confirm the new tools are exposed consistently with `stdio`.

### Project Structure Notes

- No `project-context.md` file was present in this repo during story creation, so architecture, planning, source, and previous-story artifacts are the authoritative guidance set.
- This story fits the documented capability-family structure directly. Do not create a temporary `group_audio.py` tool module or a generic catch-all service just for this slice.
- Keep the repo stateless. Group audio state remains authoritative on Sonos devices, not in any application database or cache added by this story.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Data-Architecture`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Structure-Patterns`]

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-22-Add-group-level-volume-and-mute-controls`
- Epic context: `_bmad-output/planning-artifacts/epics.md#Epic-2-Input-and-Group-Audio-Expansion`
- PRD requirements: `_bmad-output/planning-artifacts/prd.md#Room-Grouping-and-Household-Topology`
- PRD safety and NFRs: `_bmad-output/planning-artifacts/prd.md#Permission-Safety-and-Control-Boundaries`
- Architecture patterns: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`
- Architecture boundaries: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries-Refresh`
- SoCo capability-gap analysis: `_bmad-output/planning-artifacts/research/technical-soco-capability-gap-research-2026-04-02.md#Gap-Category-9-Group-Volume-and-Mute`
- Previous story: `_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md`
- Grouping module pattern: `src/soniq_mcp/tools/groups.py`
- Group service baseline: `src/soniq_mcp/services/group_service.py`
- Room topology baseline: `src/soniq_mcp/services/room_service.py`
- Domain model baseline: `src/soniq_mcp/domain/models.py`
- SoCo dependency baseline: `pyproject.toml`
- External reference: official SoCo `soco.groups.ZoneGroup` docs
- External reference: PyPI `soco` release history

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

- _bmad-output/implementation-artifacts/phase-2/2-2-add-group-level-volume-and-mute-controls.md
