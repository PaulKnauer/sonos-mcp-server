# Story 5.1: Support Agent-Mediated Integration Patterns

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an advanced user,
I want the server to work cleanly in agent and automation workflows,
so that I can use it through Home Assistant, `n8n`, and similar systems.

## Acceptance Criteria

1. Given the server is running in a supported transport mode, when an external agent system invokes the MCP tools, then the same core control model is available as in direct AI-client use.
2. Given the server is running in a supported transport mode, when an automation or agent consumer uses the MCP tools, then tool semantics remain stable and predictable for automation consumers.
3. Given the current codebase, when agent-mediated integrations are documented and validated, then integration usage does not require a different internal implementation path.
4. Given the supported documentation set, when a user looks for automation guidance, then the product supports representative examples for agent-mediated usage.

## Tasks / Subtasks

- [x] Strengthen transport-agnostic integration proof in tests (AC: 1, 2, 3)
  - [x] Add or extend integration coverage to assert that `create_server()` registers the same tool surface for `stdio` and `http` without transport-specific branching beyond `transports/bootstrap.py`.
  - [x] Add or extend contract/integration assertions that representative setup-support and Sonos control tools expose stable names and schemas regardless of transport mode.
  - [x] Keep tests hardware-independent by continuing to inspect registered tool metadata and app wiring rather than requiring live Sonos devices.

- [x] Document supported agent-mediated integration patterns (AC: 1, 2, 4)
  - [x] Replace the Epic 5 placeholder text in `docs/integrations/README.md` with actual guidance for agent and automation consumers.
  - [x] Add `docs/integrations/home-assistant.md` describing supported runtime pattern, MCP endpoint expectations, safe deployment posture, and what is and is not productized.
  - [x] Add `docs/integrations/n8n.md` with the same level of guidance, focused on using SoniqMCP as an MCP action layer rather than embedding vendor-specific product logic into the server.
  - [x] Update cross-links from `README.md` and `docs/setup/README.md` so the new integration docs are discoverable from the main setup flow.

- [x] Add representative automation and agent usage examples (AC: 2, 4)
  - [x] Expand `docs/prompts/example-uses.md` with automation-oriented examples that show stable room targeting, playback, queue, favourites, and grouping flows for downstream agents.
  - [x] Keep examples scenario-based and transport-aware: local `stdio` for same-machine clients, `Streamable HTTP` for remote or long-running services.
  - [x] Ensure examples reinforce existing safety constraints such as explicit room targeting and `SONIQ_MCP_MAX_VOLUME_PCT`.

- [x] Preserve architectural boundaries while adding docs and validation (AC: 1, 2, 3)
  - [x] Do not add Home Assistant, `n8n`, or any other agent-specific runtime dependency to `src/`.
  - [x] Do not create transport-specific Sonos logic; keep integration guidance in docs and keep runtime behavior flowing through the existing `tools -> services -> adapters` path.
  - [x] Reuse the existing MCP tool registration path in `src/soniq_mcp/tools/__init__.py` and existing server composition in `src/soniq_mcp/server.py`.

- [x] Verify the story with the project’s canonical command surface (AC: 1, 2, 4)
  - [x] Run targeted tests covering transport parity and tool-surface stability.
  - [x] Run the relevant documentation-safe quality gates from the Makefile so docs and any touched tests stay aligned with CI expectations.

## Dev Notes

### Story Intent

This story is primarily about proving and productizing an existing architectural property:

- The server already exposes a single MCP tool surface via `create_server()` and `register_all()`.
- `stdio` and `Streamable HTTP` are already transport boundaries, not separate business-logic implementations.
- The missing work is making that integration stance explicit, test-backed, and consumable for agent/automation users through docs and examples.

The dev should assume this is a docs-plus-validation story unless testing reveals a real parity gap. Do not invent a new runtime path just to satisfy the examples.

### What Already Exists

**Existing architecture and runtime behavior**

- `src/soniq_mcp/server.py` builds one `FastMCP` app and registers the shared tool surface once.
- `src/soniq_mcp/transports/bootstrap.py` dispatches only at the transport boundary to `stdio` or `streamable-http`.
- `src/soniq_mcp/tools/__init__.py` wires the tool registration stack once for all transports.
- `tests/integration/transports/test_http_bootstrap.py` already asserts that HTTP and stdio expose the same tool set.

**Existing docs and gaps**

- `docs/integrations/README.md` only lists Claude Desktop and still says other integrations are "planned for Epic 5".
- `docs/integrations/claude-desktop.md` establishes the current integration-doc style for local stdio and remote HTTP guidance.
- `docs/prompts/example-uses.md` covers direct client prompts well, but it does not yet give representative automation or agent-mediated usage patterns.
- `README.md` and `docs/setup/README.md` currently surface Claude Desktop prominently but do not yet route users to Home Assistant or `n8n` integration guides.

### Architecture Guardrails

- Keep MCP capability semantics transport-agnostic. The architecture explicitly requires the same tool surface across `stdio` and `Streamable HTTP`.
- Keep transport-specific concerns at the boundary. Do not move client-specific behavior into `services/`, `tools/`, or `adapters/`.
- Treat Home Assistant and `n8n` as reference integration patterns, not hard dependencies.
- Distinguish user-facing guidance from diagnostics, and avoid exposing sensitive config or network details unnecessarily in examples.
- Keep docs, examples, and operational assets as product-critical artifacts, not optional follow-up material.

### Expected File Touches

Likely to modify:

- `docs/integrations/README.md`
- `docs/setup/README.md`
- `docs/prompts/example-uses.md`
- `README.md`
- `tests/integration/transports/test_http_bootstrap.py`
- `tests/integration/transports/test_server_bootstrap.py`

Likely to add:

- `docs/integrations/home-assistant.md`
- `docs/integrations/n8n.md`

Potentially inspect but avoid changing unless required:

- `src/soniq_mcp/server.py`
- `src/soniq_mcp/transports/bootstrap.py`
- `src/soniq_mcp/tools/__init__.py`
- `src/soniq_mcp/tools/setup_support.py`

### Implementation Guidance

**Integration documentation**

- Follow the same structure used in `docs/integrations/claude-desktop.md`: state the supported runtime pattern, configuration expectations, when to use local vs remote mode, and concrete endpoint examples.
- Be explicit that remote agent or automation systems should usually consume the `Streamable HTTP` endpoint at `/mcp`.
- Keep guidance vendor-neutral where possible. Product-specific setup belongs in examples and configuration notes, not in source code.

**Testing**

- Reuse the existing parity strategy: inspect registered tool names and metadata instead of exercising hardware-dependent Sonos flows.
- If adding schema-level stability checks, prefer contract/integration tests that compare tool names, annotations, or schema presence across transports.
- Preserve the project rule that most automated tests must run without real Sonos hardware.

**Documentation examples**

- Use scenarios that match the PRD: Home Assistant, `n8n`, and custom agent workflows.
- Show that the same tool semantics apply whether the consumer is a direct AI client or a larger automation system.
- Reinforce safe default exposure. Local workflows should prefer `stdio`; networked automation should use trusted home-network HTTP deployments, not public exposure.

### Anti-Patterns To Avoid

- Do not add Home Assistant or `n8n` SDK dependencies to `pyproject.toml`.
- Do not create new agent-specific tool handlers or alternate service paths.
- Do not duplicate existing setup content from `docs/setup/` when a cross-link is enough.
- Do not document unsupported public-internet exposure as a normal setup pattern.
- Do not introduce examples that bypass explicit room targeting or ignore safety constraints already enforced by the product.

### Verification Notes

Use the Makefile as the canonical command surface. Prefer the smallest commands that prove the story:

- `make lint`
- `make type-check`
- `make test`
- or narrower `uv run pytest ...` targets if you only touch docs-adjacent tests during iteration

At minimum, the final implementation should demonstrate that the docs are updated and the transport-parity/tool-surface assertions still pass.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Integration-Diagnostics-and-Productized-Adoption]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-51-Support-Agent-Mediated-Integration-Patterns]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey-5-Integration-User-Building-Agentic-Experiences]
- [Source: _bmad-output/planning-artifacts/prd.md#Client-Integration-Examples]
- [Source: _bmad-output/planning-artifacts/prd.md#Documentation-and-Example-Requirements]
- [Source: _bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration]
- [Source: _bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting]
- [Source: _bmad-output/planning-artifacts/prd.md#Integration]
- [Source: _bmad-output/planning-artifacts/prd.md#Maintainability-and-Quality]
- [Source: _bmad-output/planning-artifacts/architecture.md#API--Communication-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Organization-Patterns]
- [Source: src/soniq_mcp/server.py]
- [Source: src/soniq_mcp/transports/bootstrap.py]
- [Source: src/soniq_mcp/tools/__init__.py]
- [Source: src/soniq_mcp/tools/setup_support.py]
- [Source: tests/integration/transports/test_http_bootstrap.py]
- [Source: docs/integrations/README.md]
- [Source: docs/integrations/claude-desktop.md]
- [Source: docs/prompts/example-uses.md]
- [Source: README.md]
- [Source: docs/setup/README.md]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Red phase: added transport-parity and documentation regression tests, then ran `./.venv/bin/python -m pytest tests/integration/transports/test_http_bootstrap.py tests/unit/test_integration_docs.py`; the new docs tests failed until the integration guides and links were implemented.
- Green phase: added Home Assistant and `n8n` integration guides, updated integration and setup index docs, expanded automation examples, and reran the targeted test selection successfully.
- Validation phase: `./.venv/bin/python -m pytest` passed 650 tests with 3 skipped and 4 sandbox-related smoke-test errors; reran the blocked smoke tests outside the sandbox and they passed.
- Validation phase: `./.venv/bin/ruff check src tests && ./.venv/bin/ruff format --check src tests` passed.
- Validation phase: `./.venv/bin/mypy src` passed.
- Review follow-up red phase: strengthened `tests/unit/test_integration_docs.py` to require explicit remote deployment caveats for Docker on Linux and Helm's `hostNetwork: true` manual workaround, then confirmed the new assertions failed against the prior wording.
- Review follow-up green phase: updated `README.md`, `docs/integrations/home-assistant.md`, and `docs/integrations/n8n.md` so remote deployment guidance no longer overstates Helm support and now points readers toward documented caveats.
- Review follow-up validation phase: `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/unit/test_integration_docs.py tests/integration/transports/test_http_bootstrap.py`, `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check src tests`, `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check src tests`, and `env UV_CACHE_DIR=/tmp/uv-cache uv run mypy src` all passed.
- Review follow-up validation phase: `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest` passed except for the known sandbox restrictions in Docker and streamable HTTP smoke tests; reran `env UV_CACHE_DIR=/tmp/uv-cache uv run pytest tests/smoke/docker/test_docker_smoke.py tests/smoke/streamable_http/test_streamable_http_smoke.py` outside the sandbox and all 4 smoke tests passed.

### Completion Notes List

- Added representative tool-metadata parity assertions in `tests/integration/transports/test_http_bootstrap.py` so representative tools keep matching annotations, parameter schemas, and output schemas across `stdio` and `Streamable HTTP`.
- Added `tests/unit/test_integration_docs.py` to lock in the presence of Home Assistant and `n8n` integration guides, index links, and automation examples.
- Replaced the integration placeholder content in `docs/integrations/README.md` with actual guidance and product boundaries for agent-mediated usage.
- Created `docs/integrations/home-assistant.md` and `docs/integrations/n8n.md` with supported runtime patterns, safety posture, and troubleshooting guidance.
- Updated `docs/setup/README.md` and `README.md` so the new integration guides are reachable from the primary documentation flow.
- Expanded `docs/prompts/example-uses.md` with agent and automation workflow examples that preserve explicit targeting and volume-cap safety constraints.
- Story 5.1 moved from `ready-for-dev` to `review`, and sprint tracking was updated to match.
- Tightened remote deployment wording so Docker guidance is explicitly Linux-oriented and Helm guidance is explicitly framed as a documented advanced path with a `hostNetwork: true` manual workaround.
- Extended the documentation regression tests to prevent future overstatement of Docker and Helm productization in the root and integration guides.
- Story 5.1 was accepted and marked done after review follow-up validation completed.

### File List

- `docs/integrations/README.md` (modified)
- `docs/integrations/home-assistant.md` (created)
- `docs/integrations/n8n.md` (created)
- `docs/setup/README.md` (modified)
- `docs/prompts/example-uses.md` (modified)
- `README.md` (modified)
- `tests/integration/transports/test_http_bootstrap.py` (modified)
- `tests/unit/test_integration_docs.py` (created)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified)
- `_bmad-output/implementation-artifacts/5-1-support-agent-mediated-integration-patterns.md` (modified)

## Change Log

- 2026-03-29: Story 5.1 implemented. Added transport metadata parity coverage, added integration docs for Home Assistant and `n8n`, updated documentation entry points, expanded automation examples, and validated with targeted tests, lint, mypy, and smoke-test follow-up. Status -> review.
- 2026-03-29: Addressed review follow-up on deployment claims. Qualified Docker as Linux-oriented, clarified Helm's documented `hostNetwork: true` manual workaround, expanded doc regression coverage, and revalidated the targeted and blocked smoke tests.
- 2026-03-29: Story 5.1 accepted and moved from review to done.
