# Story 3.2: Access and Play Favourites and Playlists

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to browse Sonos favourites and playlists and start them in a room,
so that I can use my saved Sonos content naturally through AI.

## Acceptance Criteria

1. Given the connected Sonos system has saved favourites, when the user invokes the list favourites tool, then the server returns available Sonos favourites as a structured list with title and identifier.
2. Given a valid favourite identifier and a valid target room, when the user invokes the play favourite tool, then playback of that favourite begins in the target room and the response confirms success.
3. Given the connected Sonos system has saved playlists, when the user invokes the list playlists tool, then the server returns available Sonos playlists as a structured list with title and identifier.
4. Given a valid playlist identifier and a valid target room, when the user invokes the play playlist tool, then playback of that playlist begins in the target room and the response confirms success.

## Tasks / Subtasks

- [x] Add `FavouritesError` to the domain exception taxonomy (AC: 1, 2, 3, 4)
  - [x] Add `FavouritesError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [x] Add `ErrorResponse.from_favourites_error(exc)` factory to `src/soniq_mcp/schemas/errors.py`

- [x] Add domain models for favourites and playlists (AC: 1, 2, 3, 4)
  - [x] Add `Favourite` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields: `title: str`, `uri: str`, `meta: str | None = None` (DIDL-Lite XML string used when playing)
  - [x] Add `SonosPlaylist` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields: `title: str`, `uri: str`, `item_id: str | None = None`

- [x] Add response schemas for favourites and playlists (AC: 1, 3)
  - [x] Add `FavouriteResponse` and `FavouritesListResponse` Pydantic models to `src/soniq_mcp/schemas/responses.py`
  - [x] `FavouritesListResponse` has fields: `items: list[FavouriteResponse]`, `count: int`
  - [x] Add `PlaylistResponse` and `PlaylistsListResponse` Pydantic models to `src/soniq_mcp/schemas/responses.py`
  - [x] `PlaylistsListResponse` has fields: `items: list[PlaylistResponse]`, `count: int`

- [x] Extend `SoCoAdapter` with favourites and playlists operations (AC: 1, 2, 3, 4)
  - [x] Add `get_favourites(ip_address: str) -> list[Favourite]` — calls `zone.music_library.get_sonos_favorites()`, maps each result to `Favourite(title=item.title, uri=item.uri, meta=item.to_didl_string())`
  - [x] Add `play_favourite(ip_address: str, uri: str, meta: str | None) -> None` — calls `zone.play_uri(uri=uri, meta=meta or "")` to play directly; wraps all SoCo exceptions in `FavouritesError`
  - [x] Add `get_playlists(ip_address: str) -> list[SonosPlaylist]` — calls `zone.music_library.get_music_library_information('sonos_playlists')`, maps each result to `SonosPlaylist(title=item.title, uri=item.uri, item_id=getattr(item, 'item_id', None))`
  - [x] Add `play_playlist(ip_address: str, uri: str) -> None` — clears queue, adds playlist URI via `zone.add_uri_to_queue(uri)`, then calls `zone.play_from_queue(0)`; wraps all SoCo exceptions in `FavouritesError`
  - [x] Keep all `soco` imports inside `_make_zone` / existing lazy-import pattern — no top-level `import soco`

- [x] Create `FavouritesService` (AC: 1, 2, 3, 4)
  - [x] Create `src/soniq_mcp/services/favourites_service.py`
  - [x] Constructor: `FavouritesService(room_service: object, adapter: SoCoAdapter)` — takes a `RoomService` for room lookup and a `SoCoAdapter` for content operations
  - [x] Implement `get_favourites(ip_address: str) -> list[Favourite]` — calls `adapter.get_favourites(ip)` directly (no room needed for listing — favourites are system-wide); pass the IP of any reachable room to get the household list
  - [x] Implement `play_favourite(room_name: str, uri: str, meta: str | None) -> None` — resolves room via `room_service.get_room(room_name)`, calls `adapter.play_favourite(ip, uri, meta)`
  - [x] Implement `get_playlists(ip_address: str) -> list[SonosPlaylist]` — calls `adapter.get_playlists(ip)` directly (system-wide)
  - [x] Implement `play_playlist(room_name: str, uri: str) -> None` — resolves room via `room_service.get_room(room_name)`, calls `adapter.play_playlist(ip, uri)`
  - [x] For `get_favourites` and `get_playlists`, the caller provides an `ip_address` obtained from `room_service.list_rooms()[0].ip_address`; the service handles empty-room-list gracefully by raising `FavouritesError`

- [x] Create `tools/favourites.py` with MCP tool handlers (AC: 1, 2)
  - [x] Create `src/soniq_mcp/tools/favourites.py` following the exact same pattern as `tools/playback.py`
  - [x] `register(app, config, favourites_service)` function registers tools if not in `config.tools_disabled`
  - [x] `list_favourites() -> dict` — `_READ_ONLY_TOOL_HINTS`; calls `favourites_service.get_favourites(ip)` (resolves IP internally), returns `FavouritesListResponse.model_dump()`
  - [x] `play_favourite(room: str, uri: str) -> dict` — `_CONTROL_TOOL_HINTS`; calls `favourites_service.play_favourite(room, uri, meta=None)`; returns `{"status": "ok", "room": room, "uri": uri}`
  - [x] All handlers catch `RoomNotFoundError`, `FavouritesError`, and `SonosDiscoveryError`, return `ErrorResponse.model_dump()`
  - [x] Each handler starts with `assert_tool_permitted(tool_name, config)`

- [x] Create `tools/playlists.py` with MCP tool handlers (AC: 3, 4)
  - [x] Create `src/soniq_mcp/tools/playlists.py` following the exact same pattern as `tools/playback.py`
  - [x] `register(app, config, favourites_service)` function — playlists reuse the same `FavouritesService` instance
  - [x] `list_playlists() -> dict` — `_READ_ONLY_TOOL_HINTS`; calls `favourites_service.get_playlists(ip)`, returns `PlaylistsListResponse.model_dump()`
  - [x] `play_playlist(room: str, uri: str) -> dict` — `_CONTROL_TOOL_HINTS`; calls `favourites_service.play_playlist(room, uri)`; returns `{"status": "ok", "room": room, "uri": uri}`
  - [x] All handlers catch `RoomNotFoundError`, `FavouritesError`, and `SonosDiscoveryError`, return `ErrorResponse.model_dump()`
  - [x] Each handler starts with `assert_tool_permitted(tool_name, config)`

- [x] Wire favourites and playlists tools into `tools/__init__.py` (AC: 1, 2, 3, 4)
  - [x] Import `FavouritesService` from `services/favourites_service.py`
  - [x] Import `register as register_favourites` from `tools/favourites.py`
  - [x] Import `register as register_playlists` from `tools/playlists.py`
  - [x] Construct ONE `favourites_service = FavouritesService(room_service, SoCoAdapter())` — both tools/favourites and tools/playlists share this single instance
  - [x] Call `register_favourites(app, config, favourites_service)` and `register_playlists(app, config, favourites_service)` at the end of `register_all`
  - [x] Add after the volume wiring (before any queue wiring if story 3.1 is done)

- [x] Add automated tests (AC: 1, 2, 3, 4)
  - [x] `tests/unit/adapters/test_soco_adapter_favourites.py` — unit tests for `SoCoAdapter` favourites/playlists methods using mock `soco.SoCo` zone; cover happy paths and `FavouritesError` wrapping; mock `zone.music_library`
  - [x] `tests/unit/services/test_favourites_service.py` — unit tests for `FavouritesService`; cover all four methods; `RoomNotFoundError` propagation; `FavouritesError` propagation; empty-room-list guard
  - [x] `tests/unit/tools/test_favourites.py` — unit tests for all two favourites tool handlers; verify response shapes, error translation, tool-disabled guard
  - [x] `tests/unit/tools/test_playlists.py` — unit tests for all two playlists tool handlers; verify response shapes, error translation, tool-disabled guard
  - [x] `tests/contract/tool_schemas/test_favourites_tool_schemas.py` — contract tests asserting tool names (`list_favourites`, `play_favourite`) and parameter names (`room`, `uri`) remain stable
  - [x] `tests/contract/tool_schemas/test_playlists_tool_schemas.py` — contract tests asserting tool names (`list_playlists`, `play_playlist`) and parameter names (`room`, `uri`) remain stable
  - [x] Run `make test` and confirm full suite passes with no regressions

## Dev Notes

### Architecture Constraints (Must Follow)

- `tools/` handles MCP-facing inputs and outputs only — no `SoCo` imports, no room lookup.
- `services/` owns orchestration — room resolution plus calling the adapter.
- `adapters/soco_adapter.py` is the only module that imports `soco`. All new SoCo calls must be in `SoCoAdapter`.
- `FavouritesService` constructor pattern: `FavouritesService(room_service, adapter)` — peer of `QueueService` (story 3.1) and `SonosService`.
- Both `tools/favourites.py` and `tools/playlists.py` accept `favourites_service` — they share one `FavouritesService` instance.
- Tool names use `snake_case` verb-oriented naming consistent with existing tools.
- All response schemas are Pydantic models in `schemas/responses.py`; tool handlers call `.model_dump()`.
- All error responses are `ErrorResponse.model_dump()` — never raise from a tool handler.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`]

### SoCo Favourites and Playlists API Reference

The following `SoCo` zone methods are needed for this story:

| Operation | SoCo call | Notes |
|---|---|---|
| Get favourites | `zone.music_library.get_sonos_favorites()` | Returns a `SearchResult` (list of `DidlFavorite` / `DidlObject`). Each item has `.title` (str), `.uri` (str), and `.to_didl_string()` (str) for the DIDL-Lite XML metadata. |
| Play favourite | `zone.play_uri(uri=uri, meta=meta)` | `meta` is the DIDL-Lite XML string from `.to_didl_string()`. Works for most favourite types. If `meta` is `None`, pass `""`. |
| Get playlists | `zone.music_library.get_music_library_information('sonos_playlists')` | Returns a `SearchResult`. Each item has `.title` (str), `.uri` (str), and optionally `.item_id` (str). |
| Play playlist | `zone.clear_queue()` + `zone.add_uri_to_queue(uri)` + `zone.play_from_queue(0)` | Queue-based: clear first, add the playlist URI, play from start. `add_uri_to_queue` accepts either a string URI or a `DidlObject`. |

All SoCo exceptions must be caught and re-raised as `FavouritesError`.

**Important note on `get_sonos_favorites` return type:** In some SoCo versions the items may not have `to_didl_string()` available or may return an empty string. Guard with `meta = getattr(item, 'to_didl_string', lambda: "")()` if needed.

### Listing Favourites/Playlists — IP Address Resolution

Sonos favourites and playlists are household-wide, not room-specific. To call the SoCo music library API, you need any reachable zone's IP. The `FavouritesService` should resolve this by calling `room_service.list_rooms()[0].ip_address`. If no rooms are found, raise `FavouritesError("No Sonos rooms found — cannot fetch favourites/playlists")`.

This is different from queue/playback operations which always target a specific room. The tool handler `list_favourites()` takes **no parameters** — it lists household-wide content.

### Tool Handler Design — list_favourites and list_playlists (No room parameter)

`list_favourites` and `list_playlists` are read-only household queries — they do **not** take a `room` parameter. The tool implementation handles IP resolution internally via the service. Example:

```python
# In tools/favourites.py:
if "list_favourites" not in config.tools_disabled:
    @app.tool(title="List Favourites", annotations=_READ_ONLY_TOOL_HINTS)
    def list_favourites() -> dict:
        """Return all Sonos favourites in the household."""
        assert_tool_permitted("list_favourites", config)
        try:
            items = favourites_service.get_favourites()
            return FavouritesListResponse.from_domain(items).model_dump()
        except FavouritesError as exc:
            ...
        except SonosDiscoveryError as exc:
            ...
```

The service resolves the IP internally.

### Current Codebase Reality (After Story 2.4)

The wiring in `tools/__init__.py` currently is:

```python
room_service = RoomService(DiscoveryAdapter())
register_system(app, config, room_service)

sonos_service = SonosService(room_service, SoCoAdapter(), config)
playback_service = PlaybackService(sonos_service=sonos_service)
register_playback(app, config, playback_service)

volume_service = VolumeService(sonos_service=sonos_service)
register_volume(app, config, volume_service)
```

Story 3.1 adds queue wiring after this. For story 3.2, add after any existing wiring:

```python
from soniq_mcp.services.favourites_service import FavouritesService
from soniq_mcp.tools.favourites import register as register_favourites
from soniq_mcp.tools.playlists import register as register_playlists

favourites_service = FavouritesService(room_service, SoCoAdapter())
register_favourites(app, config, favourites_service)
register_playlists(app, config, favourites_service)
```

A new `SoCoAdapter()` instance is fine — it is stateless and creates `soco.SoCo` objects on demand.

### Domain Model Shapes

Add to `src/soniq_mcp/domain/models.py`:

```python
@dataclass(frozen=True)
class Favourite:
    title: str
    uri: str
    meta: str | None = field(default=None)  # DIDL-Lite XML for play_uri


@dataclass(frozen=True)
class SonosPlaylist:
    title: str
    uri: str
    item_id: str | None = field(default=None)
```

### Response Schema Shapes

Add to `src/soniq_mcp/schemas/responses.py`:

```python
class FavouriteResponse(BaseModel):
    title: str
    uri: str

    @classmethod
    def from_domain(cls, fav: Favourite) -> "FavouriteResponse":
        return cls(title=fav.title, uri=fav.uri)


class FavouritesListResponse(BaseModel):
    items: list[FavouriteResponse]
    count: int

    @classmethod
    def from_domain(cls, items: list[Favourite]) -> "FavouritesListResponse":
        return cls(items=[FavouriteResponse.from_domain(f) for f in items], count=len(items))


class PlaylistResponse(BaseModel):
    title: str
    uri: str

    @classmethod
    def from_domain(cls, pl: SonosPlaylist) -> "PlaylistResponse":
        return cls(title=pl.title, uri=pl.uri)


class PlaylistsListResponse(BaseModel):
    items: list[PlaylistResponse]
    count: int

    @classmethod
    def from_domain(cls, items: list[SonosPlaylist]) -> "PlaylistsListResponse":
        return cls(items=[PlaylistResponse.from_domain(p) for p in items], count=len(items))
```

Note: `meta` is intentionally excluded from `FavouriteResponse` — it's an internal detail used by `play_favourite` and not needed in the list response exposed to clients.

### Error Taxonomy Extension

Add to `src/soniq_mcp/domain/exceptions.py`:

```python
class FavouritesError(SoniqDomainError):
    """Raised when a Sonos favourites or playlists operation fails."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
```

Add to `src/soniq_mcp/schemas/errors.py`:

```python
@classmethod
def from_favourites_error(cls, exc: Exception) -> "ErrorResponse":
    return cls(
        error=str(exc),
        field="favourites",
        suggestion=(
            "Check that the Sonos system is reachable and has saved favourites or playlists. "
            "Use 'list_rooms' to verify the network is discoverable."
        ),
    )
```

### Tool Name Registry (for contract tests and tools_disabled)

| Tool name | Method | Hint type | Parameters |
|---|---|---|---|
| `list_favourites` | GET | `_READ_ONLY_TOOL_HINTS` | *(none)* |
| `play_favourite` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `uri: str` |
| `list_playlists` | GET | `_READ_ONLY_TOOL_HINTS` | *(none)* |
| `play_playlist` | MUTATE | `_CONTROL_TOOL_HINTS` | `room: str`, `uri: str` |

### Testing Requirements

- Use the existing test fakes pattern — inject a fake `FavouritesService` with controlled return values and side effects.
- For `test_soco_adapter_favourites.py`, mock `zone.music_library.get_sonos_favorites` and `zone.music_library.get_music_library_information` using `unittest.mock.MagicMock`. Also mock `zone.play_uri`, `zone.clear_queue`, `zone.add_uri_to_queue`, `zone.play_from_queue`.
- For `test_favourites_service.py`, use a fake `RoomService` that returns a dummy `Room` or raises `RoomNotFoundError`. Use a fake `SoCoAdapter` with controlled returns.
- Contract tests: follow the exact same pattern as `test_playback_tool_schemas.py` and `test_volume_tool_schemas.py`.
- Run `make test` before marking done; all existing tests must still pass plus new coverage.
  [Source: `_bmad-output/planning-artifacts/architecture.md#File-Organization-Patterns`]

### Files to Create

```text
src/soniq_mcp/services/favourites_service.py
src/soniq_mcp/tools/favourites.py
src/soniq_mcp/tools/playlists.py
tests/unit/adapters/test_soco_adapter_favourites.py
tests/unit/services/test_favourites_service.py
tests/unit/tools/test_favourites.py
tests/unit/tools/test_playlists.py
tests/contract/tool_schemas/test_favourites_tool_schemas.py
tests/contract/tool_schemas/test_playlists_tool_schemas.py
```

### Files to Modify

```text
src/soniq_mcp/domain/exceptions.py          (add FavouritesError)
src/soniq_mcp/domain/models.py              (add Favourite, SonosPlaylist)
src/soniq_mcp/adapters/soco_adapter.py      (add 4 favourites/playlists methods)
src/soniq_mcp/schemas/errors.py             (add from_favourites_error)
src/soniq_mcp/schemas/responses.py          (add FavouriteResponse, FavouritesListResponse, PlaylistResponse, PlaylistsListResponse)
src/soniq_mcp/tools/__init__.py             (wire FavouritesService + register_favourites + register_playlists)
```

### Story 3.1 Dependency Note

Story 3.2 can be implemented independently of story 3.1 (queue management) — they are parallel capability areas with no code dependencies. However, both stories are in the same epic and the wiring patterns are identical. If story 3.1 has been implemented before this story, use the `QueueService` wiring as a concrete reference pattern (same constructor shape: `service(room_service, adapter)`).

If story 3.1 is NOT yet implemented, the wiring in `tools/__init__.py` still follows the established pattern from story 2.4 — just add the favourites wiring at the end of `register_all`.

### Previous Story Intelligence

- Story 2.4 established the shared `SoCoAdapter` + service layer boundary. Story 3.2 follows the same architectural shape: `FavouritesService(room_service, adapter)` mirrors the constructor pattern.
- All existing tool schemas, error mappings, and response shapes must remain unchanged.
- The `_make_zone` static method in `SoCoAdapter` is the correct factory for new methods; do not inline `soco.SoCo(ip)` directly.
- Tool handlers must guard with `assert_tool_permitted(tool_name, config)` at the start of each handler body — matches the pattern in `tools/playback.py`.
- `_READ_ONLY_TOOL_HINTS` and `_CONTROL_TOOL_HINTS` are defined at module level in each tools file — duplicate them in `favourites.py` and `playlists.py` (do not import from `playback.py`).

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-32-Access-and-Play-Favourites-and-Playlists`
- Architecture structure: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries`
- Naming and pattern rules: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Consistency-Rules`
- Previous story: `_bmad-output/implementation-artifacts/3-1-manage-the-sonos-queue.md`
- Pattern reference tool module: `src/soniq_mcp/tools/playback.py`
- Pattern reference service: `src/soniq_mcp/services/room_service.py`
- Pattern reference adapter: `src/soniq_mcp/adapters/soco_adapter.py`

## Dev Agent Record

### Agent Model Used

gpt-5-codex

### Debug Log References

- Fixed `FakeRoomService` in test using `rooms if rooms is not None else [ROOM]` (not `rooms or [ROOM]`) to correctly handle empty list case.
- Added `list_favourites`, `play_favourite`, `list_playlists`, `play_playlist` to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py` so `tools_disabled` validation accepts them.
- Follow-up fix for review finding: `FavouritesService.play_favourite()` now resolves DIDL metadata by URI before delegating to `SoCoAdapter.play_favourite()` when the caller does not supply `meta`.
- Replaced the placeholder `assert True` service test with a real adapter-call assertion and added metadata-resolution coverage to prevent regressions.

### Completion Notes List

- Implemented `FavouritesError` domain exception and `ErrorResponse.from_favourites_error` factory.
- Added `Favourite` and `SonosPlaylist` frozen dataclasses to domain models.
- Added `FavouriteResponse`, `FavouritesListResponse`, `PlaylistResponse`, `PlaylistsListResponse` Pydantic schemas.
- Extended `SoCoAdapter` with `get_favourites`, `play_favourite`, `get_playlists`, `play_playlist` — all wrap SoCo exceptions in `FavouritesError`.
- Created `FavouritesService` with IP resolution via `room_service.list_rooms()[0]`; raises `FavouritesError` on empty room list.
- Created `tools/favourites.py` and `tools/playlists.py` following playback.py patterns exactly.
- Wired single `FavouritesService` instance into `tools/__init__.py`.
- Follow-up review fix: `play_favourite` now looks up the favourite by URI and reuses its stored DIDL metadata so favourites that require metadata still satisfy AC2.
- Strengthened favourites service and tool tests to assert metadata lookup and concrete adapter/service calls instead of placeholder coverage.
- Full regression after the follow-up fix: 464 tests passed, 3 pre-existing integration skips.

### File List

- `src/soniq_mcp/domain/exceptions.py` (modified — added FavouritesError)
- `src/soniq_mcp/domain/models.py` (modified — added Favourite, SonosPlaylist)
- `src/soniq_mcp/schemas/errors.py` (modified — added from_favourites_error)
- `src/soniq_mcp/schemas/responses.py` (modified — added FavouriteResponse, FavouritesListResponse, PlaylistResponse, PlaylistsListResponse)
- `src/soniq_mcp/adapters/soco_adapter.py` (modified — added 4 favourites/playlists methods)
- `src/soniq_mcp/services/favourites_service.py` (created)
- `src/soniq_mcp/tools/favourites.py` (created)
- `src/soniq_mcp/tools/playlists.py` (created)
- `src/soniq_mcp/tools/__init__.py` (modified — wired FavouritesService + register_favourites + register_playlists)
- `src/soniq_mcp/config/models.py` (modified — added 4 new tool names to KNOWN_TOOL_NAMES)
- `tests/unit/adapters/test_soco_adapter_favourites.py` (created)
- `tests/unit/services/test_favourites_service.py` (created)
- `tests/unit/tools/test_favourites.py` (created)
- `tests/unit/tools/test_playlists.py` (created)
- `tests/contract/tool_schemas/test_favourites_tool_schemas.py` (created)
- `tests/contract/tool_schemas/test_playlists_tool_schemas.py` (created)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified — status updated)
