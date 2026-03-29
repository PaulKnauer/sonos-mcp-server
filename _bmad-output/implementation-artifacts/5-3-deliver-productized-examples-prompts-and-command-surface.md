# Story 5.3: Deliver Productized Examples, Prompts, and Command Surface

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want examples and common commands collected in one place,
so that I can adopt the product quickly and use it confidently.

## Acceptance Criteria

1. Given the MVP features are implemented, when the user reviews the product documentation and command surface, then the project provides example prompts and example use cases for direct and agent-mediated usage.
2. Given the MVP features are implemented, when the user reviews the product documentation and command surface, then the `Makefile` exposes the agreed developer and operator commands.
3. Given the MVP features are implemented, when the user reviews the product documentation and command surface, then documentation treats examples, diagnostics, and onboarding as first-class product assets.
4. Given the MVP features are implemented, when the user reviews the product documentation and command surface, then the docs remain aligned with the actual implementation and deployment paths.

## Tasks / Subtasks

- [x] Consolidate the user-facing prompt and command surface into an intentional docs path (AC: 1, 3, 4)
  - [x] Audit `README.md`, `docs/setup/README.md`, `docs/prompts/README.md`, and `docs/prompts/example-uses.md` for overlap, stale guidance, and missing navigation between setup, integrations, troubleshooting, and prompts.
  - [x] Decide whether the product should keep a single canonical prompt/command reference in `docs/prompts/example-uses.md` or split prompt examples from operator command references, then implement that structure consistently without duplicating unsupported claims.
  - [x] Ensure the entry-point docs route readers clearly from quick start to setup model, integration guide, troubleshooting, and prompt/reference material.

- [x] Align the `Makefile` command surface with the documented developer/operator workflows (AC: 2, 4)
  - [x] Audit current targets in `Makefile` against the commands already promised across `README.md`, `docs/setup/*.md`, and `docs/prompts/example-uses.md`.
  - [x] Add, rename, or clarify targets only if needed to make the command surface coherent for MVP users and maintainers; avoid speculative targets that are not backed by actual workflows.
  - [x] Document the final command surface in the canonical user-facing location with brief intent for each supported target.

- [x] Expand and tighten scenario-based examples for direct and agent-mediated usage (AC: 1, 3, 4)
  - [x] Keep direct-client examples for setup verification, room targeting, playback, volume, queue, favourites, and grouping aligned with the current tool names and safety rules.
  - [x] Add or refine representative agent-mediated examples that build on Story 5.1 guidance for Home Assistant, `n8n`, and generic remote MCP consumers without implying product-specific runtime logic inside `src/`.
  - [x] Ensure examples distinguish local `stdio` usage from remote `Streamable HTTP` usage and reinforce explicit room targeting, safe defaults, and current deployment caveats.

- [x] Add regression coverage so docs and command references cannot silently drift (AC: 2, 3, 4)
  - [x] Extend `tests/unit/test_integration_docs.py` or add a focused docs-regression test module that asserts the root docs surface prompt/reference guidance, key `Makefile` targets, and supported deployment caveats.
  - [x] Add a lightweight test that inspects `Makefile` content directly so the documented core targets stay aligned with the actual file.
  - [x] Keep the coverage hardware-independent and content-focused; validate truthfulness of docs and command names rather than exercising Sonos devices.

- [x] Verify the story using the canonical quality gates (AC: 1, 2, 3, 4)
  - [x] Run targeted pytest coverage for the docs and command-surface assertions while iterating.
  - [x] Run the relevant repo gates from the `Makefile` or equivalent `uv run` commands for linting, typing, and tests before review.

## Dev Notes

### Story Intent

This story should make the product feel finished at the entry points users actually read:

- the root README and setup overview should explain where to start,
- the prompt/examples docs should help users succeed quickly,
- and the `Makefile` should function as a reliable, documented command surface instead of a grab-bag of semi-documented targets.

The likely center of gravity is docs consolidation plus docs-regression testing. Only change runtime code if a real mismatch between the documented command surface and actual implementation forces it.

### What Already Exists

**Current docs surface**

- `README.md` already provides a quick start, configuration table, docs index, and a `Make targets` table.
- `docs/setup/README.md` already compares the three deployment models and routes users into setup and integration guides.
- `docs/prompts/example-uses.md` already mixes direct-client prompts, automation examples, a Makefile reference, CLI invocation examples, and Claude Desktop config snippets.
- `docs/prompts/README.md` exists, but today it is a thin index and not yet a strong product entry point.

**Current command surface**

- `Makefile` already exposes install, run, quality, Docker, Compose, and Helm targets.
- Setup docs already reference concrete targets such as `make install`, `make run`, `make docker-build`, `make docker-run`, `make helm-lint`, `make helm-template`, and `make helm-install`.
- The main product docs currently duplicate some of the same command explanations in multiple places, which creates drift risk.

**Current regression coverage**

- `tests/unit/test_integration_docs.py` already protects the Story 5.1 integration docs, prompt examples, and deployment-caveat wording.
- There is not yet a dedicated regression test ensuring the user-facing command reference stays aligned with the real `Makefile`.

### Previous Story Intelligence

Story 5.1 and Story 5.2 established patterns this story should keep:

- treat documentation, examples, diagnostics, and onboarding as product work rather than follow-up polish,
- avoid overstating Docker, Helm, or automation support beyond what the code and docs actually provide,
- keep all transport and integration semantics shared across `stdio` and `Streamable HTTP`,
- and prefer hardware-independent regression tests that lock in truthful user-facing guidance.

Story 5.2 also tightened the troubleshooting posture. Story 5.3 should link to that guidance where helpful instead of repeating large chunks of diagnostic content.

### Architecture Guardrails

- Keep documentation and examples under the documented structure: `docs/setup/`, `docs/integrations/`, and `docs/prompts/`.
- Keep MCP semantics transport-agnostic. Do not create a separate "agent mode" or alternate command surface in runtime code.
- Treat examples, diagnostics, and onboarding content as first-class architecture concerns, not secondary artifacts.
- Keep deployment guidance aligned with real paths: local `stdio`, Docker HTTP, and Helm HTTP with the documented caveats.
- Avoid exposing sensitive configuration, private network details, or filesystem-specific secrets in examples and sample outputs.

### Project Structure Notes

- The architecture file mentions `docs/prompts/example-uses.md` but not a richer docs reference subtree. Prefer evolving the current docs layout rather than inventing a new top-level documentation area unless there is a clear product reason.
- `docs/prompts/example-uses.md` is currently doing multiple jobs: prompts, operator commands, CLI examples, and client config snippets. The dev should decide whether to keep that as the canonical "product command surface" page or split it cleanly into smaller docs with obvious entry points.
- If a split is introduced, keep links explicit from `README.md` and `docs/prompts/README.md` so the product surface becomes easier to navigate, not more fragmented.

### Expected File Touches

Likely to modify:

- `Makefile`
- `README.md`
- `docs/setup/README.md`
- `docs/prompts/README.md`
- `docs/prompts/example-uses.md`
- `tests/unit/test_integration_docs.py`

Likely to add only if a split improves clarity:

- a focused prompt/reference markdown file under `docs/prompts/`
- a focused docs regression test module under `tests/unit/`

Potentially inspect but avoid changing unless required:

- `docs/setup/stdio.md`
- `docs/setup/docker.md`
- `docs/setup/helm.md`
- `docs/setup/troubleshooting.md`
- `docs/integrations/README.md`
- `docs/integrations/claude-desktop.md`
- `docs/integrations/home-assistant.md`
- `docs/integrations/n8n.md`

### Implementation Guidance

**Docs information architecture**

- Pick one canonical place where users can see supported prompt examples and the supported command surface.
- Keep `README.md` concise: it should route, summarize, and set expectations, not become the only reference for every command and usage pattern.
- Use `docs/prompts/README.md` as a real index if you add more than one prompt/reference page.

**Command-surface discipline**

- The `Makefile` should remain the canonical executable command surface for developers and operators.
- If a target is documented prominently, it should exist and do what the docs say.
- If a target exists but is not meant to be part of the supported product workflow, document it minimally or move it out of the main user-facing tables.
- Avoid introducing shell-heavy, environment-specific, or destructive targets just to make the docs look comprehensive.

**Examples and prompts**

- Keep natural-language prompts grounded in the current tool names: `list_rooms`, `get_system_topology`, `play`, `set_volume`, `get_queue`, `list_favourites`, `get_group_topology`, `ping`, `server_info`, and related implemented tools.
- Preserve the existing safety posture around explicit room targeting and `SONIQ_MCP_MAX_VOLUME_PCT`.
- Make it obvious when a workflow assumes local `stdio` versus remote `http://<host>:8000/mcp`.
- Reuse and link the integration guides rather than embedding large vendor-specific walkthroughs in the prompt page.

**Testing**

- Prefer string/content assertions that protect the documented product surface from drift.
- Tests should verify both presence and truthfulness: key links exist, core targets are documented, and caveated deployment paths remain caveated.
- Keep tests resilient to minor wording changes by focusing on the product-critical phrases and command names rather than copying full paragraphs.

### Anti-Patterns To Avoid

- Do not add client-specific runtime logic or dependencies to `src/` to satisfy example docs.
- Do not duplicate the same Make target table and full prompt catalog across multiple docs without a clear canonical source.
- Do not document public-internet exposure, remote platform behavior, or deployment guarantees that the current implementation does not support.
- Do not let examples bypass explicit targeting or existing safety constraints.
- Do not create test coverage that depends on real Sonos hardware for a docs-and-command-surface story.

### Git Intelligence Summary

Recent Epic 5 work has followed a "docs plus truthfulness plus regression tests" pattern:

- `9370bea` implemented Story 5.1 with docs and parity validation.
- `6e34f76` tightened Story 5.1 after review by correcting overstatements in deployment guidance.
- `6a68e1d` marked Story 5.1 done after follow-up validation.
- `4f55185` implemented Story 5.2 with shared diagnostics, docs alignment, and tests.
- `feac5bf` addressed Story 5.2 findings and fixes.

Use the same standard here: improve the product-facing surface, then lock the claims in with tests so later changes cannot silently drift.

### Library / Framework Requirements

- Stay within the current project baseline in `pyproject.toml`: Python `>=3.12`, `mcp[cli]>=1.26.0`, `python-dotenv>=1.2.2`, and `soco>=0.30.14`.
- Use the existing quality stack only: `pytest`, `ruff`, and `mypy`.
- Do not add a documentation framework, CLI helper library, or task-runner dependency for this story unless there is a concrete gap the current markdown-plus-Makefile structure cannot solve.

### Verification Notes

Use the Makefile as the canonical command surface when practical. Prefer the smallest commands that prove the story while iterating:

- `uv run pytest tests/unit/test_integration_docs.py`
- `uv run pytest tests/unit/test_integration_docs.py tests/integration/transports/test_http_bootstrap.py`
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src`

Run broader `make test`, `make lint`, `make type-check`, or `make ci` if the final diff changes more than docs and doc-regression coverage.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Integration-Diagnostics-and-Productized-Adoption]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-53-Deliver-Productized-Examples-Prompts-and-Command-Surface]
- [Source: _bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting]
- [Source: _bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration]
- [Source: _bmad-output/planning-artifacts/prd.md#Integration]
- [Source: _bmad-output/planning-artifacts/prd.md#Security]
- [Source: _bmad-output/planning-artifacts/prd.md#Maintainability-and-Quality]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend-Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Development-Server-Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Deployment-Structure]
- [Source: _bmad-output/implementation-artifacts/5-1-support-agent-mediated-integration-patterns.md]
- [Source: _bmad-output/implementation-artifacts/5-2-deliver-consistent-diagnostics-and-troubleshooting-support.md]
- [Source: README.md]
- [Source: Makefile]
- [Source: docs/setup/README.md]
- [Source: docs/prompts/README.md]
- [Source: docs/prompts/example-uses.md]
- [Source: docs/integrations/README.md]
- [Source: tests/unit/test_integration_docs.py]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from sprint-status auto-discovery and Epic 5 artifact analysis on 2026-03-29.
- `uv run pytest tests/unit/test_integration_docs.py`
- `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff check tests/unit/test_integration_docs.py`
- `env UV_CACHE_DIR=/tmp/uv-cache uv run ruff format --check tests/unit/test_integration_docs.py`
- `env UV_CACHE_DIR=/tmp/uv-cache uv run mypy src`
- `make test`

### Completion Notes List

- Split the product-facing docs surface so `docs/prompts/example-uses.md` stays focused on prompts and usage flows while `docs/prompts/command-reference.md` becomes the canonical command surface.
- Tightened the root README and setup overview so users are routed from quick start into setup, troubleshooting, integrations, prompt examples, and the command reference without repeating large target tables.
- Kept the existing `Makefile` targets unchanged after auditing them against the docs, then documented the supported targets and direct CLI paths in one canonical location.
- Extended docs regression coverage to assert prompt/reference routing, deployment caveats, and alignment between documented core `make` targets and the actual `Makefile`.
- Verified the story with targeted docs regression tests, Ruff checks, `mypy src`, and a full `make test` run.

### File List

- README.md
- docs/setup/README.md
- docs/prompts/README.md
- docs/prompts/example-uses.md
- docs/prompts/command-reference.md
- tests/unit/test_integration_docs.py

### Change Log

- 2026-03-29: Implemented Story 5.3 by productizing the prompt and command docs surface, adding a canonical command reference, and extending docs regression coverage; moved story to review.
