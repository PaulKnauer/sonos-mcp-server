# Story 3.1: Manage the Sonos Queue

Status: in-progress

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to inspect and manage the queue for a room,
so that I can use AI to control what plays next.

## Acceptance Criteria

1. Given a valid room with queue-capable playback, when the user invokes the queue view tool, then the server returns the current queue for that room as a structured list of items.
2. Given a valid room, when the user provides a URI and invokes the add-to-queue tool, then the item is appended to the room's queue and the response confirms the new queue position.
3. Given a valid room with a non-empty queue, when the user provides a position and invokes the remove-from-queue tool, then the item at that position is removed and the response confirms success.
4. Given a valid room, when the user invokes the clear-queue tool, then all items are removed and the response confirms the queue is empty.
5. Given a valid room with a non-empty queue, when the user provides a position and invokes the play-from-queue tool, then playback begins at that queue position and the response confirms success.

## Tasks / Subtasks

- [ ] Add `QueueError` to the domain exception taxonomy (AC: 1, 2, 3, 4, 5)
  - [ ] Add `QueueError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [ ] Add `ErrorResponse.from_queue_error(exc)` factory to `src/soniq_mcp/schemas/errors.py`

- [ ] Add `QueueItem` domain model and queue response schemas (AC: 1, 2)
  - [ ] Add `QueueItem` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields: `position: int`, `title: str | None`, `artist: str | None`, `album: str | None`, `uri: str`, `album_art_uri: str | None`
  - [ ] Add `QueueItemResponse` and `QueueResponse` Pydantic models to `src/soniq_mcp/schemas/responses.py`
  - [ ] `QueueResponse` has fields: `room: str`, `items: list[QueueItemResponse]`, `count: int`

- [ ] Extend `SoCoAdapter` with queue operations (AC: 1, 2, 3, 4, 5)
  - [ ] Add `get_queue(ip_address: str) -> list[QueueItem]` — calls `zone.get_queue(max_items=200)`, maps each `DidlObject` to `QueueItem` with 1-based `position`
  - [ ] Add `add_to_queue(ip_address: str, uri: str) -> int` — calls `zone.add_uri_to_queue(uri)`, returns 1-based queue position
  - [ ] Add `remove_from_queue(ip_address: str, position: int) -> None` — fetches queue, finds item at `position` (1-based), calls `zone.remove_from_queue(item)`; raises `QueueError` if position is out of range
  - [ ] Add `clear_queue(ip_address: str) -> None` — calls `zone.clear_queue()`
  - [ ] Add `play_from_queue(ip_address: str, position: int) -> None` — calls `zone.play_from_queue(position - 1)` (SoCo is 0-based); raises `QueueError` if position is ≤ 0
  - [ ] Wrap all SoCo exceptions in `QueueError`; keep `soco` import inside `_make_zone` / `_call_playback` pattern

- [ ] Create `QueueService` (AC: 1, 2, 3, 4, 5)
  - [ ] Create `src/soniq_mcp/services/queue_service.py`
  - [ ] Constructor: `QueueService(room_service: object, adapter: SoCoAdapter)` — takes the shared adapter, no config needed
  - [ ] Implement `get_queue(room_name: str) -> list[QueueItem]` — resolves room, calls `adapter.get_queue(ip)`
  - [ ] Implement `add_to_queue(room_name: str, uri: str) -> int` — resolves room, calls `adapter.add_to_queue(ip, uri)`, returns position
  - [ ] Implement `remove_from_queue(room_name: str, position: int) -> None` — resolves room, calls `adapter.remove_from_queue(ip, position)`
  - [ ] Implement `clear_queue(room_name: str) -> None` — resolves room, calls `adapter.clear_queue(ip)`
  - [ ] Implement `play_from_queue(room_name: str, position: int) -> None` — resolves room, calls `adapter.play_from_queue(ip, position)`

- [ ] Create `tools/queue.py` with MCP tool handlers (AC: 1, 2, 3, 4, 5)
  - [ ] Create `src/soniq_mcp/tools/queue.py` following the exact same pattern as `tools/playback.py`
  - [ ] `register(app, config, queue_service)` function registers each tool if not in `config.tools_disabled`
  - [ ] `get_queue(room: str) -> dict` — `_READ_ONLY_TOOL_HINTS`; returns `QueueResponse.model_dump()`
  - [ ] `add_to_queue(room: str, uri: str) -> dict` — `_CONTROL_TOOL_HINTS`; returns `{"status": "ok", "room": room, "queue_position": position}`
  - [ ] `remove_from_queue(room: str, position: int) -> dict` — `_CONTROL_TOOL_HINTS`; returns `{"status": "ok", "room": room}`
  - [ ] `clear_queue(room: str) -> dict` — `_CONTROL_TOOL_HINTS`; returns `{"status": "ok", "room": room}`
  - [ ] `play_from_queue(room: str, position: int) -> dict` — `_CONTROL_TOOL_HINTS`; returns `{"status": "ok", "room": room, "position": position}`
  - [ ] All handlers catch `RoomNotFoundError`, `QueueError`, and `SonosDiscoveryError` and return the corresponding `ErrorResponse.model_dump()`

- [ ] Wire queue tools into `tools/__init__.py` (AC: 1, 2, 3, 4, 5)
  - [ ] Import `QueueService` from `services/queue_service.py`
  - [ ] Import `register as register_queue` from `tools/queue.py`
  - [ ] Construct `queue_service = QueueService(room_service, SoCoAdapter())` — reuse the existing `room_service` instance; construct a second `SoCoAdapter()` instance rather than coupling into the `sonos_service` internal one
  - [ ] Call `register_queue(app, config, queue_service)` at the end of `register_all`

- [ ] Add automated tests (AC: 1, 2, 3, 4, 5)
  - [ ] `tests/unit/adapters/test_soco_adapter_queue.py` — unit tests for new `SoCoAdapter` queue methods using a fake/mock `soco.SoCo` zone; cover happy paths and `QueueError` wrapping
  - [ ] `tests/unit/services/test_queue_service.py` — unit tests for `QueueService`; cover all five methods, `RoomNotFoundError` propagation, and `QueueError` propagation
  - [ ] `tests/unit/tools/test_queue.py` — unit tests for all five tool handlers; verify response shapes, error translation, and tool-disabled guard
  - [ ] `tests/contract/tool_schemas/test_queue_tool_schemas.py` — contract tests asserting tool names (`get_queue`, `add_to_queue`, `remove_from_queue`, `clear_queue`, `play_from_queue`) and parameter names (`room`, `uri`, `position`) remain stable
  - [ ] Run `make test` and confirm full suite passes

## Dev Notes

### Architecture Constraints (Must Follow)

- `tools/` handles MCP-facing inputs and outputs only — no `SoCo` imports, no room lookup.
- `services/` owns orchestration — room resolution plus calling the adapter.
- `adapters/soco_adapter.py` is the only module that imports `soco`. All new SoCo calls must be in `SoCoAdapter`.
- `QueueService` should be a direct peer of `SonosService` (same constructor pattern: `room_service + adapter`), not a facade layered over `SonosService`. Queue operations are a distinct capability area.
- Tool names use `snake_case` verb-oriented naming consistent with existing tools.
- All response schemas are Pydantic models in `schemas/responses.py`; tool handlers call `.model_dump()`.
- All error responses are `ErrorResponse.model_dump()` — never raise from a tool handler.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`]

### SoCo Queue API Reference

The following `SoCo` zone methods are needed for this story:

| Operation | SoCo call | Notes |
|---|---|---|
| Get queue | `zone.get_queue(start=0, max_items=200)` | Returns a `SocoQueue` (list of `DidlObject`). Each item has `.title`, `.creator` (artist), `.album`, `.album_art_uri`, `.uri` attributes. Items are 0-indexed in the returned list but should be exposed 1-indexed to users. |
| Add to queue | `zone.add_uri_to_queue(uri)` | Returns the 1-based queue position of the newly added item (int). |
| Remove from queue | `zone.remove_from_queue(item)` | `item` is a `DidlObject` retrieved from `get_queue()`. To remove by position: call `get_queue()`, access index `position - 1`, pass that object. Raises if out of range. |
| Clear queue | `zone.clear_queue()` | No return value. |
| Play from queue | `zone.play_from_queue(index)` | `index` is **0-based**. User-facing `position` is 1-based; convert with `index = position - 1`. |

All SoCo exceptions must be caught and re-raised as `QueueError`.

### Position Convention

- User-facing positions (in tool parameters and responses) are **1-indexed** (first item = 1).
- SoCo `play_from_queue(index)` is **0-indexed**. Convert: `soco_index = user_position - 1`.
- The returned list from `get_queue()` is 0-indexed. When building `QueueItem`, set `position = list_index + 1`.
- Validate `position >= 1` before calling SoCo; raise `QueueError` with a clear message if invalid.

### Current Codebase Reality

After Story 2.4, the wiring in `tools/__init__.py` is:

```python
room_service = RoomService(DiscoveryAdapter())
sonos_service = SonosService(room_service, SoCoAdapter(), config)
playback_service = PlaybackService(sonos_service=sonos_service)
volume_service = VolumeService(sonos_service=sonos_service)
```

For Story 3.1, add after the volume wiring:

```python
queue_service = QueueService(room_service, SoCoAdapter())
register_queue(app, config, queue_service)
```

A second `SoCoAdapter()` instance is fine — `SoCoAdapter` is stateless and creates `soco.SoCo` objects on demand inside each method call.

### Domain Model Shape

Add to `src/soniq_mcp/domain/models.py`:

```python
@dataclass(frozen=True)
class QueueItem:
    position: int          # 1-based
    uri: str
    title: str | None = field(default=None)
    artist: str | None = field(default=None)
    album: str | None = field(default=None)
    album_art_uri: str | None = field(default=None)
```

### Response Schema Shape

Add to `src/soniq_mcp/schemas/responses.py`:

```python
class QueueItemResponse(BaseModel):
    position: int
    uri: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    album_art_uri: str | None = None

class QueueResponse(BaseModel):
    room: str
    items: list[QueueItemResponse]
    count: int

    @classmethod
    def from_domain(cls, room_name: str, items: list[QueueItem]) -> "QueueResponse":
        return cls(
            room=room_name,
            items=[QueueItemResponse(...) for item in items],
            count=len(items),
        )
```

### Error Taxonomy Extension

Add to `src/soniq_mcp/domain/exceptions.py`:

```python
class QueueError(SoniqDomainError):
    """Raised when a Sonos queue operation fails."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
```

Add to `src/soniq_mcp/schemas/errors.py`:

```python
@classmethod
def from_queue_error(cls, exc: Exception) -> "ErrorResponse":
    return cls(
        error=str(exc),
        field="queue",
        suggestion=(
            "Check that the room is reachable and has queue-capable playback. "
            "Some operations require a non-empty queue or a valid queue position."
        ),
    )
```

### Tool Name Registry (for contract tests and tools_disabled)

| Tool name | Method | Hint type | Parameters |
|---|---|---|---|
| `get_queue` | GET | `_READ_ONLY_TOOL_HINTS` | `room: str` |
| `add_to_queue` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `uri: str` |
| `remove_from_queue` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `position: int` |
| `clear_queue` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `position: int` |
| `play_from_queue` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `position: int` |

### Testing Requirements

- Use the existing test fakes pattern: create a fake `QueueService` or mock `SoCoAdapter` using `unittest.mock` or local test doubles — no real Sonos hardware.
- For `test_soco_adapter_queue.py`, mock `soco.SoCo` at the import level (see how existing adapter tests work).
- For `test_queue_service.py`, use a fake `RoomService` that returns a dummy `Room` or raises `RoomNotFoundError` as needed.
- For `test_queue.py`, inject a fake `queue_service` object with controlled return values and side effects.
- Contract tests: follow the exact same pattern as `test_playback_tool_schemas.py` and `test_volume_tool_schemas.py`.
- Run `make test` before marking done; all existing 391 tests must still pass, plus new coverage.
  [Source: `_bmad-output/planning-artifacts/architecture.md#File-Organization-Patterns`]

### Files to Create

```text
src/soniq_mcp/services/queue_service.py
src/soniq_mcp/tools/queue.py
tests/unit/adapters/test_soco_adapter_queue.py
tests/unit/services/test_queue_service.py
tests/unit/tools/test_queue.py
tests/contract/tool_schemas/test_queue_tool_schemas.py
```

### Files to Modify

```text
src/soniq_mcp/domain/exceptions.py          (add QueueError)
src/soniq_mcp/domain/models.py              (add QueueItem)
src/soniq_mcp/adapters/soco_adapter.py      (add 5 queue methods)
src/soniq_mcp/schemas/errors.py             (add from_queue_error)
src/soniq_mcp/schemas/responses.py          (add QueueItemResponse, QueueResponse)
src/soniq_mcp/tools/__init__.py             (wire QueueService + register_queue)
```

### Previous Story Intelligence

- Story 2.4 established the shared `SoCoAdapter` + `SonosService` boundary pattern. Story 3.1 follows the same architectural shape: new `QueueService(room_service, adapter)` mirrors `SonosService(room_service, adapter, config)`.
- All existing playback and volume tool schemas, error mappings, and response shapes must remain unchanged.
- Story 2.4 baseline: `391 passed, 3 skipped` — this is the regression target.
- The `_make_zone` static method in `SoCoAdapter` is the correct factory to use for new methods; do not inline `soco.SoCo(ip)` directly in queue methods.
- Tool handlers must guard with `assert_tool_permitted(tool_name, config)` at the start of each handler body, matching the exact pattern in `tools/playback.py`.

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-31-Manage-the-Sonos-Queue`
- Architecture structure: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries`
- Naming and pattern rules: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`
- Previous story: `_bmad-output/implementation-artifacts/2-4-apply-reliable-sonos-service-and-adapter-boundaries.md`
- Pattern reference tool module: `src/soniq_mcp/tools/playback.py`
- Pattern reference service: `src/soniq_mcp/services/sonos_service.py`
- Pattern reference adapter: `src/soniq_mcp/adapters/soco_adapter.py`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change |
|------|--------|
