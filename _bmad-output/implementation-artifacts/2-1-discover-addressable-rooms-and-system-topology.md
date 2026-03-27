# Story 2.1: Discover Addressable Rooms and System Topology

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to list available Sonos rooms and basic system information,
so that I can target the correct room for playback operations.

## Acceptance Criteria

1. Given the server has a valid Sonos configuration, when the user invokes the room discovery tool, then the server returns the available rooms it can control.
2. Given the available rooms are returned, when an AI client reads the response, then each room entry includes the identifiers needed for later room-targeted actions (name, uid).
3. Given the server has a valid Sonos configuration, when the user invokes the system info tool, then system-level room and speaker information is returned in a structured format.
4. Given a Sonos speaker is unreachable or the network produces no results, when discovery is invoked, then the tool returns a clear, structured response indicating the problem without crashing.

## Tasks / Subtasks

- [x] Add domain models for Room and SystemTopology (AC: 2, 3)
  - [x] Create `src/soniq_mcp/domain/models.py` with `Room` and `SystemTopology` dataclasses/Pydantic models
  - [x] `Room` must include: `name: str`, `uid: str`, `ip_address: str`, `is_coordinator: bool`, `group_coordinator_uid: str | None`
  - [x] `SystemTopology` must include: `rooms: list[Room]`, `coordinator_count: int`, `total_count: int`
  - [x] Add `RoomNotFoundError` exception to `src/soniq_mcp/domain/exceptions.py`
  - [x] Write unit tests in `tests/unit/domain/test_models.py`

- [x] Implement the SoCo discovery adapter (AC: 1, 4)
  - [x] Create `src/soniq_mcp/adapters/discovery_adapter.py` with `DiscoveryAdapter` class
  - [x] `DiscoveryAdapter.discover_rooms(timeout: float = 5.0) -> list[Room]` — calls `soco.discover()`, maps each `SoCo` instance to `Room`
  - [x] Handle empty discovery result (return `[]`, never raise)
  - [x] Handle `soco` exceptions gracefully — convert to `SoniqDomainError` subclass
  - [x] Add `SonosDiscoveryError` to `domain/exceptions.py` for connectivity/scan failures
  - [x] Add `ErrorResponse.from_discovery_error()` factory to `schemas/errors.py`
  - [x] Write unit tests in `tests/unit/adapters/test_discovery_adapter.py` using fake/mock SoCo (no real hardware required)

- [x] Implement the room service (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/services/room_service.py` with `RoomService` class
  - [x] `RoomService(adapter: DiscoveryAdapter)` — receives adapter via constructor (testable without SoCo)
  - [x] `RoomService.list_rooms(timeout: float = 5.0) -> list[Room]` — delegates to adapter
  - [x] `RoomService.get_topology(timeout: float = 5.0) -> SystemTopology` — builds topology from rooms
  - [x] `RoomService.get_room(name: str, timeout: float = 5.0) -> Room` — raises `RoomNotFoundError` if not found (needed by Stories 2.2–2.3)
  - [x] Write unit tests in `tests/unit/services/test_room_service.py` using injected fake adapter

- [x] Add response schemas for rooms and topology (AC: 2, 3)
  - [x] Create `src/soniq_mcp/schemas/responses.py` with `RoomResponse`, `RoomListResponse`, `SystemTopologyResponse`
  - [x] `RoomResponse`: `name`, `uid`, `ip_address`, `is_coordinator`
  - [x] `RoomListResponse`: `rooms: list[RoomResponse]`, `count: int`
  - [x] `SystemTopologyResponse`: `rooms: list[RoomResponse]`, `coordinator_count: int`, `total_count: int`
  - [x] All response models extend `pydantic.BaseModel` using `snake_case` fields
  - [x] Write unit tests in `tests/unit/schemas/test_responses.py`

- [x] Implement system tools (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/tools/system.py` with `register(app, config, room_service)` function
  - [x] Register `list_rooms` tool: calls `room_service.list_rooms()`, returns `RoomListResponse` as dict, catches `SonosDiscoveryError` and returns `ErrorResponse`
  - [x] Register `get_system_topology` tool: calls `room_service.get_topology()`, returns `SystemTopologyResponse` as dict, catches `SonosDiscoveryError` and returns `ErrorResponse`
  - [x] Both tools annotated with `ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)` — match existing pattern in `setup_support.py`
  - [x] Both tools call `assert_tool_permitted(tool_name, config)` at invocation time — match existing pattern
  - [x] Write unit tests in `tests/unit/tools/test_system.py` using fake `RoomService`

- [x] Wire system tools into the server (AC: 1)
  - [x] Update `src/soniq_mcp/tools/__init__.py`: import and call `register` from `tools/system.py`, constructing `DiscoveryAdapter` and `RoomService` inside `register_all()`
  - [x] Update `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py` to include `"list_rooms"` and `"get_system_topology"`
  - [x] Run `uv run pytest` and confirm all existing tests still pass (no regressions)

- [x] Add integration and contract tests (AC: 1, 2, 3, 4)
  - [x] Add `tests/integration/adapters/__init__.py` and `tests/integration/adapters/test_discovery_adapter_integration.py` — skips when no real Sonos hardware available, uses `SONIQ_HARDWARE_TESTS=1` env guard
  - [x] Add `tests/contract/tool_schemas/test_system_tool_schemas.py` — validates `list_rooms` and `get_system_topology` tool schemas are stable (name, parameters, description)

## Dev Notes

### Architecture Constraints (MUST Follow)

- **Layer order**: tools → services → adapters → SoCo. `tools/system.py` MUST NOT import from `soco` directly. `services/room_service.py` MUST NOT import from `soco` directly.
- **Adapter isolation**: `adapters/discovery_adapter.py` is the only file that imports `soco`.
- **Dependency injection**: `RoomService` takes `DiscoveryAdapter` in its constructor. `tools/system.py` takes `RoomService` as a parameter to `register()`. This makes everything testable without real hardware.
- **Error flow**: SoCo exceptions → `SoniqDomainError` (in adapter) → `ErrorResponse` (in tool handler). Never let `soco` exceptions leak past the adapter layer.
- **Response schemas**: Use `schemas/responses.py` Pydantic models, call `.model_dump()` before returning from tool handlers (MCP serialization expects dicts/primitives, not Pydantic objects).
- **Tool permissions**: Follow the exact pattern from `setup_support.py` — check `tools_disabled` before registering and call `assert_tool_permitted` at invocation time.

### SoCo Discovery API (Key Facts)

```python
import soco

# Discovery: returns set of SoCo objects, or empty set if none found
# Timeout default is 5 seconds. Can raise network exceptions.
zones = soco.discover(timeout=5)  # returns set[soco.SoCo] | None

# Each SoCo object provides:
zone.player_name    # str — human-readable room name (e.g. "Living Room")
zone.uid            # str — unique identifier (e.g. "RINCON_...")
zone.ip_address     # str — LAN IP address
zone.is_coordinator # bool — True if this zone is a group coordinator
zone.group          # soco.groups.ZoneGroup — contains group.coordinator.uid
```

- `soco.discover()` returns `set[SoCo] | None` — treat `None` as empty set.
- Discovery uses SSDP multicast on the local network. Works fine in plain local dev; may not work in Docker without `--network=host`.
- Never call `soco.discover()` from `services/` or `tools/` layers.

### New Files to Create

```
src/soniq_mcp/
├── domain/
│   ├── models.py          # NEW: Room, SystemTopology dataclasses
│   └── exceptions.py      # EXTEND: add RoomNotFoundError, SonosDiscoveryError
├── adapters/
│   └── discovery_adapter.py  # NEW: DiscoveryAdapter
├── services/
│   └── room_service.py    # NEW: RoomService
├── schemas/
│   └── responses.py       # NEW: RoomResponse, RoomListResponse, SystemTopologyResponse
└── tools/
    └── system.py          # NEW: register list_rooms, get_system_topology

tests/
├── unit/
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── test_discovery_adapter.py  # NEW
│   ├── domain/
│   │   └── test_models.py             # NEW
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── test_responses.py          # NEW
│   └── services/
│       ├── __init__.py
│       └── test_room_service.py       # NEW
│   └── tools/
│       ├── __init__.py
│       └── test_system.py             # NEW (existing __init__ may need creating)
├── integration/
│   └── adapters/
│       ├── __init__.py
│       └── test_discovery_adapter_integration.py  # NEW (skipped without hardware)
└── contract/
    └── tool_schemas/
        └── test_system_tool_schemas.py  # NEW
```

### Files to Modify

| File | Change |
|------|--------|
| `src/soniq_mcp/domain/exceptions.py` | Add `RoomNotFoundError`, `SonosDiscoveryError` |
| `src/soniq_mcp/schemas/errors.py` | Add `ErrorResponse.from_discovery_error()` factory |
| `src/soniq_mcp/tools/__init__.py` | Import and wire `system.register()` |
| `src/soniq_mcp/config/models.py` | Add `"list_rooms"`, `"get_system_topology"` to `KNOWN_TOOL_NAMES` |

### Test Patterns (From Previous Stories)

- All unit tests use `pytest` and follow the `tests/unit/` hierarchy.
- Integration tests go in `tests/integration/`, smoke tests in `tests/smoke/`.
- Fakes over mocks where possible. For hardware-free SoCo tests, create a fake `DiscoveryAdapter` that returns hard-coded `Room` objects. Do NOT use `unittest.mock.patch` on SoCo globally — use constructor injection instead.
- Hardware-dependent tests must be guarded with `SONIQ_HARDWARE_TESTS=1` environment variable and skipped automatically otherwise.
- Test discovery with empty result (`[]`) and error cases to validate graceful degradation (AC: 4).
- Run full suite with `uv run pytest` before marking any task complete (120 tests currently pass from Story 1.5).

### Tool Response Format (Reference)

Existing tools (`ping`, `server_info`) return plain Python values. New tools should return `.model_dump()` of a Pydantic response model. Example pattern:

```python
@app.tool(title="List Rooms", annotations=_READ_ONLY_TOOL_HINTS)
def list_rooms() -> dict:
    """List all available Sonos rooms."""
    assert_tool_permitted("list_rooms", config)
    try:
        rooms = room_service.list_rooms()
        return RoomListResponse(
            rooms=[RoomResponse(...) for r in rooms],
            count=len(rooms),
        ).model_dump()
    except SonosDiscoveryError as exc:
        return ErrorResponse.from_discovery_error(exc).model_dump()
```

### Configuration Note

`SoniqConfig` has `default_room: str | None` already — this will be used in Stories 2.2+ for room-targeted actions. Story 2.1 does NOT need to use it; just be aware it exists.

### KNOWN_TOOL_NAMES Must Stay in Sync

`config/models.py` has a `KNOWN_TOOL_NAMES` frozenset used by the `tools_disabled` validator. **Any new tool name MUST be added here or the validator will reject configs that try to disable it.** After this story, it should contain: `{"ping", "server_info", "list_rooms", "get_system_topology"}`.

### Previous Story Learnings (Story 1.5)

- `uv run pytest` is the correct test command. All 120 tests pass from Story 1.5.
- `python-dotenv` is a declared runtime dep. `.env` loading happens before env-var override.
- `make run-stdio` starts the stdio server. Use `uv run python -m soniq_mcp` directly in tests.
- `register_all(app, config)` in `tools/__init__.py` is the single wiring point. Add new calls there.
- The `ToolAnnotations` import is `from mcp.types import ToolAnnotations` — confirmed working in `setup_support.py`.

### References

- Story source: `_bmad-output/planning-artifacts/epics.md#story-21-discover-addressable-rooms-and-system-topology`
- FRs covered: FR1 (list rooms), FR2 (room targeting identifiers), FR29 (system-level info)
- Architecture layer diagram: `_bmad-output/planning-artifacts/architecture.md#component-boundaries`
- SoCo library: installed as `soco>=0.30.14` in `pyproject.toml`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (container-use environment: knowing-fish)

### Debug Log References

- Discovered `Tool.parameters` is the correct attribute (not `inputSchema`) in `mcp>=1.26.0` — fixed contract tests.
- `KNOWN_TOOL_NAMES` must be updated before tool `tools_disabled` tests can pass — updated in Task 6.
- 120 baseline tests → 176 passing after implementation (56 new tests, 3 hardware tests skipped).

### Completion Notes List

- `src/soniq_mcp/domain/models.py`: `Room` (frozen dataclass with name, uid, ip_address, is_coordinator, group_coordinator_uid) and `SystemTopology` (frozen dataclass with rooms tuple, coordinator_count, total_count; `from_rooms()` factory).
- `src/soniq_mcp/domain/exceptions.py`: Added `RoomNotFoundError` and `SonosDiscoveryError`.
- `src/soniq_mcp/adapters/discovery_adapter.py`: `DiscoveryAdapter.discover_rooms()` wraps `soco.discover()`, maps zones to `Room` objects, converts all SoCo exceptions to `SonosDiscoveryError`. Only file importing `soco`.
- `src/soniq_mcp/services/room_service.py`: `RoomService` with `list_rooms()` (sorted by name, case-insensitive), `get_topology()`, and `get_room()` (case-insensitive lookup, raises `RoomNotFoundError`).
- `src/soniq_mcp/schemas/responses.py`: `RoomResponse`, `RoomListResponse`, `SystemTopologyResponse` — all Pydantic `BaseModel` with `from_domain()` factories and `model_dump()` for MCP serialization.
- `src/soniq_mcp/schemas/errors.py`: Added `from_discovery_error()` and `from_room_not_found()` factory methods.
- `src/soniq_mcp/tools/system.py`: Thin handlers for `list_rooms` and `get_system_topology`. Permission-checked, `READ_ONLY` annotated, delegates to `RoomService`, catches `SonosDiscoveryError` and returns structured `ErrorResponse`.
- `src/soniq_mcp/tools/__init__.py`: Wired `DiscoveryAdapter` → `RoomService` → `system.register()` inside `register_all()`.
- `src/soniq_mcp/config/models.py`: `KNOWN_TOOL_NAMES` updated to include `"list_rooms"` and `"get_system_topology"`.
- Tests: 56 new tests across unit/adapters, unit/domain, unit/services, unit/schemas, unit/tools, integration/adapters, contract/tool_schemas.

### File List

- `src/soniq_mcp/domain/models.py`
- `src/soniq_mcp/domain/exceptions.py`
- `src/soniq_mcp/adapters/discovery_adapter.py`
- `src/soniq_mcp/services/room_service.py`
- `src/soniq_mcp/schemas/responses.py`
- `src/soniq_mcp/schemas/errors.py`
- `src/soniq_mcp/tools/system.py`
- `src/soniq_mcp/tools/__init__.py`
- `src/soniq_mcp/config/models.py`
- `tests/unit/domain/test_models.py`
- `tests/unit/adapters/__init__.py`
- `tests/unit/adapters/test_discovery_adapter.py`
- `tests/unit/services/__init__.py`
- `tests/unit/services/test_room_service.py`
- `tests/unit/schemas/__init__.py`
- `tests/unit/schemas/test_responses.py`
- `tests/unit/tools/__init__.py`
- `tests/unit/tools/test_system.py`
- `tests/integration/adapters/__init__.py`
- `tests/integration/adapters/test_discovery_adapter_integration.py`
- `tests/contract/tool_schemas/__init__.py`
- `tests/contract/tool_schemas/test_system_tool_schemas.py`

## Change Log

- 2026-03-25: Story 2.1 implemented. Room discovery adapter, service, tools, schemas, and tests. 176 passing, 3 hardware tests skipped. Status → review.
