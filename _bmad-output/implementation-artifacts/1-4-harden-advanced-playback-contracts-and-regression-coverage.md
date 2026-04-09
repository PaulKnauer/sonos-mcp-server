# Story 1.4: Harden advanced playback contracts and regression coverage

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want the new advanced playback and audio tools to use consistent schemas and tests,
so that the expanded capability surface remains stable across transports and future changes.

## Acceptance Criteria

1. **Contract stability across transports:** Given the advanced playback and audio tools are implemented, when contract tests run, then tool names, parameter shapes, and response fields remain stable across supported transports.

2. **Hardware-independent regression coverage:** Given unit and integration tests run in default CI, when the advanced playback and audio stories are exercised, then the tests pass without requiring real Sonos hardware.

3. **Direct and agent-mediated documentation parity:** Given the new tools are documented, when examples are reviewed, then the documentation shows how the same capability family works in both direct AI-client and agent-mediated usage.

## Tasks / Subtasks

- [x] Harden advanced playback and audio contract tests (AC: 1)
  - [x] Audit `tests/contract/tool_schemas/test_play_mode_tool_schemas.py`, `tests/contract/tool_schemas/test_playback_tool_schemas.py`, and `tests/contract/tool_schemas/test_audio_tool_schemas.py` for missing assertions around parameter types, required fields, and normalized response fields.
  - [x] Add regression assertions that explicitly lock the request schema for `set_play_mode`, `seek`, `set_sleep_timer`, `set_bass`, `set_treble`, and `set_loudness`.
  - [x] Extend transport-parity coverage in `tests/integration/transports/test_http_bootstrap.py` so representative advanced playback/audio tools compare metadata and parameter schemas between `stdio` and HTTP.
  - [x] Keep the checks hardware-independent by using registered-app fakes and server bootstrap only; do not introduce live Sonos dependencies.

- [x] Expand unit and integration regression coverage for advanced playback/audio paths (AC: 1, 2)
  - [x] Add or extend unit tests in `tests/unit/tools/test_playback.py`, `tests/unit/tools/test_audio.py`, `tests/unit/services/test_playback_service_seek_sleep_timer.py`, and other adjacent playback/audio suites to cover regression-prone validation and response-shape behavior.
  - [x] Cover the same failure taxonomy already established elsewhere: `RoomNotFoundError`, typed validation errors, operational errors, and discovery errors.
  - [x] Add focused tests for advanced-playback contract edge cases that have recently proven fragile, especially schema drift, FastMCP coercion boundaries, and stable error-field/category mapping.
  - [x] Keep the default automated path green under `uv run pytest -q` and `make lint`.

- [x] Document advanced playback/audio examples for both direct and agent-mediated usage (AC: 3)
  - [x] Update `docs/prompts/example-uses.md` with direct-client examples for play modes, seek, sleep timer, and room EQ.
  - [x] Add matching automation/agent-mediated examples in the same prompt guide showing the same tool family over Streamable HTTP, without inventing a separate "agent mode".
  - [x] Update any nearby documentation index or prompt reference only if needed to keep the new examples discoverable; prefer extending the existing prompt docs over creating new parallel docs.

- [x] Verify story-complete quality gates (AC: 1, 2, 3)
  - [x] Run the focused advanced playback/audio test slices first.
  - [x] Run the full regression suite and lint checks before moving the story to review.
  - [x] Confirm documentation examples match the implemented tool names and current transport guidance.

## Dev Notes

### Story intent and scope

- This is a hardening story, not a new capability story.
- Reuse the existing advanced playback and audio implementation from Stories `1.1`, `1.2`, and `1.3`; do not introduce new Sonos feature surface unless a failing contract/test/doc gap proves it is required.
- The goal is to make the current tool surface harder to break through schema drift, transport drift, weak regression coverage, or stale prompt documentation.

### Existing capability surface to protect

- Play mode tools: `get_play_mode`, `set_play_mode`
- Playback tools added in Story `1.2`: `seek`, `get_sleep_timer`, `set_sleep_timer`
- Audio tools added in Story `1.3`: `get_eq_settings`, `set_bass`, `set_treble`, `set_loudness`

### Architecture guardrails

- Preserve the existing `transport -> tools -> services -> adapters` boundary. Do not call `SoCo` outside `SoCoAdapter`. [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries]
- Keep advanced playback in `tools/playback.py` and service-layer playback modules, and keep EQ in `tools/audio.py` / `services/audio_settings_service.py`. Do not collapse these capabilities back into a generic service or module. [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries]
- Request/response consistency and error taxonomy remain shared cross-cutting concerns handled through `schemas/responses.py`, `schemas/errors.py`, and `domain/exceptions.py`. [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping]

### Testing requirements

- Contract tests must continue to validate tool names, parameter schemas, response formats, and error mappings, and they must stay stable across transports. [Source: _bmad-output/planning-artifacts/architecture.md#Test Organization]
- Integration tests should validate MCP bootstrap and transport parity, not real speaker interaction. [Source: _bmad-output/planning-artifacts/architecture.md#Test Organization]
- Most tests must run without real Sonos hardware; hardware-dependent paths must stay isolated from default automation. [Source: _bmad-output/planning-artifacts/architecture.md#Test Organization]
- The canonical repo commands are `make test`, `make lint`, and the full local quality gate already wraps `uv` consistently; prefer those patterns instead of inventing new command flows. [Source: docs/prompts/command-reference.md]

### Documentation requirements

- `docs/prompts/example-uses.md` is already the main place for direct-client prompts plus agent-mediated examples. Extend that file instead of creating a new duplicated guide unless a clear gap remains.
- Keep the documented rule intact: direct AI clients and automations use the same tool surface; there is no separate "agent mode" in SoniqMCP. [Source: docs/prompts/example-uses.md]
- Any direct vs remote wording must stay aligned with the existing setup docs for `stdio` and Streamable HTTP. [Source: docs/setup/README.md, docs/integrations/README.md, docs/integrations/claude-desktop.md]

### Previous story intelligence

- Story `1.3` exposed a real regression risk: preserving service-level validation behavior can accidentally loosen the client-visible MCP schema if FastMCP/Pydantic signatures are changed carelessly.
- The accepted fix pattern in `tools/audio.py` uses `Annotated[object, Field(json_schema_extra=...)]` so invalid raw inputs still reach service validation while the generated schema keeps explicit `integer` / `boolean` types.
- Story `1.4` should generalize that lesson into regression tests where appropriate rather than relying on memory or one-off review fixes.
- Story `1.3` also established that full regression verification is expected before review (`uv run pytest -q`, `make lint`).

### Git and repo intelligence

- Recent commits show Story `1.3` hardening happened in multiple passes, including review follow-ups (`5e387c7 Story 1.3 more review findings and fixes`, `3436b72 Fixed Story 1.3 lint errors`).
- Treat this as a signal that advanced-playback contract stability is regression-prone enough to deserve explicit guardrail tests, not just happy-path coverage.

### Latest technical information

- The repo currently targets Python `>=3.12`, `mcp[cli]>=1.26.0`, and `soco>=0.30.14`; new work in this story should stay inside that stack rather than introducing alternative tooling. [Source: pyproject.toml]
- The MCP tools specification defines a tool’s `inputSchema` as the JSON Schema for expected parameters, so schema regressions are externally visible API changes, not just internal typing issues. [Source: https://modelcontextprotocol.io/specification/2025-06-18/server/tools]
- Pydantic v2 documents `Field(..., json_schema_extra=...)` as a supported field-level way to customize generated JSON Schema, which is directly relevant to preserving tool schemas without forcing runtime coercion. [Source: https://docs.pydantic.dev/latest/concepts/json_schema/]

### Likely files to touch

- `tests/contract/tool_schemas/test_play_mode_tool_schemas.py`
- `tests/contract/tool_schemas/test_playback_tool_schemas.py`
- `tests/contract/tool_schemas/test_audio_tool_schemas.py`
- `tests/contract/error_mapping/test_error_schemas.py` if advanced playback/audio error mapping gaps are found
- `tests/integration/transports/test_http_bootstrap.py`
- `tests/unit/tools/test_playback.py`
- `tests/unit/tools/test_audio.py`
- `tests/unit/services/test_playback_service_seek_sleep_timer.py`
- `docs/prompts/example-uses.md`
- Possibly `docs/prompts/README.md` or `README.md` only if discoverability of the new examples is otherwise poor

### Project Structure Notes

- The project already uses capability-aligned modules under `src/soniq_mcp/tools`, `src/soniq_mcp/services`, `tests/unit`, `tests/integration/transports`, and `tests/contract/tool_schemas`; keep new work within those established slices.
- Avoid creating a generic “advanced_controls” module or a parallel test bucket. The architecture explicitly prefers capability-area grouping such as `playback.py`, `audio.py`, and their matching tests.
- Keep `snake_case` tool names, parameters, and response fields. Contract tests should enforce the public surface, not just internal behavior.

### References

- Story definition and acceptance criteria: [epics.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/epics.md)
- Phase-2 feature intent and NFR coverage: [prd.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd.md)
- Architecture boundaries, testing, and capability mapping: [architecture.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/architecture.md)
- Previous story implementation learnings: [1-3-add-room-level-audio-eq-controls.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/1-3-add-room-level-audio-eq-controls.md)
- Existing prompt examples for direct and agent-mediated usage: [example-uses.md](/Users/paul/github/sonos-mcp-server/docs/prompts/example-uses.md)
- Canonical repo command surface: [command-reference.md](/Users/paul/github/sonos-mcp-server/docs/prompts/command-reference.md)
- Claude Desktop and transport guidance: [claude-desktop.md](/Users/paul/github/sonos-mcp-server/docs/integrations/claude-desktop.md)
- Integration posture for agent-mediated usage: [README.md](/Users/paul/github/sonos-mcp-server/docs/integrations/README.md)
- MCP tools specification: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- Pydantic JSON Schema customization: https://docs.pydantic.dev/latest/concepts/json_schema/

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- Ultimate context engine analysis completed - comprehensive developer guide created
- Added explicit schema-type guardrails for advanced playback and audio contract tests, including `set_play_mode`, `seek`, and `set_sleep_timer`.
- Expanded HTTP-vs-stdio metadata parity checks to include advanced playback/audio tools so transport drift is caught in one integration slice.
- Focused advanced playback/audio validation: `191 passed` across contract, transport, tool, and service suites.
- Full regression rerun after Story 1.4 changes: `928 passed, 3 skipped`; `make lint` passes.

### Completion Notes List

- Identified Story `1.4` as the next backlog story in sprint order and generated a dedicated implementation story file.
- Included cross-story guardrails from Stories `1.1` through `1.3`, especially the schema-drift lesson from the Story `1.3` review follow-up.
- Mapped the story to the exact test and documentation files already used for advanced playback/audio capability coverage.
- Hardened advanced playback contract coverage by asserting stable parameter schema types and normalized response fields for play mode, seek, sleep timer, and EQ setters.
- Extended transport parity coverage in `tests/integration/transports/test_http_bootstrap.py` to compare advanced playback/audio tool metadata and parameter schemas across HTTP and `stdio`.
- Added missing playback tool assertions for stable `field` values on playback and discovery failures in sleep timer flows.
- Expanded `docs/prompts/example-uses.md` with direct-client and Streamable HTTP automation examples for play mode, seek, sleep timer, and room EQ.

### File List

- `_bmad-output/implementation-artifacts/1-4-harden-advanced-playback-contracts-and-regression-coverage.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `docs/prompts/example-uses.md`
- `tests/contract/tool_schemas/test_play_mode_tool_schemas.py`
- `tests/contract/tool_schemas/test_playback_tool_schemas.py`
- `tests/integration/transports/test_http_bootstrap.py`
- `tests/unit/tools/test_playback.py`

### Change Log

- Story 1.4 implementation: harden advanced playback/audio contract tests, transport parity checks, and prompt examples for direct and agent-mediated usage (Date: 2026-04-09)
