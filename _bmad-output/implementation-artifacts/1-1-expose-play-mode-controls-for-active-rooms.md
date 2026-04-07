# Story 1.1: Expose play mode controls for active rooms

Status: done

## Story

As a Sonos user,
I want to view and change shuffle, repeat, and crossfade for a target room,
so that I can control playback behavior without leaving my AI workflow.

## Acceptance Criteria

1. **GET play mode:** Given a reachable target room with an active coordinator, when the client requests current play mode state, the service returns normalized `shuffle` (bool), `repeat` ("none"|"all"|"one"), and `cross_fade` (bool) values for that room using stable `snake_case` fields.

2. **SET play mode:** Given a reachable target room with an active coordinator, when the client requests a shuffle, repeat, or crossfade change, the service applies the requested mode through the phase-2 playback boundary and returns the target room and resulting mode state.

3. **Capability/coordinator guard:** Given a room that cannot perform the requested mode change (coordinator unavailable, constraint violation), the service returns a typed validation or capability error and does NOT return a raw SoCo error object.

## Tasks / Subtasks

- [x] Add `PlayModeState` domain model (AC: 1, 2)
  - [x] Add frozen dataclass to `src/soniq_mcp/domain/models.py`: fields `room_name: str`, `shuffle: bool`, `repeat: str` (literal "none"|"all"|"one"), `cross_fade: bool`

- [x] Add `PlayModeResponse` schema (AC: 1, 2)
  - [x] Add Pydantic model to `src/soniq_mcp/schemas/responses.py` with `from_domain(state: PlayModeState)` factory

- [x] Extend `SoCoAdapter` with play mode methods (AC: 1, 2, 3)
  - [x] Add `get_play_mode(ip_address: str, room_name: str) -> PlayModeState` — reads `zone.play_mode` and `zone.cross_fade`, normalizes via `_SOCO_TO_DOMAIN` map; wraps all exceptions as `PlaybackError`
  - [x] Add `set_play_mode(ip_address: str, room_name: str, shuffle, repeat, cross_fade) -> PlayModeState` — reads current mode, applies only provided fields, writes computed `zone.play_mode` string and/or `zone.cross_fade`; wraps all exceptions as `PlaybackError`
  - [x] `play_mode` → `PlayModeState` normalization: all 6 SoCo strings mapped via `_SOCO_TO_DOMAIN` / `_DOMAIN_TO_SOCO` dicts
  - [x] Reverse mapping for set: combine current + new values → SoCo play_mode string

- [x] Create `PlayModeService` (AC: 1, 2, 3)
  - [x] New file `src/soniq_mcp/services/play_mode_service.py`
  - [x] `__init__(self, room_service, adapter, config)` — same signature pattern as other services
  - [x] `get_play_mode(room_name: str) -> PlayModeState` — resolves coordinator, delegates to adapter
  - [x] `set_play_mode(room_name: str, shuffle, repeat, cross_fade) -> PlayModeState` — resolves coordinator, validates repeat ("none"|"all"|"one"), delegates to adapter

- [x] Create `tools/play_modes.py` (AC: 1, 2, 3)
  - [x] New file `src/soniq_mcp/tools/play_modes.py`
  - [x] `register(app, config, play_mode_service)` function following existing pattern
  - [x] `get_play_mode` tool: `readOnlyHint=True`, param `room: str`
  - [x] `set_play_mode` tool: `readOnlyHint=False`, optional `shuffle`, `repeat`, `cross_fade` params
  - [x] Error handling: `RoomNotFoundError`, `PlaybackError`, `SonosDiscoveryError` → `ErrorResponse` factories

- [x] Wire registration in `tools/__init__.py` (AC: 1, 2)
  - [x] Import and instantiate `PlayModeService` in `register_all`
  - [x] Call `register_play_modes(app, config, play_mode_service)`

- [x] Unit tests: adapter (AC: 3)
  - [x] `tests/unit/adapters/test_soco_adapter_play_modes.py` — 15 tests covering all 6 SoCo mode strings, cross_fade, shuffle/repeat/combined changes, error wrapping

- [x] Unit tests: service (AC: 1, 2, 3)
  - [x] `tests/unit/services/test_play_mode_service.py` — 10 tests covering coordinator routing, fallback, invalid repeat validation, room not found

- [x] Unit tests: tools (AC: 1, 2, 3)
  - [x] `tests/unit/tools/test_play_modes.py` — 13 tests covering happy paths, all 3 error types, tools_disabled

- [x] Contract tests (AC: 2)
  - [x] `tests/contract/tool_schemas/test_play_mode_tool_schemas.py` — 13 tests validating tool names, params, annotations, response field stability

## Dev Notes

### SoCo play_mode mapping (critical)

SoCo `zone.play_mode` returns one of 6 strings. Map to/from domain fields:

| SoCo play_mode         | shuffle | repeat  |
|------------------------|---------|---------|
| "NORMAL"               | False   | "none"  |
| "REPEAT_ALL"           | False   | "all"   |
| "REPEAT_ONE"           | False   | "one"   |
| "SHUFFLE_NOREPEAT"     | True    | "none"  |
| "SHUFFLE"              | True    | "all"   |
| "SHUFFLE_REPEAT_ONE"   | True    | "one"   |

Reverse map for set: `(shuffle: bool, repeat: str) → play_mode string`. Read current state first, apply only the provided fields, then write the computed string.

`zone.cross_fade` is an independent property — get/set separately from `play_mode`.

### Coordinator routing (critical)

Play mode is a coordinator-level property in Sonos. When a room is grouped, read/write play mode against the **coordinator's IP**, not the room's IP. Reuse the same coordinator resolution pattern from `SonosService._resolve_track_info_room`:

```python
def _resolve_coordinator(self, room_name: str):
    room = self._room_service.get_room(room_name)
    if not room.group_coordinator_uid:
        return room
    for candidate in self._room_service.list_rooms():
        if candidate.uid == room.group_coordinator_uid:
            return candidate
    return room  # fallback
```

### New exception type NOT needed

Do not create a new exception class for play modes. Reuse `PlaybackError` — it maps to `ErrorResponse.from_playback_error()` which already has a correct suggestion message. Adding a new exception type is unnecessary complexity.

### repeat parameter validation

The `set_play_mode` service method must validate `repeat` against `{"none", "all", "one"}` before constructing the SoCo play_mode string. Raise `PlaybackError` with a clear message listing allowed values if invalid. Do NOT let an invalid string reach `zone.play_mode`.

### File locations

| Layer | File |
|-------|------|
| Domain model | `src/soniq_mcp/domain/models.py` (append `PlayModeState`) |
| Response schema | `src/soniq_mcp/schemas/responses.py` (append `PlayModeResponse`) |
| Adapter methods | `src/soniq_mcp/adapters/soco_adapter.py` (append `get_play_mode`, `set_play_mode`) |
| Service | `src/soniq_mcp/services/play_mode_service.py` (new file) |
| Tools | `src/soniq_mcp/tools/play_modes.py` (new file) |
| Wire-up | `src/soniq_mcp/tools/__init__.py` (extend `register_all`) |
| Unit: adapter | `tests/unit/adapters/test_soco_adapter_play_modes.py` (new file) |
| Unit: service | `tests/unit/services/test_play_mode_service.py` (new file) |
| Unit: tools | `tests/unit/tools/test_play_modes.py` (new file) |
| Contract | `tests/contract/tool_schemas/test_play_mode_tool_schemas.py` (new file) |

### Tool annotations

Follow existing pattern from `tools/playback.py`:
- `get_play_mode`: `_READ_ONLY_TOOL_HINTS` (readOnlyHint=True, destructiveHint=False, idempotentHint=True)
- `set_play_mode`: `_CONTROL_TOOL_HINTS` (readOnlyHint=False, destructiveHint=False, idempotentHint=False)

### tools_disabled check pattern

Each tool must check `if "get_play_mode" not in config.tools_disabled:` before registering, and call `assert_tool_permitted("get_play_mode", config)` inside the handler. Follow the exact pattern in `tools/playback.py`.

### Test patterns

**Adapter tests** — use `unittest.mock.MagicMock` for the SoCo zone and `unittest.mock.patch` context manager (see `tests/unit/adapters/test_soco_adapter.py`):

```python
from unittest.mock import MagicMock, patch

def make_fake_zone(play_mode="NORMAL", cross_fade=False): ...

def _patch_soco(zone):
    return patch("soco.SoCo", return_value=zone)
```

**Service tests** — inject fake room_service and fake adapter, verify coordinator routing behavior.

**Tool tests** — define `FakePlayModeService` with `calls` list, `make_app()` helper, then use `app._tool_manager` to invoke tools (see `test_playback.py`).

**Contract tests** — use `_StubPlayModeService`, register tools, call `get_tools(app)` dict, assert names, parameters, and annotations.

### Architecture compliance

- `SoCoAdapter` is the ONLY place that imports `soco` — play mode adapter methods follow `_call_playback` exception-wrapping pattern
- `PlayModeService` does NOT import `soco` — delegates all Sonos calls to adapter
- Tools layer does NOT import `soco` or call adapter directly
- All response fields use `snake_case`
- No raw SoCo objects or stack traces in error responses — use `_sanitize_text` via `ErrorResponse` factories

### Project Structure Notes

- All new source files go under `src/soniq_mcp/` — do NOT create files outside this tree
- Test files mirror source paths under `tests/`
- Do not add play mode methods to `SonosService` — create a dedicated `PlayModeService` per the phase-2 architecture guidance ("Add or refine capability-specific modules for `playback`, `audio`, `inputs`, `alarms`, `playlists`, `library`, and `groups`")
- `PlayModeState` and `PlayModeResponse` follow the exact frozen dataclass + Pydantic model pattern already used for `PlaybackState`/`PlaybackStateResponse` and `VolumeState`/`VolumeStateResponse`

### References

- Existing playback tool pattern: [Source: src/soniq_mcp/tools/playback.py]
- Service orchestration pattern: [Source: src/soniq_mcp/services/sonos_service.py]
- Coordinator resolution: [Source: src/soniq_mcp/services/sonos_service.py#_resolve_track_info_room]
- Adapter pattern: [Source: src/soniq_mcp/adapters/soco_adapter.py]
- Domain models: [Source: src/soniq_mcp/domain/models.py]
- Response schemas: [Source: src/soniq_mcp/schemas/responses.py]
- Error schemas: [Source: src/soniq_mcp/schemas/errors.py]
- Domain exceptions: [Source: src/soniq_mcp/domain/exceptions.py]
- Tool registration wire-up: [Source: src/soniq_mcp/tools/__init__.py]
- Adapter unit test pattern: [Source: tests/unit/adapters/test_soco_adapter.py]
- Tool unit test pattern: [Source: tests/unit/tools/test_playback.py]
- Contract test pattern: [Source: tests/contract/tool_schemas/test_playback_tool_schemas.py]
- Phase-2 architecture direction: [Source: _bmad-output/planning-artifacts/architecture.md#Additional Requirements]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- container-use environment `included-grouse` — Dagger session expired after contract tests; work recovered via git merge from `container-use/included-grouse` remote ref

### Completion Notes List

- Implemented `PlayModeState` frozen dataclass in `domain/models.py` with `room_name`, `shuffle`, `repeat`, `cross_fade` fields
- Added `PlayModeResponse` Pydantic model in `schemas/responses.py` with `from_domain()` factory
- Extended `SoCoAdapter` with `get_play_mode` and `set_play_mode`; all 6 SoCo play_mode strings normalized via bidirectional lookup dicts; SoCo exceptions wrapped as `PlaybackError`
- Created `PlayModeService` with `_resolve_coordinator()` for group-aware routing; validates repeat values before adapter call
- Created `tools/play_modes.py` with `get_play_mode` (read-only) and `set_play_mode` (control) tools respecting `tools_disabled`
- Wired `PlayModeService` in `tools/__init__.py` `register_all()`
- Added `get_play_mode` and `set_play_mode` to `KNOWN_TOOL_NAMES` in `config/models.py`
- Updated `tests/integration/transports/test_http_bootstrap.py` tool parity test from 29 → 31 tools
- 51 new tests across adapter (15), service (10), tool (13), contract (13) layers; 750 total pass, 0 regressions

### File List

- `src/soniq_mcp/domain/models.py` — added `PlayModeState`
- `src/soniq_mcp/schemas/responses.py` — added `PlayModeResponse`
- `src/soniq_mcp/adapters/soco_adapter.py` — added `get_play_mode`, `set_play_mode`, `_SOCO_TO_DOMAIN`, `_DOMAIN_TO_SOCO`
- `src/soniq_mcp/services/play_mode_service.py` — new file
- `src/soniq_mcp/tools/play_modes.py` — new file
- `src/soniq_mcp/tools/__init__.py` — wired `PlayModeService` and `register_play_modes`
- `src/soniq_mcp/config/models.py` — added `get_play_mode`, `set_play_mode` to `KNOWN_TOOL_NAMES`
- `tests/unit/adapters/test_soco_adapter_play_modes.py` — new file (15 tests)
- `tests/unit/services/test_play_mode_service.py` — new file (10 tests)
- `tests/unit/tools/test_play_modes.py` — new file (13 tests)
- `tests/contract/tool_schemas/test_play_mode_tool_schemas.py` — new file (13 tests)
- `tests/integration/transports/test_http_bootstrap.py` — updated tool count 29 → 31

### Review Findings

- [x] [Review][Patch] Spurious `zone.play_mode` write when only `cross_fade` changed — adapter writes `zone.play_mode` unconditionally even when shuffle/repeat are unchanged; only `cross_fade` should write in that case [`src/soniq_mcp/adapters/soco_adapter.py`]
- [x] [Review][Patch] Unknown SoCo play_mode strings silently fall back to `("none", False)` with no log warning — unrecognized mode strings cause invisible data loss [`src/soniq_mcp/adapters/soco_adapter.py`]
- [x] [Review][Patch] `repeat` field typed as bare `str` instead of `Literal["none", "all", "one"]` — no type-checker or schema enforcement on this constraint [`src/soniq_mcp/domain/models.py`, `src/soniq_mcp/schemas/responses.py`]
- [x] [Review][Patch] No test asserts that `zone.play_mode` is not written when `set_play_mode` is called with all-`None` arguments [`tests/unit/adapters/test_soco_adapter_play_modes.py`]
- [x] [Review][Defer] Untyped `object` parameters in `PlayModeService.__init__` — deferred, pre-existing pattern across all services
- [x] [Review][Defer] `_resolve_coordinator` calls `list_rooms()` on every invocation — deferred, pre-existing pattern in `SonosService`
- [x] [Review][Defer] `PlayModeResponse` duplicates `PlayModeState` field-for-field without constraints — deferred, pre-existing pattern across all response schemas
- [x] [Review][Defer] Partial-write atomicity: `zone.play_mode` write then `zone.cross_fade` write are not atomic — deferred, no rollback mechanism available in SoCo
- [x] [Review][Defer] Contract tests access `app._tool_manager` private API — deferred, pre-existing pattern in all contract tests
- [x] [Review][Defer] Unexpected exception types in tool handlers not caught by broad handler — deferred, pre-existing 3-exception pattern from `playback.py` template
