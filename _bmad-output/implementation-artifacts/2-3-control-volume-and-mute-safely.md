# Story 2.3: Control Volume and Mute Safely

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to inspect and change volume in a room,
so that I can adjust playback without disruptive surprises.

## Acceptance Criteria

1. Given a valid target room, when the user invokes volume or mute controls, then the server supports get volume, set volume, adjust volume, mute, unmute, and get mute state.
2. Given a valid target room, when the user requests a volume level, then volume operations are validated against the allowed 0-100 range and the configured `max_volume_pct` cap.
3. Given a request that would exceed `max_volume_pct` or is out of the 0-100 range, when the volume tool is invoked, then safety logic prevents the request from being applied and a clear, structured error is returned.
4. Given an invalid room name or Sonos connectivity failure, when any volume or mute tool is invoked, then errors are returned using the shared `ErrorResponse` model.

## Tasks / Subtasks

- [x] Add `VolumeState` domain model and `VolumeError` exception (AC: 1, 2)
  - [x] Add `VolumeState` frozen dataclass to `src/soniq_mcp/domain/models.py`: fields `room_name: str`, `volume: int`, `is_muted: bool`
  - [x] Add `VolumeError` exception to `src/soniq_mcp/domain/exceptions.py` (subclass of `SoniqDomainError`) — used for SoCo operation failures, distinct from the existing `VolumeCapExceeded`
  - [x] Extend unit tests in `tests/unit/domain/test_models.py` with `VolumeState` tests
  - [x] **DO NOT redefine `VolumeCapExceeded`** — it already exists in `domain/exceptions.py`

- [x] Add `VolumeStateResponse` schema and `from_volume_error()` factory (AC: 1, 3, 4)
  - [x] Add `VolumeStateResponse` to `src/soniq_mcp/schemas/responses.py`: fields `room_name: str`, `volume: int`, `is_muted: bool`, with `from_domain(state: VolumeState)` classmethod
  - [x] Add `ErrorResponse.from_volume_error(exc: Exception) -> ErrorResponse` classmethod to `src/soniq_mcp/schemas/errors.py` — for SoCo operation failures
  - [x] **DO NOT redefine `ErrorResponse.from_volume_cap()`** — it already exists in `schemas/errors.py`
  - [x] Extend unit tests in `tests/unit/schemas/test_responses.py` with `VolumeStateResponse` tests

- [x] Implement the volume adapter (AC: 1)
  - [x] Create `src/soniq_mcp/adapters/volume_adapter.py` with `VolumeAdapter` class
  - [x] `VolumeAdapter.get_volume(ip_address: str) -> int` — creates `soco.SoCo(ip_address)`, returns `zone.volume`
  - [x] `VolumeAdapter.set_volume(ip_address: str, volume: int) -> None` — sets `zone.volume = volume`
  - [x] `VolumeAdapter.get_mute(ip_address: str) -> bool` — returns `zone.mute`
  - [x] `VolumeAdapter.set_mute(ip_address: str, muted: bool) -> None` — sets `zone.mute = muted`
  - [x] All SoCo exceptions caught and re-raised as `VolumeError` with a user-readable message
  - [x] This is the ONLY file that imports `soco` for volume operations; do NOT add soco imports to service or tool layers
  - [x] Write unit tests in `tests/unit/adapters/test_volume_adapter.py` using fake/mock SoCo zone (no real hardware)

- [x] Implement the volume service (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/services/volume_service.py` with `VolumeService` class
  - [x] `VolumeService(room_service: RoomService, adapter: VolumeAdapter, config: SoniqConfig)` — all injected via constructor
  - [x] `VolumeService.get_volume_state(room_name: str) -> VolumeState` — calls `room_service.get_room(room_name)`, then `adapter.get_volume()` and `adapter.get_mute()`, returns `VolumeState`
  - [x] `VolumeService.set_volume(room_name: str, volume: int) -> None` — calls `check_volume(volume, config)` from `domain/safety.py`, then `room_service.get_room()`, then `adapter.set_volume()`
  - [x] `VolumeService.adjust_volume(room_name: str, delta: int) -> VolumeState` — gets current volume via adapter, computes `target = max(0, min(100, current + delta))`, calls `check_volume(target, config)`, sets volume, returns updated `VolumeState`
  - [x] `VolumeService.mute(room_name: str) -> None` — calls `room_service.get_room()`, then `adapter.set_mute(ip, True)`
  - [x] `VolumeService.unmute(room_name: str) -> None` — calls `room_service.get_room()`, then `adapter.set_mute(ip, False)`
  - [x] `RoomNotFoundError` and `SonosDiscoveryError` from `get_room()` propagate up naturally — no re-wrapping
  - [x] `VolumeCapExceeded` from `check_volume()` propagates up naturally to the tool layer
  - [x] Write unit tests in `tests/unit/services/test_volume_service.py` using fake `RoomService` and fake `VolumeAdapter`

- [x] Implement volume tools (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/tools/volume.py` with `register(app, config, volume_service)` function
  - [x] Register `get_volume(room: str)`: returns `VolumeStateResponse.from_domain(state).model_dump()` on success
  - [x] Register `set_volume(room: str, volume: int)`: calls `volume_service.set_volume(room, volume)`, returns `{"status": "ok", "room": room, "volume": volume}` on success
  - [x] Register `adjust_volume(room: str, delta: int)`: returns `VolumeStateResponse.from_domain(state).model_dump()` on success (state from service return value)
  - [x] Register `mute(room: str)`: calls `volume_service.mute(room)`, returns `{"status": "ok", "room": room, "is_muted": True}`
  - [x] Register `unmute(room: str)`: calls `volume_service.unmute(room)`, returns `{"status": "ok", "room": room, "is_muted": False}`
  - [x] Register `get_mute(room: str)`: calls `volume_service.get_volume_state(room)`, returns `{"room": room, "is_muted": state.is_muted}`
  - [x] Read tools (`get_volume`, `get_mute`) use `_READ_ONLY_TOOL_HINTS`
  - [x] Write tools use `_CONTROL_TOOL_HINTS` (see ToolAnnotations pattern in Dev Notes)
  - [x] All tools call `assert_tool_permitted(tool_name, config)` at invocation time
  - [x] All tools catch `VolumeCapExceeded as exc` → `ErrorResponse.from_volume_cap(exc.requested, exc.cap).model_dump()`
  - [x] All tools catch `VolumeError as exc` → `ErrorResponse.from_volume_error(exc).model_dump()`
  - [x] All tools catch `RoomNotFoundError` → `ErrorResponse.from_room_not_found(room).model_dump()`
  - [x] All tools catch `SonosDiscoveryError as exc` → `ErrorResponse.from_discovery_error(exc).model_dump()`
  - [x] Write unit tests in `tests/unit/tools/test_volume.py` using fake `VolumeService`

- [x] Wire volume tools into the server (AC: 1)
  - [x] Update `src/soniq_mcp/tools/__init__.py`: import and call `register` from `tools/volume.py`, constructing `VolumeAdapter` and `VolumeService` inside `register_all()`
  - [x] `room_service` already exists in `register_all()` from Story 2.1 — reuse it for `VolumeService`, do NOT create a second instance
  - [x] Update `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py` to add the 6 new tool names: `"get_volume"`, `"set_volume"`, `"adjust_volume"`, `"mute"`, `"unmute"`, `"get_mute"`
  - [x] Run `make test` and confirm all existing tests still pass (no regressions)

- [x] Add contract tests (AC: 1, 2, 3)
  - [x] Add `tests/contract/tool_schemas/test_volume_tool_schemas.py` — validates all 6 volume tool names, descriptions, and parameter schemas are stable

## Dev Notes

### Architecture Constraints (MUST Follow)

- **Layer order enforced**: `tools/volume.py` → `services/volume_service.py` → `adapters/volume_adapter.py` → SoCo. No layer may skip.
- **SoCo isolation**: `adapters/volume_adapter.py` is the ONLY new file that imports `soco`. Do NOT import `soco` in service or tool layers.
- **Connect by IP**: Use `soco.SoCo(ip_address)` directly — do NOT call `soco.discover()` per action. Room IP comes from `RoomService.get_room()`.
- **Dependency injection**: `VolumeService(room_service, adapter, config)`. `register(app, config, volume_service)`. This makes everything testable without hardware.
- **Reuse existing safety infrastructure**: `domain/safety.py:check_volume()` and `domain/exceptions.py:VolumeCapExceeded` already exist. The service MUST call `check_volume()` — do NOT reimplement the cap logic.
- **Reuse existing error factories**: `ErrorResponse.from_volume_cap()` already exists in `schemas/errors.py`. Add only `from_volume_error()`.
- **Response schemas**: All tool handlers return `.model_dump()` — never return raw Pydantic objects.
- **`KNOWN_TOOL_NAMES` must be updated BEFORE running tests** — otherwise `tools_disabled` validator rejects test configs that reference these tools.

### Existing Infrastructure to Reuse (Critical — Do NOT Reinvent)

```python
# domain/safety.py — already implemented in Story 1.4
from soniq_mcp.domain.safety import check_volume
# check_volume(requested: int, config: SoniqConfig) -> int
# Raises ValueError if not 0-100; raises VolumeCapExceeded if > max_volume_pct

# domain/exceptions.py — already implemented in Story 1.4
from soniq_mcp.domain.exceptions import VolumeCapExceeded
# VolumeCapExceeded.requested: int, VolumeCapExceeded.cap: int

# schemas/errors.py — already implemented in Story 1.4
ErrorResponse.from_volume_cap(exc.requested, exc.cap)

# config/models.py — already implemented in Story 1.4
config.max_volume_pct  # int, default 80, range 0-100
```

### SoCo Volume API (Key Facts)

```python
import soco

zone = soco.SoCo("192.168.1.10")  # connect by IP, do NOT re-discover per action

# Volume (int, 0-100)
current_volume = zone.volume        # getter → int
zone.volume = 50                    # setter → None

# Mute (bool)
is_muted = zone.mute                # getter → bool
zone.mute = True                    # setter → None

# SoCo volume errors — catch broadly and wrap as VolumeError
# soco.exceptions.SoCoUPnPException is the primary error type
```

**Notes:**
- `zone.volume` and `zone.mute` are properties, not methods.
- Setting volume outside 0-100 raises `SoCoUPnPException`. Always validate before calling the adapter.
- Catch `Exception` broadly in the adapter and wrap as `VolumeError` to prevent SoCo types from leaking.

### `adjust_volume` Safety Pattern

```python
# In VolumeService.adjust_volume():
room = self._room_service.get_room(room_name)
current = self._adapter.get_volume(room.ip_address)
target = max(0, min(100, current + delta))   # clamp to 0-100 first
check_volume(target, self._config)           # enforces max_volume_pct cap
self._adapter.set_volume(room.ip_address, target)
is_muted = self._adapter.get_mute(room.ip_address)
return VolumeState(room_name=room.name, volume=target, is_muted=is_muted)
```

- Negative deltas that would go below 0 are silently floored to 0 (not an error — just silence).
- Positive deltas that would push past `max_volume_pct` raise `VolumeCapExceeded` (safety enforcement — the user must be informed).

### ToolAnnotations Pattern

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
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)
```

Use `_READ_ONLY_TOOL_HINTS` for: `get_volume`, `get_mute`.
Use `_CONTROL_TOOL_HINTS` for: `set_volume`, `adjust_volume`, `mute`, `unmute`.

### Tool Registration Pattern

Follow the EXACT pattern from `tools/system.py` and `tools/playback.py`:

```python
def register(app: FastMCP, config: SoniqConfig, volume_service: object) -> None:
    if "get_volume" not in config.tools_disabled:
        @app.tool(title="Get Volume", annotations=_READ_ONLY_TOOL_HINTS)
        def get_volume(room: str) -> dict:
            """Get the current volume and mute state for a Sonos room."""
            assert_tool_permitted("get_volume", config)
            try:
                state = volume_service.get_volume_state(room)
                return VolumeStateResponse.from_domain(state).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except VolumeError as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except SonosDiscoveryError as exc:
                return ErrorResponse.from_discovery_error(exc).model_dump()

    if "set_volume" not in config.tools_disabled:
        @app.tool(title="Set Volume", annotations=_CONTROL_TOOL_HINTS)
        def set_volume(room: str, volume: int) -> dict:
            """Set the volume for a Sonos room (0-100, capped by max_volume_pct)."""
            assert_tool_permitted("set_volume", config)
            try:
                volume_service.set_volume(room, volume)
                return {"status": "ok", "room": room, "volume": volume}
            except VolumeCapExceeded as exc:
                return ErrorResponse.from_volume_cap(exc.requested, exc.cap).model_dump()
            except (ValueError, VolumeError) as exc:
                return ErrorResponse.from_volume_error(exc).model_dump()
            except RoomNotFoundError:
                return ErrorResponse.from_room_not_found(room).model_dump()
            except SonosDiscoveryError as exc:
                return ErrorResponse.from_discovery_error(exc).model_dump()
```

### Wiring in tools/__init__.py

```python
from soniq_mcp.adapters.volume_adapter import VolumeAdapter
from soniq_mcp.services.volume_service import VolumeService
from soniq_mcp.tools.volume import register as register_volume

# Inside register_all() — after room_service is constructed:
volume_adapter = VolumeAdapter()
volume_service = VolumeService(room_service, volume_adapter, config)
register_volume(app, config, volume_service)
```

### `KNOWN_TOOL_NAMES` After This Story

Story 2.3 adds 6 tool names. After this story (assuming Story 2.2 is done), the full set is:

```python
KNOWN_TOOL_NAMES: frozenset[str] = frozenset({
    "ping", "server_info",
    "list_rooms", "get_system_topology",
    "play", "pause", "stop", "next_track", "previous_track",
    "get_playback_state", "get_track_info",
    "get_volume", "set_volume", "adjust_volume", "mute", "unmute", "get_mute",
})
```

**If Story 2.2 is not yet merged**, only add the 6 volume names to whatever is currently in `KNOWN_TOOL_NAMES`. Do NOT add Story 2.2's tool names — that is 2.2's responsibility.

### New Files to Create

```
src/soniq_mcp/
├── adapters/
│   └── volume_adapter.py     # NEW: SoCo volume/mute operations
├── services/
│   └── volume_service.py     # NEW: Volume/mute business logic + safety
└── tools/
    └── volume.py             # NEW: register get_volume, set_volume, adjust_volume, mute, unmute, get_mute

tests/
├── unit/
│   ├── adapters/
│   │   └── test_volume_adapter.py    # NEW
│   ├── services/
│   │   └── test_volume_service.py    # NEW
│   └── tools/
│       └── test_volume.py            # NEW
└── contract/
    └── tool_schemas/
        └── test_volume_tool_schemas.py  # NEW
```

### Files to Modify

| File | Change |
|------|--------|
| `src/soniq_mcp/domain/models.py` | Add `VolumeState` frozen dataclass |
| `src/soniq_mcp/domain/exceptions.py` | Add `VolumeError` (subclass of `SoniqDomainError`) |
| `src/soniq_mcp/schemas/responses.py` | Add `VolumeStateResponse` with `from_domain()` |
| `src/soniq_mcp/schemas/errors.py` | Add `from_volume_error()` factory method |
| `src/soniq_mcp/tools/__init__.py` | Wire `VolumeAdapter`, `VolumeService`, `register_volume` |
| `src/soniq_mcp/config/models.py` | Add 6 volume tool names to `KNOWN_TOOL_NAMES` |
| `tests/unit/domain/test_models.py` | Extend with `VolumeState` tests |
| `tests/unit/schemas/test_responses.py` | Extend with `VolumeStateResponse` tests |

### Test Patterns (Match Story 2.1 and 2.2)

- Use fake classes (`FakeVolumeAdapter`, `FakeVolumeService`) — no `unittest.mock.patch`
- `FakeVolumeAdapter` stores `volume: int = 50`, `muted: bool = False`; has `raise_error: bool` param
- `FakeVolumeService` has per-method control (e.g., `raise_volume_cap: bool`, `raise_on_room: str | None`)
- For `test_volume.py`, follow `test_system.py` and `test_playback.py`: `make_app_with_service()`, `get_tool()` helper, `@pytest.mark.anyio` for async call tests
- Test all 6 tools: registration, disabled-check, success path, `RoomNotFoundError` path, `VolumeError` path, `VolumeCapExceeded` path (for set_volume and adjust_volume)
- Test `adjust_volume` floor clamping: delta that would go below 0 → volume becomes 0, not an error
- Test `adjust_volume` cap enforcement: delta that would exceed `max_volume_pct` → `VolumeCapExceeded`
- Run `make test` before marking any task complete; baseline after Story 2.2 is expected ~225-235 tests

**Contract test pattern** (match `test_system_tool_schemas.py` and `test_playback_tool_schemas.py`):

```python
# tests/contract/tool_schemas/test_volume_tool_schemas.py
from mcp.server.fastmcp import FastMCP
from soniq_mcp.config.models import SoniqConfig
from soniq_mcp.tools.volume import register

class FakeVolumeService: ...  # minimal fake with all required methods

def test_get_volume_tool_schema():
    app = FastMCP("test")
    config = SoniqConfig()
    register(app, config, FakeVolumeService())
    tools = {t.name: t for t in app._tool_manager.list_tools()}
    tool = tools["get_volume"]
    assert tool.description
    assert "room" in tool.parameters["properties"]
    assert tool.parameters["required"] == ["room"]

def test_set_volume_tool_schema():
    ...  # verify "room" and "volume" in parameters, both required
```

### Previous Story Learnings (Stories 2.1 and 2.2)

- `make test` is the correct test command (wraps `uv run pytest`).
- All tool handlers return `.model_dump()` of a Pydantic response — NOT raw Python objects or domain types.
- Tool tests use `await app.call_tool("name", {"param": val})` and parse `result[0].text` as JSON.
- `KNOWN_TOOL_NAMES` validator rejects unknown tool names in `tools_disabled` — update it BEFORE writing tests that set `tools_disabled`.
- Reuse the same `room_service` instance in `register_all()` — do NOT construct a second `RoomService`.
- `from mcp.types import ToolAnnotations` — confirmed working import.
- `from mcp.server.fastmcp import FastMCP` — confirmed working import.
- `_tool_manager.list_tools()` gives access to registered tools. Attribute is `tool.parameters` (NOT `tool.inputSchema`).
- `assert_tool_permitted` is imported from `soniq_mcp.domain.safety`, not from `tools/setup_support.py`.

### References

- Story source: `_bmad-output/planning-artifacts/epics.md#story-23-control-volume-and-mute-safely`
- FRs covered: FR10 (get volume), FR11 (set volume), FR12 (adjust volume), FR13 (mute), FR14 (unmute), FR15 (get mute state)
- Safety infrastructure: `src/soniq_mcp/domain/safety.py` (check_volume, assert_tool_permitted)
- Existing exceptions: `src/soniq_mcp/domain/exceptions.py` (VolumeCapExceeded already exists)
- Existing error factories: `src/soniq_mcp/schemas/errors.py` (from_volume_cap already exists)
- Architecture layer diagram: `_bmad-output/planning-artifacts/architecture.md#component-boundaries`
- SoCo library: installed as `soco>=0.30.14` in `pyproject.toml`
- Previous story: `_bmad-output/implementation-artifacts/2-2-control-core-playback-in-a-target-room.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation proceeded cleanly with no blocking issues.

### Completion Notes List

- Implemented full volume and mute layer stack: VolumeAdapter → VolumeService → tools/volume.py, following the same architecture as Stories 2.1 and 2.2.
- VolumeAdapter wraps soco.SoCo by-IP; all SoCo exceptions caught and re-raised as VolumeError — no SoCo types leak into higher layers.
- VolumeService reuses existing check_volume() and VolumeCapExceeded from domain/safety.py — no safety logic reimplemented.
- adjust_volume() clamps target to 0-100 before cap check: negative deltas flooring to 0 are silent; positive deltas exceeding max_volume_pct raise VolumeCapExceeded.
- ErrorResponse.from_volume_error() added to schemas/errors.py alongside existing from_volume_cap().
- KNOWN_TOOL_NAMES updated with 6 names before any test that uses tools_disabled.
- Built on committed baseline (Story 2.2 was in-progress/uncommitted); only added the 6 volume tool names as instructed.
- All 282 tests pass (3 skipped for hardware integration tests). No regressions.

### File List

New files:
- `src/soniq_mcp/adapters/volume_adapter.py`
- `src/soniq_mcp/services/volume_service.py`
- `src/soniq_mcp/tools/volume.py`
- `tests/unit/adapters/test_volume_adapter.py`
- `tests/unit/services/test_volume_service.py`
- `tests/unit/tools/test_volume.py`
- `tests/contract/tool_schemas/test_volume_tool_schemas.py`

Modified files:
- `src/soniq_mcp/domain/models.py` — added VolumeState dataclass
- `src/soniq_mcp/domain/exceptions.py` — added VolumeError exception
- `src/soniq_mcp/schemas/responses.py` — added VolumeStateResponse with from_domain()
- `src/soniq_mcp/schemas/errors.py` — added ErrorResponse.from_volume_error()
- `src/soniq_mcp/tools/__init__.py` — wired VolumeAdapter, VolumeService, register_volume
- `src/soniq_mcp/config/models.py` — added 6 volume tool names to KNOWN_TOOL_NAMES
- `tests/unit/domain/test_models.py` — extended with TestVolumeState class
- `tests/unit/schemas/test_responses.py` — extended with TestVolumeStateResponse class
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — updated story status

## Change Log

| Date | Change |
|------|--------|
| 2026-03-28 | Story 2.3 implemented — volume and mute layer stack (adapter, service, 6 tools, contract tests). 282 tests passing. |
