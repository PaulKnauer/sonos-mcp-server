# Story 2.4: Document and test expanded group and input behavior

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want group-audio and input-switching features to have stable contracts and examples,
so that integrators can adopt them safely across transports.

## Acceptance Criteria

1. Given the group and input tools are implemented, when contract and integration tests run, then the tests verify normalized responses, guard behavior, and safe error handling for these tools.
2. Given documentation and examples are updated, when a user reviews setup and integration guidance, then they can identify when to use room-level, group-level, and input-specific controls.

## Tasks / Subtasks

- [x] Audit and extend documentation for the current Epic 2 input and group surface (AC: 2)
  - [x] Update `README.md` so the top-level tool inventory reflects the implemented input and expanded group-audio tools, not just the original grouping surface
  - [x] Update `docs/prompts/example-uses.md` with direct-client and automation examples for:
    - [x] `switch_to_line_in`
    - [x] `switch_to_tv`
    - [x] `get_group_volume`, `set_group_volume`, `adjust_group_volume`
    - [x] `group_mute`, `group_unmute`
    - [x] `group_rooms`
  - [x] Make the docs clearly distinguish room-level controls from group-level controls and input-specific controls
  - [x] Preserve the existing deployment guidance split between local `stdio` and remote HTTP; do not introduce transport-specific tool semantics

- [x] Refresh integration guidance for agent-mediated and automation use (AC: 2)
  - [x] Update `docs/integrations/home-assistant.md` with at least one representative input-switching or group-audio flow that uses the current tool surface
  - [x] Update `docs/integrations/n8n.md` with at least one representative flow that uses `group_rooms` or the current group-audio controls instead of only the legacy grouping primitives
  - [x] Ensure the integration docs still route users to `ping`, `server_info`, and `list_rooms` for diagnostic setup checks before mutation
  - [x] Keep the docs transport-neutral at the tool layer: integrations decide orchestration, SoniqMCP remains the execution surface only

- [x] Add documentation regression tests for the expanded Epic 2 surface (AC: 1, 2)
  - [x] Extend `tests/unit/test_integration_docs.py` so the docs regressions lock:
    - [x] input-switching tool visibility in product-facing docs
    - [x] expanded group-audio tool visibility in product-facing docs
    - [x] examples that explain when to use room-level vs group-level vs input-specific controls
  - [x] Verify the docs tests assert only the currently supported surface; avoid speculative references to future alarm/library tools

- [x] Audit and harden contract coverage for input and group tools (AC: 1)
  - [x] Review the current contract suites under `tests/contract/tool_schemas/` for:
    - [x] input tools
    - [x] grouping topology tools
    - [x] group-audio tools
    - [x] topology tools that support group-aware targeting
  - [x] Add or tighten assertions where needed so the tests explicitly lock:
    - [x] stable tool names and parameters
    - [x] tool annotations relevant to safe invocation behavior
    - [x] normalized response-shape expectations used by docs/examples
    - [x] typed error translation for validation and discovery paths where this is not already covered
  - [x] Keep these tests aligned with the current FastMCP tool API (`tool.parameters`, not speculative or deprecated attributes)

- [x] Preserve transport and bootstrap parity for the expanded tool families (AC: 1, 2)
  - [x] Re-run and extend `tests/integration/transports/test_http_bootstrap.py` only if the current docs or test updates expose parity gaps
  - [x] Confirm the documented tool surface for direct and agent-mediated use matches the actual registered tool surface across local and HTTP transports
  - [x] Do not add new tools or rename existing tools as part of this story; this story is documentation and test hardening only

- [x] Validate the end-to-end docs-and-tests hardening pass (AC: 1, 2)
  - [x] Run the focused contract, docs, and transport suites touched by this story
  - [x] Run `make test` and confirm the full suite still passes

### Review Findings

- [x] [Review][Patch] Home Assistant example uses `set_group_volume` without first establishing a grouped target [docs/prompts/example-uses.md:289]

## Dev Notes

### Story intent

- This is a hardening story for already-implemented Epic 2 features, not a new feature-delivery story.
- The core input and group capabilities already landed in Stories 2.1, 2.2, and 2.3.
- Story 2.4 should make those capabilities easier and safer to consume by tightening docs, examples, and regression coverage around the existing tool surface.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-24-Document-and-test-expanded-group-and-input-behavior`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-2-Input-and-Group-Audio-Expansion`]

### Current implementation gap to close

- The current repository already exposes the relevant Epic 2 tools in code and tests, including:
  - input switching via `switch_to_line_in` and `switch_to_tv`
  - group-audio state and controls via `get_group_volume`, `set_group_volume`, `adjust_group_volume`, `group_mute`, and `group_unmute`
  - explicit room-set grouping via `group_rooms`
- But the product-facing docs are behind the code:
  - `README.md` still lists only the original grouping tools and does not surface the Epic 2 input or expanded group-audio additions
  - `docs/prompts/example-uses.md` still focuses on `get_group_topology`, `join_group`, `unjoin_room`, and `party_mode`
  - `docs/integrations/home-assistant.md` and `docs/integrations/n8n.md` still describe integration flows mainly in terms of the older grouping surface
- The docs regression suite in `tests/unit/test_integration_docs.py` validates broad navigation and integration guidance, but it does not yet lock the new Epic 2 input/group examples or their terminology.
  [Source: `README.md`]
  [Source: `docs/prompts/example-uses.md`]
  [Source: `docs/integrations/home-assistant.md`]
  [Source: `docs/integrations/n8n.md`]
  [Source: `tests/unit/test_integration_docs.py`]

### Scope guardrails

- Do not use this story to redesign the already-completed playback/volume boundary work from the older Phase 1 `2-4` slot.
- The current Phase 2 `2-4` story is specifically about docs and tests for expanded group and input behavior.
- Do not add or rename MCP tools here.
- Do not refactor `tools -> services -> adapters` ownership unless a docs/test change reveals a concrete bug that blocks the story’s acceptance criteria.
- Keep the repo stateless and Sonos-backed; this story should not introduce stored examples, a database, or a generated docs system.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]

### Architecture guardrails

- Preserve the existing `tools -> services -> adapters` boundary model.
- Keep `SoCoAdapter` as the only direct Sonos integration boundary.
- Keep transport-neutral semantics across `stdio` and HTTP; docs may explain deployment differences, but the tool meaning must remain the same.
- Normalize Sonos-specific state before it leaves the service boundary; docs and tests should describe and assert normalized MCP responses rather than internal SoCo behavior.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Format-Patterns`]

### Existing repo patterns to reuse

- `tests/unit/test_integration_docs.py` already acts as the regression harness for docs navigation, integration guidance, and prompt/reference stability; extend that file rather than inventing a second docs-test pattern.
- The contract suites in `tests/contract/tool_schemas/` already lock tool names, parameters, and annotations by capability family.
- `tests/integration/transports/test_http_bootstrap.py` is the current parity check for public tool registration over HTTP and should remain the transport-level backstop if docs/test updates surface a mismatch.
- The prompt docs structure is already established:
  - `docs/prompts/example-uses.md` for product-facing usage flows
  - `docs/prompts/command-reference.md` for runtime and operator commands
  - `docs/integrations/*.md` for client-specific automation guidance
  - `README.md` for the concise top-level product/tool inventory
  [Source: `tests/unit/test_integration_docs.py`]
  [Source: `tests/contract/tool_schemas/test_input_tool_schemas.py`]
  [Source: `tests/contract/tool_schemas/test_groups_tool_schemas.py`]
  [Source: `tests/contract/tool_schemas/test_groups_audio_tool_schemas.py`]
  [Source: `tests/contract/tool_schemas/test_group_rooms_tool_schema.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]

### Current implementation reality

- Epic 2 input switching is already implemented with dedicated service/tool boundaries in:
  - `src/soniq_mcp/services/input_service.py`
  - `src/soniq_mcp/tools/inputs.py`
- Epic 2 group and topology expansion is already implemented across:
  - `src/soniq_mcp/services/group_service.py`
  - `src/soniq_mcp/tools/groups.py`
  - `src/soniq_mcp/tools/system.py`
  - `src/soniq_mcp/schemas/responses.py`
- Registration is centralized in `src/soniq_mcp/tools/__init__.py`, which is the real source of truth for the live tool surface exposed in docs and bootstrap tests.
  [Source: `src/soniq_mcp/services/input_service.py`]
  [Source: `src/soniq_mcp/tools/inputs.py`]
  [Source: `src/soniq_mcp/services/group_service.py`]
  [Source: `src/soniq_mcp/tools/groups.py`]
  [Source: `src/soniq_mcp/tools/system.py`]
  [Source: `src/soniq_mcp/tools/__init__.py`]

### Documentation guidance

- `README.md` should stay concise and should not become a full tool manual, but it must no longer advertise an outdated subset of the implemented surface.
- `docs/prompts/example-uses.md` is the right place to explain:
  - when to use `group_rooms` versus `join_group` / `party_mode`
  - when to use group-level audio controls versus room-level volume controls
  - when to use input-switching tools and the capability-aware expectations around them
- `docs/prompts/command-reference.md` is about runtime commands and operator paths, not an exhaustive tool encyclopedia. Update it only if the story needs better routing between command docs and the Epic 2 usage docs.
- Integration guides should show realistic orchestrations but must keep SoniqMCP as the execution layer rather than embedding Home Assistant or `n8n` semantics into product docs.

This is an inference from the current docs layout and test suite:
- the repo already differentiates prompt examples, command/operator docs, and integration guides,
- Story 2.4 should improve those existing lanes instead of creating a parallel docs structure.

### Testing requirements

- Add or extend docs regression tests in `tests/unit/test_integration_docs.py` for the Epic 2 input/group surface.
- Reuse the current contract suites first; add only the missing assertions needed to lock the implemented group/input semantics and docs-facing tool expectations.
- Keep tests hardware-free; do not introduce any requirement for real Sonos devices.
- Run the focused suites you touch, then run `make test`.

Focused suites likely to be relevant:

```text
tests/unit/test_integration_docs.py
tests/contract/tool_schemas/test_input_tool_schemas.py
tests/contract/tool_schemas/test_groups_tool_schemas.py
tests/contract/tool_schemas/test_groups_audio_tool_schemas.py
tests/contract/tool_schemas/test_group_rooms_tool_schema.py
tests/contract/tool_schemas/test_system_tool_schemas.py
tests/integration/transports/test_http_bootstrap.py
```

### Previous story intelligence

- Story 2.1 established the dedicated input-switching capability boundary and already includes contract/tool coverage for `switch_to_line_in` and `switch_to_tv`.
- Story 2.2 established the group-audio surface and the current validation/error-translation expectations for group volume and mute.
- Story 2.3 established the explicit `group_rooms` tool, exposed `group_coordinator_uid` in normalized topology responses, and tightened exact-room-set grouping behavior via follow-up review fixes.
- Carry these lessons forward:
  - do not document stale or superseded grouping workflows as the only recommended path,
  - keep docs/examples aligned with the actual normalized response surface,
  - prefer adding regression tests for externally visible docs/API expectations over broad prose-only edits with no guardrails.
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-2-add-group-level-volume-and-mute-controls.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/2-3-strengthen-topology-and-grouping-support-for-expanded-audio-flows.md`]

### Latest dependency and protocol check

- The repo currently pins `mcp[cli]>=1.26.0` and `soco>=0.30.14`.
- PyPI currently lists `soco 0.31.0` as the latest release, published on April 5, 2026.
- The repo lockfile is still on `soco 0.30.14`, uploaded on December 31, 2025.
- The current MCP tools specification documents `inputSchema`, optional `annotations`, and tool-execution error handling as externally visible parts of the tool contract. Treat schema and annotation regressions as API changes, not internal details.
- Do not bundle an MCP or SoCo upgrade into this story. Implement against the repo’s pinned baseline and only use the external references to keep the docs/tests aligned with the current contract concepts.
  [Source: `pyproject.toml`]
  [Source: `uv.lock`]
  [Source: [PyPI soco](https://pypi.org/project/soco/)]
  [Source: [MCP Tools Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)]

### Files likely to change

```text
_bmad-output/implementation-artifacts/phase-2/2-4-document-and-test-expanded-group-and-input-behavior.md
README.md
docs/prompts/example-uses.md
docs/prompts/command-reference.md
docs/integrations/home-assistant.md
docs/integrations/n8n.md
tests/unit/test_integration_docs.py
tests/contract/tool_schemas/test_input_tool_schemas.py
tests/contract/tool_schemas/test_groups_tool_schemas.py
tests/contract/tool_schemas/test_groups_audio_tool_schemas.py
tests/contract/tool_schemas/test_group_rooms_tool_schema.py
tests/contract/tool_schemas/test_system_tool_schemas.py
tests/integration/transports/test_http_bootstrap.py
```

### Project Structure Notes

- No `project-context.md` file was present during story creation, so the BMAD planning artifacts, current docs tree, and current source/test tree are the authoritative context.
- This story should strengthen the existing docs-and-tests layers around Epic 2. It should not create a new documentation subsystem or a separate integration-specific runtime path.
- The legacy Phase 1 tracker key for `2-4` still exists in the sprint tracker. Preserve that tracker shape, but treat this Phase 2 story file and the phase index as the canonical reference for the current work item.

### References

- Story definition: `_bmad-output/planning-artifacts/epics.md#Story-24-Document-and-test-expanded-group-and-input-behavior`
- Epic context: `_bmad-output/planning-artifacts/epics.md#Epic-2-Input-and-Group-Audio-Expansion`
- Architecture patterns: `_bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions-Refresh`
- Implementation patterns: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`
- Current tool wiring: `src/soniq_mcp/tools/__init__.py`
- Current docs regression suite: `tests/unit/test_integration_docs.py`
- Current top-level product docs: `README.md`
- Current usage docs: `docs/prompts/example-uses.md`
- Current command/operator docs: `docs/prompts/command-reference.md`
- Current integration docs: `docs/integrations/home-assistant.md`
- Current integration docs: `docs/integrations/n8n.md`
- Previous story context: `_bmad-output/implementation-artifacts/phase-2/2-1-support-capability-aware-input-switching.md`
- Previous story context: `_bmad-output/implementation-artifacts/phase-2/2-2-add-group-level-volume-and-mute-controls.md`
- Previous story context: `_bmad-output/implementation-artifacts/phase-2/2-3-strengthen-topology-and-grouping-support-for-expanded-audio-flows.md`
- External reference: [PyPI soco](https://pypi.org/project/soco/)
- External reference: [MCP Tools Specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- 2026-04-10 13:02:33 SAST: audited the Epic 2 docs surface in `README.md`, `docs/prompts/example-uses.md`, `docs/integrations/home-assistant.md`, and `docs/integrations/n8n.md` against the registered tools in `src/soniq_mcp/tools/__init__.py`
- 2026-04-10 13:02:33 SAST: added docs regressions in `tests/unit/test_integration_docs.py` and tightened contract coverage in `tests/contract/tool_schemas/test_input_tool_schemas.py`, `tests/contract/tool_schemas/test_groups_audio_tool_schemas.py`, and `tests/contract/tool_schemas/test_group_rooms_tool_schema.py`
- 2026-04-10 13:02:33 SAST: verified focused suites with `uv run pytest tests/unit/test_integration_docs.py tests/contract/tool_schemas/test_input_tool_schemas.py tests/contract/tool_schemas/test_groups_tool_schemas.py tests/contract/tool_schemas/test_groups_audio_tool_schemas.py tests/contract/tool_schemas/test_group_rooms_tool_schema.py tests/contract/tool_schemas/test_system_tool_schemas.py tests/integration/transports/test_http_bootstrap.py`
- 2026-04-10 13:02:33 SAST: verified repo-wide regressions with `make test` and style checks with `make lint`

### Completion Notes List

- Updated the top-level product docs and usage examples to surface the shipped Epic 2 input, `group_rooms`, and group-audio tools without changing transport semantics.
- Added direct-client and automation examples that explicitly distinguish room-level controls from group-level controls and input-specific controls.
- Refreshed the Home Assistant and `n8n` integration guides so both start with `ping`, `server_info`, and `list_rooms`, then demonstrate current input/group flows while keeping SoniqMCP as the execution layer only.
- Extended docs regressions to lock Epic 2 tool visibility and the control-boundary language used in user-facing guidance.
- Tightened contract coverage for input and group tools to lock safe-invocation annotations plus structured validation/connectivity error shapes relied on by docs and integrators.
- Validation completed: focused docs/contract/transport suites passed, `make test` passed (`1119 passed, 3 skipped`), and `make lint` passed.
- Resolved the Home Assistant example review finding by grouping the target rooms before calling `set_group_volume`.

### File List

- README.md
- docs/prompts/example-uses.md
- docs/integrations/home-assistant.md
- docs/integrations/n8n.md
- tests/unit/test_integration_docs.py
- tests/contract/tool_schemas/test_input_tool_schemas.py
- tests/contract/tool_schemas/test_groups_audio_tool_schemas.py
- tests/contract/tool_schemas/test_group_rooms_tool_schema.py

### Change Log

- 2026-04-10: Hardened Epic 2 docs and regression coverage for input switching, explicit room grouping, and group-audio controls; validated focused suites plus full test and lint passes.
