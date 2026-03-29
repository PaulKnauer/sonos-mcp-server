# Story 5.4: Publish Operational Security and Release Guidance

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a self-hosting operator,
I want explicit security and release guidance,
so that I can run, upgrade, and expose the product without relying on guesswork.

## Acceptance Criteria

1. Given a user evaluates the product for home or home-lab deployment, when they review the operational documentation, then they can understand the default trust model, supported exposure boundaries, and recommended protections for remote operation.
2. Given a user evaluates the product for home or home-lab deployment, when they review the operational documentation, then the project includes a clear security contact or policy for reporting issues.
3. Given a user evaluates the product for home or home-lab deployment, when they review the operational documentation, then release, upgrade, and compatibility expectations are documented for supported deployment paths.
4. Given a user evaluates the product for home or home-lab deployment, when they review the operational documentation, then examples and logs avoid exposing unnecessary sensitive information by default.

## Tasks / Subtasks

- [x] Create a canonical operational security policy and reporting path (AC: 1, 2, 4)
  - [x] Add a repository-level `SECURITY.md` in the root, `docs/`, or `.github/` so GitHub surfaces the policy automatically; include supported deployment posture, what is in and out of scope, how to report vulnerabilities privately, and expectations for coordinated disclosure.
  - [x] Link the policy from the root `README.md` and the operator-facing setup docs so users do not need to discover it through GitHub UI alone.
  - [x] State clearly that the product has no built-in end-user auth and is intended for local or trusted home-network use unless operators add boundary protections such as reverse proxy auth, ingress auth, network ACLs, or VPN-only access.

- [x] Consolidate operator-facing trust-model and exposure guidance into the setup docs (AC: 1, 4)
  - [x] Audit `README.md`, `docs/setup/README.md`, `docs/setup/docker.md`, `docs/setup/helm.md`, and `docs/setup/troubleshooting.md` for fragmented or inconsistent statements about local-only use, home-network exposure, `hostNetwork`, ingress, and remote client reachability.
  - [x] Introduce one canonical operator guidance path, likely under `docs/setup/` or a dedicated ops doc, that explains supported exposure boundaries for `stdio`, Docker HTTP, and Helm/k3s deployments without overstating internet-facing readiness.
  - [x] Ensure examples keep safe defaults: redact private addresses, tokens, secrets, and filesystem paths where they are not required for understanding.

- [x] Document release, upgrade, and compatibility expectations for the supported artifacts (AC: 3)
  - [x] Describe the current release artifacts and how they are produced from `.github/workflows/publish.yml`: PyPI package distribution and GHCR container publishing on version tags matching `v*.*.*`.
  - [x] Document the operator-visible upgrade flow for each supported path: local Python/uv install, Docker image refresh, and Helm upgrade with image tag coordination.
  - [x] Define compatibility expectations that are truthful for the current repo, including Python 3.12 baseline, supported transports (`stdio`, `Streamable HTTP`), Linux bias for Docker discovery, and the current Helm `hostNetwork: true` limitation.
  - [x] Clarify versioning expectations for operators: what a tag represents, where to inspect release notes or changelog material if introduced, and what assumptions are unsafe until a stronger compatibility policy exists.

- [x] Add regression coverage to lock the operator guidance to the real product surface (AC: 1, 2, 3, 4)
  - [x] Extend `tests/unit/test_integration_docs.py` or add a focused doc-regression module that asserts the existence of `SECURITY.md`, links from the root docs surface, and core security/trust-model language.
  - [x] Add assertions that the operational docs mention the real release automation entry points (`publish.yml`, version tags, PyPI/GHCR outputs) and the known deployment caveats (`hostNetwork: true`, local/trusted-network posture, no built-in auth).
  - [x] Keep tests content-focused and hardware-independent; verify truthfulness of docs and release guidance rather than exercising Sonos devices or GitHub Actions.

- [x] Verify the story with the canonical quality gates (AC: 1, 2, 3, 4)
  - [x] Run targeted pytest coverage for the updated docs-regression assertions while iterating.
  - [x] Run the relevant repo gates from the `Makefile` or equivalent `uv run` commands for linting, typing, and tests before review.

## Dev Notes

### Story Intent

This story finishes Epic 5 by treating operational trust as a product feature instead of tribal knowledge:

- operators need a single, explicit explanation of what is safe by default,
- maintainers need a clear path for receiving security reports,
- and users need truthful release and upgrade expectations that match the repository's real packaging and deployment surface.

The center of gravity should be docs plus docs-regression tests. Avoid adding runtime auth, remote policy enforcement, or speculative release machinery unless an actual product gap forces a small implementation change.

### What Already Exists

**Current operational surface**

- `README.md` already describes the three deployment models and routes users to setup, troubleshooting, prompts, and integration docs.
- `docs/setup/README.md` already distinguishes local `stdio`, Docker HTTP, and Helm/k3s HTTP with current caveats.
- `docs/setup/docker.md` already documents Linux-only reliability for Sonos discovery when using `--network=host`.
- `docs/setup/helm.md` already documents the `hostNetwork: true` requirement for Sonos SSDP discovery and warns that ingress exposure requires boundary-layer auth.
- `docs/setup/troubleshooting.md` already states that user-facing diagnostics should avoid exposing config file paths, secret values, and private host details.

**Current release surface**

- `.github/workflows/ci.yml` already enforces quality gates for linting, typing, coverage, package build verification, and Helm linting on pushes and pull requests.
- `.github/workflows/publish.yml` already publishes PyPI artifacts and GHCR container images when a tag matching `v*.*.*` is pushed.
- `pyproject.toml` already defines the package baseline: Python `>=3.12`, `mcp[cli]>=1.26.0`, `python-dotenv>=1.2.2`, and `soco>=0.30.14`.
- `Makefile` already exposes the command surface operators and maintainers use for quality checks, packaging, Docker, and Helm.

**Current gaps this story must close**

- No `SECURITY.md` or equivalent repository security policy exists today.
- No canonical operator-facing release or upgrade guide exists today.
- Current docs mention deployment caveats and publishing automation in pieces, but there is no single operational page that ties trust model, exposure boundaries, release flow, and upgrade expectations together.
- `tests/unit/test_integration_docs.py` protects integration and prompt docs today, but it does not yet lock the security-policy and release-guidance surface.

### Previous Story Intelligence

Story 5.2 and Story 5.3 established the working pattern this story should reuse:

- treat documentation, diagnostics, and examples as first-class product assets,
- prefer truthfulness over aspirational claims,
- keep transport and integration semantics shared across `stdio` and `Streamable HTTP`,
- and add hardware-independent regression tests whenever docs become part of the supported product surface.

Specific lessons to preserve:

- Story 5.2 tightened the redaction posture. Security and release docs must continue to avoid leaking private hosts, config paths, raw secrets, or unnecessary environment details in examples and logs.
- Story 5.3 split canonical doc responsibilities instead of letting command and usage guidance drift across many pages. Do the same here: choose one canonical operator/security path and link to it from entry points rather than copying the same policy text everywhere.
- Both stories corrected overstatements after review. For 5.4, do not imply internet-hardening, cloud-Kubernetes support, automatic upgrade safety, or a formal compatibility guarantee that the repo does not actually provide.

### Architecture Guardrails

- Preserve the documented operating model from `_bmad-output/planning-artifacts/architecture.md`: the product is scoped to a single Sonos household and should default to local or trusted home-network exposure.
- Keep boundary-layer security at deployment edges. The MVP does not include built-in end-user authentication; remote protection belongs in reverse proxy, ingress, VPN, firewall, or equivalent operator-managed controls.
- Keep transport guidance aligned with the architecture and MCP spec: local clients should prefer `stdio`, and remote or deployed usage should describe `Streamable HTTP`, not legacy SSE-first wording.
- Treat docs as product surface under `docs/setup/`, `docs/integrations/`, and `docs/prompts/`. Do not create a second undocumented operational path in ad hoc markdown files unless the structure clearly improves discoverability.
- Keep examples and logs sanitized. User-facing docs should not normalize printing secrets, private IPs, raw environment dumps, or unnecessary filesystem paths.

### Implementation Guidance

**Likely files to touch**

- `SECURITY.md`
- `README.md`
- `docs/setup/README.md`
- `docs/setup/docker.md`
- `docs/setup/helm.md`
- `docs/setup/troubleshooting.md`
- `docs/prompts/README.md` only if a navigation link materially improves discoverability
- `tests/unit/test_integration_docs.py`

**Recommended documentation shape**

- Add a canonical security and release guidance page, either as `SECURITY.md` plus a dedicated setup/operations doc, or by keeping `SECURITY.md` for reporting policy and adding a focused operator guide under `docs/setup/`.
- Keep `SECURITY.md` concise and actionable: supported deployment posture, reporting path, disclosure expectation, and supported-version guidance based on what the repo can truthfully maintain.
- Keep release and upgrade guidance equally concrete: how tags drive publish automation, what artifacts are produced, how operators upgrade local installs, Docker deployments, and Helm releases, and what caveats still require manual judgment.

**Release guidance should reflect the actual repo**

- PyPI publish is tag-driven through GitHub Actions OIDC trusted publishing in `.github/workflows/publish.yml`; there is no manual token flow documented in the repo today.
- Docker release publishing targets GHCR and uses semver, major.minor, and `latest` tags generated by `docker/metadata-action`.
- Helm deployment currently assumes the operator manages image tags and, when discovery is required, may need manual `hostNetwork: true` handling outside the chart's default values.
- There is no changelog, release-notes generator, or automated upgrade migration framework in the repo today. If you add one, keep scope modest and tied directly to operator guidance.

### Anti-Patterns To Avoid

- Do not implement built-in authentication, user accounts, OAuth flows, or remote authorization features as part of this story.
- Do not claim that public-internet exposure is supported by default or safe without additional controls.
- Do not promise zero-downtime upgrades, backward compatibility across arbitrary versions, or managed Kubernetes support when the repo does not currently prove those guarantees.
- Do not duplicate the same security and release policy text in `README.md`, setup guides, and troubleshooting docs. Link to the canonical source instead.
- Do not add tests that depend on GitHub Actions, PyPI publication, container registry access, or Sonos hardware.

### Git Intelligence Summary

Recent Epic 5 work shows a stable pattern:

- `feac5bf` addressed Story 5.2 review findings by tightening troubleshooting guidance to match the real implementation.
- `1fb9728` marked Story 5.2 done after those corrections.
- `bc2d12a` implemented Story 5.3 by consolidating docs and command-surface truthfulness.
- `06d7342` addressed Story 5.3 findings and fixes.
- `070fe9d` marked Story 5.3 done.

Use the same standard here: improve the operator-facing docs surface, then add regression checks so later edits cannot silently overstate security posture, deployment safety, or release behavior.

### Library / Framework Requirements

- Stay within the current project baseline in `pyproject.toml`: Python `>=3.12`, `mcp[cli]>=1.26.0`, `python-dotenv>=1.2.2`, and `soco>=0.30.14`.
- Use the existing quality stack only: `pytest`, `ruff`, and `mypy`.
- Do not add a docs site generator, release-management framework, or security-scanning dependency unless the current markdown-plus-tests approach cannot meet the story.

### Latest Technical Information

- GitHub currently recommends adding a `SECURITY.md` file in the repository root, `docs`, or `.github` so the repository exposes a formal security policy and reporting instructions in the Security tab. That matches this story's need for a repository-visible vulnerability-reporting path.
- PyPI trusted publishing documentation currently describes GitHub Actions OIDC publishing as the preferred path and notes that `id-token: write` is required. The existing `publish.yml` already follows that direction, so the story should document the operator/maintainer expectations rather than redesign the workflow.
- The current MCP specification still defines `stdio` and `Streamable HTTP` as the standard transports, and recent spec revisions added more HTTP security guidance rather than changing the basic transport direction. Release and security docs should continue to describe remote usage in `Streamable HTTP` terms.

### Verification Notes

Use the Makefile as the canonical command surface when practical. Prefer the smallest commands that prove the story while iterating:

- `uv run pytest tests/unit/test_integration_docs.py`
- `uv run ruff check tests/unit/test_integration_docs.py`
- `uv run ruff format --check tests/unit/test_integration_docs.py`
- `uv run mypy src`

Run broader `make test`, `make lint`, `make type-check`, or `make ci` if the final diff reaches beyond docs and docs-regression coverage.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Integration-Diagnostics-and-Productized-Adoption]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-54-Publish-Operational-Security-and-Release-Guidance]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey-3-Home-Lab-Deployment-and-Networked-Use]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey-4-Mobile-and-Cross-Device-AI-Access]
- [Source: _bmad-output/planning-artifacts/prd.md#Security]
- [Source: _bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#API--Communication-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: _bmad-output/planning-artifacts/architecture.md#Deployment-Structure]
- [Source: _bmad-output/implementation-artifacts/5-2-deliver-consistent-diagnostics-and-troubleshooting-support.md]
- [Source: _bmad-output/implementation-artifacts/5-3-deliver-productized-examples-prompts-and-command-surface.md]
- [Source: README.md]
- [Source: Makefile]
- [Source: pyproject.toml]
- [Source: docs/setup/README.md]
- [Source: docs/setup/docker.md]
- [Source: docs/setup/helm.md]
- [Source: docs/setup/troubleshooting.md]
- [Source: docs/prompts/README.md]
- [Source: docs/integrations/README.md]
- [Source: tests/unit/test_integration_docs.py]
- [Source: .github/workflows/ci.yml]
- [Source: .github/workflows/publish.yml]
- [Source: https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository]
- [Source: https://docs.pypi.org/trusted-publishers/]
- [Source: https://docs.pypi.org/trusted-publishers/using-a-publisher/]
- [Source: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports]
- [Source: https://modelcontextprotocol.io/specification/2025-06-18/changelog]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from sprint-status auto-discovery and Epic 5 artifact analysis on 2026-03-29.
- 2026-03-29: Review-fix pass addressed two Story 5.4 findings in operator guidance truthfulness and re-ran verification.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story scope is docs-first: security policy, operator guidance, release/upgrade guidance, and docs-regression coverage.
- The developer should prefer canonical docs plus regression tests over runtime feature additions.
- Implementation complete (2026-03-29): Created SECURITY.md (root) with supported deployment posture, in/out-of-scope definitions, GitHub private vulnerability reporting path, and coordinated disclosure expectations. Created docs/setup/operations.md as the canonical operator guide covering trust model, exposure boundaries, release artifacts (PyPI + GHCR via publish.yml on v*.*.* tags), upgrade flows (uv/Docker/Helm), compatibility baseline (Python 3.12+, stdio/Streamable HTTP, Linux/hostNetwork), and versioning expectations. Added no-built-in-auth trust-model note to docs/setup/README.md. Added security note to docs/setup/docker.md (matching existing helm.md note). Linked both new docs from root README.md and docs/setup/README.md. Extended test_integration_docs.py with 18 new TestSecurityAndOperationsDocs assertions; all 31 doc-regression tests pass. Full CI passes: lint, type-check, 686 tests (93.6% coverage), audit, build.
- Review-fix complete (2026-03-29): Corrected `docs/setup/operations.md` so release tags are described as triggering publish automation rather than implying CI success, and replaced the misleading `uv sync --upgrade` / `uv add soniq-mcp` guidance with truthful local upgrade paths (`git pull` + `uv sync` for checked-out repo installs, `pip install --upgrade soniq-mcp` for direct package installs). Extended doc-regression coverage to lock those truthfulness constraints. Verification passed with targeted docs tests plus full `make ci`.

### File List

- _bmad-output/implementation-artifacts/5-4-publish-operational-security-and-release-guidance.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- SECURITY.md
- docs/setup/operations.md
- docs/setup/README.md
- docs/setup/docker.md
- README.md
- tests/unit/test_integration_docs.py

### Change Log

- 2026-03-29: Created Story 5.4 and marked it ready for development.
- 2026-03-29: Implemented Story 5.4 — created SECURITY.md and docs/setup/operations.md; added trust-model note and operations link to docs/setup/README.md; added security note to docs/setup/docker.md; linked SECURITY.md and operations.md from root README.md; extended tests/unit/test_integration_docs.py with 18 new regression assertions covering security policy, operations guide, release automation, and deployment caveats; all 31 doc-regression tests pass; full CI (lint, type-check, 686 tests, audit, build) passes.
- 2026-03-29: Addressed Story 5.4 review findings by tightening `docs/setup/operations.md` to match the actual release/tag semantics and supported local upgrade flows; extended doc regressions accordingly; targeted docs tests and full `make ci` passed.
