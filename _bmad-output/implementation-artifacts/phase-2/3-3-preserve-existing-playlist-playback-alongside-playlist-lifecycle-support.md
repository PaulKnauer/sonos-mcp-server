# Story 3.3: Preserve existing playlist playback alongside playlist lifecycle support

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want playlist playback to remain stable while new playlist lifecycle features are added,
so that the expanded playlist surface does not break established usage.

## Acceptance Criteria

1. Given the playlist lifecycle tools are implemented, when the client invokes existing playlist playback behavior, then playback still works through the same target-room workflow as before.
2. Given a playlist created or updated through the new lifecycle tools, when the client selects it for playback, then the playlist is discoverable and playable through the playlist playback flow.

## Tasks / Subtasks

- [x] Validate and preserve the public playlist playback contract (AC: 1)
  - [x] Keep the existing public tool name `play_playlist(room: str, uri: str)` unchanged
  - [x] Keep playback routing inside `src/soniq_mcp/tools/playlists.py` and `src/soniq_mcp/services/playlist_service.py`; do not move playlist playback into another module
  - [x] Confirm `play_playlist` continues to accept playlist `uri` values from `list_playlists` results without requiring lifecycle identifiers such as `item_id`
  - [x] Preserve existing room-targeting semantics and error mapping for `RoomNotFoundError`, `PlaylistError`, and `SonosDiscoveryError`

- [x] Harden interoperability between playlist playback and lifecycle operations (AC: 2)
  - [x] Confirm playlists returned from `create_playlist(...)` remain visible in `list_playlists()` with stable `title`, `uri`, and `item_id`
  - [x] Confirm playlists changed through `update_playlist(...)` remain playable through `play_playlist(room, uri)` without additional user steps
  - [x] Ensure delete behavior removes the playlist from subsequent playback discovery flows
  - [x] Keep rename out of scope for this story; do not reintroduce public rename support here

- [x] Preserve architecture and transport parity for the expanded playlist surface (AC: 1, 2)
  - [x] Keep `tools -> services -> adapters` boundaries intact
  - [x] Do not call `SoCo` directly from tool handlers, tests, or transport bootstrap code
  - [x] Preserve registration and behavior parity across `stdio` and HTTP transports
  - [x] Avoid changing unrelated capability modules while hardening playlist playback compatibility

- [x] Expand regression coverage for playlist playback compatibility (AC: 1, 2)
  - [x] Update `tests/unit/tools/test_playlists.py` to lock existing `play_playlist` behavior after the lifecycle additions
  - [x] Add or update service-level coverage in `tests/unit/services/test_playlist_service.py` for playback plus lifecycle interplay
  - [x] Add or update adapter-level coverage in `tests/unit/adapters/test_soco_adapter_playlists.py` for playlist discovery/playback continuity
  - [x] Update contract and transport-parity tests if needed so the exposed playlist playback surface remains stable
  - [x] Cover at least:
    - [x] playback of an existing discovered playlist by `uri`
    - [x] playback of a newly created playlist returned by lifecycle flow
    - [x] playback of an updated playlist after queue-backed replacement
    - [x] failure behavior for unknown room and playlist/network errors
    - [x] no regression in tool registration and annotations for `play_playlist`

- [x] Run targeted validation for playlist playback compatibility (AC: 1, 2)
  - [x] Run the targeted playlist unit, contract, and transport tests
  - [x] Run the relevant lint/format checks for touched files

### Review Findings

- [x] [Review][Patch] Tool-level interoperability tests bypass `create_playlist` and `update_playlist`, so AC2 is not actually verified through the public lifecycle tool outputs [`tests/unit/tools/test_playlists.py:206`]
- [x] [Review][Patch] `test_delete_prevents_play_of_unknown_playlist` does not perform a delete and only asserts generic adapter error propagation, so it does not validate the claimed delete/playback interaction [`tests/unit/services/test_playlist_service.py:303`]

## Dev Notes

### Story intent

- Story 3.2 introduced playlist inventory and lifecycle support through `PlaylistService` while preserving the existing playback tool name and flow.
- Story 3.3 exists to prove that the expanded playlist surface did not break established playback behavior and that lifecycle-created or lifecycle-updated playlists still work through the legacy playback path.
- Rename has been intentionally deferred from the public MCP surface. This story must not reopen that scope.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-32-Introduce-Sonos-playlist-CRUD-operations`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-33-Preserve-existing-playlist-playback-alongside-playlist-lifecycle-support`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md`]

### Previous story intelligence

- Story 3.2 established the current playlist ownership boundary:
  - `src/soniq_mcp/tools/playlists.py` exposes inventory, playback, and supported lifecycle tools
  - `src/soniq_mcp/services/playlist_service.py` orchestrates both playback and lifecycle flows
  - `src/soniq_mcp/adapters/soco_adapter.py` remains the only direct `SoCo` integration layer
- Code review on Story 3.2 found and fixed multiple lifecycle risks:
  - adapter lookup now preserves real SoCo/library failures
  - bounded title fallback exists only for playlists without `item_id`
  - queue-backed playlist updates now restore state on partial failure and read the full queue
  - public rename exposure was removed because current `SoCo` does not provide a supported clean rename path
- This story should build on those fixes, not work around or undo them.
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md#Review-Findings`]
  [Source: `git log --oneline -5`]

### Current implementation shape

- `play_playlist(room, uri)` is still the public playback tool and returns `{"status": "ok", "room": room, "uri": uri}` on success.
- Lifecycle tools now rely on `item_id` for targeting, but playback still uses playlist `uri`; this split is intentional and should remain stable unless a broader contract change is explicitly planned.
- Tool descriptions in `src/soniq_mcp/tools/playlists.py` already explain that lifecycle operations use `item_id` while playback uses `uri`.
- The compatibility risk in this story is not just whether playback still works for old playlists, but whether playlists coming out of create/update flows remain discoverable and playable through the old playback contract.
  [Source: `src/soniq_mcp/tools/playlists.py`]
  [Source: `src/soniq_mcp/services/playlist_service.py`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- `tools/playlists.py` owns MCP registration, permission checks, success response conversion, and error translation only.
- `services/playlist_service.py` owns playback orchestration and lifecycle interoperability rules.
- `src/soniq_mcp/adapters/soco_adapter.py` remains the only direct `SoCo` boundary.
- Preserve transport-neutral tool semantics across local `stdio` and HTTP exposure modes.
- Do not split playlist playback into a generic playback module just because lifecycle support now exists.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]

### Technical requirements

- Preserve the public tool name `play_playlist`.
- Keep playlist playback based on Sonos playlist `uri`, not `item_id`.
- Ensure playlists surfaced by `list_playlists()` remain suitable input for `play_playlist`.
- Ensure playlists returned by `create_playlist(...)` and `update_playlist(...)` remain consistent with playback discovery and playback invocation expectations.
- Do not reintroduce `rename_playlist` to tool registration, config models, or tests in this story.
- Avoid broad schema churn unless needed to preserve compatibility or fix a proven regression.

### Library and framework requirements

- Continue using the existing Python + `SoCo` + FastMCP stack already established in Story 3.2.
- Keep all `SoCo` object handling inside `src/soniq_mcp/adapters/soco_adapter.py`.
- Continue to use Pydantic response models and `.model_dump()` for structured MCP responses.
- Reuse the current playlist-domain error types and response mapping patterns; do not invent a parallel playback error contract for playlists.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Format-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]
  [Source: `src/soniq_mcp/tools/playlists.py`]

### File structure requirements

- Primary source files likely to change:
  - `src/soniq_mcp/tools/playlists.py`
  - `src/soniq_mcp/services/playlist_service.py`
  - `src/soniq_mcp/adapters/soco_adapter.py` only if a real compatibility defect is identified
- Primary tests likely to change:
  - `tests/unit/tools/test_playlists.py`
  - `tests/unit/services/test_playlist_service.py`
  - `tests/unit/adapters/test_soco_adapter_playlists.py`
  - `tests/contract/tool_schemas/test_playlists_tool_schemas.py`
  - `tests/integration/transports/test_http_bootstrap.py`
- Do not reopen unrelated modules such as alarms, group audio, or library access while working this story.

### Testing requirements

- Favor hardware-independent regression tests using fakes and mocks around the adapter/service boundary.
- Keep existing `play_playlist` registration, annotations, success shape, and error mapping locked down in unit tests.
- Add interoperability-focused tests that connect lifecycle outputs to playback inputs.
- Preserve transport parity by updating HTTP bootstrap / contract tests only if the exposed playlist playback behavior changed unintentionally.
- Re-run the targeted playlist suites after any changes.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/unit/tools/test_playlists.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]

### Project Structure Notes

- Existing phase-2 story files live under `_bmad-output/implementation-artifacts/phase-2/`.
- Story 3.2 is the direct predecessor and should be treated as the implementation baseline for playlist behavior.
- No dedicated UX artifact exists; use PRD, architecture, and current tool descriptions for user-facing behavior expectations.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-33-Preserve-existing-playlist-playback-alongside-playlist-lifecycle-support`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-32-Introduce-Sonos-playlist-CRUD-operations`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `src/soniq_mcp/tools/playlists.py`]
- [Source: `src/soniq_mcp/services/playlist_service.py`]
- [Source: `tests/unit/tools/test_playlists.py`]
- [Source: `tests/integration/transports/test_http_bootstrap.py`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- 2026-04-11: Story created from updated Epic 3 and Story 3.2 implementation baseline.
- 2026-04-11: Implementation confirmed no source-code changes needed — contract already stable. All tasks addressed via test additions.
- `test_deleted_playlist_absent_when_get_playlists_rechecked` required 3 side_effect entries: pre-delete get, internal delete lookup, post-delete get.

### Completion Notes List

- Confirmed `play_playlist(room, uri)` tool name and routing unchanged — existing tests already lock this.
- Added `TestPlayPlaylistLifecycleInteroperability` (3 tests) to `test_playlists.py`: plays URI from real `create_playlist` tool output, plays URI from real `update_playlist` tool output, verifies uri forwarded unchanged to service.
- Added `TestPlaylistLifecycleInteroperability` (5 tests) to `test_playlist_service.py`: created playlist URI is playable, updated playlist URI is playable, created playlist has required fields, updated playlist preserves item_id, deleted playlist disappears from later list results.
- Added `TestPlaylistDiscoveryPlaybackContinuity` (3 tests) to `test_soco_adapter_playlists.py`: created playlist URI usable with play_playlist, get_playlists returns stable URI, deleted playlist absent from subsequent get.
- Architecture boundaries verified intact: no SoCo imports outside adapter, no new modules, transport parity unchanged.
- Validation run: targeted playlist suites passed and lint remained clean.

### File List

- `_bmad-output/implementation-artifacts/phase-2/3-3-preserve-existing-playlist-playback-alongside-playlist-lifecycle-support.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `tests/unit/tools/test_playlists.py`
- `tests/unit/services/test_playlist_service.py`
- `tests/unit/adapters/test_soco_adapter_playlists.py`

### Change Log

- Story 3.3 implementation: Harden playlist playback compatibility with 11 new interoperability tests across tool, service, and adapter layers. No source changes needed — contract was already stable. (Date: 2026-04-11)
