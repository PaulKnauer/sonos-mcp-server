# Story 3.3: Control Room Grouping and Multi-Room Playback

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to inspect and change room grouping,
so that I can control playback across multiple Sonos rooms.

## Acceptance Criteria

1. Given a Sonos household with multiple rooms, when the user invokes the get grouping topology tool, then the server returns the current grouping state showing which rooms are grouped together and their coordinators.
2. Given a valid room name and a valid coordinator room name, when the user invokes the join group tool, then the room is added to the coordinator's playback group and the response confirms success.
3. Given a room that belongs to a group, when the user invokes the unjoin room tool, then the room is removed from its current group and begins operating independently, and the response confirms success.
4. Given a Sonos household with multiple rooms, when the user invokes the party mode tool, then all rooms are joined into a single whole-home group and the response confirms success.

## Tasks / Subtasks

- [x] Add `GroupError` to the domain exception taxonomy (AC: 1, 2, 3, 4)
  - [x] Add `GroupError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [x] Add `ErrorResponse.from_group_error(exc)` factory to `src/soniq_mcp/schemas/errors.py`

- [x] Add response schemas for group topology (AC: 1)
  - [x] Add `GroupResponse` and `GroupTopologyResponse` Pydantic models to `src/soniq_mcp/schemas/responses.py`
  - [x] `GroupResponse`: fields `coordinator: str`, `members: list[str]`
  - [x] `GroupTopologyResponse`: fields `groups: list[GroupResponse]`, `total_groups: int`, `total_rooms: int`
  - [x] Add `GroupTopologyResponse.from_rooms(rooms: list[Room]) -> "GroupTopologyResponse"` classmethod (see Dev Notes for grouping logic)

- [x] Extend `SoCoAdapter` with grouping operations (AC: 2, 3, 4)
  - [x] Add `join_group(ip_address: str, coordinator_ip: str) -> None` — calls `zone.join(self._make_zone(coordinator_ip))`; wraps all SoCo exceptions in `GroupError`
  - [x] Add `unjoin_room(ip_address: str) -> None` — calls `zone.unjoin()`; wraps all SoCo exceptions in `GroupError`
  - [x] Add `party_mode(ip_address: str) -> None` — calls `zone.partymode()`; wraps all SoCo exceptions in `GroupError`
  - [x] All new methods use `_make_zone` — no top-level `import soco`

- [x] Create `GroupService` (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/services/group_service.py`
  - [x] Constructor: `GroupService(room_service: object, adapter: SoCoAdapter)` — same pattern as `QueueService` and `FavouritesService`
  - [x] `get_group_topology() -> list[Room]` — calls `room_service.list_rooms()` and returns all rooms (topology is derived from Room fields at the schema layer)
  - [x] `join_group(room_name: str, coordinator_name: str) -> None` — resolves both via `room_service.get_room()`, calls `adapter.join_group(room.ip_address, coordinator.ip_address)`
  - [x] `unjoin_room(room_name: str) -> None` — resolves via `room_service.get_room(room_name)`, calls `adapter.unjoin_room(ip)`
  - [x] `party_mode() -> None` — calls `room_service.list_rooms()`; raises `GroupError("No Sonos rooms found — cannot execute party mode")` if empty; calls `adapter.party_mode(rooms[0].ip_address)`

- [x] Create `tools/groups.py` with MCP tool handlers (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/tools/groups.py` following the exact pattern of `tools/playback.py`
  - [x] `register(app, config, group_service)` registers tools if not in `config.tools_disabled`
  - [x] `get_group_topology() -> dict` — `_READ_ONLY_TOOL_HINTS`; calls `group_service.get_group_topology()`, returns `GroupTopologyResponse.from_rooms(rooms).model_dump()`; catches `SonosDiscoveryError` and `GroupError`
  - [x] `join_group(room: str, coordinator: str) -> dict` — `_CONTROL_TOOL_HINTS`; calls `group_service.join_group(room, coordinator)`; returns `{"status": "ok", "room": room, "coordinator": coordinator}`
  - [x] `unjoin_room(room: str) -> dict` — `_CONTROL_TOOL_HINTS`; calls `group_service.unjoin_room(room)`; returns `{"status": "ok", "room": room}`
  - [x] `party_mode() -> dict` — `_CONTROL_TOOL_HINTS`; calls `group_service.party_mode()`; returns `{"status": "ok"}`
  - [x] All handlers catch `RoomNotFoundError`, `GroupError`, and `SonosDiscoveryError`, return `ErrorResponse.model_dump()`
  - [x] Each handler starts with `assert_tool_permitted(tool_name, config)`
  - [x] Define `_READ_ONLY_TOOL_HINTS` and `_CONTROL_TOOL_HINTS` at module level (do not import from `playback.py`)

- [x] Wire groups tools into `tools/__init__.py` (AC: 1, 2, 3, 4)
  - [x] Import `GroupService` from `services/group_service.py`
  - [x] Import `register as register_groups` from `tools/groups.py`
  - [x] Construct `group_service = GroupService(room_service, SoCoAdapter())` — a fresh `SoCoAdapter()` instance is fine (stateless)
  - [x] Call `register_groups(app, config, group_service)` at the end of `register_all`

- [x] Update `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py` (AC: 1, 2, 3, 4)
  - [x] Add `"get_group_topology"`, `"join_group"`, `"unjoin_room"`, `"party_mode"` to the frozenset

- [x] Add automated tests (AC: 1, 2, 3, 4)
  - [x] `tests/unit/adapters/test_soco_adapter_groups.py` — mock `zone.join`, `zone.unjoin`, `zone.partymode`; cover happy paths and `GroupError` wrapping for each method
  - [x] `tests/unit/services/test_group_service.py` — cover all 4 methods; `RoomNotFoundError` propagation; `GroupError` propagation; empty-room-list guard in `party_mode`; use fake `RoomService` and fake `SoCoAdapter`
  - [x] `tests/unit/tools/test_groups.py` — unit tests for all 4 tool handlers; verify response shapes, error translation, tool-disabled guard
  - [x] `tests/contract/tool_schemas/test_groups_tool_schemas.py` — contract tests asserting tool names and parameter names remain stable (follow pattern of `test_playback_tool_schemas.py`)
  - [x] Run `make test` and confirm full suite passes with no regressions

## Dev Notes

### Architecture Constraints (Must Follow)

- `tools/` handles MCP-facing inputs and outputs only — no `SoCo` imports, no room lookup.
- `services/` owns orchestration — room resolution plus calling the adapter.
- `adapters/soco_adapter.py` is the only module that imports `soco`. All new SoCo calls go in `SoCoAdapter`.
- `GroupService` constructor pattern: `GroupService(room_service, adapter)` — peer of `QueueService` and `FavouritesService`.
- Tool names use `snake_case` verb-oriented naming consistent with existing tools.
- All response schemas are Pydantic models in `schemas/responses.py`; tool handlers call `.model_dump()`.
- All error responses are `ErrorResponse.model_dump()` — never raise from a tool handler.
- `_READ_ONLY_TOOL_HINTS` and `_CONTROL_TOOL_HINTS` are defined at module level in each tools file — duplicate them in `groups.py` (do not import from `playback.py`).
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]

### SoCo Grouping API Reference

| Operation | SoCo call | Notes |
|---|---|---|
| Join group | `zone.join(coordinator_zone)` | `coordinator_zone` is a `soco.SoCo(coordinator_ip)` instance. The zone joins the coordinator's current group. |
| Unjoin room | `zone.unjoin()` | Zone leaves its group and becomes a standalone coordinator. |
| Party mode | `zone.partymode()` | All zones in the household join a single group with `zone` as coordinator. Only need to call on one zone. |

All SoCo exceptions must be caught and re-raised as `GroupError`.

**Important:** `zone.join(coordinator_zone)` takes a live `soco.SoCo` object, not just an IP string. Use `self._make_zone(coordinator_ip)` to create it. This means both IPs must be valid and reachable at call time.

### `get_group_topology` — Deriving Groups from Room Data

The `Room` domain model already captures grouping state:
- `is_coordinator: bool` — True if this zone is currently a group coordinator (or standalone)
- `group_coordinator_uid: str | None` — UID of the group's coordinator; `None` if the room IS the coordinator

Derive groups in `GroupTopologyResponse.from_rooms()`:

```python
@classmethod
def from_rooms(cls, rooms: list[Room]) -> "GroupTopologyResponse":
    uid_to_name = {r.uid: r.name for r in rooms}
    groups_map: dict[str, list[str]] = {}  # coordinator_uid -> member names

    for room in rooms:
        if room.is_coordinator:
            groups_map.setdefault(room.uid, []).insert(0, room.name)
        else:
            coord_uid = room.group_coordinator_uid or room.uid
            groups_map.setdefault(coord_uid, []).append(room.name)

    groups = [
        GroupResponse(
            coordinator=uid_to_name.get(coord_uid, coord_uid),
            members=members,
        )
        for coord_uid, members in groups_map.items()
    ]
    return cls(groups=groups, total_groups=len(groups), total_rooms=len(rooms))
```

Note: this uses existing data from `room_service.list_rooms()` — no additional SoCo calls needed for the read path.

### Current `tools/__init__.py` Wiring (After Stories 3.1 and 3.2)

```python
room_service = RoomService(DiscoveryAdapter())
register_system(app, config, room_service)

sonos_service = SonosService(room_service, SoCoAdapter(), config)
playback_service = PlaybackService(sonos_service=sonos_service)
register_playback(app, config, playback_service)

volume_service = VolumeService(sonos_service=sonos_service)
register_volume(app, config, volume_service)

favourites_service = FavouritesService(room_service, SoCoAdapter())
register_favourites(app, config, favourites_service)
register_playlists(app, config, favourites_service)

queue_service = QueueService(room_service, SoCoAdapter())
register_queue(app, config, queue_service)
```

Add grouping wiring after the queue wiring:

```python
from soniq_mcp.services.group_service import GroupService
from soniq_mcp.tools.groups import register as register_groups

group_service = GroupService(room_service, SoCoAdapter())
register_groups(app, config, group_service)
```

### Domain Exception Extension

Add to `src/soniq_mcp/domain/exceptions.py`:

```python
class GroupError(SoniqDomainError):
    """Raised when a Sonos grouping operation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
```

Add to `src/soniq_mcp/schemas/errors.py`:

```python
@classmethod
def from_group_error(cls, exc: Exception) -> "ErrorResponse":
    return cls(
        error=str(exc),
        field="group",
        suggestion=(
            "Check that all rooms are reachable and on the same Sonos network. "
            "Use 'list_rooms' to verify available rooms before grouping operations."
        ),
    )
```

### Response Schema Shapes

Add to `src/soniq_mcp/schemas/responses.py`:

```python
class GroupResponse(BaseModel):
    coordinator: str
    members: list[str]


class GroupTopologyResponse(BaseModel):
    groups: list[GroupResponse]
    total_groups: int
    total_rooms: int

    @classmethod
    def from_rooms(cls, rooms: list[Room]) -> "GroupTopologyResponse":
        # See Dev Notes for implementation
        ...
```

`Room` is already imported at the top of `schemas/responses.py` — no new imports needed.

### Tool Name Registry (for contract tests and `tools_disabled`)

| Tool name | Method | Hint type | Parameters |
|---|---|---|---|
| `get_group_topology` | GET | `_READ_ONLY_TOOL_HINTS` | *(none)* |
| `join_group` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `coordinator: str` |
| `unjoin_room` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str` |
| `party_mode` | MUTATE | `_CONTROL_TOOL_HINTS` | *(none)* |

### `KNOWN_TOOL_NAMES` Update Required

`config/models.py` validates `tools_disabled` entries against `KNOWN_TOOL_NAMES`. Without adding the four new tool names, any attempt to use `tools_disabled` with grouping tools will raise a validation error. **This was the cause of a regression in story 3.2** — do not forget this step.

Current `KNOWN_TOOL_NAMES` (as of story 3.2 completion): `ping`, `server_info`, `list_rooms`, `get_system_topology`, `play`, `pause`, `stop`, `next_track`, `previous_track`, `get_playback_state`, `get_track_info`, `get_volume`, `set_volume`, `adjust_volume`, `mute`, `unmute`, `get_mute`, `list_favourites`, `play_favourite`, `list_playlists`, `play_playlist`, *plus queue tools from 3.1*.

Add: `"get_group_topology"`, `"join_group"`, `"unjoin_room"`, `"party_mode"`.

### Testing Requirements

- Use the existing fake-injection pattern — `FakeGroupService` with controlled return values and side effects.
- For `test_soco_adapter_groups.py`: mock `zone.join`, `zone.unjoin`, `zone.partymode` using `unittest.mock.MagicMock`. For `join_group`, also mock `_make_zone` to return a controllable zone for both the target and coordinator.
- For `test_group_service.py`: use a fake `RoomService` returning predefined `Room` instances (or raising `RoomNotFoundError`). Use a fake `SoCoAdapter` with controlled outcomes.
- Contract tests: follow the exact same pattern as `test_playback_tool_schemas.py`.
- Run `make test` before marking done; all existing 539+ tests must still pass.
  [Source: `_bmad-output/planning-artifacts/architecture.md#File-Organization-Patterns`]

### `join_group` — Coordinator Must Be a Coordinator

SoCo's `zone.join(master)` expects `master` to be any zone in the target group — typically the coordinator. If the user provides a room name that is not currently a group coordinator, SoCo will still join to that zone's group (SoCo internally finds the coordinator). The service should NOT validate whether the coordinator room IS a coordinator — just pass both IPs to the adapter and let SoCo handle it.

### `unjoin_room` — Idempotent Behavior

Calling `zone.unjoin()` on an already-standalone zone (not in a group) is safe — SoCo treats it as a no-op or returns gracefully. The tool handler does not need to pre-check group membership.

### Previous Story Intelligence

- Stories 3.1 and 3.2 established the service pattern (`ServiceName(room_service, adapter)`), tool pattern, and wiring pattern. Story 3.3 follows the same shape exactly.
- The `_make_zone` static method in `SoCoAdapter` is the correct factory for new methods — do not inline `soco.SoCo(ip)` directly.
- Tool handlers must guard with `assert_tool_permitted(tool_name, config)` at the start of each handler body.
- Story 3.2 debug log notes a regression from forgetting to add new tool names to `KNOWN_TOOL_NAMES` — ensure all 4 grouping tools are added.
- `FakeRoomService` in tests should use `rooms if rooms is not None else [ROOM]` (not `rooms or [ROOM]`) to correctly handle the empty list case (relevant for `party_mode` empty-room guard).

### Files to Create

```text
src/soniq_mcp/services/group_service.py
src/soniq_mcp/tools/groups.py
tests/unit/adapters/test_soco_adapter_groups.py
tests/unit/services/test_group_service.py
tests/unit/tools/test_groups.py
tests/contract/tool_schemas/test_groups_tool_schemas.py
```

### Files to Modify

```text
src/soniq_mcp/domain/exceptions.py          (add GroupError)
src/soniq_mcp/schemas/errors.py             (add from_group_error)
src/soniq_mcp/schemas/responses.py          (add GroupResponse, GroupTopologyResponse)
src/soniq_mcp/adapters/soco_adapter.py      (add join_group, unjoin_room, party_mode)
src/soniq_mcp/tools/__init__.py             (wire GroupService + register_groups)
src/soniq_mcp/config/models.py              (add 4 new tool names to KNOWN_TOOL_NAMES)
```

## Dev Agent Record

### Agent Model Used

gpt-5-codex

### Completion Notes

- Added `GroupError(SoniqDomainError)` to `domain/exceptions.py` and `ErrorResponse.from_group_error()` factory to `schemas/errors.py`.
- Added `GroupResponse` and `GroupTopologyResponse` Pydantic models to `schemas/responses.py`. `GroupTopologyResponse.from_rooms()` derives group structure from existing `Room.is_coordinator` and `Room.group_coordinator_uid` fields — no extra SoCo calls needed for the read path.
- Extended `SoCoAdapter` with three methods: `join_group` (calls `zone.join(coordinator_zone)`), `unjoin_room` (calls `zone.unjoin()`), `party_mode` (calls `zone.partymode()`). All wrap exceptions in `GroupError`. Lazy `soco` import preserved via `_make_zone`.
- Created `GroupService` following the `QueueService`/`FavouritesService` constructor pattern. `party_mode()` raises `GroupError` on empty room list.
- Created `tools/groups.py` with 4 tool handlers (`get_group_topology`, `join_group`, `unjoin_room`, `party_mode`). All follow `tools/playback.py` patterns exactly.
- Wired `GroupService` into `tools/__init__.py` at end of `register_all`.
- Added queue tool names to `KNOWN_TOOL_NAMES` (were missing) plus the 4 new grouping tools.
- 55 new tests added across 4 files. Full suite: 597 passed, 3 skipped (pre-existing), zero regressions.
- Follow-up review fix: corrected `join_group` room-not-found handling to use `RoomNotFoundError.room_name` instead of wrapping the exception string, which restores the expected user-facing error message.
- Added an explicit assertion for the `join_group` room-not-found error message so malformed nested messages are caught by tests.

### File List

- `src/soniq_mcp/domain/exceptions.py` (modified — added GroupError)
- `src/soniq_mcp/schemas/errors.py` (modified — added from_group_error)
- `src/soniq_mcp/schemas/responses.py` (modified — added GroupResponse, GroupTopologyResponse)
- `src/soniq_mcp/adapters/soco_adapter.py` (modified — added join_group, unjoin_room, party_mode)
- `src/soniq_mcp/services/group_service.py` (created)
- `src/soniq_mcp/tools/groups.py` (created)
- `src/soniq_mcp/tools/__init__.py` (modified — wired GroupService + register_groups)
- `src/soniq_mcp/config/models.py` (modified — added queue + 4 grouping tool names to KNOWN_TOOL_NAMES)
- `tests/unit/adapters/test_soco_adapter_groups.py` (created)
- `tests/unit/services/test_group_service.py` (created)
- `tests/unit/tools/test_groups.py` (created)
- `tests/contract/tool_schemas/test_groups_tool_schemas.py` (created)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-33-Control-Room-Grouping-and-Multi-Room-Playback`
- Architecture structure: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries`
- Naming and pattern rules: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`
- Previous story: `_bmad-output/implementation-artifacts/3-2-access-and-play-favourites-and-playlists.md`
- Pattern reference tool module: `src/soniq_mcp/tools/playback.py`
- Pattern reference service: `src/soniq_mcp/services/queue_service.py`
- Pattern reference adapter: `src/soniq_mcp/adapters/soco_adapter.py`
