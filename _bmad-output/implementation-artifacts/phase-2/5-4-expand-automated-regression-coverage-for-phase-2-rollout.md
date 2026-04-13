# Story 5.4: Expand automated regression coverage for phase-2 rollout

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want the expanded capability surface covered by automated regression checks,
so that phase 2 can ship without weakening transport, safety, or documentation guarantees.

## Acceptance Criteria

1. Given the phase-2 epics are implemented, when unit, integration, contract, and smoke tests run in CI, then the checks cover the new capability families, transport parity, and regression-prone validation behavior.
2. Given phase-2 documentation and examples change, when release validation is performed, then the release includes current docs and example assets aligned with the implemented tool surface.

## Tasks / Subtasks

- [x] Audit the current regression matrix for remaining phase-2 rollout gaps (AC: 1, 2)
  - [x] Review the current test layers under `tests/unit/`, `tests/contract/`, `tests/integration/`, and `tests/smoke/` to identify which phase-2 families are already frozen by automation and which are still protected only indirectly
  - [x] Review `Makefile`, `pyproject.toml`, the build outputs under `dist/`, and any release-helper tests to determine what release validation currently proves about docs/example assets versus what it merely assumes
  - [x] Confirm the story expands regression coverage additively without duplicating Story 5.1 schema/error work, Story 5.2 transport/exposure work, or Story 5.3 docs-routing checks unless a real gap is found

- [x] Expand automated regression coverage for the highest-signal phase-2 risks (AC: 1)
  - [x] Add or refine tests at the right layer for any phase-2 families whose request/response behavior, typed validation semantics, or transport parity remain weakly covered
  - [x] Prefer contract and unit tests for schema and validation guarantees, integration tests for transport/bootstrap boundaries, and smoke tests for end-to-end invocation parity without a real Sonos environment
  - [x] Keep the regression additions hardware-independent and focused on behaviors that are most likely to drift during rollout hardening

- [x] Strengthen release-validation coverage for phase-2 docs and example assets (AC: 2)
  - [x] Add or extend release-oriented tests so the intended release process proves that the current docs and prompt/example assets exist, are the expected canonical files, and remain aligned with the implemented phase-2 surface
  - [x] Be explicit about the current artifact boundary: the built wheel and sdist do not presently include the docs tree, so validation must either check the intended release channel directly or make a deliberate packaging change instead of assuming the assets are already shipped
  - [x] Keep the validation truthful about what a package build, GitHub release, or repo-based release flow actually distributes in this project

- [x] Reuse and extend the existing regression anchors instead of inventing parallel ones (AC: 1, 2)
  - [x] Build on `tests/integration/transports/test_http_bootstrap.py`, `tests/smoke/streamable_http/test_streamable_http_smoke.py`, `tests/unit/test_integration_docs.py`, and the existing release-helper tests where they already cover part of the rollout contract
  - [x] Add new test files only when the current suite has no clear home for the missing signal
  - [x] Keep the assertions truth-focused and resilient enough to support editorial cleanup and safe refactors without turning CI into a prose lockfile

- [x] Verify the expanded rollout regression suite with the canonical quality gates (AC: 1, 2)
  - [x] Run the targeted test files added or updated for this story while iterating
  - [x] Run lint and format checks on any touched Python files
  - [x] Run `make ci` after the final regression additions to confirm the full rollout gate passes end-to-end

### Review Findings

- [x] [Review][Patch] Release-channel asset check only proves local file existence, not tagged-release truth [tests/unit/test_release_script.py:119]
- [x] [Review][Patch] Publish workflow test is brittle to YAML formatting and exact checkout count instead of asserting release semantics [tests/unit/test_release_script.py:137]
- [x] [Review][Patch] Command-reference coverage guardrail relies on a hand-maintained subset, so undocumented phase-2 tools can still slip through [tests/unit/test_release_script.py:128]

## Dev Notes

### Story intent

- Epic 5 is the rollout-hardening epic for the expanded phase-2 surface. Story 5.4 is the final regression-expansion slice: it should tighten automated guardrails around the shipped phase-2 surface, not add new Sonos capabilities and not re-open the docs-refresh scope from Story 5.3 except where release validation must check those docs explicitly.
- The implementation goal is to increase confidence that the phase-2 rollout can be shipped repeatedly through CI and release validation without silent drift in schemas, validation behavior, transport parity, or canonical docs/example assets.
- This story should prefer high-signal automation at the correct layer over broad refactors or redundant test churn.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-54-Expand-automated-regression-coverage-for-phase-2-rollout`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]

### Previous story intelligence

- Story 5.1 already hardened schema and typed-error contracts for the phase-2 families. Story 5.4 should reuse those contract anchors rather than recreating broad schema coverage from scratch.
- Story 5.2 already froze transport-visible parity and startup-time `tools_disabled` exposure behavior across `stdio` and Streamable HTTP, including a smoke-level parity check for `browse_library` validation behavior. Story 5.4 should extend that coverage only where meaningful rollout risk remains.
- Story 5.3 already tightened the product-facing docs surface and its regression checks. Story 5.4 should treat `tests/unit/test_integration_docs.py` as an existing anchor and layer release-validation truth checks around it instead of replacing it.
- Recent Epic 5 work has followed a consistent pattern: audit the real repo surface first, tighten the highest-signal gaps, and lock the outcome with hardware-independent tests. That same pattern should remain the default here.
  [Source: `_bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/5-2-preserve-transport-parity-and-tool-exposure-controls.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/5-3-update-setup-examples-and-troubleshooting-for-phase-2.md`]
  [Source: `git log --oneline -5`]

### Current repo state to build on

- `Makefile` defines the canonical repo-wide quality gate as `make ci`, which runs Ruff, mypy, pytest with coverage, `pip-audit`, and `uv build`. Story 5.4 should keep this target authoritative and verify any new rollout guardrails fit naturally inside it.
- The current regression suite is already layered by concern:
  - `tests/contract/` for tool-schema and error-contract stability
  - `tests/integration/` for bootstrap and transport-wiring behavior
  - `tests/smoke/` for end-to-end runtime checks without real Sonos hardware
  - `tests/unit/` for service, tool, config, docs, and release-helper behavior
- `tests/integration/transports/test_http_bootstrap.py` already freezes the full tool inventory and representative metadata parity across HTTP and `stdio`, including disabled-tool parity for the phase-2 families.
- `tests/smoke/streamable_http/test_streamable_http_smoke.py` already proves a real phase-2 invocation path (`browse_library` validation) returns identical typed validation semantics across `stdio` and Streamable HTTP.
- `tests/unit/test_integration_docs.py` already protects the canonical docs routing and prompt surface created in Story 5.3.
- `tests/unit/test_release_script.py` currently covers only semantic-version bumping and release-helper mechanics. It does not yet validate whether release outputs or release-validation steps account for current docs and example assets.
- The current built sdist and wheel under `dist/` contain the Python package and metadata, but not the `docs/` tree or prompt/example assets. Story 5.4 must treat that as a real repo fact when defining “release includes current docs and example assets”; it should not assume package artifacts already ship those files.
  [Source: `Makefile`]
  [Source: `tests/integration/transports/test_http_bootstrap.py`]
  [Source: `tests/smoke/streamable_http/test_streamable_http_smoke.py`]
  [Source: `tests/unit/test_integration_docs.py`]
  [Source: `tests/unit/test_release_script.py`]
  [Source: `scripts/release.py`]
  [Source: `dist/soniq_mcp-0.4.0.tar.gz`]
  [Source: `dist/soniq_mcp-0.4.0-py3-none-any.whl`]

### Architecture guardrails

- Preserve the documented `tools -> services -> adapters` boundary model and keep test additions aligned to the existing layer responsibilities.
- Keep transport-specific assertions in transport integration and smoke tests, not in service or adapter tests.
- Keep schema and typed-error assertions in contract or unit tests, not hidden inside end-to-end smoke coverage.
- Maintain hardware independence: rollout regression coverage should rely on fake clients, bootstrap composition, typed responses, and package/build inspection rather than live Sonos hardware, Docker daemons, or Helm clusters unless a smoke test is already designed to skip safely when the environment is unavailable.
- Do not invent a second release workflow. If release validation needs to cover docs/example assets, it should extend the existing `Makefile` / `scripts/release.py` / build-validation posture or clearly validate the intended release channel.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Developer-Tool-Specific-Requirements`]

### Technical requirements

- Story 5.4 covers automated regression coverage for the full phase-2 surface introduced across Epics 1-4:
  - play modes
  - seek and sleep timer
  - room EQ
  - input switching
  - group topology and group audio controls
  - alarms
  - playlist playback and lifecycle
  - local music library browsing and playback
- AC1 is about coverage breadth and placement. The resulting automation should collectively cover capability-family behavior, transport parity, and validation paths that are most likely to regress during rollout hardening.
- AC2 is about release validation truthfulness. The implementation must validate current docs/example assets through the repo’s actual release model. If docs are not shipped in existing package artifacts, the story must not pretend they are; it must either validate the actual release channel or make a deliberate packaging/release-process change.
- The story should preserve the current repo convention that `make ci` is the final confirmation gate.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-54-Expand-automated-regression-coverage-for-phase-2-rollout`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Journey-2-Primary-User-Setup-Failure-and-Recovery-Path`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Journey-3-Home-Lab-Deployment-and-Networked-Use`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Journey-4-Mobile-and-Cross-Device-AI-Access`]

### Likely files to inspect or update

- CI and release-validation surfaces:
  - `Makefile`
  - `pyproject.toml`
  - `scripts/release.py`
  - `tests/unit/test_release_script.py`
- Existing regression anchors:
  - `tests/integration/transports/test_http_bootstrap.py`
  - `tests/smoke/streamable_http/test_streamable_http_smoke.py`
  - `tests/smoke/docker/test_docker_smoke.py`
  - `tests/smoke/helm/test_helm_smoke.py`
  - `tests/unit/test_integration_docs.py`
  - `tests/contract/tool_schemas/*.py`
  - `tests/contract/error_mapping/test_error_schemas.py`
- Product-facing docs only if release validation needs to name specific canonical assets:
  - `docs/prompts/README.md`
  - `docs/prompts/example-uses.md`
  - `docs/prompts/command-reference.md`
  - `docs/setup/README.md`
  - `docs/setup/troubleshooting.md`

### Implementation guidance

- Start by identifying real regression gaps, not by adding one test per file type mechanically. The current suite is already broad, so Story 5.4 should add the smallest set of tests that closes the highest-risk rollout holes.
- Prefer reuse over duplication. If the signal belongs naturally in `test_http_bootstrap.py`, `test_streamable_http_smoke.py`, `test_integration_docs.py`, or `test_release_script.py`, extend those files first.
- Treat the package-artifact observation as a guardrail: if the release-validation requirement is implemented through artifact inspection, the test must reflect the actual artifact boundaries. If the intended product decision is that docs/example assets must ride with package artifacts, that is a deliberate packaging change and should be implemented explicitly, not implied.
- Keep assertions robust. Story 5.3 already tightened docs regressions to avoid brittle prose lock-in; Story 5.4 should follow the same truth-focused style.
- Avoid changing runtime Sonos logic just to make tests easier. This story is about regression coverage and release validation, not product-surface behavior changes.

### Testing guidance

- Use targeted test runs while iterating for the files you touch.
- Finish with `make ci`; that is the story’s final validation gate.
- Keep all new checks safe for local development and CI:
  - no live Sonos requirement
  - no mandatory Docker/Helm runtime unless the existing smoke tests already handle environment constraints safely
  - no dependency on private release infrastructure
- If release-validation tests need temporary build outputs, generate them through the existing `uv build` / `make ci` path instead of custom ad hoc commands where possible.
  [Source: `Makefile`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]

### Project Structure Notes

- Story files for the active phase live under `_bmad-output/implementation-artifacts/phase-2/`.
- Epic 5 remains `in-progress`; this story creation should move `5-4` from `backlog` to `ready-for-dev`.
- No `project-context.md` artifact is currently present in the repo, so implementation context should come from the planning artifacts, the completed Epic 5 stories, the existing regression suite, and the current build/release surfaces.

### Git intelligence summary

- `16d574d` finalized Story 5.3, including review-driven doc regression hardening and truthful docs/tool-surface routing.
- `60c04ce` completed Story 5.2 with additive transport-parity and startup-time exposure regression coverage rather than runtime churn.
- `e312d80` completed Story 5.1 with schema and typed-error hardening for the phase-2 families.
- The recent Epic 5 pattern is consistent: add the missing guardrail at the correct layer, prove it with hardware-independent automation, and keep the implementation surface narrow.
  [Source: `git log --oneline -5`]

### Latest technical information

- The repo currently pins `mcp[cli]>=1.26.0`, `pip-audit>=2.8.0`, and `pytest>=9.0.3` in `pyproject.toml`; Story 5.4 should build on the current CI toolchain rather than introducing a parallel one.
- `make ci` currently passes end-to-end with Ruff, mypy, pytest + coverage, `pip-audit`, and `uv build`.
- `uv build` currently emits a non-blocking warning that `uv-build>=0.10.12,<0.11.0` does not include the installed `uv 0.11.0`. That warning does not currently fail CI; Story 5.4 should not absorb unrelated toolchain churn unless a regression test truly requires it.
- The current sdist and wheel contents confirm that package artifacts include Python package code and metadata, but not the `docs/` tree. Release-validation work must account for that explicitly.
  [Source: `pyproject.toml`]
  [Source: `Makefile`]
  [Source: `dist/soniq_mcp-0.4.0.tar.gz`]
  [Source: `dist/soniq_mcp-0.4.0-py3-none-any.whl`]

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-54-Expand-automated-regression-coverage-for-phase-2-rollout`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Journey-2-Primary-User-Setup-Failure-and-Recovery-Path`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Journey-3-Home-Lab-Deployment-and-Networked-Use`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Journey-4-Mobile-and-Cross-Device-AI-Access`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Developer-Tool-Specific-Requirements`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Architectural-Boundaries`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/5-2-preserve-transport-parity-and-tool-exposure-controls.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/5-3-update-setup-examples-and-troubleshooting-for-phase-2.md`]
- [Source: `Makefile`]
- [Source: `pyproject.toml`]
- [Source: `scripts/release.py`]
- [Source: `tests/integration/transports/test_http_bootstrap.py`]
- [Source: `tests/smoke/streamable_http/test_streamable_http_smoke.py`]
- [Source: `tests/smoke/docker/test_docker_smoke.py`]
- [Source: `tests/smoke/helm/test_helm_smoke.py`]
- [Source: `tests/unit/test_integration_docs.py`]
- [Source: `tests/unit/test_release_script.py`]
- [Source: `git log --oneline -5`]
- [Source: `dist/soniq_mcp-0.4.0.tar.gz`]
- [Source: `dist/soniq_mcp-0.4.0-py3-none-any.whl`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- 2026-04-13: Story created from Epic 5 planning artifacts, the phase tracker, completed Stories 5.1 through 5.3, recent git history, the current CI/build surfaces, and the existing regression suite under `tests/`.
- 2026-04-13: Confirmed `Makefile` remains the canonical quality-gate surface via `make ci`.
- 2026-04-13: Confirmed the current regression suite already has meaningful anchors in unit, contract, integration, and smoke layers, especially around transport parity and docs truthfulness.
- 2026-04-13: Confirmed the built sdist and wheel currently do not include the `docs/` tree, which is a critical release-validation fact for Story 5.4.
- 2026-04-13: Added Streamable HTTP versus `stdio` smoke parity coverage for `set_sleep_timer` validation errors so phase-2 transport validation parity is not frozen only by `browse_library`.
- 2026-04-13: Expanded release-helper tests to verify canonical docs/example assets exist in the tagged repo release surface, that `publish.yml` releases from a checked-out tag, that command-reference coverage matches the implemented phase-2 tool surface, and that built wheel/sdist artifacts still exclude `docs/`.
- 2026-04-13: Validation runs passed: `uv run pytest tests/smoke/streamable_http/test_streamable_http_smoke.py`, `uv run pytest tests/unit/test_release_script.py`, `uv run ruff check tests/smoke/streamable_http/test_streamable_http_smoke.py tests/unit/test_release_script.py`, `uv run ruff format --check tests/smoke/streamable_http/test_streamable_http_smoke.py tests/unit/test_release_script.py`, and `make ci`.
- 2026-04-13: Resolved code-review patches by making the release-channel asset check assert tracked repo content, making the publish workflow check semantic rather than formatting-count based, and tightening command-reference coverage against the full derived phase-2 runtime tool set.
- 2026-04-13: Post-review validation passed: `uv run pytest tests/unit/test_release_script.py tests/smoke/streamable_http/test_streamable_http_smoke.py`, `uv run ruff check tests/unit/test_release_script.py tests/smoke/streamable_http/test_streamable_http_smoke.py`, `uv run ruff format --check tests/unit/test_release_script.py tests/smoke/streamable_http/test_streamable_http_smoke.py`, and `make ci`.
- 2026-04-13: Follow-up review-fix pass corrected the Home Assistant and `n8n` guides to include the shared `internal` error category, moved phase-2 command-surface coverage back to the dedicated docs regression suite instead of a hand-maintained release-test partition, and simplified the publish-workflow regression check to assert release semantics without indentation-sensitive parsing.
- 2026-04-13: Follow-up validation passed: `uv run pytest -q tests/unit/test_integration_docs.py tests/unit/test_release_script.py tests/smoke/streamable_http/test_streamable_http_smoke.py`, `uv run ruff check tests/unit/test_integration_docs.py tests/unit/test_release_script.py docs/integrations/home-assistant.md docs/integrations/n8n.md tests/smoke/streamable_http/test_streamable_http_smoke.py`, and `uv run ruff format --check tests/unit/test_integration_docs.py tests/unit/test_release_script.py tests/smoke/streamable_http/test_streamable_http_smoke.py`.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story 5.4 is scoped as regression and release-validation hardening, not runtime feature expansion.
- The highest-signal implementation path is to audit existing guardrails first, then add the smallest set of missing tests at the correct layer.
- Release-validation work must stay truthful about the current artifact model: docs/example assets are not currently present in the built package artifacts.
- Added a second phase-2 smoke parity check for `set_sleep_timer` validation behavior so transport-neutral validation semantics are covered beyond the existing `browse_library` path.
- Extended `tests/unit/test_release_script.py` to verify the tagged repo release surface contains the canonical docs/example assets, the publish workflow releases from a checked-out tag, the canonical command reference still covers the implemented phase-2 tool surface, and package artifacts continue to omit `docs/`.
- Full validation completed successfully with `make ci` (`1427 passed, 3 skipped`) and targeted smoke/release test runs.
- Resolved all three review patch findings by replacing tautological and brittle release tests with tracked-repo and workflow-semantics assertions, then revalidated with targeted tests and the full `make ci` gate.
- Corrected the Home Assistant and `n8n` integration guides so they document the current shared error-category set, including `internal`.
- Moved exact phase-2 command-reference coverage back to `tests/unit/test_integration_docs.py`, which already asserts the full documented phase-2 tool surface explicitly, instead of maintaining a second tool partition inside the release-helper tests.
- Simplified the publish-workflow release test so it asserts tag-trigger and release-command semantics without relying on indentation-sensitive job-block parsing.
- Follow-up targeted validation passed: `63 passed` across docs, release, and Streamable HTTP smoke checks.

### File List

- _bmad-output/implementation-artifacts/phase-2/5-4-expand-automated-regression-coverage-for-phase-2-rollout.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- docs/integrations/home-assistant.md
- docs/integrations/n8n.md
- tests/smoke/streamable_http/test_streamable_http_smoke.py
- tests/unit/test_integration_docs.py
- tests/unit/test_release_script.py

### Change Log

- 2026-04-13: Created Story 5.4 with concrete guidance for phase-2 regression expansion, release-validation truthfulness, and final `make ci` confirmation.
- 2026-04-13: Implemented Story 5.4 by expanding transport validation smoke coverage and release-truth regression checks for canonical docs/example assets and package artifact boundaries.
- 2026-04-13: Addressed code review findings - 3 items resolved.
- 2026-04-13: Applied a follow-up review-fix pass to align integration-guide error categories with the `internal` diagnostic class and to make the release-helper regression checks less brittle and less dependent on hand-maintained tool partitions.
