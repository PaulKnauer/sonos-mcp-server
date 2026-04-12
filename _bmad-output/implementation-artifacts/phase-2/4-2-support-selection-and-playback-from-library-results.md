# Story 4.2: Support selection and playback from library results

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to select a browsed library item and play it in a room,
so that library discovery leads directly to listening actions.

## Acceptance Criteria

1. Given a valid normalized library item, when the client selects it for playback in a target room, then the service resolves the selection into a playable action and returns the resulting normalized playback confirmation.
2. Given an invalid or unsupported library selection, when the client invokes the selection flow, then the service returns a typed validation or unsupported-operation error and no unintended playback begins.

## Tasks / Subtasks

- [x] Add a typed library-playback contract without breaking the Story 4.1 browse shape (AC: 1, 2)
  - [x] Add `LibraryUnsupportedOperationError(LibraryError)` to `src/soniq_mcp/domain/exceptions.py` for selections that are syntactically valid but not safely playable
  - [x] Add a `LibraryPlaybackResponse` model to `src/soniq_mcp/schemas/responses.py`
  - [x] Ensure the playback confirmation includes stable `snake_case` fields:
    - [x] `status`
    - [x] `room`
    - [x] `title`
    - [x] `item_id`
    - [x] `uri`
  - [x] Preserve the existing `LibraryItemResponse` and `LibraryBrowseResponse` contracts from Story 4.1 without breaking field names or semantics
  - [x] Extend `ErrorResponse.from_library_error(exc)` guidance so unsupported or non-playable selections point users back to `browse_library`

- [x] Extend `SoCoAdapter` with library-item playback support using the existing playback boundary patterns (AC: 1, 2)
  - [x] Add `play_library_item(ip_address: str, uri: str) -> None` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Keep all `soco` imports and Sonos object handling inside `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Reuse the established queue-oriented playback pattern already used by `play_playlist` unless a verified local-library path requires a different adapter-local implementation
  - [x] Keep any fallback behavior adapter-local; do not leak raw SoCo objects, metadata XML, or transport-specific details to the service/tool layer
  - [x] Wrap SoCo playback failures in `LibraryError`
  - [x] Do not synthesize playback URIs from `item_id` alone or introduce a local shadow index/cache in this story

- [x] Extend `LibraryService` with selection validation and playback orchestration (AC: 1, 2)
  - [x] Add `play_library_item(...)` to `src/soniq_mcp/services/library_service.py`
  - [x] Resolve the target room through `RoomService.get_room(room)`; do not accept client-supplied IP addresses
  - [x] Validate selection inputs against the normalized Story 4.1 browse contract
  - [x] Reject malformed inputs such as blank `uri`, blank `title` when supplied, non-string `item_id`, or invalid boolean-like `is_playable` values
  - [x] Reject non-playable or ambiguous selections with `LibraryUnsupportedOperationError`
  - [x] Preserve the intentional Story 4.1 split:
    - [x] `item_id` remains useful for browse/drill-down identity
    - [x] playback uses a queueable/playable `uri`
  - [x] Return a structured confirmation payload rather than a bare string/dict with ad hoc fields
  - [x] Do not broaden `browse_library` scope or re-query the whole library by title just to make playback work

- [x] Add a stable MCP tool for playing a normalized library selection (AC: 1, 2)
  - [x] Extend `src/soniq_mcp/tools/library.py`
  - [x] Register a control tool named `play_library_item`
  - [x] Keep tool handlers thin: permission guard first, service call second, schema/error translation only
  - [x] If FastMCP coercion would hide invalid boolean/string selection inputs, use the established raw-input `Annotated[object, Field(json_schema_extra=...)]` pattern so validation still happens in the service layer
  - [x] Catch `RoomNotFoundError`, `SonosDiscoveryError`, and `LibraryError` and map them through `ErrorResponse`
  - [x] Preserve `browse_library` as read-only and do not collapse browse + playback into one overloaded tool

- [x] Wire the library playback capability into registration and tool exposure controls (AC: 1, 2)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to register the new tool with the existing `LibraryService`
  - [x] Add `play_library_item` to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [x] Preserve stable registration order and parity across `stdio` and HTTP transports
  - [x] Keep the `library` capability family isolated; do not fold this into favourites, playlists, queue, or generic playback modules

- [x] Add regression coverage for selection validation and playback behavior (AC: 1, 2)
  - [x] Extend `tests/unit/services/test_library_service.py`
  - [x] Extend `tests/unit/adapters/test_soco_adapter_library.py`
  - [x] Extend `tests/unit/tools/test_library.py`
  - [x] Extend `tests/contract/tool_schemas/test_library_tool_schemas.py`
  - [x] Extend `tests/contract/error_mapping/test_error_schemas.py`
  - [x] Extend `tests/integration/transports/test_http_bootstrap.py`
  - [x] Cover at least:
    - [x] successful playback of a valid normalized playable selection
    - [x] rejection of a non-playable selection from browse results
    - [x] rejection of missing/blank `uri`
    - [x] room lookup failure
    - [x] adapter failure mapping without leaking raw SoCo details
    - [x] transport parity for the new tool
    - [x] no regression to the existing bounded browse schema/behavior

## Dev Notes

### Story intent

- Story 4.2 is the playback half of Epic 4. Story 4.1 established bounded browse-only access; Story 4.2 must convert a normalized browse result into a safe listening action.
- Story 4.2 does **not** expand browse categories, pagination semantics, or direct-vs-agent documentation parity. Those concerns remain in Story 4.1 and Story 4.3 respectively.
- The accepted input shape for this story should come from the normalized `browse_library` response, not from raw SoCo objects or new out-of-band lookup formats.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-42-Support-selection-and-playback-from-library-results`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/4-1-add-bounded-local-music-library-browsing.md`]

### Previous Story Intelligence (Story 4.1)

- Story 4.1 deliberately made the browse response selection-ready by normalizing `title`, `item_type`, `item_id`, `uri`, `is_browsable`, and `is_playable`; Story 4.2 should consume that contract rather than redesign it.
- Story 4.1 review follow-ups tightened validation around malformed and category-incompatible `parent_id` values and around pagination behavior. Do not reopen browse behavior just to add playback.
- Current `LibraryService` already validates category, pagination, and drill-down identity. Story 4.2 should add a separate playback path rather than intertwining playback state into browse validation.
- The library capability family already exists in `src/soniq_mcp/tools/library.py`, `src/soniq_mcp/services/library_service.py`, and `SoCoAdapter.browse_library(...)`; extend those exact files first.
  [Source: `_bmad-output/implementation-artifacts/phase-2/4-1-add-bounded-local-music-library-browsing.md#Completion-Notes-List`]
  [Source: `src/soniq_mcp/tools/library.py`]
  [Source: `src/soniq_mcp/services/library_service.py`]
  [Source: `src/soniq_mcp/adapters/soco_adapter.py`]

### Current repo state to build on

- Existing playback patterns already split inventory from playback:
  - favourites inventory returns normalized entries and playback uses `uri`
  - playlist lifecycle targets `item_id`, while playlist playback uses `uri`
- That same split is the safest pattern for library playback: keep browse identity and playback URI separate and explicit.
- `SoCoAdapter.play_playlist(...)` already demonstrates the current queue-oriented playback pattern (`clear_queue` + `add_uri_to_queue` + `play_from_queue(0)`).
- `FavouritesService` and `PlaylistService` show the expected service-layer orchestration pattern: resolve room through `RoomService`, validate inputs locally, then delegate a single playback action to the adapter.
  [Source: `src/soniq_mcp/services/favourites_service.py`]
  [Source: `src/soniq_mcp/services/playlist_service.py`]
  [Source: `src/soniq_mcp/tools/favourites.py`]
  [Source: `src/soniq_mcp/tools/playlists.py`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-3-preserve-existing-playlist-playback-alongside-playlist-lifecycle-support.md`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- Tool handlers stay thin and transport-facing only.
- Service code owns validation, room resolution, and orchestration decisions.
- `src/soniq_mcp/adapters/soco_adapter.py` remains the only direct SoCo integration boundary.
- Keep the phase-2 implementation stateless. Do not add an application database, shadow library index, or long-lived cache for library items.
- Preserve stable `snake_case` request/response semantics and typed error mapping.
  [Source: `_bmad-output/planning-artifacts/architecture.md`]
  [Source: `_bmad-output/planning-artifacts/prd.md`]

### Implementation guidance

- Add exactly one new control capability for this story: `play_library_item`.
- Favor the same user mental model already established elsewhere in the repo:
  - browse/list operations expose normalized inventory
  - play operations consume a room plus a stable playback identifier
- Treat a library item as playable only when the normalized selection includes a non-empty `uri` and explicitly indicates `is_playable=true`.
- For selections that are browse-only containers, missing a usable `uri`, or otherwise ambiguous, fail safely with a typed unsupported-operation error and direct the user to browse deeper.
- Do not try to recover by fuzzy title lookup, by rebuilding raw SoCo music-library objects from incomplete client input, or by converting `item_id` into a playback URI with ad hoc rules.
- Keep story scope focused on direct playback from a browsed selection. Do not add queue-management variants, shuffle semantics, or transport-specific documentation in this story.
  [Source: `src/soniq_mcp/domain/models.py`]
  [Source: `src/soniq_mcp/schemas/responses.py`]
  [Source: `src/soniq_mcp/schemas/errors.py`]
  [Source: `_bmad-output/planning-artifacts/research/technical-soco-capability-gap-research-2026-04-02.md`]

### Latest technical information

- The repo dependency floor is `mcp[cli]>=1.26.0` and `soco>=0.30.14`, and `uv.lock` currently resolves `mcp==1.26.0` and `soco==0.30.14`. Build against the locked surface in this story; do not turn Story 4.2 into a dependency-upgrade task.
- Official MCP Python SDK packaging guidance still recommends `uv add "mcp[cli]"`, which matches the current project setup.
- Official SoCo music-library docs still document `get_music_library_information(...)` and `browse_by_idstring(...)` for browsing, and distinguish imported library playlists from Sonos playlists. Inference: local-library playback should stay in the library capability family and should not be rerouted through playlist lifecycle APIs.
- There is a newer upstream `mcp` release available than the project lock. Unless the implementation is blocked by a verified SDK issue, keep Story 4.2 on the repo’s pinned dependency set.
  [Source: `pyproject.toml`]
  [Source: `uv.lock`]
  [Source: `https://pypi.org/project/mcp/1.26.0/`]
  [Source: `https://docs.python-soco.com/en/v0.26.3/api/soco.music_library.html`]

### Testing requirements

- Keep default automated validation hardware-independent with fakes/mocks around the adapter boundary.
- Add service tests that prove unsupported selections fail before adapter playback is attempted.
- Add adapter tests that lock the chosen queue/play implementation and error wrapping behavior.
- Add contract tests for the new tool name and parameter/response schema.
- Keep HTTP bootstrap parity current so the new tool appears across both supported transports.
- Preserve Story 4.1 browse tests; this story should add playback coverage without weakening the browse guarantees that are already in place.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/unit/services/test_library_service.py`]
  [Source: `tests/unit/adapters/test_soco_adapter_library.py`]
  [Source: `tests/unit/tools/test_library.py`]
  [Source: `tests/contract/tool_schemas/test_library_tool_schemas.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]

### Project Structure Notes

- Expected source files to modify:
  - `src/soniq_mcp/tools/library.py`
  - `src/soniq_mcp/services/library_service.py`
  - `src/soniq_mcp/adapters/soco_adapter.py`
  - `src/soniq_mcp/domain/exceptions.py`
  - `src/soniq_mcp/schemas/responses.py`
  - `src/soniq_mcp/schemas/errors.py`
  - `src/soniq_mcp/tools/__init__.py`
  - `src/soniq_mcp/config/models.py`
- Expected tests to modify:
  - `tests/unit/services/test_library_service.py`
  - `tests/unit/adapters/test_soco_adapter_library.py`
  - `tests/unit/tools/test_library.py`
  - `tests/contract/tool_schemas/test_library_tool_schemas.py`
  - `tests/contract/error_mapping/test_error_schemas.py`
  - `tests/integration/transports/test_http_bootstrap.py`
- No `project-context.md` file was present in the repo during story creation, so planning artifacts plus the existing Phase 2 implementation files are the authoritative context set for this story.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-42-Support-selection-and-playback-from-library-results`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-41-Add-bounded-local-music-library-browsing`]
- [Source: `_bmad-output/planning-artifacts/architecture.md`]
- [Source: `_bmad-output/planning-artifacts/prd.md`]
- [Source: `_bmad-output/planning-artifacts/research/technical-soco-capability-gap-research-2026-04-02.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/4-1-add-bounded-local-music-library-browsing.md`]
- [Source: `src/soniq_mcp/tools/library.py`]
- [Source: `src/soniq_mcp/services/library_service.py`]
- [Source: `src/soniq_mcp/adapters/soco_adapter.py`]
- [Source: `src/soniq_mcp/services/favourites_service.py`]
- [Source: `src/soniq_mcp/services/playlist_service.py`]
- [Source: `src/soniq_mcp/tools/favourites.py`]
- [Source: `src/soniq_mcp/tools/playlists.py`]
- [Source: `src/soniq_mcp/domain/models.py`]
- [Source: `src/soniq_mcp/schemas/responses.py`]
- [Source: `src/soniq_mcp/schemas/errors.py`]
- [Source: `src/soniq_mcp/config/models.py`]
- [Source: `pyproject.toml`]
- [Source: `uv.lock`]
- [Source: `https://pypi.org/project/mcp/1.26.0/`]
- [Source: `https://docs.python-soco.com/en/v0.26.3/api/soco.music_library.html`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Story created from Epic 4 planning artifacts, Story 4.1 implementation notes, current library/playback code paths, and locked dependency metadata.
- Confirmed the repo already has `browse_library` only; Story 4.2 should extend the existing `library` capability family instead of creating a second library module.
- Confirmed the current project lock is `mcp==1.26.0` and `soco==0.30.14`.
- Confirmed the current normalized `LibraryItem` contract is the intended selection input shape for this story.
- Confirmed existing playback patterns split inventory identifiers from playback URIs for favourites and playlists.
- Red phase: added failing unit, contract, schema, adapter, tool, and HTTP parity tests for `play_library_item`; initial collection failed because `LibraryUnsupportedOperationError` and `LibraryPlaybackResponse` did not yet exist.
- Implemented `LibraryUnsupportedOperationError`, `LibraryPlaybackResponse`, `SoCoAdapter.play_library_item(...)`, `LibraryService.play_library_item(...)`, and the `play_library_item` MCP tool.
- Preserved Story 4.1 browse contracts and added `play_library_item` to `KNOWN_TOOL_NAMES` for exposure-control validation.
- Validation: `uv run pytest -q tests/unit/services/test_library_service.py tests/unit/adapters/test_soco_adapter_library.py tests/unit/tools/test_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py` passed (`142 passed`).
- Validation: `uv run ruff check src/soniq_mcp/domain/exceptions.py src/soniq_mcp/schemas/responses.py src/soniq_mcp/adapters/soco_adapter.py src/soniq_mcp/services/library_service.py src/soniq_mcp/tools/library.py src/soniq_mcp/config/models.py tests/unit/services/test_library_service.py tests/unit/adapters/test_soco_adapter_library.py tests/unit/tools/test_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py` passed.
- Validation: `uv run pytest -q` passed (`1384 passed, 3 skipped`).
- Tightened `ErrorResponse.from_library_error(...)` guidance so unsupported selections explicitly direct callers back to `browse_library` and to choosing a playable item.
- Code review follow-up: tightened `play_library_item` so it now rejects missing `item_id` values and rejects non-library URI schemes even when callers spoof `is_playable=true`.
- Code review follow-up: switched `title` and `item_id` to raw-input tool parameters so malformed payloads reach service-layer validation instead of being pre-validated by FastMCP/Pydantic.
- Validation: `uv run pytest -q tests/unit/services/test_library_service.py -k 'missing_item_id or non_library_uri' tests/unit/tools/test_library.py -k 'non_string_title_reaches_service_validation or non_string_item_id_reaches_service_validation'` passed (`2 passed`).
- Validation: `uv run pytest -q tests/unit/services/test_library_service.py tests/unit/adapters/test_soco_adapter_library.py tests/unit/tools/test_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py` passed (`146 passed`).
- Validation: `uv run ruff check src/soniq_mcp/services/library_service.py src/soniq_mcp/tools/library.py tests/unit/services/test_library_service.py tests/unit/tools/test_library.py` passed.
- Validation: `uv run pytest -q` passed (`1388 passed, 3 skipped`).

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added `play_library_item` as the single new control tool in the `library` capability family, using the normalized Story 4.1 browse contract as input.
- Added typed rejection for malformed and non-playable selections before adapter playback is attempted, preventing unintended playback on invalid inputs.
- Reused the existing queue-oriented playback pattern in `SoCoAdapter` to keep library playback aligned with established playlist behavior.
- Preserved browse schema stability while extending transport parity, tool schema coverage, response schema coverage, and error-mapping coverage for library playback.
- Full regression suite and lint checks passed; story is ready for code review.
- Addressed code-review findings by enforcing library-shaped selections in the service layer and by eliminating pre-service coercion for `title` and `item_id`.
- Story remains in review with the follow-up fixes applied and fully revalidated.

### File List

- _bmad-output/implementation-artifacts/phase-2/4-2-support-selection-and-playback-from-library-results.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- src/soniq_mcp/adapters/soco_adapter.py
- src/soniq_mcp/config/models.py
- src/soniq_mcp/domain/exceptions.py
- src/soniq_mcp/schemas/responses.py
- src/soniq_mcp/schemas/errors.py
- src/soniq_mcp/services/library_service.py
- src/soniq_mcp/tools/library.py
- tests/contract/error_mapping/test_error_schemas.py
- tests/contract/tool_schemas/test_library_tool_schemas.py
- tests/integration/transports/test_http_bootstrap.py
- tests/unit/adapters/test_soco_adapter_library.py
- tests/unit/schemas/test_responses.py
- tests/unit/services/test_library_service.py
- tests/unit/tools/test_library.py

### Change Log

- 2026-04-12: Implemented Story 4.2 local music-library selection playback with typed validation, a new `play_library_item` tool, adapter/service wiring, and full regression coverage.
- 2026-04-12: Addressed code-review findings for Story 4.2 by tightening library-selection validation and shifting `title`/`item_id` to raw-input tool handling.
