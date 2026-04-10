# Story 2.3: Strengthen topology and grouping support for expanded audio flows

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want topology and grouping tools to support whole-home and specified-room-set flows reliably,
so that group-audio and input-aware behavior can build on accurate room context.

## Acceptance Criteria

1. Given a reachable household with multiple rooms, when the client requests current topology, then the service returns room names, coordinator state, group membership, and addressable room identity data.
2. Given a whole-home or specified-room-set grouping request, when the client invokes the grouping tool, then the service applies the grouping request explicitly against the discovered room set and returns the resulting topology in a normalized structure.
3. Given an invalid grouping target or ambiguous room set, when the client invokes the grouping tool, then the service returns an actionable validation error and the current grouping remains unchanged.

## Tasks / Subtasks

- [x] Extend normalized topology output to expose group membership explicitly (AC: 1, 3)
  - [x] Add `group_coordinator_uid: str | None` to the MCP-facing room topology schema in `src/soniq_mcp/schemas/responses.py`
  - [x] Keep `Room` as the authoritative domain object for room identity, coordinator state, and group membership
  - [x] Update `RoomResponse.from_domain(...)` and `SystemTopologyResponse.from_domain(...)` to surface room membership data without leaking raw SoCo objects
  - [x] Extend topology response tests and contract tests to lock the added field and preserve `snake_case`

- [x] Add explicit room-set grouping orchestration to `GroupService` (AC: 2, 3)
  - [x] Add a service method for explicit room-set grouping, e.g. `group_rooms(room_names: list[str], coordinator: str | None = None) -> list[Room]`
  - [x] Resolve all requested rooms case-insensitively from one discovery snapshot
  - [x] Reject:
    - [x] empty requested room sets
    - [x] duplicate or ambiguous room targets after normalization
    - [x] unknown room names
    - [x] coordinators not present in the requested room set
  - [x] Implement whole-home grouping by applying the request against the full discovered room set rather than assuming the caller knows all room names
  - [x] Reuse existing adapter grouping operations (`join_group`, `unjoin_room`, `party_mode`) where they fit instead of introducing duplicate grouping APIs
  - [x] Return the resulting normalized topology after the grouping change

- [x] Decide and implement the public grouping tool surface (AC: 2, 3)
  - [x] Add a single explicit multi-room grouping tool to `src/soniq_mcp/tools/groups.py`, such as:
    - [x] `group_rooms(rooms: list[str], coordinator: str | None = None)`
  - [x] Keep `party_mode()` for whole-home convenience if the implementation still maps to an all-room request
  - [x] Do not remove or silently change the semantics of `join_group` and `unjoin_room`
  - [x] Ensure the new tool returns normalized topology via `GroupTopologyResponse`
  - [x] Keep tool handlers thin: permission guard first, service call second, schema/error translation only

- [x] Harden grouping validation and error taxonomy (AC: 2, 3)
  - [x] Reuse `GroupValidationError(GroupError)` for actionable user-correctable grouping failures
  - [x] Make grouped-room-set validation deterministic so invalid requests fail before any adapter mutation
  - [x] Distinguish validation failures from Sonos/SoCo operational failures and discovery failures
  - [x] Preserve existing `RoomNotFoundError`, `GroupError`, and `SonosDiscoveryError` mapping patterns in tools

- [x] Preserve transport and contract parity for topology/grouping flows (AC: 1, 2, 3)
  - [x] Add the new grouping tool name to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [x] Ensure HTTP/bootstrap expectations are updated if the tool surface changes
  - [x] Extend contract tests for both system and grouping tool schemas
  - [x] Keep parity between `stdio` and HTTP surfaces

- [x] Add automated regression coverage for topology and explicit grouping (AC: 1, 2, 3)
  - [x] Extend `tests/unit/services/test_room_service.py` if topology normalization or lookup helpers change
  - [x] Extend `tests/unit/services/test_group_service.py` with explicit room-set grouping coverage
  - [x] Extend `tests/unit/tools/test_system.py` and `tests/unit/tools/test_groups.py` for topology and grouping payloads
  - [x] Extend `tests/contract/tool_schemas/test_system_tool_schemas.py` and `tests/contract/tool_schemas/test_groups_tool_schemas.py`
  - [x] Update integration/bootstrap coverage if the public tool list changes
  - [x] Run `make test` and confirm the full suite still passes

## Dev Notes

### Story intent

- This story is the topology and grouping reliability story for Epic 2.
- It should make explicit room-set grouping and topology context strong enough to support the group-audio and input-aware capabilities added in Stories 2.1 and 2.2.
- It is not another group-volume story and it is not an input-switching story.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-23-Strengthen-topology-and-grouping-support-for-expanded-audio-flows`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Room-Grouping-and-Household-Topology`]

### Current implementation gap to close

- `get_system_topology` already returns rooms and speakers, but the current `RoomResponse` omits `group_coordinator_uid`, so group membership is not actually exposed in the MCP response.
- `party_mode()` exists for whole-home grouping, and `join_group()` / `unjoin_room()` exist for pairwise operations, but there is no explicit specified-room-set grouping tool that takes a room set and returns the resulting normalized topology.
- That means AC 1 is only partially met today and AC 2 is not met with a single explicit user-facing workflow.
  [Source: `src/soniq_mcp/tools/system.py`]
  [Source: `src/soniq_mcp/schemas/responses.py`]
  [Source: `src/soniq_mcp/tools/groups.py`]
  [Source: `src/soniq_mcp/services/group_service.py`]

### Architecture guardrails

- Keep topology and grouping changes inside the documented capability boundaries:
  - topology discovery stays under `tools/system.py` + `services/room_service.py` + `adapters/discovery_adapter.py`
  - grouping orchestration stays under `tools/groups.py` + `services/group_service.py` + `adapters/soco_adapter.py`
- Do not move grouping orchestration into `RoomService`.
- Do not move topology schema changes into tool handlers.
- `SoCoAdapter` remains the only direct `soco` integration boundary.
- Tools own:
  - MCP registration,
  - permission checks,
  - payload formatting,
  - error translation only.
- Services own:
  - room-set validation,
  - coordinator selection,
  - topology normalization decisions,
  - grouping orchestration,
  - guard behavior.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Structure-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]

### Existing repo patterns to reuse

- `RoomService.get_topology()` already centralizes topology discovery and speaker enrichment.
- `GroupTopologyResponse.from_rooms(...)` already reconstructs group membership from `Room.is_coordinator` and `Room.group_coordinator_uid`.
- `GroupService` already owns grouping operations and now also owns group-audio validation/orchestration.
- The new story should extend those current boundaries, not replace them.
  [Source: `src/soniq_mcp/services/room_service.py`]
  [Source: `src/soniq_mcp/schemas/responses.py#GroupTopologyResponse`]
  [Source: `src/soniq_mcp/services/group_service.py`]

### Previous story intelligence

- Story 2.1 established the capability-aware input and topology baseline by enriching speaker metadata with capability fields and keeping validation in services.
- Story 2.2 established the current group-oriented orchestration pattern:
  - one topology snapshot per operation when practical,
  - case-insensitive room targeting,
  - typed `GroupValidationError` for user-correctable paths,
  - stable contract tests for new group tools.
- Carry these lessons forward:
  - resolve all requested rooms from one snapshot before mutating anything,
  - keep case-insensitive room normalization consistent with `RoomService.get_room(...)`,
  - avoid partial mutation on invalid room-set requests,
  - return normalized topology, not ad hoc status blobs, for the new explicit grouping flow.
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-2-add-group-level-volume-and-mute-controls.md`]
  [Source: `src/soniq_mcp/services/room_service.py#L66`]

### Recommended grouping design

- Implement explicit room-set grouping as a service-level orchestration over existing adapter primitives:
  1. discover and normalize the full room snapshot once,
  2. resolve the requested room set from that snapshot,
  3. choose a coordinator explicitly:
     - if the caller provides one, validate it belongs to the requested set,
     - otherwise choose a deterministic default, such as the first normalized requested room,
  4. unjoin rooms that should not remain grouped if the operation is meant to produce an exact requested set,
  5. join the requested non-coordinator rooms to the selected coordinator,
  6. return the resulting normalized topology.
- Keep `party_mode()` as a convenience wrapper for whole-home grouping, but make the new explicit grouping path the canonical way to request a specified room set.
- Preserve `join_group()` and `unjoin_room()` for fine-grained operations and backward compatibility.

This is an inference from the current codebase and requirements:
- the repo already has pairwise join/unjoin and whole-home grouping primitives,
- the missing user-facing capability is an exact requested room-set operation that returns normalized topology.

### Topology response requirements

- AC 1 requires room names, coordinator state, group membership, and addressable room identity data.
- Today, `SystemTopologyResponse` includes `rooms` and `speakers`, but `RoomResponse` only exposes:
  - `name`
  - `uid`
  - `ip_address`
  - `is_coordinator`
- Extend the topology response so group membership is explicit and stable for clients.
- Keep the response transport-neutral and `snake_case`.
- Do not leak raw SoCo group objects or speaker objects.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-23-Strengthen-topology-and-grouping-support-for-expanded-audio-flows`]
  [Source: `src/soniq_mcp/schemas/responses.py`]

### SoCo baseline and latest check

- The repo currently pins `soco>=0.30.14`.
- PyPI shows the latest release is `0.31.0`, published on April 5, 2026.
- Current SoCo docs still document the grouping primitives this repo already relies on:
  - `partymode()`
  - `join(master, **kwargs)`
  - `unjoin(**kwargs)`
  - `all_zones`
  - `visible_zones`
  - `group.coordinator`
  - `group.members`
- Implement against the repo’s pinned baseline and do not bundle a SoCo upgrade into this story.
- The online docs currently reflect a newer dev stream than the pinned dependency, so prefer only the primitives already proven by the repo and tests.
  [Source: [PyPI soco](https://pypi.org/project/soco/)]
  [Source: [SoCo core docs](https://soco.readthedocs.io/en/latest/api/soco.core.html)]
  [Source: [SoCo groups docs](https://soco.readthedocs.io/en/latest/api/soco.groups.html)]

### Suggested public tool surface

- Keep:
  - `get_group_topology()`
  - `join_group(room: str, coordinator: str)`
  - `unjoin_room(room: str)`
  - `party_mode()`
- Add one explicit room-set grouping tool, for example:
  - `group_rooms(rooms: list[str], coordinator: str | None = None) -> GroupTopologyResponse`

Suggested normalized response shape for the explicit grouping tool:

```python
{
    "groups": [
        {
            "coordinator": "Living Room",
            "members": ["Living Room", "Kitchen", "Office"],
        }
    ],
    "total_groups": 1,
    "total_rooms": 3,
}
```

- If you choose a different tool name, keep it explicit, capability-oriented, and aligned with the repo’s current naming conventions.

### Files likely to change

```text
_bmad-output/implementation-artifacts/phase-2/2-3-strengthen-topology-and-grouping-support-for-expanded-audio-flows.md
src/soniq_mcp/schemas/responses.py
src/soniq_mcp/services/room_service.py
src/soniq_mcp/services/group_service.py
src/soniq_mcp/tools/system.py
src/soniq_mcp/tools/groups.py
src/soniq_mcp/config/models.py
tests/unit/services/test_room_service.py
tests/unit/services/test_group_service.py
tests/unit/tools/test_system.py
tests/unit/tools/test_groups.py
tests/contract/tool_schemas/test_system_tool_schemas.py
tests/contract/tool_schemas/test_groups_tool_schemas.py
tests/integration/transports/test_http_bootstrap.py
```

### Testing requirements

- Room-service/system tests must verify that topology responses expose:
  - room identity,
  - coordinator state,
  - explicit group membership,
  - speaker identity data.
- Group-service tests must verify:
  - deterministic coordinator selection,
  - exact room-set grouping behavior,
  - whole-home grouping behavior if routed through the new service method,
  - rejection of unknown, duplicate, empty, and ambiguous room sets,
  - no adapter mutations when validation fails.
- Group tool tests must verify:
  - new tool registration,
  - response shape stability,
  - typed error mapping for validation, discovery, and operational failures.
- Contract tests must lock the new tool name, parameters, and annotations.
- Integration/bootstrap coverage must be updated if the tool list changes.

### Project Structure Notes

- No `project-context.md` file was present during story creation, so the BMAD planning artifacts and the current source tree are the authoritative context.
- This story should strengthen the current `system` and `groups` capability slices. Do not create a temporary topology-only module or a generic orchestration layer outside those established boundaries.
- Keep the repo stateless. Topology and grouping remain Sonos-backed runtime state, not application-owned state.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Data-Architecture`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Enforcement-Guidelines`]

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-23-Strengthen-topology-and-grouping-support-for-expanded-audio-flows`
- Epic context: `_bmad-output/planning-artifacts/epics.md#Epic-2-Input-and-Group-Audio-Expansion`
- PRD grouping requirements: `_bmad-output/planning-artifacts/prd.md#Room-Grouping-and-Household-Topology`
- Architecture patterns: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`
- System topology tool baseline: `src/soniq_mcp/tools/system.py`
- Grouping tool baseline: `src/soniq_mcp/tools/groups.py`
- Room service baseline: `src/soniq_mcp/services/room_service.py`
- Group service baseline: `src/soniq_mcp/services/group_service.py`
- Topology research inventory: `_bmad-output/planning-artifacts/research/technical-soco-capability-gap-research-2026-04-02.md`
- Previous story context: `_bmad-output/implementation-artifacts/phase-2/2-2-add-group-level-volume-and-mute-controls.md`
- Dependency baseline: `pyproject.toml`
- External reference: [PyPI soco](https://pypi.org/project/soco/)
- External reference: [SoCo core docs](https://soco.readthedocs.io/en/latest/api/soco.core.html)
- External reference: [SoCo groups docs](https://soco.readthedocs.io/en/latest/api/soco.groups.html)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `uv run pytest tests/unit/services/test_group_rooms_service.py -q`
- `uv run pytest tests/unit/tools/test_group_rooms_tool.py tests/contract/tool_schemas/test_group_rooms_tool_schema.py tests/unit/tools/test_system.py tests/contract/tool_schemas/test_system_tool_schemas.py tests/integration/transports/test_http_bootstrap.py -q`
- `uv run pytest tests/unit/schemas/test_responses.py tests/unit/services/test_group_service.py tests/unit/tools/test_groups.py -q`
- `make test`

### Completion Notes List

- All 6 tasks completed. `make test` passes with 1107 tests, 3 skipped.
- `RoomResponse` now exposes `group_coordinator_uid: str | None` — surfaced from `Room.group_coordinator_uid`; flows through `RoomListResponse` (list_rooms) and `SystemTopologyResponse` (get_system_topology).
- `GroupService.group_rooms()` added: resolves all rooms from one snapshot, validates deterministically (empty, duplicates, ambiguous normalized names, unknown names, coordinator-not-in-set), unjoins requested members that are still attached to other groups, unjoins stale followers of any requested room, joins requested non-coordinators to coordinator, returns updated topology.
- `group_rooms` MCP tool added to `tools/groups.py` — returns `GroupTopologyResponse`, uses `_CONTROL_TOOL_HINTS`, catches `GroupValidationError`, `RoomNotFoundError`, `GroupError`, `SonosDiscoveryError`.
- `KNOWN_TOOL_NAMES` updated (47 tool names total).
- HTTP bootstrap test updated to expect 47 tools.
- Follow-up review fixes applied: ambiguous room requests now fail before mutation, and exact room-set grouping no longer carries stale members from pre-existing groups into the requested topology.

### File List

**New files:**
- `tests/unit/services/test_group_rooms_service.py`
- `tests/unit/tools/test_group_rooms_tool.py`
- `tests/contract/tool_schemas/test_group_rooms_tool_schema.py`

**Modified files:**
- `src/soniq_mcp/schemas/responses.py` — added `group_coordinator_uid` to `RoomResponse`
- `src/soniq_mcp/services/group_service.py` — added `group_rooms()` method
- `src/soniq_mcp/tools/groups.py` — added `group_rooms` tool
- `src/soniq_mcp/config/models.py` — added `group_rooms` to `KNOWN_TOOL_NAMES`
- `tests/unit/schemas/test_responses.py` — extended `TestRoomResponse` with `group_coordinator_uid` tests
- `tests/unit/tools/test_system.py` — extended with `group_coordinator_uid` topology tests
- `tests/contract/tool_schemas/test_system_tool_schemas.py` — added `group_coordinator_uid` contract test
- `tests/integration/transports/test_http_bootstrap.py` — updated `EXPECTED_TOOL_NAMES` and count
- `_bmad-output/implementation-artifacts/phase-2/2-3-strengthen-topology-and-grouping-support-for-expanded-audio-flows.md` — updated story

### Change Log

- 2026-04-10: Implemented Story 2.3 — topology group membership exposure and explicit room-set grouping. Added `group_coordinator_uid` to `RoomResponse`, `GroupService.group_rooms()` with full validation, `group_rooms` MCP tool, and comprehensive test coverage (1104 tests passing).
- 2026-04-10: Addressed Story 2.3 code review findings. `group_rooms()` now rejects ambiguous normalized room names and detaches requested rooms or stale followers before regrouping so exact room-set requests do not inherit old group state.
