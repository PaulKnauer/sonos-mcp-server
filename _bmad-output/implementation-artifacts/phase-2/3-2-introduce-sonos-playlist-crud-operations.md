# Story 3.2: Introduce Sonos playlist CRUD operations

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to view, create, update, and delete Sonos playlists,
so that I can manage reusable listening collections from the same control surface.

## Acceptance Criteria

1. Given a reachable household with playlist support, when the client requests playlist inventory, then the service returns normalized playlist metadata for the household.
2. Given a valid supported playlist lifecycle request, when the client creates, updates, or deletes a playlist, then the service performs the requested operation through the playlist-service boundary and returns the resulting normalized playlist state or structured delete confirmation.
3. Given an invalid playlist identifier or an unsupported household playlist mutation, when the client invokes the playlist lifecycle tool, then the service returns a typed validation or unsupported-operation error.

## Tasks / Subtasks

- [x] Split playlist ownership into a dedicated capability boundary (AC: 1, 2, 3)
  - [x] Create `src/soniq_mcp/services/playlist_service.py`
  - [x] Move playlist inventory and playback ownership out of `FavouritesService` and into `PlaylistService`
  - [x] Keep `FavouritesService` focused on favourites only; do not leave playlist CRUD as an extension of that service
  - [x] Preserve the existing playlist playback tool names and playback flow while moving the underlying orchestration boundary

- [x] Add playlist lifecycle domain primitives and normalized MCP schemas (AC: 1, 2, 3)
  - [x] Add `PlaylistError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [x] Add `PlaylistValidationError(PlaylistError)` for malformed identifiers, invalid titles, and invalid update payloads
  - [x] Add `PlaylistUnsupportedOperationError(PlaylistError)` for households or library paths that cannot perform a requested lifecycle mutation
  - [x] Reuse `SonosPlaylist` in `src/soniq_mcp/domain/models.py` as the normalized playlist record and keep `item_id` populated for lifecycle targeting
  - [x] Extend `PlaylistResponse` / `PlaylistsListResponse` in `src/soniq_mcp/schemas/responses.py` so playlist inventory exposes `title`, `uri`, and `item_id`
  - [x] Add structured success responses for create/update and a structured delete confirmation response
  - [x] Add `ErrorResponse.from_playlist_error(exc)` to `src/soniq_mcp/schemas/errors.py`

- [x] Extend `SoCoAdapter` with Sonos playlist lifecycle methods using current SoCo APIs (AC: 1, 2, 3)
  - [x] Keep all `soco` imports and Sonos object handling inside `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Preserve and reuse the existing playlist inventory and playback adapter methods rather than duplicating them elsewhere
  - [x] Add adapter support for:
    - [x] household playlist inventory lookup by IP address
    - [x] playlist lookup by `item_id` (and title only as a bounded fallback when needed)
    - [x] playlist creation
    - [x] playlist content replacement/update
    - [x] playlist deletion
  - [x] Use the documented SoCo playlist surface where applicable:
    - [x] `get_sonos_playlists()` / `get_music_library_information("sonos_playlists")`
    - [x] `create_sonos_playlist(title)`
    - [x] `create_sonos_playlist_from_queue(title)` when queue-backed creation is the chosen bounded implementation
    - [x] `remove_sonos_playlist(sonos_playlist)`
    - [x] `clear_sonos_playlist(sonos_playlist, update_id=0)`
    - [x] `add_item_to_sonos_playlist(queueable_item, sonos_playlist)`
    - [x] `reorder_sonos_playlist(...)` / helper methods when needed for deterministic updates
    - [x] `get_sonos_playlist_by_attr(attr_name, match)` for stable identifier resolution
  - [x] Wrap SoCo failures in `PlaylistError` or `PlaylistUnsupportedOperationError`
  - [x] Never leak raw `DidlPlaylistContainer`, queue items, or SoCo exceptions outside the adapter boundary

- [x] Implement `PlaylistService` validation and orchestration rules (AC: 1, 2, 3)
  - [x] Constructor: `PlaylistService(room_service: object, adapter: object)`
  - [x] Implement:
    - [x] `list_playlists() -> list[SonosPlaylist]`
    - [x] `play_playlist(room_name: str, uri: str) -> None`
    - [x] `create_playlist(...) -> SonosPlaylist`
    - [x] `update_playlist(...) -> SonosPlaylist`
    - [x] `delete_playlist(playlist_id: str) -> str | dict`
  - [x] Resolve household reachability through `RoomService` instead of trusting client-supplied IPs
  - [x] Treat `item_id` as the canonical lifecycle identifier; do not rely on playlist title as the primary target key
  - [x] Validate blank or malformed playlist identifiers before adapter calls
  - [x] Validate title inputs before adapter writes and reject empty or whitespace-only titles with `PlaylistValidationError`
  - [x] Keep playlist update semantics bounded and explicit:
    - [x] Prefer replacing playlist contents from an existing room queue rather than inventing an unbounded free-form track-editing payload in this story
    - [x] If queue-backed update is used, validate the source room and require a non-empty queue before mutation
  - [x] Return `PlaylistValidationError` for missing or unknown playlist ids
  - [x] Return `PlaylistUnsupportedOperationError` for truly unsupported household mutations rather than generic operation errors

- [x] Expand the public playlist MCP tool surface without breaking existing playback behavior (AC: 1, 2, 3)
  - [x] Update `src/soniq_mcp/tools/playlists.py` so it depends on `PlaylistService`, not `FavouritesService`
  - [x] Preserve existing stable tool names:
    - [x] `list_playlists()`
    - [x] `play_playlist(room: str, uri: str)`
  - [x] Add stable lifecycle tool names:
    - [x] `create_playlist(...)`
    - [x] `update_playlist(...)`
    - [x] `delete_playlist(playlist_id: str)`
  - [x] Use `_READ_ONLY_TOOL_HINTS` for listing and `_CONTROL_TOOL_HINTS` for create/update
  - [x] Mark `delete_playlist` as destructive in its tool annotations
  - [x] Keep tool handlers thin: permission checks, service call, response conversion, and error translation only
  - [x] Catch `PlaylistError`, `PlaylistValidationError`, `PlaylistUnsupportedOperationError`, `RoomNotFoundError`, and `SonosDiscoveryError` and map them through `ErrorResponse`

- [x] Wire the capability into registration and configuration (AC: 2, 3)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to construct and register `PlaylistService`
  - [x] Update `src/soniq_mcp/config/models.py` to include the new playlist lifecycle tool names in `KNOWN_TOOL_NAMES`
  - [x] Preserve registration order and transport parity across `stdio` and HTTP
  - [x] Do not move playlist lifecycle work into `SonosService`, `QueueService`, or `FavouritesService`

- [x] Add automated regression coverage for playlist lifecycle behavior (AC: 1, 2, 3)
  - [x] Add `tests/unit/adapters/test_soco_adapter_playlists.py`
  - [x] Add `tests/unit/services/test_playlist_service.py`
  - [x] Update `tests/unit/tools/test_playlists.py`
  - [x] Update `tests/contract/tool_schemas/test_playlists_tool_schemas.py`
  - [x] Extend `tests/contract/error_mapping/test_error_schemas.py` for playlist lifecycle errors
  - [x] Update any response-schema tests affected by adding `item_id` to playlist responses
  - [x] Cover at least:
    - [x] empty playlist inventory
    - [x] normalized playlist list output with `item_id`
    - [x] create flow
    - [x] update flow
    - [x] delete flow
    - [x] blank playlist-id validation
    - [x] unknown playlist-id validation
    - [x] unsupported mutation mapping
    - [x] preservation of existing `play_playlist` behavior
    - [x] SoCo failure wrapping without leaking library details
- [x] Run the targeted playlist suites plus `make test` and `make lint`
- [x] Defer public playlist rename support until a supported dependency or alternate Sonos integration path is verified

### Review Findings

- [x] [Review][Patch] Adapter lookup suppresses real SoCo/library failures and misreports them as unknown playlist IDs [`src/soniq_mcp/adapters/soco_adapter.py:329`]
- [x] [Review][Patch] Playlist lifecycle targeting breaks for inventory entries that expose `item_id=None`; the required bounded title fallback is missing [`src/soniq_mcp/adapters/soco_adapter.py:329`]
- [x] [Review][Patch] `update_playlist` clears the saved playlist before copying items and can leave it partially destroyed on mid-copy failure [`src/soniq_mcp/adapters/soco_adapter.py:284`]
- [x] [Review][Patch] `create_playlist` and `rename_playlist` validate titles but still pass the untrimmed input through to the adapter [`src/soniq_mcp/services/playlist_service.py:96`]
- [x] [Review][Patch] `update_playlist` copies only the first 200 queued tracks, silently truncating longer queues [`src/soniq_mcp/adapters/soco_adapter.py:278`]
- [x] [Review][Patch] `rename_playlist` is still registered as a normal lifecycle tool, but the adapter unconditionally raises `PlaylistUnsupportedOperationError`, so valid rename requests can never satisfy AC2 [`src/soniq_mcp/adapters/soco_adapter.py:235`]

## Dev Notes

### Story intent

- This story introduces the playlist lifecycle capability family that Epic 3 adds on top of the existing playlist playback surface.
- Story 3.1 already established the Epic 3 pattern: a dedicated capability service, normalized domain objects, typed errors, thin tools, and adapter-only SoCo access. Story 3.2 should mirror that shape for playlists.
- Story 3.3 will verify that legacy playlist playback remains stable after lifecycle support lands, so Story 3.2 must preserve that behavior rather than postponing compatibility work.
- Playlist rename is intentionally out of committed Story 3.2 scope because the current supported `SoCo` stack does not expose a clean first-class rename capability. Future rename work should be handled as a separate investigation or follow-up story.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-32-Introduce-Sonos-playlist-CRUD-operations`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-33-Preserve-existing-playlist-playback-alongside-playlist-lifecycle-support`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md`]

### Current repo state to build on

- Playlist inventory and playback currently live in `tools/playlists.py`, `FavouritesService`, and the playlist-related methods inside `SoCoAdapter`.
- `SonosPlaylist` already exists in the domain layer and already contains the lifecycle-relevant `item_id`, but the MCP response model currently drops that field.
- `tools/__init__.py` currently wires `register_playlists(app, config, favourites_service)`, which is the ownership boundary this story should correct.
- Queue operations already exist and can provide a bounded source of playlist contents for create/update flows if the story chooses queue-backed mutations.
  [Source: `src/soniq_mcp/tools/playlists.py`]
  [Source: `src/soniq_mcp/services/favourites_service.py`]
  [Source: `src/soniq_mcp/adapters/soco_adapter.py`]
  [Source: `src/soniq_mcp/domain/models.py`]
  [Source: `src/soniq_mcp/tools/__init__.py`]
  [Source: `src/soniq_mcp/tools/queue.py`]
  [Source: `src/soniq_mcp/services/queue_service.py`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- `tools/playlists.py` owns MCP registration, permission checks, and success/error translation only.
- `services/playlist_service.py` owns playlist validation, household reachability checks, lifecycle orchestration, and compatibility-preserving playback orchestration.
- `src/soniq_mcp/adapters/soco_adapter.py` remains the only direct `SoCo` boundary.
- Do not call `SoCo` directly from tools, transports, or bootstrap code.
- Do not collapse playlist lifecycle work back into `FavouritesService` or `SonosService`.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]

### SoCo and library requirements

- The repo currently depends on `soco>=0.30.14`; implement against that version family unless the dependency is intentionally changed in this story.
- The current public SoCo playlist API documented for the supported version family includes:
  - `get_sonos_playlists()`
  - `create_sonos_playlist(title)`
  - `create_sonos_playlist_from_queue(title)`
  - `remove_sonos_playlist(sonos_playlist)`
  - `add_item_to_sonos_playlist(queueable_item, sonos_playlist)`
  - `reorder_sonos_playlist(...)`
  - `clear_sonos_playlist(sonos_playlist, update_id=0)`
  - `get_sonos_playlist_by_attr(attr_name, match)`
- The public docs do not advertise a top-level `rename_sonos_playlist(...)` helper. Treat rename as an implementation-risk item:
  - first verify the supported title-update path in the installed `soco>=0.30.14` code/docs
  - keep that logic entirely inside the adapter
  - if the dependency truly cannot rename playlists on the supported household, raise `PlaylistUnsupportedOperationError` rather than faking success or leaking a raw SoCo failure
- Prefer queue-backed create/update semantics over inventing a large new track-payload contract unless implementation proves that a smaller, more stable SoCo-backed mutation path already exists in the current dependency version.
  [Source: `pyproject.toml`]
  [Source: https://docs.python-soco.com/en/stable/api/soco.core.html]

### Response and error-shape requirements

- Preserve `snake_case` across tool parameters, response fields, config fields, and internal models.
- Playlist inventory responses must expose a stable identifier for lifecycle follow-up calls; use `item_id` in the normalized response shape.
- Keep successful lifecycle responses structured and deterministic rather than returning ad hoc dicts.
- Use typed playlist-domain errors for:
  - blank or malformed playlist identifiers
  - unknown playlist identifiers
  - blank or invalid titles
  - unsupported rename/update paths
  - Sonos/SoCo operational failures
- Never leak raw SoCo playlist objects, IP addresses, URLs, or filesystem paths through user-facing error text.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Format-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Process-Patterns`]
  [Source: `src/soniq_mcp/schemas/errors.py`]

### Implementation guidance

- Reuse `RoomService` for household reachability and target-room resolution; do not build a second discovery path.
- Follow the same implementation style established in Story 3.1:
  - thin tool handlers
  - service-owned validation and orchestration
  - adapter-owned SoCo interaction
  - Pydantic response models returned via `.model_dump()`
- Keep playlist lifecycle scope bounded:
  - inventory, create, update, and delete are in scope
  - broad local-library browsing and arbitrary free-form playlist editing are not
  - preserve current playlist playback behavior rather than redesigning it
- If update semantics are queue-backed, document that clearly in tool descriptions and examples so the later docs story can explain the difference between queue control and playlist persistence.
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md`]
  [Source: `src/soniq_mcp/tools/playlists.py`]
  [Source: `src/soniq_mcp/tools/queue.py`]

### Testing requirements

- Add unit coverage for playlist service validation and adapter-level playlist translation separately.
- Update contract tests to lock the new lifecycle tool names, parameters, annotations, and response shapes.
- Keep default automated validation hardware-independent by using fakes and mocks around the adapter boundary.
- Re-run the full regression suite after the targeted playlist suites pass.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/unit/tools/test_playlists.py`]
  [Source: `tests/contract/tool_schemas/test_playlists_tool_schemas.py`]
  [Source: `tests/unit/services/test_favourites_service.py`]

### Project Structure Notes

- New source file expected:
  - `src/soniq_mcp/services/playlist_service.py`
- Existing source files expected to change:
  - `src/soniq_mcp/tools/playlists.py`
  - `src/soniq_mcp/tools/__init__.py`
  - `src/soniq_mcp/services/favourites_service.py`
  - `src/soniq_mcp/adapters/soco_adapter.py`
  - `src/soniq_mcp/domain/exceptions.py`
  - `src/soniq_mcp/schemas/responses.py`
  - `src/soniq_mcp/schemas/errors.py`
  - `src/soniq_mcp/config/models.py`
- New or updated test files expected:
  - `tests/unit/adapters/test_soco_adapter_playlists.py`
  - `tests/unit/services/test_playlist_service.py`
  - `tests/unit/tools/test_playlists.py`
  - `tests/contract/tool_schemas/test_playlists_tool_schemas.py`
  - `tests/contract/error_mapping/test_error_schemas.py`
- No dedicated UX document exists for this project; use PRD + architecture guidance for user-facing clarity and error semantics.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
  [Source: `_bmad-output/planning-artifacts/epics.md#UX-Design-Requirements`]

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-32-Introduce-Sonos-playlist-CRUD-operations`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-33-Preserve-existing-playlist-playback-alongside-playlist-lifecycle-support`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md`]
- [Source: `src/soniq_mcp/tools/playlists.py`]
- [Source: `src/soniq_mcp/services/favourites_service.py`]
- [Source: `src/soniq_mcp/adapters/soco_adapter.py`]
- [Source: `src/soniq_mcp/tools/__init__.py`]
- [Source: `src/soniq_mcp/domain/models.py`]
- [Source: `src/soniq_mcp/schemas/errors.py`]
- [Source: `src/soniq_mcp/tools/queue.py`]
- [Source: `src/soniq_mcp/services/queue_service.py`]
- [Source: `tests/unit/tools/test_playlists.py`]
- [Source: `tests/contract/tool_schemas/test_playlists_tool_schemas.py`]
- [Source: `tests/unit/services/test_favourites_service.py`]
- [Source: `pyproject.toml`]
- [Source: https://docs.python-soco.com/en/stable/api/soco.core.html]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Implemented `PlaylistService` as a dedicated capability service following the Story 3.1 pattern (AlarmService).
- Playlist ownership fully moved from `FavouritesService` to `PlaylistService`; FavouritesService now handles favourites only.
- Adapter's `get_playlists` and `play_playlist` now raise `PlaylistError` instead of `FavouritesError` — `test_soco_adapter_favourites.py` updated accordingly, playlist adapter tests moved to new `test_soco_adapter_playlists.py`.
- Rename is intentionally unsupported: SoCo 0.30.x does not expose a stable rename endpoint; `PlaylistUnsupportedOperationError` is raised and surfaces cleanly through `ErrorResponse.from_playlist_error`.
- Update uses queue-backed semantics: clears target playlist content then adds all tracks from the source room's queue. Source queue must be non-empty (validated at both service and adapter boundary).
- `PlaylistResponse` now exposes `item_id` for lifecycle follow-up calls; `PlaylistDeleteResponse` provides structured delete confirmation.
- Integration test for HTTP tool surface parity updated to include the 4 new tool names (55 tools total). Test method renamed to `test_http_server_exposes_all_expected_tools`.
- All 1312 tests pass; `make lint` clean.

### File List

- `src/soniq_mcp/services/playlist_service.py` (new)
- `src/soniq_mcp/domain/exceptions.py` (modified)
- `src/soniq_mcp/schemas/responses.py` (modified)
- `src/soniq_mcp/schemas/errors.py` (modified)
- `src/soniq_mcp/adapters/soco_adapter.py` (modified)
- `src/soniq_mcp/services/favourites_service.py` (modified)
- `src/soniq_mcp/tools/playlists.py` (modified)
- `src/soniq_mcp/tools/__init__.py` (modified)
- `src/soniq_mcp/config/models.py` (modified)
- `tests/unit/adapters/test_soco_adapter_playlists.py` (new)
- `tests/unit/adapters/test_soco_adapter_favourites.py` (modified)
- `tests/unit/services/test_playlist_service.py` (new)
- `tests/unit/services/test_favourites_service.py` (modified)
- `tests/unit/tools/test_playlists.py` (modified)
- `tests/contract/tool_schemas/test_playlists_tool_schemas.py` (modified)
- `tests/contract/error_mapping/test_error_schemas.py` (modified)
- `tests/integration/transports/test_http_bootstrap.py` (modified)

## Change Log

- 2026-04-11: Story implemented — introduced PlaylistService, playlist lifecycle tools (view/create/update/delete plus preserved playback), PlaylistError hierarchy, updated schemas, adapter, and all tests. 1312 tests pass, lint clean.
