# Story 2.2: Control Core Playback in a Target Room

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to play, pause, stop, skip, and inspect playback state in a room,
so that I can use AI for basic day-to-day Sonos control.

## Acceptance Criteria

1. Given a valid target room, when the user invokes playback controls, then the server supports play, pause, stop, next, and previous actions.
2. Given a valid target room, when the user invokes a state query, then the server can return the current playback state (PLAYING, PAUSED_PLAYBACK, STOPPED, TRANSITIONING).
3. Given a valid target room, when the user invokes a track info query, then current track information is available in a structured response (title, artist, album, duration, position).
4. Given an invalid room name, when any playback or query tool is invoked, then a consistent, user-correctable error is returned.

## Tasks / Subtasks

- [x] Extend domain models with PlaybackState and TrackInfo (AC: 2, 3)
  - [x] Add `PlaybackState` frozen dataclass to `src/soniq_mcp/domain/models.py`: fields `transport_state: str`, `room_name: str`
  - [x] Add `TrackInfo` frozen dataclass to `src/soniq_mcp/domain/models.py`: fields `title: str | None`, `artist: str | None`, `album: str | None`, `duration: str | None`, `position: str | None`, `uri: str | None`, `album_art_uri: str | None`, `queue_position: int | None`
  - [x] Add `PlaybackError` exception to `src/soniq_mcp/domain/exceptions.py` (subclass of `SoniqDomainError`)
  - [x] Extend unit tests in `tests/unit/domain/test_models.py` with PlaybackState and TrackInfo

- [x] Implement the playback adapter (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/adapters/playback_adapter.py` with `PlaybackAdapter` class
  - [x] `PlaybackAdapter.play(ip_address: str) -> None` — creates `soco.SoCo(ip_address)`, calls `.play()`
  - [x] `PlaybackAdapter.pause(ip_address: str) -> None` — calls `.pause()`
  - [x] `PlaybackAdapter.stop(ip_address: str) -> None` — calls `.stop()`
  - [x] `PlaybackAdapter.next_track(ip_address: str) -> None` — calls `.next()`
  - [x] `PlaybackAdapter.previous_track(ip_address: str) -> None` — calls `.previous()`
  - [x] `PlaybackAdapter.get_playback_state(ip_address: str, room_name: str) -> PlaybackState` — calls `.get_current_transport_info()`, maps to `PlaybackState`
  - [x] `PlaybackAdapter.get_track_info(ip_address: str) -> TrackInfo` — calls `.get_current_track_info()`, maps to `TrackInfo`
  - [x] All SoCo exceptions caught and re-raised as `PlaybackError` with a user-readable message
  - [x] Write unit tests in `tests/unit/adapters/test_playback_adapter.py` using a fake/mock SoCo zone (no real hardware)

- [x] Implement the playback service (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/services/playback_service.py` with `PlaybackService` class
  - [x] `PlaybackService(room_service: RoomService, adapter: PlaybackAdapter)` — both injected via constructor
  - [x] `PlaybackService.play(room_name: str) -> None` — calls `room_service.get_room(room_name)` then `adapter.play(room.ip_address)`
  - [x] `PlaybackService.pause(room_name: str) -> None`
  - [x] `PlaybackService.stop(room_name: str) -> None`
  - [x] `PlaybackService.next_track(room_name: str) -> None`
  - [x] `PlaybackService.previous_track(room_name: str) -> None`
  - [x] `PlaybackService.get_playback_state(room_name: str) -> PlaybackState`
  - [x] `PlaybackService.get_track_info(room_name: str) -> TrackInfo`
  - [x] `RoomNotFoundError` from `get_room()` propagates up naturally — no re-wrapping
  - [x] `SonosDiscoveryError` from `get_room()` propagates up naturally
  - [x] Write unit tests in `tests/unit/services/test_playback_service.py` using fake `RoomService` and fake `PlaybackAdapter`

- [x] Add response schemas for playback (AC: 2, 3)
  - [x] Add `PlaybackStateResponse` to `src/soniq_mcp/schemas/responses.py`: fields `transport_state: str`, `room_name: str`
  - [x] Add `TrackInfoResponse` to `src/soniq_mcp/schemas/responses.py`: all `TrackInfo` fields plus `room_name: str`
  - [x] Both models extend `pydantic.BaseModel` using `snake_case` fields with `from_domain()` factory classmethod
  - [x] Extend unit tests in `tests/unit/schemas/test_responses.py` with PlaybackStateResponse and TrackInfoResponse

- [x] Implement playback tools (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/tools/playback.py` with `register(app, config, playback_service)` function
  - [x] Register `play(room: str)`: calls `playback_service.play(room)`, returns `{"status": "ok", "room": room}` on success
  - [x] Register `pause(room: str)`: calls `playback_service.pause(room)`, returns `{"status": "ok", "room": room}`
  - [x] Register `stop(room: str)`: calls `playback_service.stop(room)`, returns `{"status": "ok", "room": room}`
  - [x] Register `next_track(room: str)`: calls `playback_service.next_track(room)`, returns `{"status": "ok", "room": room}`
  - [x] Register `previous_track(room: str)`: calls `playback_service.previous_track(room)`, returns `{"status": "ok", "room": room}`
  - [x] Register `get_playback_state(room: str)`: returns `PlaybackStateResponse.from_domain(state).model_dump()`
  - [x] Register `get_track_info(room: str)`: returns `TrackInfoResponse.from_domain(info, room).model_dump()`
  - [x] Control tools (`play`, `pause`, `stop`, `next_track`, `previous_track`) use `_CONTROL_TOOL_HINTS`
  - [x] Query tools (`get_playback_state`, `get_track_info`) use `_READ_ONLY_TOOL_HINTS`
  - [x] All tools call `assert_tool_permitted(tool_name, config)` at invocation time
  - [x] All tools catch `RoomNotFoundError` → `ErrorResponse.from_room_not_found(room)`
  - [x] All tools catch `PlaybackError` → `ErrorResponse.from_playback_error(exc)`
  - [x] All tools catch `SonosDiscoveryError` → `ErrorResponse.from_discovery_error(exc)`
  - [x] Write unit tests in `tests/unit/tools/test_playback.py` using fake `PlaybackService`

- [x] Add `from_playback_error()` factory to ErrorResponse (AC: 4)
  - [x] Add `ErrorResponse.from_playback_error(exc: Exception) -> ErrorResponse` classmethod to `src/soniq_mcp/schemas/errors.py`

- [x] Wire playback tools into the server (AC: 1)
  - [x] Update `src/soniq_mcp/tools/__init__.py`: import and call `register` from `tools/playback.py`, constructing `PlaybackAdapter` and `PlaybackService` inside `register_all()`
  - [x] Update `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py` to add the 7 new tool names: `"play"`, `"pause"`, `"stop"`, `"next_track"`, `"previous_track"`, `"get_playback_state"`, `"get_track_info"`
  - [x] Run `make test` and confirm all existing tests still pass

- [x] Add contract tests (AC: 1, 2, 3)
  - [x] Add `tests/contract/tool_schemas/test_playback_tool_schemas.py` — validates all 7 playback tool names, descriptions, and parameter schemas are stable

## Dev Notes

### Architecture Constraints (MUST Follow)

- **Layer order enforced**: `tools/playback.py` → `services/playback_service.py` → `adapters/playback_adapter.py` → SoCo. No layer may skip to a lower layer.
- **SoCo isolation**: `adapters/playback_adapter.py` is the ONLY new file that imports `soco`. `adapters/discovery_adapter.py` remains the ONLY file for discovery. Do NOT add SoCo imports anywhere else.
- **SoCo zone connection by IP**: For playback, use `soco.SoCo(ip_address)` directly — do NOT call `soco.discover()` again per action (too slow). Room IP comes from `RoomService.get_room()` which itself uses `DiscoveryAdapter`. This is the correct pattern.
- **Dependency injection**: `PlaybackService(room_service, adapter)`. `register(app, config, playback_service)`. Makes everything testable without hardware.
- **Error flow**: SoCo exceptions → `PlaybackError` (in adapter) → `ErrorResponse` (in tool). `RoomNotFoundError` from `RoomService` propagates through service to tool where it's caught.
- **response schemas**: `PlaybackStateResponse` and `TrackInfoResponse` MUST use `.model_dump()` before returning from tool handlers.
- **File location**: New adapter → `adapters/playback_adapter.py` (NOT `soco_adapter.py` yet — that generic name is reserved for future consolidation). New service → `services/playback_service.py`.
- **`KNOWN_TOOL_NAMES` must be updated**: Add all 7 new names BEFORE running tests, or `tools_disabled` validator will reject test configs.

### SoCo Playback API (Key Facts)

```python
import soco

# Connect to a zone by IP (do NOT re-discover on each request)
zone = soco.SoCo("192.168.1.10")

# Playback controls — all raise soco.exceptions.SoCoUPnPException on failure
zone.play()       # start/resume playback
zone.pause()      # pause playback
zone.stop()       # stop playback
zone.next()       # skip to next track (raises if no next track)
zone.previous()   # previous track (raises if at first)

# Transport state
info = zone.get_current_transport_info()
# Returns dict:
# {
#   "current_transport_state": str,   # "PLAYING" | "PAUSED_PLAYBACK" | "STOPPED" | "TRANSITIONING"
#   "current_transport_status": str,  # "OK"
#   "current_speed": str              # "1"
# }

# Track info
track = zone.get_current_track_info()
# Returns dict:
# {
#   "title": str,             # track title (empty string if none)
#   "artist": str,            # artist name (empty string if none)
#   "album": str,             # album name (empty string if none)
#   "album_art": str,         # URL to album art (empty string if none)
#   "position": str,          # current position "0:01:23" (empty string if none)
#   "duration": str,          # track duration "0:03:45" ("NOT_IMPLEMENTED" if streaming)
#   "playlist_position": int, # 1-based queue position (0 if not in queue)
#   "uri": str,               # stream URI
#   "metadata": str           # DIDL-Lite XML metadata
# }
```

**Notes on SoCo exceptions**: `soco.exceptions.SoCoUPnPException` is the main error. It has a `error_code` attribute. Catch `Exception` broadly and wrap in `PlaybackError` to avoid leaking internal SoCo types.

**Empty vs None**: SoCo track info fields return empty strings `""` instead of `None` when unavailable. Normalize: treat `""` as `None` in `TrackInfo` domain model. Specifically, `duration` may return `"NOT_IMPLEMENTED"` for radio streams — treat as `None`.

### ToolAnnotations Pattern

Two sets of annotations needed in `tools/playback.py`:

```python
from mcp.types import ToolAnnotations

_READ_ONLY_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

_CONTROL_TOOL_HINTS = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,    # playback controls aren't data-destructive
    idempotentHint=False,     # calling play() twice changes state
    openWorldHint=False,
)
```

Use `_CONTROL_TOOL_HINTS` for: `play`, `pause`, `stop`, `next_track`, `previous_track`.
Use `_READ_ONLY_TOOL_HINTS` for: `get_playback_state`, `get_track_info`.

### Tool Registration Pattern

Follow the EXACT pattern from `tools/system.py` and `tools/setup_support.py`:

```python
def register(app: FastMCP, config: SoniqConfig, playback_service: object) -> None:
    if "play" not in config.tools_disabled:
        @app.tool(title="Play", annotations=_CONTROL_TOOL_HINTS)
        def play(room: str) -> dict:
            """Start or resume playback in a target Sonos room."""
            assert_tool_permitted("play", config)
            try:
                playback_service.play(room)
                return {"status": "ok", "room": room}
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except PlaybackError as exc:
                return ErrorResponse.from_playback_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                return ErrorResponse.from_discovery_error(exc).model_dump()
```

All 7 tools follow this pattern. Define them inside the `register()` function, gated by `if "tool_name" not in config.tools_disabled`.

### Wiring in tools/__init__.py

```python
from soniq_mcp.adapters.playback_adapter import PlaybackAdapter
from soniq_mcp.services.playback_service import PlaybackService
from soniq_mcp.tools.playback import register as register_playback

# Inside register_all():
playback_adapter = PlaybackAdapter()
playback_service = PlaybackService(room_service, playback_adapter)
register_playback(app, config, playback_service)
```

`room_service` already exists in `register_all()` from Story 2.1. Reuse it — do NOT create a second `RoomService` instance.

### New Files to Create

```
src/soniq_mcp/
├── adapters/
│   └── playback_adapter.py   # NEW: SoCo playback operations
├── services/
│   └── playback_service.py   # NEW: Playback business logic
└── tools/
    └── playback.py            # NEW: register play, pause, stop, next_track, previous_track, get_playback_state, get_track_info

tests/
├── unit/
│   ├── adapters/
│   │   └── test_playback_adapter.py  # NEW
│   ├── services/
│   │   └── test_playback_service.py  # NEW
│   └── tools/
│       └── test_playback.py          # NEW
└── contract/
    └── tool_schemas/
        └── test_playback_tool_schemas.py  # NEW
```

### Files to Modify

| File | Change |
|------|--------|
| `src/soniq_mcp/domain/models.py` | Add `PlaybackState`, `TrackInfo` frozen dataclasses |
| `src/soniq_mcp/domain/exceptions.py` | Add `PlaybackError` |
| `src/soniq_mcp/schemas/responses.py` | Add `PlaybackStateResponse`, `TrackInfoResponse` |
| `src/soniq_mcp/schemas/errors.py` | Add `from_playback_error()` factory |
| `src/soniq_mcp/tools/__init__.py` | Wire `PlaybackAdapter`, `PlaybackService`, `register_playback` |
| `src/soniq_mcp/config/models.py` | Add 7 tool names to `KNOWN_TOOL_NAMES` |
| `tests/unit/domain/test_models.py` | Extend with PlaybackState, TrackInfo tests |
| `tests/unit/schemas/test_responses.py` | Extend with PlaybackStateResponse, TrackInfoResponse tests |

### Test Patterns (Match Story 2.1)

- Use fake classes (`FakePlaybackAdapter`, `FakePlaybackService`) — no `unittest.mock.patch`
- `FakePlaybackAdapter` has `raise_error: bool` param to trigger `PlaybackError` in tests
- `FakePlaybackService` has per-method control (e.g., `raise_on_room: str | None` to trigger `RoomNotFoundError`)
- For `test_playback.py`, follow `test_system.py` exactly: `make_app_with_service()`, `get_tool()` helper, `@pytest.mark.anyio` for async call tests
- Test all 7 tools: registration, disabled-check, success path, `RoomNotFoundError` path, `PlaybackError` path
- Run `make test` and confirm total passing count increases (baseline: 186 tests, expect ~40-50 new tests)

**Contract test pattern** (match `test_system_tool_schemas.py`):
```python
# tests/contract/tool_schemas/test_playback_tool_schemas.py
def test_play_tool_schema():
    app = FastMCP("test")
    config = SoniqConfig()
    register(app, config, FakePlaybackService())
    tools = {t.name: t for t in app._tool_manager.list_tools()}
    tool = tools["play"]
    assert tool.description  # non-empty
    assert "room" in tool.parameters["properties"]
    assert tool.parameters["required"] == ["room"]
```

### TrackInfo Field Normalization

In `PlaybackAdapter.get_track_info()`, normalize SoCo's empty-string fields to `None`:

```python
def _coerce_str(val: object) -> str | None:
    if not isinstance(val, str) or not val.strip() or val == "NOT_IMPLEMENTED":
        return None
    return val

info = zone.get_current_track_info()
return TrackInfo(
    title=_coerce_str(info.get("title")),
    artist=_coerce_str(info.get("artist")),
    album=_coerce_str(info.get("album")),
    duration=_coerce_str(info.get("duration")),
    position=_coerce_str(info.get("position")),
    uri=_coerce_str(info.get("uri")),
    album_art_uri=_coerce_str(info.get("album_art")),
    queue_position=info.get("playlist_position") or None,  # 0 → None
)
```

### Previous Story Learnings (Story 2.1)

- `make test` is the correct test command (wraps `uv run pytest`).
- All tool handlers return `.model_dump()` of a Pydantic response, NOT raw Python objects.
- Tool tests use `await app.call_tool("name", {})` and parse `result[0].text` as JSON.
- `KNOWN_TOOL_NAMES` validator rejects unknown tool names in `tools_disabled` — update it BEFORE writing tests that set `tools_disabled`.
- `DiscoveryAdapter` and `RoomService` are constructed inside `register_all()` — reuse the same `room_service` instance for `PlaybackService` rather than creating a new one.
- `from mcp.types import ToolAnnotations` — confirmed working import.
- `from mcp.server.fastmcp import FastMCP` — confirmed working import.
- `_tool_manager.list_tools()` gives access to registered tools — confirmed working in contract tests. Attribute is `tool.parameters` (NOT `tool.inputSchema`).

### config/models.py KNOWN_TOOL_NAMES After This Story

```python
KNOWN_TOOL_NAMES: frozenset[str] = frozenset({
    "ping", "server_info",
    "list_rooms", "get_system_topology",
    "play", "pause", "stop", "next_track", "previous_track",
    "get_playback_state", "get_track_info",
})
```

### References

- Story source: `_bmad-output/planning-artifacts/epics.md#story-22-control-core-playback-in-a-target-room`
- FRs covered: FR2 (room targeting), FR3 (play), FR4 (pause), FR5 (stop), FR6 (next), FR7 (previous), FR8 (playback state), FR9 (track info)
- Architecture layer diagram: `_bmad-output/planning-artifacts/architecture.md#component-boundaries`
- SoCo library: installed as `soco>=0.30.14` in `pyproject.toml`
- Previous story: `_bmad-output/implementation-artifacts/2-1-discover-addressable-rooms-and-system-topology.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- All 8 tasks completed. 266 tests passing (80 new tests added: 12 adapter, 12 service, 14 schema, 19 tools, 26 contract — plus 3 domain model tests).
- `PlaybackState` and `TrackInfo` are frozen dataclasses in `domain/models.py`; `PlaybackError` in `domain/exceptions.py`.
- `PlaybackAdapter` normalizes SoCo empty strings and `"NOT_IMPLEMENTED"` duration to `None` via `_coerce_str()`.
- `PlaybackService` uses constructor-injected `room_service` and `adapter`; all error types propagate naturally.
- `tools/playback.py` follows the exact `tools/system.py` pattern with `_CONTROL_TOOL_HINTS` / `_READ_ONLY_TOOL_HINTS`.
- `KNOWN_TOOL_NAMES` updated to 11 tool names total.
- `tools/__init__.py` reuses the existing `room_service` instance for `PlaybackService` (no duplicate RoomService).

### File List

**New files:**
- `src/soniq_mcp/adapters/playback_adapter.py`
- `src/soniq_mcp/services/playback_service.py`
- `src/soniq_mcp/tools/playback.py`
- `tests/unit/adapters/test_playback_adapter.py`
- `tests/unit/services/test_playback_service.py`
- `tests/unit/tools/test_playback.py`
- `tests/contract/tool_schemas/test_playback_tool_schemas.py`

**Modified files:**
- `src/soniq_mcp/domain/models.py` — added `PlaybackState`, `TrackInfo`
- `src/soniq_mcp/domain/exceptions.py` — added `PlaybackError`
- `src/soniq_mcp/schemas/responses.py` — added `PlaybackStateResponse`, `TrackInfoResponse`
- `src/soniq_mcp/schemas/errors.py` — added `from_playback_error()`
- `src/soniq_mcp/tools/__init__.py` — wired `PlaybackAdapter`, `PlaybackService`, `register_playback`
- `src/soniq_mcp/config/models.py` — added 7 tool names to `KNOWN_TOOL_NAMES`
- `tests/unit/domain/test_models.py` — extended with `PlaybackState`, `TrackInfo` tests
- `tests/unit/schemas/test_responses.py` — extended with `PlaybackStateResponse`, `TrackInfoResponse` tests
