# Story 4.3: Preserve parity for library access across direct and agent-mediated usage

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an integrator,
I want local music library capabilities to behave the same in direct AI and agent workflows,
so that I do not need different mental models for the same library actions.

## Acceptance Criteria

1. Given the library tools are exposed over supported transports, when a direct AI client or an agent workflow invokes the same library capability, then the request and response semantics are equivalent aside from transport-specific envelope details.
2. Given documentation and examples are reviewed, when a user compares direct and agent-mediated library usage, then the same named capability family and expected result structure are shown consistently.

## Tasks / Subtasks

- [x] Audit and lock the library capability surface as transport-neutral behavior (AC: 1)
  - [x] Verify `browse_library` and `play_library_item` remain registered in the same capability family with matching annotations and parameter schemas across local `stdio` and HTTP bootstrap paths
  - [x] Expand `tests/contract/tool_schemas/test_library_tool_schemas.py` only where needed to lock the final public schema, required parameters, and normalized response shapes for both tools
  - [x] Extend `tests/integration/transports/test_http_bootstrap.py` only where needed to prove library-tool metadata parity between `stdio` and `Streamable HTTP`
  - [x] If the audit finds no runtime mismatch, preserve the current code path and encode that parity through regression tests rather than introducing unnecessary service or adapter refactors

- [x] Add documentation regression coverage for library parity guidance (AC: 1, 2)
  - [x] Extend `tests/unit/test_integration_docs.py` to assert the README, prompts, and integration guides all surface the library capability family with the same tool names
  - [x] Add assertions that direct-client guidance and agent/automation guidance both reference `browse_library` and `play_library_item`
  - [x] Add assertions that the docs distinguish browse results from playback selections and keep transport-specific differences limited to connection/setup details

- [x] Update the canonical command and prompt docs for the library capability family (AC: 2)
  - [x] Update `docs/prompts/command-reference.md` with a dedicated library section covering `browse_library` and `play_library_item`, their required parameters, and the normalized result expectations
  - [x] Update `docs/prompts/example-uses.md` with representative direct-client examples for bounded browsing, drill-down, and playback from a normalized selection
  - [x] Keep examples grounded in the current supported contract:
    - [x] `browse_library` stays a bounded browse operation
    - [x] `play_library_item` consumes a normalized playable selection
    - [x] non-playable containers should be described as browse-deeper targets, not implicit playback targets

- [x] Update integrator-facing docs so agent workflows use the same library mental model (AC: 2)
  - [x] Update `docs/integrations/README.md` to call out the library capability family as part of the shared MCP tool surface
  - [x] Update `docs/integrations/home-assistant.md` with a representative library flow that starts with diagnostics, then uses `browse_library`, then `play_library_item` when a playable selection is available
  - [x] Update `docs/integrations/n8n.md` with the same named library flow and result expectations, preserving the "execution layer only" boundary
  - [x] Update `README.md` if the top-level feature summary still omits the library tools from the supported phase-2 surface

- [x] Keep direct and agent guidance aligned to the actual library contract (AC: 1, 2)
  - [x] Use the current public tool names and parameter shapes exactly as exposed by the server
  - [x] Preserve `snake_case` field names and current normalized result semantics in examples and documentation
  - [x] Do not introduce undocumented capabilities such as library search, queue mutation from library results, fuzzy selection, or alternate playback identifiers
  - [x] Keep transport-specific discussion focused on connection method and envelope differences, not on differing business semantics

- [x] Run targeted validation for parity hardening (AC: 1, 2)
  - [x] Run the relevant contract and transport tests for the library tool surface
  - [x] Run `tests/unit/test_integration_docs.py`
  - [x] Run lint or formatting checks on touched Python and Markdown files as appropriate

## Dev Notes

### Story intent

- Story 4.1 established bounded local music-library browsing.
- Story 4.2 established playback from normalized library selections with typed validation and unsupported-operation handling.
- Story 4.3 is the parity-hardening pass for Epic 4: confirm the library capability family behaves the same across direct and agent-mediated usage, then document that shared mental model clearly.
- This story is not for adding new library capabilities. It is for locking the existing browse/play surface and making the operator guidance match the shipped contract.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-41-Add-bounded-local-music-library-browsing`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-42-Support-selection-and-playback-from-library-results`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-43-Preserve-parity-for-library-access-across-direct-and-agent-mediated-usage`]

### Previous story intelligence

- Story 4.1 deliberately created a normalized browse contract that is selection-ready: `title`, `item_type`, `item_id`, `uri`, `album_art_uri`, `is_browsable`, and `is_playable`.
- Story 4.2 deliberately kept browse identity and playback identity separate: callers browse first, then play a normalized selection using `uri` plus the existing metadata, and non-playable containers fail safely.
- Do not reopen the Story 4.1 bounded-browse rules or the Story 4.2 playback validation rules just to improve parity docs. Story 4.3 should document and regression-lock them.
  [Source: `_bmad-output/implementation-artifacts/phase-2/4-1-add-bounded-local-music-library-browsing.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/4-2-support-selection-and-playback-from-library-results.md`]

### Current repo state to build on

- The code already exposes both library tools inside `src/soniq_mcp/tools/library.py`, and `tests/integration/transports/test_http_bootstrap.py` already includes them in the representative parity set.
- The canonical command-surface docs currently lag the implementation: `docs/prompts/command-reference.md` has alarm and playlist lifecycle sections but no equivalent dedicated library section.
- The prompt examples and integration guides already establish a pattern for documenting direct and agent-mediated parity. Reuse that structure for library access rather than inventing a new docs layout.
- `tests/unit/test_integration_docs.py` is the existing regression suite for top-level docs linkage and guide consistency. Extend that suite instead of creating isolated ad hoc docs assertions elsewhere.
  [Source: `src/soniq_mcp/tools/library.py`]
  [Source: `tests/contract/tool_schemas/test_library_tool_schemas.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]
  [Source: `tests/unit/test_integration_docs.py`]
  [Source: `docs/prompts/command-reference.md`]
  [Source: `docs/prompts/example-uses.md`]
  [Source: `docs/integrations/README.md`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- Preserve transport-neutral tool semantics across `stdio` and `Streamable HTTP`.
- Keep docs and examples aligned to the actual supported command surface rather than aspirational future capabilities.
- Keep `browse_library` as the read-only browse entry point and `play_library_item` as the control operation for normalized playable selections.
- Do not leak raw SoCo library objects, transport-specific internals, or alternate identifiers into public examples.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]

### Technical requirements

- The same library tool names must remain usable across direct AI-client usage and agent-mediated workflows: `browse_library` and `play_library_item`.
- Request/response semantics must remain equivalent across transports; only transport-specific envelope/setup details may differ.
- `browse_library` examples should continue to show bounded category browsing and drill-down via `parent_id`, not unbounded dumps or fuzzy search.
- `play_library_item` examples should continue to show playback from a normalized playable selection and should preserve the current required parameters: `room`, `title`, `uri`, and `is_playable`, with optional `item_id`.
- Documentation must clearly signal that browse-only containers are not safe playback targets and should lead users to browse deeper instead.
- Keep all user-facing fields in `snake_case` and align examples with the normalized response models already locked by contract tests.
  [Source: `src/soniq_mcp/tools/library.py`]
  [Source: `tests/contract/tool_schemas/test_library_tool_schemas.py`]
  [Source: `tests/unit/tools/test_library.py`]
  [Source: `tests/unit/services/test_library_service.py`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]

### Git intelligence summary

- Recent work already completed Story 4.1 and Story 4.2, and the latest library-related commits touched the library adapter, service, tool registration, schema contracts, transport parity tests, and the sprint tracker.
- Inference: Story 4.3 should avoid reopening adapter/service behavior unless a real parity bug is discovered. The highest-signal work is contract hardening plus docs/example alignment.
- Relevant recent commits:
  - `b7349fc` - Mark Story 4.2 as done; fix line-length lint in errors.py
  - `e0eb933` - Complete Story 4.1 bounded library browsing
  - `ce14da9` - Fix CI: add types-requests stub and reformat two files

### Latest technical information

- The current MCP specification draft defines two standard transports: `stdio` and `Streamable HTTP`. The transport spec explicitly states that Streamable HTTP replaces the earlier HTTP+SSE transport shape from protocol version `2024-11-05`. Keep parity language and examples centered on `Streamable HTTP`, not legacy SSE-first wording.
- The MCP transport spec also states that Streamable HTTP uses a single MCP endpoint supporting both `POST` and `GET`. Inference: user-facing docs should describe the same library tool semantics across transports while limiting transport-specific guidance to connection/setup details.
- The current MCP Python SDK docs still show `FastMCP` and `mcp.run(transport="streamable-http")` as the standard Python direction. Story 4.3 should not invent a transport-specific library API surface outside the existing FastMCP tool model.
- MCP tool annotations remain hints for clients and UIs, not separate business semantics. Preserve the current read-only/control distinction for `browse_library` and `play_library_item` instead of documenting different behaviors for direct versus agent usage.
  [Source: `https://modelcontextprotocol.io/specification/draft/basic/transports`]
  [Source: `https://py.sdk.modelcontextprotocol.io/`]
  [Source: `https://modelcontextprotocol.io/legacy/concepts/tools`]

### Likely files to inspect or update

- Code and contract tests:
  - `src/soniq_mcp/tools/library.py`
  - `tests/contract/tool_schemas/test_library_tool_schemas.py`
  - `tests/integration/transports/test_http_bootstrap.py`
  - `tests/unit/tools/test_library.py`
- Documentation regression tests:
  - `tests/unit/test_integration_docs.py`
- Docs and examples:
  - `README.md`
  - `docs/prompts/example-uses.md`
  - `docs/prompts/command-reference.md`
  - `docs/integrations/README.md`
  - `docs/integrations/home-assistant.md`
  - `docs/integrations/n8n.md`

### Documentation guidance

- `docs/prompts/command-reference.md` is the canonical command-surface document and should gain the authoritative library section first.
- `docs/prompts/example-uses.md` should show both direct-client library flows and agent/automation flows without changing the underlying tool names or result semantics.
- `docs/integrations/home-assistant.md` and `docs/integrations/n8n.md` should show the same library capability family as direct usage, with workflow orchestration remaining outside SoniqMCP.
- Avoid broad setup-guide rewrites unless the parity hardening work uncovers a real mismatch in runtime guidance.
  [Source: `docs/prompts/command-reference.md`]
  [Source: `docs/prompts/example-uses.md`]
  [Source: `docs/integrations/README.md`]
  [Source: `docs/integrations/home-assistant.md`]
  [Source: `docs/integrations/n8n.md`]

### Testing guidance

- Prefer additive regression tests over large refactors of existing docs or schema suites.
- Reuse the current `test_library_tool_schemas.py` and `test_http_bootstrap.py` surfaces to lock parity rather than duplicating weaker checks elsewhere.
- Reuse `tests/unit/test_integration_docs.py` for doc-surface assertions so future parity drift is caught in CI.
- Keep default validation hardware-independent. This story should not add real Sonos dependencies.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/contract/tool_schemas/test_library_tool_schemas.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]
  [Source: `tests/unit/test_integration_docs.py`]

### Project Structure Notes

- Existing phase-2 story files live under `_bmad-output/implementation-artifacts/phase-2/`.
- This story is primarily a parity, regression-test, and documentation hardening pass; avoid expanding library feature scope into search, queue workflows, playlist reuse, or transport implementation changes unless a verified parity defect requires a minimal fix.
- No dedicated UX artifact exists; use the PRD, architecture, and existing prompt/integration guide structure for wording and example flow decisions.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-43-Preserve-parity-for-library-access-across-direct-and-agent-mediated-usage`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/4-1-add-bounded-local-music-library-browsing.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/4-2-support-selection-and-playback-from-library-results.md`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]
- [Source: `src/soniq_mcp/tools/library.py`]
- [Source: `tests/contract/tool_schemas/test_library_tool_schemas.py`]
- [Source: `tests/integration/transports/test_http_bootstrap.py`]
- [Source: `tests/unit/test_integration_docs.py`]
- [Source: `README.md`]
- [Source: `docs/prompts/example-uses.md`]
- [Source: `docs/prompts/command-reference.md`]
- [Source: `docs/integrations/README.md`]
- [Source: `docs/integrations/home-assistant.md`]
- [Source: `docs/integrations/n8n.md`]
- [Source: `https://modelcontextprotocol.io/specification/draft/basic/transports`]
- [Source: `https://py.sdk.modelcontextprotocol.io/`]
- [Source: `https://modelcontextprotocol.io/legacy/concepts/tools`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- 2026-04-12: Story created from Epic 4 planning artifacts, completed Stories 4.1 and 4.2, current library tool/transport tests, the docs regression suite, and the current prompt/integration docs.
- 2026-04-12: Confirmed `browse_library` and `play_library_item` are already registered and included in HTTP parity coverage; the primary remaining gap is canonical docs and direct-versus-agent guidance alignment.
- 2026-04-12: Added failing documentation regression assertions for library parity across `README.md`, `docs/prompts/example-uses.md`, `docs/prompts/command-reference.md`, and the Home Assistant / `n8n` integration guides.
- 2026-04-12: Updated the canonical command surface, prompt examples, integration guides, and top-level README to document the existing `browse_library` and `play_library_item` contract consistently across direct and agent-mediated usage.
- 2026-04-12: Validation passed:
  - `uv run pytest -q tests/unit/test_integration_docs.py`
  - `uv run pytest -q tests/contract/tool_schemas/test_library_tool_schemas.py tests/integration/transports/test_http_bootstrap.py`
  - `uv run ruff check tests/unit/test_integration_docs.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/integration/transports/test_http_bootstrap.py`
  - `uv run ruff format --check tests/unit/test_integration_docs.py tests/contract/tool_schemas/test_library_tool_schemas.py tests/integration/transports/test_http_bootstrap.py`
  - `uv run pytest -q`

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story scope is parity hardening only; it should lock the existing library capability family and align docs/examples to the shipped tool surface.
- Command/reference and integration docs currently need explicit library coverage to match the already-implemented code and tests.
- Added documentation regression coverage that now fails if the README, prompt guide, command reference, or agent integration guides drift away from the library capability surface.
- Updated the canonical docs to present `browse_library` and `play_library_item` as the same transport-neutral capability family for direct clients and agent workflows.
- Verified that runtime parity remained intact without service or adapter changes; the implementation work stayed focused on docs and regression hardening.
- Full regression suite passed after the updates: `1392 passed, 3 skipped`.

### File List

- _bmad-output/implementation-artifacts/phase-2/4-3-preserve-parity-for-library-access-across-direct-and-agent-mediated-usage.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- README.md
- docs/prompts/command-reference.md
- docs/prompts/example-uses.md
- docs/integrations/README.md
- docs/integrations/home-assistant.md
- docs/integrations/n8n.md
- tests/unit/test_integration_docs.py

### Change Log

- 2026-04-12: Added library parity documentation and docs regression coverage for direct and agent-mediated workflows; validated targeted parity suites plus the full test suite.
