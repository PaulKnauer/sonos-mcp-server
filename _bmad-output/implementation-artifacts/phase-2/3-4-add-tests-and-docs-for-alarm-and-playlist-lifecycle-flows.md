# Story 3.4: Add tests and docs for alarm and playlist lifecycle flows

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want alarm and playlist lifecycle features covered by stable tests and examples,
so that phase-2 automation workflows remain safe to evolve.

## Acceptance Criteria

1. Given the alarm and playlist lifecycle features are implemented, when unit, integration, and contract tests run, then they validate normalized responses, error categories, and lifecycle behavior without requiring hardware in the default path.
2. Given the new lifecycle tools are documented, when integrators review examples, then they can distinguish playlist playback from playlist management and understand the supported alarm workflows.

## Tasks / Subtasks

- [x] Expand regression coverage for alarm lifecycle behavior (AC: 1)
  - [x] Review current alarm coverage from Story 3.1 and identify remaining gaps in unit, contract, or transport-parity tests
  - [x] Add or update alarm lifecycle tests only where they strengthen normalized response, error mapping, or hardware-independent regression protection
  - [x] Keep tests focused on supported alarm workflows: discovery, create, update, delete, and typed validation/capability errors

- [x] Expand regression coverage for playlist lifecycle behavior as a finalized post-review baseline (AC: 1)
  - [x] Ensure playlist lifecycle contract tests reflect the final public surface after rename deferral
  - [x] Confirm playlist lifecycle tests still cover normalized responses, delete confirmation, error mapping, and playback compatibility
  - [x] Avoid reintroducing `rename_playlist` to any schema, contract, config, or docs tests

- [x] Harden transport and contract parity for both lifecycle families (AC: 1)
  - [x] Update `tests/contract/tool_schemas/` coverage for alarm and playlist lifecycle tools if the final public schemas are not already fully locked
  - [x] Update `tests/contract/error_mapping/test_error_schemas.py` if lifecycle error coverage is missing any normalized alarm or playlist error path
  - [x] Update `tests/integration/transports/test_http_bootstrap.py` only if needed to preserve final tool exposure parity across `stdio` and HTTP

- [x] Add or update operator-facing docs and examples for lifecycle workflows (AC: 2)
  - [x] Update prompt/example docs to show supported alarm lifecycle flows
  - [x] Update prompt/example docs to distinguish playlist playback (`play_playlist`) from playlist management (`list/create/update/delete`)
  - [x] Ensure docs do not advertise playlist rename as a supported MCP tool
  - [x] Add or update troubleshooting/context notes only where they materially improve lifecycle clarity

- [x] Keep docs aligned with the actual supported phase-2 contract (AC: 2)
  - [x] Use the current public tool names and parameter shapes exactly as exposed by the MCP server
  - [x] Keep examples transport-neutral unless a guide is explicitly transport-specific
  - [x] Preserve the architecture rule that docs/examples mirror the supported surface rather than future or hypothetical capabilities

- [x] Run targeted validation for lifecycle tests and docs-linked contract stability (AC: 1, 2)
  - [x] Run the relevant unit, contract, and transport tests for alarms and playlists
  - [x] Run lint/format/doc checks that apply to touched files

## Dev Notes

### Story intent

- Story 3.1 implemented alarm discovery and lifecycle operations.
- Story 3.2 implemented playlist lifecycle support with rename deferred due to unsupported current `SoCo` capability.
- Story 3.3 hardened playlist playback compatibility after lifecycle support landed.
- Story 3.4 is the consolidation pass: strengthen the long-term regression suite and update operator-facing docs/examples so the shipped phase-2 lifecycle surface is both test-locked and clearly explained.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-31-Add-alarm-discovery-and-lifecycle-operations`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-32-Introduce-Sonos-playlist-CRUD-operations`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-33-Preserve-existing-playlist-playback-alongside-playlist-lifecycle-support`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-34-Add-tests-and-docs-for-alarm-and-playlist-lifecycle-flows`]

### Previous story intelligence

- Story 3.1 established the alarm lifecycle boundary and its normalized error/response model.
- Story 3.2 established the playlist lifecycle boundary, moved playlist ownership into `PlaylistService`, and removed public rename exposure after review and technical research.
- Story 3.3 added interoperability tests proving that lifecycle-created and lifecycle-updated playlists still work through the legacy playback flow.
- This story should not reopen capability-scope decisions already made in 3.1-3.3. It should document and lock them down.
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-3-preserve-existing-playlist-playback-alongside-playlist-lifecycle-support.md`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- Keep default automated validation hardware-independent.
- Preserve transport-neutral tool semantics across local `stdio` and HTTP.
- Keep docs and examples aligned to the actual supported command surface.
- Do not document unsupported or deferred capabilities, especially playlist rename.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Documentation-and-Examples`]

### Technical requirements

- Alarm and playlist lifecycle tests should validate normalized success responses and typed error responses without requiring Sonos hardware.
- Final playlist lifecycle contract must reflect `list/create/update/delete` plus `play_playlist`, with rename absent from the public surface.
- Docs must clearly separate:
  - playlist playback by `uri`
  - playlist lifecycle targeting by `item_id`
  - alarm lifecycle operations by `alarm_id`
- Examples should be useful for both direct clients and agent-mediated workflows, but must remain grounded in the actual tool surface.

### Likely files to inspect or update

- Tests:
  - `tests/unit/tools/test_playlists.py`
  - `tests/unit/services/test_playlist_service.py`
  - `tests/unit/adapters/test_soco_adapter_playlists.py`
  - `tests/unit/tools/test_alarms.py`
  - `tests/unit/services/test_alarm_service.py`
  - `tests/unit/adapters/test_soco_adapter_alarms.py`
  - `tests/contract/tool_schemas/test_playlists_tool_schemas.py`
  - `tests/contract/tool_schemas/test_alarms_tool_schemas.py`
  - `tests/contract/error_mapping/test_error_schemas.py`
  - `tests/integration/transports/test_http_bootstrap.py`
- Docs and examples:
  - `docs/prompts/example-uses.md`
  - `docs/prompts/command-reference.md`
  - `docs/setup/troubleshooting.md`
  - `README.md` if the public feature summary needs correction

### Documentation guidance

- `docs/prompts/example-uses.md` already contains favourites/playlists examples and is a likely place to extend lifecycle examples.
- `docs/prompts/command-reference.md` is the canonical command-surface document and should remain authoritative.
- Setup/troubleshooting docs should only be touched if lifecycle-specific guidance is genuinely missing.
- Avoid broad README rewrites unless the lifecycle surface shown there is actually wrong.
  [Source: `docs/prompts/example-uses.md`]
  [Source: `docs/prompts/command-reference.md`]
  [Source: `docs/setup/troubleshooting.md`]
  [Source: `README.md`]

### Testing guidance

- Prefer additive regression tests over refactoring large existing suites.
- Reuse the fake/mocked adapter patterns established in Stories 3.1-3.3.
- If contract tests are already sufficient in one area, do not duplicate them in weaker unit assertions.
- Make sure final tests protect against accidental reintroduction of `rename_playlist` in schemas, docs, or tool registration.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/3-3-preserve-existing-playlist-playback-alongside-playlist-lifecycle-support.md`]

### Project Structure Notes

- Existing phase-2 story files live under `_bmad-output/implementation-artifacts/phase-2/`.
- This story is primarily a tests-and-docs hardening pass; avoid reopening unrelated product areas such as library access, input switching, or group audio.
- No dedicated UX artifact exists; use PRD, architecture, and current docs structure for wording/flow decisions.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-34-Add-tests-and-docs-for-alarm-and-playlist-lifecycle-flows`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/3-1-add-alarm-discovery-and-lifecycle-operations.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/3-3-preserve-existing-playlist-playback-alongside-playlist-lifecycle-support.md`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `docs/prompts/example-uses.md`]
- [Source: `docs/prompts/command-reference.md`]
- [Source: `docs/setup/troubleshooting.md`]
- [Source: `README.md`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- 2026-04-11: Story created from Epic 3 plus the completed alarm and playlist lifecycle stories.
- 2026-04-11: Began implementation by auditing lifecycle contract coverage, transport parity, and prompt/operator docs against the shipped phase-2 tool surface.

### Completion Notes List

- Story focuses on stabilizing alarm/playlist lifecycle tests and docs after Stories 3.1-3.3.
- Rename is explicitly out of scope and should remain absent from public docs and contract tests.
- Added stronger alarm and playlist contract guards, including exact lifecycle tool sets, identifier field expectations, and an explicit check that `rename_playlist` remains absent.
- Extended HTTP-versus-stdio parity coverage so lifecycle tool metadata is locked across transports.
- Updated the prompt guides and README to document alarm lifecycle flows and the distinction between playlist playback by `uri` and playlist management by `item_id`.
- Validation completed with targeted lifecycle suites, the full `uv run pytest` suite, `uv run ruff check`, and Python `ruff format --check` on touched test files.

### File List

- _bmad-output/implementation-artifacts/phase-2/3-4-add-tests-and-docs-for-alarm-and-playlist-lifecycle-flows.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- README.md
- docs/prompts/example-uses.md
- docs/prompts/command-reference.md
- tests/contract/tool_schemas/test_alarms_tool_schemas.py
- tests/contract/tool_schemas/test_playlists_tool_schemas.py
- tests/integration/transports/test_http_bootstrap.py

### Change Log

- 2026-04-11: Hardened alarm and playlist lifecycle schema/parity tests and updated operator-facing docs to match the final supported phase-2 contract.
