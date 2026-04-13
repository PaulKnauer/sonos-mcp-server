# Story 5.2: Preserve transport parity and tool exposure controls

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator,
I want the expanded phase-2 tool surface to behave consistently across local and remote modes,
so that I can expose capabilities safely without transport-specific surprises.

## Acceptance Criteria

1. Given the expanded tool surface is available, when the same supported capability is invoked over local `stdio` and remote HTTP transport, then the functional result and response semantics remain equivalent aside from transport envelope details.
2. Given tool exposure controls are configured, when an operator disables restricted tool categories, then the phase-2 tool families respect the configured exposure posture before runtime.

## Tasks / Subtasks

- [x] Audit the current transport and exposure-control surface for phase-2 tools (AC: 1, 2)
  - [x] Review how `create_server(...)`, `register_all(...)`, and transport bootstrap currently expose tools for `stdio` and HTTP
  - [x] Identify any phase-2 tool families that are covered only by tool-schema tests but not by transport-parity assertions
  - [x] Identify any phase-2 tool families that rely on per-module `tools_disabled` checks without a regression test proving startup suppression

- [x] Freeze transport-visible parity for the full phase-2 surface without changing transport envelopes (AC: 1)
  - [x] Extend `tests/integration/transports/test_http_bootstrap.py` so the phase-2 families are represented by parity assertions across `stdio` and HTTP
  - [x] Verify parity at the MCP metadata level that is transport-neutral in this repo: tool names, annotations, parameter schemas, and output schemas
  - [x] Do not introduce transport-specific branching into tool or service logic to satisfy the story; parity should remain a registration/bootstrap guarantee

- [x] Harden pre-runtime tool exposure controls for phase-2 capability families (AC: 2)
  - [x] Confirm every phase-2 tool name remains present in `KNOWN_TOOL_NAMES` and is therefore valid for `tools_disabled`
  - [x] Add or extend tests proving that disabling phase-2 tools removes them from the registered tool surface before runtime in both local and remote server creation paths
  - [x] Preserve the existing per-tool suppression pattern in tool modules unless a verified defect requires a narrow correction

- [x] Add regression coverage at the right layer for expanded transport and exposure guarantees (AC: 1, 2)
  - [x] Extend unit tests around tool registration for phase-2 families where disabled-tool coverage is missing or too weak
  - [x] Keep transport integration checks in `tests/integration/transports/test_http_bootstrap.py` focused on registration and metadata parity, not live Sonos behavior
  - [x] Keep tests hardware-independent and avoid requiring a real Sonos environment

- [x] Run targeted validation for parity and exposure-control hardening (AC: 1, 2)
  - [x] Run the updated transport integration tests
  - [x] Run the relevant unit and/or contract suites covering disabled-tool registration for the touched phase-2 families
  - [x] Run lint and format checks on touched Python files

## Dev Notes

### Story intent

- Epic 5 is the rollout-hardening epic for the expanded phase-2 surface. Story 5.2 is the transport-parity and exposure-control slice, not the schema/error-contract slice from Story 5.1 and not the broader docs refresh reserved for Story 5.3.
- The implementation goal is to prove that the expanded phase-2 tool surface is exposed consistently across `stdio` and HTTP server creation, and that operators can suppress those tools predictably through `tools_disabled` before runtime.
- This story should harden parity and safety posture without adding new capabilities, changing transport envelope behavior, or reopening deployment-doc scope unless a minimal prerequisite correction is required.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-52-Preserve-transport-parity-and-tool-exposure-controls`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]

### Previous story intelligence

- Story 5.1 already hardened the phase-2 public contract surface and added a config-level regression guard for phase-2 `KNOWN_TOOL_NAMES`. Story 5.2 should build on that work rather than redefining the phase-2 inventory or response semantics.
- The completed Story 5.1 work also reinforced a useful pattern for Epic 5: prefer additive regression locking over broad refactors. That same discipline applies here for transport parity and `tools_disabled` coverage.
- Epic 4 finished with a parity/docs-hardening story instead of a new runtime feature slice. The carry-forward lesson remains valid: lock behavior with tests where the current implementation is already structurally sound.
  [Source: `_bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md`]
  [Source: `_bmad-output/implementation-artifacts/epic-4-retro-2026-04-13.md`]
  [Source: `git log --oneline -5`]

### Current repo state to build on

- `src/soniq_mcp/server.py` assembles the FastMCP application once and calls `register_all(app, config)`, which is the common entry point for both transport modes.
- `src/soniq_mcp/transports/bootstrap.py` dispatches between `stdio` and HTTP runners. The transport integration surface in this repo is therefore mainly about shared registration and metadata parity rather than separate handler implementations.
- `src/soniq_mcp/config/models.py` already validates `tools_disabled` against `KNOWN_TOOL_NAMES`, including the phase-2 tool families added across Epics 1-4.
- Existing phase-2 tool modules already suppress registration with `if "<tool_name>" not in config.tools_disabled`; Story 5.2 should verify and lock that behavior across the expanded families rather than replace the pattern.
- `tests/integration/transports/test_http_bootstrap.py` already checks all-tool parity and representative metadata parity across HTTP and `stdio`, but Story 5.2 should ensure the expanded phase-2 families and disabled-tool posture are explicitly frozen there and in the relevant unit tests.
  [Source: `src/soniq_mcp/server.py`]
  [Source: `src/soniq_mcp/transports/bootstrap.py`]
  [Source: `src/soniq_mcp/tools/__init__.py`]
  [Source: `src/soniq_mcp/config/models.py`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model.
- Keep transport logic in `src/soniq_mcp/transports/` and registration logic in `src/soniq_mcp/tools/`; do not introduce transport-specific Sonos behavior in tool or service code.
- Maintain a consistent MCP tool surface across `stdio` and `Streamable HTTP`, with parity enforced through registration/bootstrap behavior rather than duplicate implementations.
- Preserve the safe-default exposure posture and pre-runtime suppression model: operators should be able to disable tools via configuration before a client can invoke them.
- Do not bypass `SoniqConfig` validation or invent a second exposure-control mechanism for this story.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]

### Technical requirements

- Story 5.2 covers the expanded phase-2 families introduced across Epics 1-4:
  - play modes
  - seek and sleep timer
  - audio EQ
  - input switching
  - group audio additions
  - alarms
  - playlist lifecycle
  - library browsing and playback
- Transport parity here means the same supported tool inventory and transport-neutral metadata are exposed by server creation for both `stdio` and HTTP. This story does not require transport-envelope normalization beyond what FastMCP already provides.
- Exposure-control parity here means phase-2 tools can be disabled through `tools_disabled` using the same tool names regardless of transport mode, and suppressed tools do not register onto the app at startup.
- Keep the mental model transport-neutral for direct clients and agent-mediated clients. The capability names should remain identical across transports and exposure postures.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-52-Preserve-transport-parity-and-tool-exposure-controls`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]
  [Source: `src/soniq_mcp/config/models.py`]

### Likely files to inspect or update

- Server, transport, and config surfaces:
  - `src/soniq_mcp/server.py`
  - `src/soniq_mcp/transports/bootstrap.py`
  - `src/soniq_mcp/config/models.py`
  - `src/soniq_mcp/tools/__init__.py`
- Phase-2 tool modules whose suppression behavior may need explicit coverage:
  - `src/soniq_mcp/tools/play_modes.py`
  - `src/soniq_mcp/tools/playback.py`
  - `src/soniq_mcp/tools/audio.py`
  - `src/soniq_mcp/tools/inputs.py`
  - `src/soniq_mcp/tools/groups.py`
  - `src/soniq_mcp/tools/alarms.py`
  - `src/soniq_mcp/tools/playlists.py`
  - `src/soniq_mcp/tools/library.py`
- Tests:
  - `tests/integration/transports/test_http_bootstrap.py`
  - `tests/unit/config/test_models.py`
  - `tests/unit/tools/test_play_modes.py`
  - `tests/unit/tools/test_playback.py`
  - `tests/unit/tools/test_audio.py`
  - `tests/unit/tools/test_inputs.py`
  - `tests/unit/tools/test_groups.py`
  - `tests/unit/tools/test_groups_audio.py`
  - `tests/unit/tools/test_alarms.py`
  - `tests/unit/tools/test_playlists.py`
  - `tests/unit/tools/test_library.py`

### Implementation guidance

- Start with the transport integration test and the current disabled-tool unit coverage to identify real gaps before changing code.
- Prefer proving parity through shared registration behavior. If `create_server(...)` already yields equal tool metadata across transports, lock that contract with stronger assertions rather than refactoring implementation shape.
- Be careful not to overfit transport tests to FastMCP internals beyond the metadata this repo already treats as public contract: tool names, annotations, parameter schemas, and output schemas.
- Treat `tools_disabled` as a startup-time exposure-control contract. Tests should verify suppressed tools are absent from the registered surface, not merely that calls fail later.
- Avoid pulling Story 5.3 docs work into this implementation unless a code or test change is impossible without a tiny documentation correction.

### Testing guidance

- Reuse `tests/integration/transports/test_http_bootstrap.py` for transport-visible parity assertions.
- Reuse the per-family unit tool tests to lock disabled-tool behavior where the current coverage is missing or insufficient.
- Keep tests hardware-independent and avoid real Sonos interactions.
- If config validation changes are needed, prove them in `tests/unit/config/test_models.py` instead of relying only on higher-level tests.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]
  [Source: `tests/unit/config/test_models.py`]

### Project Structure Notes

- Story files for the active phase live under `_bmad-output/implementation-artifacts/phase-2/`.
- Epic 5 should remain `in-progress`; this story creation should move `5-2` from `backlog` to `ready-for-dev`.
- Story 5.2 should not absorb Story 5.1 schema/error work, Story 5.3 docs/troubleshooting refresh, or Story 5.4 broad regression expansion unless a minimal prerequisite change is unavoidable.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-52-Preserve-transport-parity-and-tool-exposure-controls`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]
- [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Advanced-Sonos-Automation-and-Library-Control`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md`]
- [Source: `_bmad-output/implementation-artifacts/epic-4-retro-2026-04-13.md`]
- [Source: `src/soniq_mcp/server.py`]
- [Source: `src/soniq_mcp/transports/bootstrap.py`]
- [Source: `src/soniq_mcp/tools/__init__.py`]
- [Source: `src/soniq_mcp/config/models.py`]
- [Source: `tests/integration/transports/test_http_bootstrap.py`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- 2026-04-13: Story created from Epic 5 planning artifacts, the phase tracker, completed Story 5.1 context, recent git history, and the current transport/config/tool-registration surfaces in the repo.
- 2026-04-13: Confirmed `create_server(...)` and `register_all(...)` are the shared application-composition path for both transport modes, so transport parity work should focus on registration and metadata parity instead of transport-specific business logic.
- 2026-04-13: Confirmed `tools_disabled` validation already routes through `KNOWN_TOOL_NAMES` and that the phase-2 tool modules suppress registration directly at startup via per-tool checks.
- 2026-04-13: Confirmed `tests/integration/transports/test_http_bootstrap.py` already locks broad tool-surface parity and representative metadata parity across HTTP and `stdio`, making it the correct integration-level anchor for Story 5.2.
- 2026-04-13: Identified the highest-signal gap as startup-time suppression parity across transports for the phase-2 families; the shared server/bootstrap path itself did not require runtime code changes.
- 2026-04-13: Extended transport integration coverage so phase-2 disabled-tool sets are asserted to disappear equally from the HTTP and `stdio` tool surfaces, and expanded representative metadata parity to include group-audio additions.
- 2026-04-13: Added missing unit registration coverage for `group_rooms`, following the actual public tool signature (`rooms`, optional `coordinator`) and normalized group-topology response shape.
- 2026-04-13: Addressed code-review feedback by adding a smoke-level phase-2 invocation parity check that calls `browse_library` with an invalid category over both `stdio` and Streamable HTTP and asserts identical typed validation payloads.
- 2026-04-13: Validation passed:
  - `uv run pytest -q tests/integration/transports/test_http_bootstrap.py tests/unit/tools/test_groups.py`
  - `uv run pytest -q tests/integration/transports/test_http_bootstrap.py tests/unit/config/test_models.py tests/unit/tools/test_play_modes.py tests/unit/tools/test_playback.py tests/unit/tools/test_audio.py tests/unit/tools/test_inputs.py tests/unit/tools/test_groups.py tests/unit/tools/test_groups_audio.py tests/unit/tools/test_alarms.py tests/unit/tools/test_playlists.py tests/unit/tools/test_library.py`
  - `uv run pytest -q tests/smoke/streamable_http/test_streamable_http_smoke.py`
  - `uv run ruff check tests/integration/transports/test_http_bootstrap.py tests/unit/tools/test_groups.py`
  - `uv run ruff format --check tests/integration/transports/test_http_bootstrap.py tests/unit/tools/test_groups.py`
  - `uv run pytest -q`
  - `make ci`

### Completion Notes List

- The implementation stayed additive and test-first; no runtime transport or tool-registration code changes were required because the shared bootstrap path already behaved correctly.
- Transport integration coverage now freezes startup-time suppression parity for the phase-2 families across HTTP and `stdio`.
- Smoke coverage now proves an actual phase-2 capability invocation path returns the same typed validation semantics across `stdio` and remote HTTP for `browse_library`.
- Representative metadata parity coverage now explicitly includes phase-2 group-audio additions so the expanded surface is less likely to drift silently across transports.
- Unit coverage now includes `group_rooms` registration and error handling, closing a gap in the phase-2 startup suppression story.
- Full regression validation passed: `1419 passed, 3 skipped`.
- `make ci` passed end-to-end, including Ruff, mypy, full pytest with coverage, `pip-audit`, and `uv build`.

### File List

- _bmad-output/implementation-artifacts/phase-2/5-2-preserve-transport-parity-and-tool-exposure-controls.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- tests/integration/transports/test_http_bootstrap.py
- tests/smoke/streamable_http/test_streamable_http_smoke.py
- tests/unit/tools/test_groups.py

### Change Log

- 2026-04-13: Created Story 5.2 with concrete guidance for transport-visible parity hardening and startup-time tool exposure controls across the phase-2 capability families.
- 2026-04-13: Implemented Story 5.2 by extending transport parity regression coverage for disabled phase-2 tool sets across HTTP and `stdio`, and by adding missing `group_rooms` registration coverage.
- 2026-04-13: Added smoke-level phase-2 invocation parity coverage for `browse_library` validation behavior across `stdio` and Streamable HTTP.
- 2026-04-13: Marked Story 5.2 done after review closure and successful `make ci`.
