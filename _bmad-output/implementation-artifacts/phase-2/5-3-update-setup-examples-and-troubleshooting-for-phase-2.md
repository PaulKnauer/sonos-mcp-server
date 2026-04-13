# Story 5.3: Update setup, examples, and troubleshooting for phase 2

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want the setup and integration documentation to reflect the expanded capability surface,
so that I can use the new features without guessing how they fit the existing product.

## Acceptance Criteria

1. Given the phase-2 capability families are implemented, when documentation is updated, then the local `stdio`, Docker, Helm, cross-device, and agent-integration guides include or reference the new capabilities where relevant.
2. Given troubleshooting content is reviewed, when a user encounters a phase-2 configuration or runtime issue, then the docs provide a corrective path without requiring source-code inspection.

## Tasks / Subtasks

- [x] Audit the current operator and product-usage docs against the shipped phase-2 tool surface (AC: 1, 2)
  - [x] Review `README.md`, `docs/setup/README.md`, `docs/setup/stdio.md`, `docs/setup/docker.md`, `docs/setup/helm.md`, `docs/setup/troubleshooting.md`, `docs/integrations/*.md`, and `docs/prompts/*.md` for omissions or stale wording around play modes, seek/sleep timer, room EQ, inputs, group audio, alarms, playlists, and local library flows
  - [x] Identify where a page should describe a capability directly versus where it should link to a canonical page instead of duplicating command-surface detail
  - [x] Confirm transport wording stays truthful: local usage is `stdio`, remote usage is `Streamable HTTP`, and business semantics stay transport-neutral

- [x] Consolidate phase-2 capability guidance into the canonical docs entry points (AC: 1)
  - [x] Keep `README.md` and `docs/setup/README.md` focused on setup-path selection and high-level capability discovery
  - [x] Use `docs/prompts/example-uses.md` for scenario-driven direct and agent-mediated examples, and `docs/prompts/command-reference.md` for the canonical named command/tool surface
  - [x] Add or refine links so users can move cleanly between setup docs, integrations, prompts, command reference, and troubleshooting without needing source inspection

- [x] Refresh setup and integration guides so phase-2 features appear where users expect them (AC: 1)
  - [x] Update local `stdio`, Docker, and Helm docs where the expanded capability families materially affect setup expectations, runtime choice, or example usage
  - [x] Update integration guides for Claude Desktop, Home Assistant, and `n8n` so direct-client and agent-mediated flows reference the same phase-2 capability families and the same diagnostics-first workflow
  - [x] Keep cross-device and remote guidance honest about Linux host-networking requirements, Helm `hostNetwork: true` caveats, and the lack of transport-specific business semantics

- [x] Strengthen troubleshooting so users can recover from phase-2 adoption issues without reading code (AC: 2)
  - [x] Expand or refine `docs/setup/troubleshooting.md` to cover the real diagnostic categories, common setup failures, missing-tool situations, runtime initialization failures, and phase-2 feature-discovery confusion
  - [x] Ensure troubleshooting steps route users toward `ping`, `server_info`, `list_rooms`, and the canonical setup/integration guides before suggesting deeper debugging
  - [x] Keep user-facing examples sanitized and product-facing; do not require users to inspect implementation modules or raw exceptions to determine the next action

- [x] Add regression coverage that locks the docs to the implemented phase-2 surface (AC: 1, 2)
  - [x] Extend `tests/unit/test_integration_docs.py` with assertions for the current phase-2 setup, prompt, troubleshooting, and integration guidance
  - [x] Prefer content-truthfulness assertions over fragile full-paragraph matching so tests enforce supported capabilities and routing without blocking normal editorial cleanup
  - [x] Keep tests hardware-independent and focused on documentation truthfulness rather than live Sonos behavior

- [x] Verify the documentation slice with the canonical quality gates (AC: 1, 2)
  - [x] Run targeted doc-regression tests while iterating
  - [x] Run lint checks on touched docs/tests as needed
  - [x] Run broader repo validation if the final diff reaches beyond documentation and doc-regression tests

### Review Findings

- [x] [Review][Patch] Sprint status marks a review story as completed [_bmad-output/implementation-artifacts/sprint-status.yaml:56]
- [x] [Review][Patch] Regression coverage skips the edited Home Assistant and n8n guides [tests/unit/test_integration_docs.py:212]
- [x] [Review][Patch] New documentation assertions are more brittle than the story guidance allows [tests/unit/test_integration_docs.py:90]
- [x] [Review][Patch] Docs overstate universal phase-2 availability when tools can be disabled [docs/prompts/command-reference.md:91]
- [x] [Review][Patch] Canonical phase-2 reference omits group topology tools [docs/prompts/command-reference.md:89]
- [x] [Review][Patch] Integration-doc route tests only check loose substrings, not the actual markdown targets [tests/unit/test_integration_docs.py:212]

## Dev Notes

### Story intent

- Epic 5 is the rollout-hardening epic for the expanded phase-2 surface. Story 5.3 is the documentation, examples, and troubleshooting slice, not the schema/error-contract slice from Story 5.1 and not the transport/exposure regression slice from Story 5.2.
- The implementation goal is to make the shipped phase-2 surface usable without guesswork by aligning setup, prompt, integration, and troubleshooting docs with the real tool inventory and behavior already in the repo.
- This story should improve adoption quality through docs and doc-regression tests. Do not add new runtime capabilities or invent transport-specific product semantics to make the docs read more cleanly.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-53-Update-setup-examples-and-troubleshooting-for-phase-2`]
  [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]

### Previous story intelligence

- Story 5.1 stabilized the public contract and typed error model for the phase-2 capability families. Story 5.3 should describe the current contract truthfully rather than redefine payloads, aliases, or capability names.
- Story 5.2 proved the expanded phase-2 surface remains transport-neutral across `stdio` and HTTP, and that startup-time exposure controls work consistently. Story 5.3 should preserve that mental model in docs: transport affects setup and envelope details, not tool semantics.
- Recent Epic 5 work followed an additive pattern: audit the real repo surface first, tighten the highest-signal gaps, and then freeze the outcome with hardware-independent tests. Reuse that pattern here.
  [Source: `_bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md`]
  [Source: `_bmad-output/implementation-artifacts/phase-2/5-2-preserve-transport-parity-and-tool-exposure-controls.md`]
  [Source: `git log --oneline -8`]

### Current repo state to build on

- The current docs surface is already organized into `README.md`, `docs/setup/`, `docs/integrations/`, and `docs/prompts/`, with `docs/prompts/command-reference.md` acting as the canonical command surface and `docs/prompts/example-uses.md` acting as the scenario/example surface.
- `tests/unit/test_integration_docs.py` already protects a meaningful portion of the user-facing docs surface, including integration guide links, command-reference targets, troubleshooting categories, and several phase-2 capability families.
- The root README already lists the current phase-2 capability families, deployment models, and the major docs entry points; Story 5.3 should refine truthfulness and routing rather than duplicate those lists in every document.
- The setup and integration docs already distinguish local `stdio` from remote `Streamable HTTP`, and already call out Linux-oriented Docker discovery and the Helm `hostNetwork: true` workaround. Preserve that truthful posture while expanding phase-2 examples and troubleshooting.
  [Source: `README.md`]
  [Source: `docs/setup/README.md`]
  [Source: `docs/setup/stdio.md`]
  [Source: `docs/setup/docker.md`]
  [Source: `docs/setup/helm.md`]
  [Source: `docs/setup/troubleshooting.md`]
  [Source: `docs/integrations/README.md`]
  [Source: `docs/prompts/README.md`]
  [Source: `docs/prompts/command-reference.md`]
  [Source: `docs/prompts/example-uses.md`]
  [Source: `tests/unit/test_integration_docs.py`]

### Architecture guardrails

- Treat documentation and onboarding as first-class product surface. The architecture explicitly calls out setup flows, configuration UX, examples, diagnostics, and troubleshooting as architecturally significant, not as secondary polish.
- Keep transport guidance aligned with the architecture: local clients should use `stdio`, remote and deployed usage should use `Streamable HTTP`, and the capability model must remain transport-neutral.
- Preserve the documented `tools -> services -> adapters` boundary model indirectly by keeping docs focused on supported user-facing behavior rather than teaching users to reason from internal module names or source files.
- Keep setup, diagnostics, and onboarding material routed through the documented docs structure under `docs/setup/`, `docs/integrations/`, and `docs/prompts/`.
- Do not normalize overclaiming. If a deployment pattern has caveats or a capability has a constrained interaction model, document that constraint plainly rather than smoothing it over.
  [Source: `_bmad-output/planning-artifacts/architecture.md#API--Communication-Patterns`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]

### Technical requirements

- Story 5.3 covers the full expanded phase-2 capability surface introduced across Epics 1-4:
  - play modes
  - seek and sleep timer
  - room EQ
  - input switching
  - group topology and group audio controls
  - alarms
  - playlist playback and lifecycle
  - local music library browsing and playback
- Documentation updates should make those families discoverable from the relevant user entry points without turning every page into a duplicate tool catalog.
- Troubleshooting must route users toward corrective action using published docs, diagnostics tools, and stable error categories rather than expecting source inspection.
- Direct-client and agent-mediated usage should continue to reference the same named tools, fields, and business semantics. Differences between local and remote paths should stay limited to setup mechanics and transport envelopes.
- The docs set called out in the PRD must remain practical for local `stdio`, Docker, Helm, cross-device access, and external automation/client integrations.
  [Source: `_bmad-output/planning-artifacts/epics.md#Story-53-Update-setup-examples-and-troubleshooting-for-phase-2`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting`]
  [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Journey-2-Setup-Failure-and-Recovery`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Journey-3-Home-Lab-Deployment-and-Networked-Use`]
  [Source: `_bmad-output/planning-artifacts/prd.md#Journey-4-Mobile-and-Cross-Device-AI-Access`]

### Likely files to inspect or update

- Core discovery and setup routing:
  - `README.md`
  - `docs/setup/README.md`
  - `docs/setup/stdio.md`
  - `docs/setup/docker.md`
  - `docs/setup/helm.md`
  - `docs/setup/troubleshooting.md`
- Product-facing usage and command docs:
  - `docs/prompts/README.md`
  - `docs/prompts/example-uses.md`
  - `docs/prompts/command-reference.md`
- Integration guides:
  - `docs/integrations/README.md`
  - `docs/integrations/claude-desktop.md`
  - `docs/integrations/home-assistant.md`
  - `docs/integrations/n8n.md`
- Regression tests:
  - `tests/unit/test_integration_docs.py`

### Implementation guidance

- Start with a docs audit mapped to the actual tool inventory in `README.md` and the current doc-regression assertions. Let observed gaps determine edits.
- Preserve a clear canonical-doc split:
  - setup-path choice and deployment expectations in `docs/setup/`
  - scenario prompts and adoption examples in `docs/prompts/example-uses.md`
  - supported command and tool surface in `docs/prompts/command-reference.md`
  - client-specific integration setup in `docs/integrations/`
- Link instead of copy when the same concept appears in multiple places. Story 5.3 should reduce drift, not create a second source of truth.
- Keep examples product-facing and deterministic. Avoid vague marketing claims or examples that depend on undocumented assumptions about room state, transport mode, or agent framework behavior.
- When editing troubleshooting, bias toward corrective paths a user can execute directly from the docs: config changes, restart instructions, diagnostics tools, documented deployment caveats, and routing to the right setup guide.

### Testing guidance

- Reuse and extend `tests/unit/test_integration_docs.py` as the primary regression guard for Story 5.3.
- Keep assertions focused on supported capabilities, doc routing, troubleshooting categories, and truthful deployment/integration language.
- Do not add tests that require a live Sonos environment, Docker runtime, Helm runtime, or external MCP clients for this story.
- If you add new canonical links or command-surface claims, add matching assertions so later edits cannot silently regress them.
  [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
  [Source: `tests/unit/test_integration_docs.py`]

### Git intelligence summary

- `60c04ce` completed Story 5.2 and froze parity/exposure guidance via tests instead of runtime churn.
- `e312d80` completed Story 5.1 and strengthened the contract/troubleshooting truth surface.
- Epic 4 ended with a docs/parity-oriented close-out rather than new behavior, reinforcing the current pattern: final rollout work should favor truthfulness, routing, and regression locking over feature expansion.
  [Source: `git log --oneline -8`]

### Latest technical information

- The current MCP specification still identifies `stdio` and Streamable HTTP as standard transport patterns. Documentation should keep using that terminology for direct local versus remote/deployed usage instead of reintroducing outdated transport language.
- GitHub still recommends placing `SECURITY.md` in the repository root, `docs/`, or `.github/` so the repository exposes a formal security policy in the Security tab. Story 5.3 should link to that existing policy where relevant rather than scattering separate security instructions.
- PyPI trusted publishing guidance continues to treat GitHub Actions OIDC publishing as the recommended path. Story 5.3 should keep release/setup language aligned with the actual docs surface rather than implying manual token-based release steps for end users.
  [Source: https://modelcontextprotocol.io/specification/2025-03-26/basic/transports]
  [Source: https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository]
  [Source: https://docs.pypi.org/trusted-publishers/]

### Project Structure Notes

- Story files for the active phase live under `_bmad-output/implementation-artifacts/phase-2/`.
- Epic 5 is already `in-progress`; this story creation should move `5-3` from `backlog` to `ready-for-dev`.
- Story 5.3 should not absorb Story 5.1 contract work, Story 5.2 transport/exposure regression work, or Story 5.4 operator security/release guidance except where a small doc-link or wording alignment is necessary to keep the user-facing surface coherent.

### References

- [Source: `_bmad-output/planning-artifacts/epics.md#Story-53-Update-setup-examples-and-troubleshooting-for-phase-2`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Epic-5-Phase-2-Contract-Hardening-and-Documentation`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting`]
- [Source: `_bmad-output/planning-artifacts/prd.md#MCP-Client-and-Agent-Integration`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Journey-2-Setup-Failure-and-Recovery`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Journey-3-Home-Lab-Deployment-and-Networked-Use`]
- [Source: `_bmad-output/planning-artifacts/prd.md#Journey-4-Mobile-and-Cross-Device-AI-Access`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#API--Communication-Patterns`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns-Refresh`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/5-1-extend-schemas-and-error-contracts-for-phase-2-capability-families.md`]
- [Source: `_bmad-output/implementation-artifacts/phase-2/5-2-preserve-transport-parity-and-tool-exposure-controls.md`]
- [Source: `README.md`]
- [Source: `docs/setup/README.md`]
- [Source: `docs/setup/stdio.md`]
- [Source: `docs/setup/docker.md`]
- [Source: `docs/setup/helm.md`]
- [Source: `docs/setup/troubleshooting.md`]
- [Source: `docs/integrations/README.md`]
- [Source: `docs/integrations/claude-desktop.md`]
- [Source: `docs/integrations/home-assistant.md`]
- [Source: `docs/integrations/n8n.md`]
- [Source: `docs/prompts/README.md`]
- [Source: `docs/prompts/example-uses.md`]
- [Source: `docs/prompts/command-reference.md`]
- [Source: `tests/unit/test_integration_docs.py`]
- [Source: `git log --oneline -8`]
- [Source: `https://modelcontextprotocol.io/specification/2025-03-26/basic/transports`]
- [Source: `https://docs.github.com/en/code-security/getting-started/adding-a-security-policy-to-your-repository`]
- [Source: `https://docs.pypi.org/trusted-publishers/`]

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- 2026-04-13: Story created from Epic 5 planning artifacts, sprint-status phase tracking, completed Stories 5.1 and 5.2, the current documentation surface under `docs/`, and the existing doc-regression suite in `tests/unit/test_integration_docs.py`.
- 2026-04-13: Confirmed no `project-context.md` artifact exists in the repository, so story guidance is based on BMAD config, planning artifacts, completed story context, current repo docs, and recent git history.
- 2026-04-13: Confirmed the current docs split already uses `docs/prompts/command-reference.md` as the canonical command surface and `docs/prompts/example-uses.md` as the scenario/example surface, which Story 5.3 should preserve.
- 2026-04-13: Confirmed `tests/unit/test_integration_docs.py` is already the correct regression anchor for setup, integration, prompts, troubleshooting, and command-surface truthfulness.
- 2026-04-13: Audited the setup, integration, prompts, and troubleshooting docs against the shipped phase-2 capability families and tightened routing so setup pages point back to the canonical prompt and command docs.
- 2026-04-13: Added phase-2 documentation regressions covering canonical prompt routing, diagnostics-first guidance, transport-neutral capability wording, and troubleshooting for feature-discovery confusion.
- 2026-04-13: Validation run completed with `uv run pytest tests/unit/test_integration_docs.py`, `uv run ruff check tests/unit/test_integration_docs.py`, `make check`, and `make test`.
- 2026-04-13: Code review fixes applied for sprint metadata consistency, disabled-tool troubleshooting guidance, missing group-topology command-reference coverage, and stronger integration-doc regression assertions.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created.
- Story scope is docs-first: align setup, integration, prompts, and troubleshooting guidance with the shipped phase-2 capability surface.
- The highest-signal implementation path is an audit of the current docs plus additive truthfulness tests in `tests/unit/test_integration_docs.py`.
- Keep the canonical-doc split intact so setup, command-surface, example, and troubleshooting responsibilities do not drift back into overlapping pages.
- Do not expand runtime scope or invent transport-specific product semantics to make examples read better.
- Added canonical routing from setup and integration guides back to `docs/prompts/example-uses.md`, `docs/prompts/command-reference.md`, and the diagnostics-first troubleshooting flow.
- Expanded the command reference so the phase-2 capability families for playback modes, seek and sleep timer, room EQ, inputs, and group audio are discoverable from the canonical command surface.
- Strengthened troubleshooting for missing-tool and phase-2 feature-discovery confusion without asking users to inspect source code.
- Extended doc-regression coverage and verified the full repository test suite stayed green.
- Resolved all six code-review patch findings and revalidated with targeted doc checks plus the full repository test suite.

### File List

- _bmad-output/implementation-artifacts/phase-2/5-3-update-setup-examples-and-troubleshooting-for-phase-2.md
- _bmad-output/implementation-artifacts/sprint-status.yaml
- docs/integrations/README.md
- docs/integrations/claude-desktop.md
- docs/integrations/home-assistant.md
- docs/integrations/n8n.md
- docs/prompts/README.md
- docs/prompts/command-reference.md
- docs/setup/docker.md
- docs/setup/helm.md
- docs/setup/stdio.md
- docs/setup/troubleshooting.md
- tests/unit/test_integration_docs.py

### Change Log

- 2026-04-13: Created Story 5.3 with concrete guidance for phase-2 documentation alignment, troubleshooting hardening, canonical doc routing, and doc-regression coverage.
- 2026-04-13: Completed Story 5.3 by aligning setup and integration docs to the canonical prompt surfaces, expanding troubleshooting for phase-2 adoption issues, and extending the documentation regression suite.
- 2026-04-13: Addressed code review findings for Story 5.3 and marked the story done after revalidation.
