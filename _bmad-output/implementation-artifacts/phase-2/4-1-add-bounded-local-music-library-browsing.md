# Story 4.1: Add bounded local music library browsing

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to browse the local Sonos music library through the MCP server,
so that I can discover playable content without leaving my AI workflow.

## Acceptance Criteria

1. Given a reachable household with a local music library, when the client requests a library browse operation, then the service returns normalized library results with bounded-result or pagination behavior.
2. Given a library with at least 1,000 items, when the client browses a large result set, then the service remains usable through pagination, bounded results, or continuation semantics and does not return an unbounded raw payload.

## Tasks / Subtasks

- [x] Add local-library domain primitives and MCP-facing schemas (AC: 1, 2)
  - [x] Add `LibraryError(SoniqDomainError)` to `src/soniq_mcp/domain/exceptions.py`
  - [x] Add `LibraryValidationError(LibraryError)` for malformed browse inputs such as unsupported categories, negative offsets, invalid limits, or malformed parent identifiers
  - [x] Add a frozen `LibraryItem` dataclass to `src/soniq_mcp/domain/models.py`
  - [x] Normalize at least these fields in `LibraryItem`:
    - [x] `title: str`
    - [x] `item_type: str`
    - [x] `item_id: str | None`
    - [x] `uri: str | None`
    - [x] `album_art_uri: str | None`
    - [x] `is_browsable: bool`
    - [x] `is_playable: bool`
  - [x] Add `LibraryBrowseResponse` and `LibraryItemResponse` to `src/soniq_mcp/schemas/responses.py`
  - [x] Ensure the browse response includes bounded-result metadata:
    - [x] `category`
    - [x] `parent_id`
    - [x] `items`
    - [x] `count`
    - [x] `start`
    - [x] `limit`
    - [x] `has_more`
    - [x] `next_start`
  - [x] Add `ErrorResponse.from_library_error(exc)` to `src/soniq_mcp/schemas/errors.py`
  - [x] Extend `tests/unit/schemas/test_responses.py` for the new library response shapes

- [x] Extend `SoCoAdapter` with bounded local music-library browse support (AC: 1, 2)
  - [x] Keep all `soco` imports and Sonos object handling inside `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Add adapter support for:
    - [x] top-level library category browsing by household IP address
    - [x] drill-down browsing into a browsable library container by `item_id`
    - [x] bounded pagination using explicit `start` and `limit`
  - [x] Implement against the current locked project dependency surface in `soco==0.30.14`:
    - [x] `zone.music_library.get_music_library_information(search_type, start=..., max_items=..., full_album_art_uri=False, complete_result=False)`
    - [x] `zone.music_library.browse_by_idstring(search_type, idstring, start=..., max_items=..., full_album_art_uri=False)` when drilling into a parent container
  - [x] Normalize supported library result objects into `LibraryItem`
  - [x] Never leak raw SoCo music-library objects or result containers outside the adapter boundary
  - [x] Wrap SoCo failures in `LibraryError`

- [x] Create `LibraryService` with bounded browse validation and orchestration (AC: 1, 2)
  - [x] Create `src/soniq_mcp/services/library_service.py`
  - [x] Constructor: `LibraryService(room_service: object, adapter: SoCoAdapter)`
  - [x] Implement `browse_library(category: str, start: int = 0, limit: int = 100, parent_id: str | None = None) -> dict | object`
  - [x] Resolve household reachability through `RoomService` rather than trusting user-supplied IP addresses
  - [x] Reuse one discovery snapshot per service operation; do not call discovery repeatedly inside one browse request
  - [x] Enforce a bounded limit with a hard maximum of 100 items per request
  - [x] Validate `start >= 0`
  - [x] Validate category against an explicit supported set before adapter calls
  - [x] Validate `parent_id` as a non-empty identifier when provided
  - [x] Return empty normalized result sets for valid-but-empty browse results
  - [x] Reserve library selection and playback behavior for Story 4.2; do not add playback here

- [x] Decide and implement the public library MCP tool surface (AC: 1, 2)
  - [x] Create `src/soniq_mcp/tools/library.py`
  - [x] Register a stable read-only browse tool:
    - [x] `browse_library(category: str, start: int = 0, limit: int = 100, parent_id: str | None = None)`
  - [x] Use read-only tool annotations
  - [x] Keep tool handlers thin: permission guard first, service call second, schema/error translation only
  - [x] Preserve raw service-layer validation for numeric parameters when needed; if FastMCP coercion would mask invalid browse inputs, use the established `Annotated[object, Field(json_schema_extra=...)]` pattern
  - [x] Catch `LibraryError` and `SonosDiscoveryError` and map them through `ErrorResponse`

- [x] Wire the library capability into registration and configuration (AC: 1, 2)
  - [x] Update `src/soniq_mcp/tools/__init__.py` to construct and register `LibraryService`
  - [x] Add `browse_library` to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [x] Preserve stable registration order and transport parity across `stdio` and HTTP
  - [x] Do not collapse library logic into `PlaylistService`, `FavouritesService`, or `SonosService`

- [x] Add automated regression coverage for bounded library browse behavior (AC: 1, 2)
  - [x] Add `tests/unit/adapters/test_soco_adapter_library.py`
  - [x] Add `tests/unit/services/test_library_service.py`
  - [x] Add `tests/unit/tools/test_library.py`
  - [x] Add `tests/contract/tool_schemas/test_library_tool_schemas.py`
  - [x] Extend `tests/contract/error_mapping/test_error_schemas.py` for library browse errors
  - [x] Update `tests/integration/transports/test_http_bootstrap.py` to include the new library tool
  - [x] Cover at least:
    - [x] bounded top-level browse results
    - [x] pagination metadata and `has_more` / `next_start` behavior
    - [x] drill-down browse via `parent_id`
    - [x] empty result sets
    - [x] unsupported category validation
    - [x] invalid `start` / `limit` validation
    - [x] SoCo failure mapping without leaking library details
  - [x] Run the targeted library suites plus the relevant full regression checks

## Dev Notes

### Story intent

- This is the first story in Epic 4 and it establishes the new `library` capability family.
- The goal is bounded browse-only access to the local Sonos music library.
- Story 4.1 does **not** include playback from library selections. That belongs to Story 4.2.
- Story 4.1 does **not** include direct/agent parity docs hardening. That belongs to Story 4.3.
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-4-Local-Music-Library-Access-and-Selection`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-41-Add-bounded-local-music-library-browsing`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-42-Support-selection-and-playback-from-library-results`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-43-Preserve-parity-for-library-access-across-direct-and-agent-mediated-usage`]

### Current repo state to build on

- There is currently no `tools/library.py` or `services/library_service.py`; this story creates the capability from scratch within the established phase-2 structure.
- `RoomService` already owns household discovery and room lookup and should remain the only discovery path used by the service layer.
- `SoCoAdapter` already groups capability-specific Sonos methods for favourites, playlists, alarms, grouping, inputs, and playback; library methods should be added to the same adapter rather than introducing a second Sonos adapter.
- Recent Epic 3 work hardened the pattern of thin tools, feature-specific services, typed domain errors, normalized response models, and HTTP/stdio parity tests. Reuse those patterns directly.
  [Source: `src/soniq_mcp/tools/__init__.py`]
  [Source: `src/soniq_mcp/services/room_service.py`]
  [Source: `src/soniq_mcp/adapters/soco_adapter.py`]
  [Source: `_bmad-output/implementation-artifacts/epic-3-retro-2026-04-12.md`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- `tools/library.py` owns MCP registration, permission checks, and response/error translation only.
- `services/library_service.py` owns browse validation, bounded result rules, category support, and household orchestration.
- `src/soniq_mcp/adapters/soco_adapter.py` remains the only direct `SoCo` integration boundary.
- Browsing tools must return bounded list structures with explicit pagination or continuation semantics.
- Raw SoCo music-library objects or result containers must not escape directly through MCP responses.
- Keep the capability area isolated; do not mix local library browsing into playlists, favourites, or generic media modules.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]

### SoCo and library requirements

- The project currently depends on `soco>=0.30.14`, and `uv.lock` resolves `soco==0.30.14`. Implement against that locked surface unless a later story explicitly upgrades the dependency.
- The available local music-library APIs confirmed in the project environment are:
  - `MusicLibrary.get_music_library_information(search_type, start=0, max_items=100, full_album_art_uri=False, search_term=None, subcategories=None, complete_result=False)`
  - `MusicLibrary.browse_by_idstring(search_type, idstring, start=0, max_items=100, full_album_art_uri=False)`
  - `MusicLibrary.browse(...)` also exists, but `browse_by_idstring(...)` is the cleaner drill-down path when you already have a normalized parent identifier
- Use the current SoCo music-library surface directly inside the adapter rather than inventing a local shadow index or local persistence layer.
- Keep browse behavior stateless and Sonos-backed. Do not add an application database or cache layer in this story.
  [Source: `pyproject.toml`]
  [Source: `uv.lock`]
  [Source: local `uv run python` introspection against `soco==0.30.14`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]

### Response and error-shape requirements

- Preserve `snake_case` across tool parameters, response fields, config fields, and internal models.
- Browsing/listing tools should return bounded list structures with explicit metadata rather than raw arrays with no pagination context.
- Library browse failures should distinguish:
  - malformed browse input
  - unsupported category or unsupported drill-down target
  - Sonos discovery/connectivity failure
  - Sonos library-operation failure
- Valid empty browse results should return a successful empty list response rather than an error.
- The normalized `LibraryItem` contract should be selection-ready for Story 4.2. Include enough stable metadata now so later playback selection does not require a breaking response rewrite.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Format-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]

### Implementation guidance

- Reuse `RoomService` to establish household reachability. Do not trust client-supplied IP addresses and do not create a separate discovery path for library browsing.
- Follow the same capability pattern used by `InputService`, `AlarmService`, and `PlaylistService`:
  - thin tool handlers
  - service-owned validation and orchestration
  - adapter-owned SoCo interaction
  - Pydantic response models returned via `.model_dump()`
- Use one explicit read-only tool for browsing in this story. Keep the surface small and predictable.
- Validate category, `start`, `limit`, and `parent_id` before adapter calls.
- Enforce a hard cap of 100 items per request. Do not expose unbounded result retrieval or `complete_result=True`.
- Favor deterministic top-level category browsing plus explicit drill-down via `parent_id`. Do not add fuzzy free-text search in this story unless required to satisfy a verified SoCo browse path without expanding scope.
- Keep playback selection out of scope here even if a returned library item appears playable; Story 4.1 is browse only.
  [Source: `src/soniq_mcp/tools/inputs.py`]
  [Source: `src/soniq_mcp/tools/alarms.py`]
  [Source: `src/soniq_mcp/tools/playlists.py`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Pattern-Examples`]

### Supported category guidance

- Use an explicit supported top-level category set and reject anything else with `LibraryValidationError`.
- Start with categories the current SoCo music-library API supports cleanly and that align with local library browsing, such as:
  - `artists`
  - `album_artists`
  - `albums`
  - `tracks`
  - `genres`
  - `composers`
- Keep the category set small and verified. Do not promise categories that have not been confirmed against the current SoCo library surface.
- Preserve the normalized `item_id` for drill-down into browsable containers where available.
  [Source: local `uv run python` introspection against `soco==0.30.14`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-41-Add-bounded-local-music-library-browsing`]

### Testing requirements

- Add unit coverage for service-level bounded browse validation separately from adapter-level SoCo translation.
- Add contract tests that lock the new tool name, parameter schema, and normalized response structure.
- Keep default automated validation hardware-independent by using fakes and mocks around the adapter boundary.
- Extend HTTP bootstrap parity so the new browse tool is visible across both supported transports.
- Reuse the existing test organization pattern:
  - adapter tests under `tests/unit/adapters/`
  - service tests under `tests/unit/services/`
  - tool tests under `tests/unit/tools/`
  - schema contract tests under `tests/contract/tool_schemas/`
- Make sure tests prevent accidental scope creep into playback or agent-parity docs before Stories 4.2 and 4.3.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/unit/adapters/test_soco_adapter_playlists.py`]
  [Source: `tests/unit/tools/test_playlists.py`]
  [Source: `tests/contract/tool_schemas/test_playlists_tool_schemas.py`]

### Project Structure Notes

- New source files expected:
  - `src/soniq_mcp/tools/library.py`
  - `src/soniq_mcp/services/library_service.py`
  - library-related extensions in `src/soniq_mcp/domain/exceptions.py`
  - library-related extensions in `src/soniq_mcp/domain/models.py`
  - library-related extensions in `src/soniq_mcp/schemas/responses.py`
  - library-related extensions in `src/soniq_mcp/schemas/errors.py`
  - registration/config updates in `src/soniq_mcp/tools/__init__.py` and `src/soniq_mcp/config/models.py`
- New test files expected:
  - `tests/unit/adapters/test_soco_adapter_library.py`
  - `tests/unit/services/test_library_service.py`
  - `tests/unit/tools/test_library.py`
  - `tests/contract/tool_schemas/test_library_tool_schemas.py`
- No dedicated UX artifact exists; use PRD + architecture guidance for user-facing clarity and bounded browse behavior.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-4-Local-Music-Library-Access-and-Selection`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-41-Add-bounded-local-music-library-browsing`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-42-Support-selection-and-playback-from-library-results`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]
- [Source: `src/soniq_mcp/tools/__init__.py`]
- [Source: `src/soniq_mcp/services/room_service.py`]
- [Source: `src/soniq_mcp/adapters/soco_adapter.py`]
- [Source: `src/soniq_mcp/config/models.py`]
- [Source: `src/soniq_mcp/schemas/responses.py`]
- [Source: `src/soniq_mcp/schemas/errors.py`]
- [Source: `src/soniq_mcp/domain/models.py`]
- [Source: `pyproject.toml`]
- [Source: `uv.lock`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Story created from Epic 4 planning artifacts, PRD FR69, and architecture library-boundary guidance.
- Confirmed the project currently has no `library.py` or `LibraryService`, so this story establishes the capability family from scratch.
- Confirmed the locked project dependency is `soco==0.30.14`.
- Confirmed via local `uv run python` introspection that `MusicLibrary.get_music_library_information(...)` and `browse_by_idstring(...)` are available in the project environment.
- Implemented `LibraryService`, `tools/library.py`, and `SoCoAdapter.browse_library(...)` with bounded browse metadata and explicit category validation.
- Used the existing FastMCP raw-validation pattern for integer browse parameters so service-level validation still sees invalid inputs before coercion hides them.
- Added adapter, service, tool, contract, response-schema, error-mapping, and HTTP parity coverage for the new browse surface.
- Validation: `uv run pytest -q tests/unit/adapters/test_soco_adapter_library.py tests/unit/services/test_library_service.py tests/unit/tools/test_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py tests/unit/config/test_models.py` passed (`128 passed`).
- Addressed review follow-ups for Story 4.1 by advancing pagination cursors by the requested page size, promoting browse-network failures to connectivity errors, and rejecting malformed `parent_id` values before adapter calls.
- Addressed a second Story 4.1 review follow-up by rejecting syntactically valid but category-incompatible drill-down targets as validation errors before adapter calls.
- Validation: `uv run pytest -q tests/unit/services/test_library_service.py tests/unit/tools/test_library.py tests/unit/adapters/test_soco_adapter_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py` passed (`116 passed`).
- Validation: `uv run pytest -q tests/unit/services/test_library_service.py tests/unit/tools/test_library.py tests/unit/adapters/test_soco_adapter_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py` passed (`118 passed`).
- Validation: `uv run pytest -q` passed (`1360 passed, 3 skipped`).
- Validation: `uv run ruff check src/soniq_mcp/adapters/soco_adapter.py src/soniq_mcp/services/library_service.py src/soniq_mcp/tools/library.py src/soniq_mcp/tools/__init__.py src/soniq_mcp/domain/exceptions.py src/soniq_mcp/domain/models.py src/soniq_mcp/schemas/responses.py src/soniq_mcp/schemas/errors.py src/soniq_mcp/config/models.py tests/unit/adapters/test_soco_adapter_library.py tests/unit/services/test_library_service.py tests/unit/tools/test_library.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/unit/schemas/test_responses.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_http_bootstrap.py` passed.

### Completion Notes List

- Story is intentionally scoped to bounded browse behavior only; playback selection remains reserved for Story 4.2.
- The story defines a single stable browse tool surface and explicitly rejects unbounded result retrieval.
- The normalized browse response is designed to be selection-ready for the next story without forcing a later breaking contract change.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- Added `LibraryError`, `LibraryValidationError`, and `LibraryItem` to support a new bounded local music-library browse capability family.
- Added `LibraryBrowseResponse` / `LibraryItemResponse` and `ErrorResponse.from_library_error(...)` so the new tool follows the same normalized response and typed error conventions as the rest of phase 2.
- Implemented `SoCoAdapter.browse_library(...)` against the locked `soco==0.30.14` `MusicLibrary` surface using `get_music_library_information(...)` and `browse_by_idstring(...)`.
- Implemented `LibraryService` with explicit supported-category validation, bounded page-size enforcement, `parent_id` validation, and `has_more` / `next_start` metadata generation.
- Added `browse_library` as a read-only MCP tool and wired it into server registration and tool-name validation.
- Added regression coverage across adapter, service, tool, contract, response-schema, error-mapping, and HTTP tool-surface parity layers.
- Tightened review follow-up behavior so browse continuations advance by request window size, malformed `parent_id` values fail fast as validation errors, and library browse network failures surface as connectivity errors.
- Tightened drill-down validation further so category-incompatible but syntactically valid `parent_id` values are rejected as validation errors instead of generic browse failures.

### File List

- _bmad-output/implementation-artifacts/phase-2/4-1-add-bounded-local-music-library-browsing.md
- src/soniq_mcp/tools/library.py
- src/soniq_mcp/services/library_service.py
- src/soniq_mcp/adapters/soco_adapter.py
- src/soniq_mcp/domain/exceptions.py
- src/soniq_mcp/domain/models.py
- src/soniq_mcp/schemas/responses.py
- src/soniq_mcp/schemas/errors.py
- src/soniq_mcp/config/models.py
- src/soniq_mcp/tools/__init__.py
- tests/unit/adapters/test_soco_adapter_library.py
- tests/unit/services/test_library_service.py
- tests/unit/tools/test_library.py
- tests/contract/tool_schemas/test_library_tool_schemas.py
- tests/contract/error_mapping/test_error_schemas.py
- tests/integration/transports/test_http_bootstrap.py

### Change Log

- 2026-04-12: Implemented Story 4.1 bounded local music-library browsing end to end with a new `library` capability boundary, bounded browse metadata, and full regression coverage.
- 2026-04-12: Addressed Story 4.1 review findings around pagination cursor advancement, malformed drill-down identifiers, and browse connectivity error mapping.
- 2026-04-12: Addressed a follow-up review finding by validating category-to-parent compatibility for library drill-down requests.
