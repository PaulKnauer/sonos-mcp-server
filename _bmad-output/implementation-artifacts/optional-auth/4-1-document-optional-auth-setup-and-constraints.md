# Story 4.1: Document Optional Auth Setup and Constraints

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator,
I want a complete authentication guide for none, static, and OIDC modes,
so that I can choose and configure the right auth path without reading source code.

## Acceptance Criteria

1. Given the auth documentation is added, when operators read it, then it explains `none`, `static`, and `oidc` modes and when to use each.
2. Given an operator wants static auth, when they follow the guide, then they can configure the required env vars and understand the expected `401` and authorized behavior.
3. Given an operator wants OIDC auth, when they follow the guide, then they can configure issuer, audience, JWKS, and CA trust inputs.
4. Given Claude Desktop limitations apply, when the guide discusses client support, then it explicitly documents the Bearer token limitation and appropriate deployment patterns.
5. Given the guide documents CA certificate handling, when operators troubleshoot TLS trust, then it references `SSL_CERT_FILE` and the supported CA bundle approach.
6. Given the guide is published, when maintainers review it, then it matches the implemented config names and startup behavior.

## Tasks / Subtasks

- [x] Create the optional-auth setup guide as a first-class setup document (AC: 1, 2, 3, 4, 5, 6)
  - [x] Add a new user-facing guide at [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md) covering `auth_mode=none`, `auth_mode=static`, and `auth_mode=oidc`.
  - [x] Explain when each mode should be used, keeping the product’s trust model and deployment assumptions aligned with current `stdio`, Docker, and Helm guidance.
  - [x] Keep the guide operator-facing and practical: required variables, expected behavior, and troubleshooting pointers rather than source-code-level internals.

- [x] Document static-auth configuration and expected behavior accurately (AC: 1, 2, 6)
  - [x] Document the required env vars: `SONIQ_MCP_AUTH_MODE=static` and `SONIQ_MCP_AUTH_TOKEN`.
  - [x] Explain the expected request behavior: missing or wrong bearer token returns `401`, valid token allows normal MCP handling.
  - [x] Keep examples aligned with the implemented HTTP auth path in [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) and preflight behavior in [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py).

- [x] Document OIDC configuration, discovery, and trust-path behavior accurately (AC: 1, 3, 5, 6)
  - [x] Document the implemented OIDC config surface: `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, optional `SONIQ_MCP_OIDC_JWKS_URI`, optional `SONIQ_MCP_OIDC_CA_BUNDLE`, and optional `SONIQ_MCP_OIDC_RESOURCE_URL`.
  - [x] Explain the current startup behavior: HTTP OIDC preflight validates issuer/resource URL shape, discovers `jwks_uri` when missing, probes JWKS reachability, and fails startup with actionable diagnostics on TLS/network/discovery/configuration problems.
  - [x] Document CA trust correctly: default Python trust honors `SSL_CERT_FILE`; `SONIQ_MCP_OIDC_CA_BUNDLE` is an optional explicit override for verifier/preflight-scoped trust.
  - [x] Use the actual troubleshooting anchor in [docs/setup/troubleshooting.md](/Users/paul/github/sonos-mcp-server/docs/setup/troubleshooting.md) for startup error recovery guidance.

- [x] Clarify Claude Desktop and remote-client support constraints without guessing beyond current evidence (AC: 4, 6)
  - [x] Update [docs/integrations/claude-desktop.md](/Users/paul/github/sonos-mcp-server/docs/integrations/claude-desktop.md) and the new auth guide so they distinguish local `claude_desktop_config.json` stdio servers from remote custom connectors.
  - [x] Explicitly document the current practical constraint for private home-lab auth: Claude Desktop remote connectors are brokered through Anthropic cloud infrastructure and therefore do not behave like same-LAN clients.
  - [x] Document the operator implication carefully: local stdio remains the straightforward Claude Desktop path; remote HTTP auth modes should be presented with the current client/deployment caveats rather than implying universal Claude Desktop bearer-header support.
  - [x] If the guide mentions OAuth-capable remote connectors, keep that scoped to what the official Claude support docs actually describe and avoid inventing unsupported header-configuration steps for Claude Desktop.

- [x] Update the docs entry points so auth guidance is discoverable without broadening into deployment examples (AC: 1, 4, 5, 6)
  - [x] Add auth-guide links from [docs/setup/README.md](/Users/paul/github/sonos-mcp-server/docs/setup/README.md), [README.md](/Users/paul/github/sonos-mcp-server/README.md), and any existing setup/troubleshooting page that now references auth startup failures.
  - [x] Ensure the setup overview and operations pages no longer state “no built-in end-user authentication” without clarifying that optional HTTP auth now exists.
  - [x] Keep this story documentation-focused: only add minimal cross-links in Docker/Helm docs where needed; detailed deployment examples stay with Story 4.2.

- [x] Preserve scope boundaries established by Epic 4 planning and Epic 3 implementation history
  - [x] Do not update `.env.example`, Helm chart values/templates, or Docker/Helm example manifests here unless a tiny docs-link correction is unavoidable; Story 4.2 owns deployment examples and config scaffolding.
  - [x] Do not change runtime auth behavior in `src/` just to make the docs easier to write; if a true documentation-blocking implementation defect is found, document it explicitly in the story notes before widening scope.
  - [x] Do not add auth smoke tests or CI validation in this story; Story 4.3 owns release-facing smoke coverage.

### Review Findings

- [x] [Review][Patch] Update docs tests for the new optional-auth wording and current guide links [tests/unit/test_integration_docs.py:337]
- [x] [Review][Patch] Correct the documented `SONIQ_MCP_HTTP_HOST` default so it matches the implementation [README.md:69]
- [x] [Review][Patch] Clarify Helm auth guidance so docs do not claim chart-level auth knobs that the current chart does not expose [docs/setup/README.md:25]
- [x] [Review][Patch] Explicitly document the Claude Desktop remote Bearer-token limitation for static auth [docs/setup/authentication.md:190]
- [x] [Review][Patch] Fix the OIDC discovery-path description so it matches the implemented issuer-path behavior [docs/setup/authentication.md:96]
- [x] [Review][Patch] Correct the `SONIQ_MCP_OIDC_RESOURCE_URL` description so it does not promise JWT `resource`-claim validation that the implementation does not perform [docs/setup/authentication.md:98]
- [x] [Review][Patch] Add troubleshooting coverage for missing `SONIQ_MCP_OIDC_AUDIENCE` in HTTP OIDC mode [docs/setup/authentication.md:210]
- [x] [Review][Patch] Align the documented missing-OIDC-field error strings with the actual model-validator messages [docs/setup/authentication.md:218]
- [x] [Review][Patch] Clarify that home-network HTTP access also requires `SONIQ_MCP_EXPOSURE=home-network`, not only a non-loopback host [README.md:69]

## Dev Notes

### Story Intent

Story 4.1 is the operator-onboarding story for optional auth. Epic 3 delivered the runtime capability. This story makes that capability usable without reading source code.

The key constraint is that the docs must reflect the implementation as it exists now, not the implementation we might wish existed:

- optional HTTP auth is real and shipped
- static auth and OIDC are HTTP transport concerns
- stdio remains a no-op for auth
- OIDC startup validation is opinionated and actionable
- Claude Desktop local and remote connection models are materially different

This is a documentation/product-surface story, not a deployment-examples story and not another runtime-auth story.

### Story Foundation

Epic 4 is about operator adoption and release readiness. Story 4.1 is the first part of that:

- document all three auth modes clearly
- explain static auth in operator terms
- explain OIDC config and trust paths in operator terms
- document client-support constraints honestly
- make the auth docs discoverable from the existing setup and integration guides

Story 4.2 will own `.env.example`, Docker/Helm auth examples, and cross-repo Authelia deployment guidance. Story 4.3 will own auth smoke/release validation. Story 4.1 should stop before those surfaces unless a link or sentence must be adjusted for consistency.

### What Already Exists

Current repo state relevant to Story 4.1:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) already defines `auth_mode`, `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, and `oidc_resource_url`.
- [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py) already maps the auth env vars:
  - `SONIQ_MCP_AUTH_MODE`
  - `SONIQ_MCP_AUTH_TOKEN`
  - `SONIQ_MCP_OIDC_ISSUER`
  - `SONIQ_MCP_OIDC_AUDIENCE`
  - `SONIQ_MCP_OIDC_JWKS_URI`
  - `SONIQ_MCP_OIDC_CA_BUNDLE`
  - `SONIQ_MCP_OIDC_RESOURCE_URL`
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) already implements HTTP-only auth preflight, including OIDC discovery, JWKS probing, CA bundle handling, and multi-line actionable errors.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) already wires both static and OIDC auth for HTTP transport and keeps stdio auth as a strict no-op.
- [docs/setup/README.md](/Users/paul/github/sonos-mcp-server/docs/setup/README.md), [docs/setup/stdio.md](/Users/paul/github/sonos-mcp-server/docs/setup/stdio.md), [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md), [docs/setup/helm.md](/Users/paul/github/sonos-mcp-server/docs/setup/helm.md), [docs/setup/operations.md](/Users/paul/github/sonos-mcp-server/docs/setup/operations.md), and [docs/setup/troubleshooting.md](/Users/paul/github/sonos-mcp-server/docs/setup/troubleshooting.md) already provide the product’s setup and troubleshooting surface.
- [docs/integrations/claude-desktop.md](/Users/paul/github/sonos-mcp-server/docs/integrations/claude-desktop.md) already distinguishes local stdio from remote HTTP, but it predates the latest Claude custom-connector guidance and likely needs correction or tighter caveats.
- [.env.example](/Users/paul/github/sonos-mcp-server/.env.example) does not yet contain auth examples. That gap is real, but it belongs to Story 4.2, not this one.
- There is currently no [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md), even though optional auth is now an implemented feature.

### Files To Read Before Implementing

Read these files completely before editing:

- [docs/setup/README.md](/Users/paul/github/sonos-mcp-server/docs/setup/README.md)
- [docs/setup/troubleshooting.md](/Users/paul/github/sonos-mcp-server/docs/setup/troubleshooting.md)
- [docs/setup/operations.md](/Users/paul/github/sonos-mcp-server/docs/setup/operations.md)
- [docs/integrations/claude-desktop.md](/Users/paul/github/sonos-mcp-server/docs/integrations/claude-desktop.md)
- [README.md](/Users/paul/github/sonos-mcp-server/README.md)
- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py)
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md)

Read these only if the docs need link or consistency touch-ups:

- [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md)
- [docs/setup/helm.md](/Users/paul/github/sonos-mcp-server/docs/setup/helm.md)
- [.env.example](/Users/paul/github/sonos-mcp-server/.env.example)

### Current-State Guardrails For Update Files

#### `docs/setup/authentication.md` (new)

Expected role:

- primary auth-mode explainer for operators
- central place for static auth, OIDC auth, CA trust, and current client-support caveats
- should link out to setup/deployment/integration guides rather than duplicate all remote deployment detail

What this story should include:

- auth mode comparison
- required env vars and what they do
- what startup validation does today
- realistic client/deployment guidance
- troubleshooting entry points

What this story should avoid:

- reproducing all Docker/Helm deployment examples
- introducing speculative OAuth/client-setup instructions not supported by the current sources

#### `docs/setup/README.md`

Current state:

- compares `stdio`, Docker HTTP, and Helm/k3s HTTP deployment models
- still says SoniqMCP has no built-in end-user authentication
- does not yet link to an auth guide

What this story changes:

- add auth guide as a top-level setup document
- correct or qualify the no-auth statement so it matches optional-auth reality

What must be preserved:

- deployment-model comparison remains concise
- this page stays an index/overview, not a full auth deep dive

#### `docs/setup/operations.md`

Current state:

- frames the trust model and exposure boundaries
- currently says the product does not include built-in end-user authentication

What this story changes:

- update trust-model wording to reflect optional HTTP auth without overselling it as a full remote security model

What must be preserved:

- boundary-layer protection guidance for remote exposure
- home-network-first posture

#### `docs/setup/troubleshooting.md`

Current state:

- already contains the `#configuration-errors-at-startup` anchor used by current OIDC preflight errors
- is setup/troubleshooting-oriented, not auth-guide-oriented

What this story changes:

- possibly add or tighten auth-specific troubleshooting links/content
- ensure auth docs point here using real anchors and real failure categories

What must be preserved:

- stable troubleshooting anchor names
- plain-language recovery guidance

#### `docs/integrations/claude-desktop.md`

Current state:

- documents local stdio via `claude_desktop_config.json`
- documents remote HTTP via Connectors UI with a simple URL model

What this story changes:

- align the remote connector discussion with current official Claude support guidance
- explain that remote connectors are brokered through Anthropic cloud infrastructure, which changes the viability of private home-lab HTTP auth patterns

What must be preserved:

- local stdio instructions remain the default Claude Desktop path
- do not invent unsupported steps such as arbitrary header injection in Claude Desktop if the current official docs do not describe it

#### `README.md`

Current state:

- serves as the quick-start and docs index
- has no auth-specific doc entry yet

What this story changes:

- add discoverability for the new auth guide
- keep top-level wording aligned with optional-auth implementation reality

What must be preserved:

- README stays concise and index-like

### Previous Story Intelligence

From the Epic 3 retrospective:

- Epic 3’s runtime auth work is done; the main remaining product risk is operator-facing accuracy in docs, deployment examples, and release validation. Story 4.1 should treat documentation correctness as the primary quality target, not as cleanup. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#Conclusion`]
- Tracker hygiene drifted repeatedly across Epics 2 and 3. Keep Story 4.1 scoped and finish-state-aware so documentation work does not create another ambiguous “implemented but not reflected” situation. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#What-Didnt-Go-Well`]
- Epic 4 does not need replanning; Story 4.1 should begin by inventorying doc paths, anchors, and config names against the implementation before drafting. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#Next-Epic-Preparation`]

From Story 3.3:

- Story 3.3 settled the runtime behavior this documentation must describe: OIDC preflight, discovery when `oidc_jwks_uri` is absent, actionable startup diagnostics, and HTTP OIDC wiring. Do not describe a different startup path. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-3-add-oidc-startup-preflight-and-actionable-errors.md#Completion-Notes`]
- `resource_server_url=None` is currently an accepted implementation path when `oidc_resource_url` is unset. If docs mention the resource URL, they must describe it as optional, not required by default. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-3-add-oidc-startup-preflight-and-actionable-errors.md#Completion-Notes`]

From Story 3.4:

- The runtime verifier behavior is now well-covered with real RS256/JWKS tests. Story 4.1 should not reopen verifier semantics or introduce speculative caveats that contradict the tested runtime contract. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-4-add-oidc-verifier-unit-coverage.md#Completion-Notes-List`]

From Story 1.5:

- Documentation is a product artifact in this repo, not a cleanup step. The local setup story succeeded by cross-checking every command and path against the implementation; Story 4.1 should use that same discipline for auth docs. [Source: `_bmad-output/implementation-artifacts/1-5-deliver-local-setup-and-troubleshooting-guidance.md#Dev-Notes`]
- Keep user-facing docs in `docs/` and `README.md`, not buried in planning artifacts. [Source: `_bmad-output/implementation-artifacts/1-5-deliver-local-setup-and-troubleshooting-guidance.md#Project-Structure-Notes`]

### Git Intelligence Summary

Recent relevant auth work sequence:

- `b1fad53` fixed `AuthSettings` typing around the OIDC server path
- `70e6802` completed Story 3.2 verifier hardening
- `52b394a` implemented the base OIDC verifier for Story 3.1

Pattern to preserve:

- story-scoped increments
- implementation first, then documentation that matches actual behavior
- auth boundaries stay narrow and intentional
- review-driven hardening is normal for auth work, so docs should describe the reviewed end state rather than early assumptions

### Architecture Guardrails

- Documentation is part of the product surface, but it must still follow the implemented architecture rather than redefining it. [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Context-Analysis`]
- Auth remains a server/transport concern only. Story 4.1 must not move auth logic into unrelated parts of the system in the name of documentation cleanup. [Source: `_bmad-output/planning-artifacts/architecture.md#Structure-Patterns`]
- Configuration validation happens at startup before normal operation; documentation should explain startup validation and failure modes in operator terms. [Source: `_bmad-output/planning-artifacts/architecture.md#Process-Patterns`]
- The deployment posture is still local or trusted home-network first. Docs must not imply a stronger built-in remote security model than the product actually provides. [Source: `_bmad-output/planning-artifacts/architecture.md#Authentication--Security`]
- `stdio` and `Streamable HTTP` remain the two primary transport modes. Auth guidance must stay aligned with those transport boundaries. [Source: `_bmad-output/planning-artifacts/architecture.md#API--Communication-Patterns`]

### Technical Requirements

- The auth guide must describe the exact shipped config names and defaults from `config/models.py`, `config/defaults.py`, and `config/loader.py`.
- Static auth requires `SONIQ_MCP_AUTH_MODE=static` plus `SONIQ_MCP_AUTH_TOKEN`; startup blocks when the token is absent on HTTP transport.
- HTTP OIDC requires `SONIQ_MCP_OIDC_ISSUER` and `SONIQ_MCP_OIDC_AUDIENCE`; `oidc_jwks_uri`, `oidc_ca_bundle`, and `oidc_resource_url` are optional.
- OIDC preflight derives `/.well-known/openid-configuration` from the issuer when `oidc_jwks_uri` is missing, validates that the resulting JWKS endpoint is HTTPS, and classifies failures as `tls`, `network`, `discovery`, or `configuration`.
- CA trust must be documented in the order the implementation actually uses:
  - default Python trust path, which honors `SSL_CERT_FILE`
  - optional `SONIQ_MCP_OIDC_CA_BUNDLE` override for explicit CA bundle use

### Architecture Compliance

- Keep Story 4.1 documentation-focused.
- Do not add or change deployment manifests, Helm values, or `.env.example` auth examples here unless the change is a tiny cross-link correction required for consistency.
- Do not change `src/` behavior unless a true documentation-blocking defect is proven.
- Prefer linking between docs pages over copying long duplicate sections into multiple setup guides.

### Library / Framework Requirements

- The installed MCP Python SDK auth surface is `TokenVerifier` plus `AuthSettings`, and current SDK docs frame MCP server auth as OAuth 2.1 resource-server behavior. Story 4.1 docs should reflect that optional auth is implemented at the server boundary rather than via a custom middleware stack. [Source: https://py.sdk.modelcontextprotocol.io/authorization/]
- The current MCP authorization spec requires protected resource metadata and resource-indicator semantics on the client/server side. Docs do not need to teach the full spec, but they should avoid contradicting it when explaining OIDC behavior or resource URLs. [Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization]
- Current Claude support guidance for remote custom connectors says the connection originates from Anthropic cloud infrastructure and the remote MCP server must be reachable from Anthropic IP ranges. This materially affects how Claude Desktop remote usage should be documented for home-lab/private-network deployments. [Source: https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp]

### File Structure Requirements

Expected touched files for Story 4.1:

- [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md) (new)
- [docs/setup/README.md](/Users/paul/github/sonos-mcp-server/docs/setup/README.md)
- [docs/setup/operations.md](/Users/paul/github/sonos-mcp-server/docs/setup/operations.md)
- [docs/setup/troubleshooting.md](/Users/paul/github/sonos-mcp-server/docs/setup/troubleshooting.md) if auth-specific troubleshooting links or sections are needed
- [docs/integrations/claude-desktop.md](/Users/paul/github/sonos-mcp-server/docs/integrations/claude-desktop.md)
- [README.md](/Users/paul/github/sonos-mcp-server/README.md)

Potentially touched only for minimal consistency links, not full examples:

- [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md)
- [docs/setup/helm.md](/Users/paul/github/sonos-mcp-server/docs/setup/helm.md)

Files this story should not modify unless a verified blocker forces it:

- [.env.example](/Users/paul/github/sonos-mcp-server/.env.example)
- [helm/soniq/values.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/values.yaml)
- Helm templates under [helm/soniq/templates/](/Users/paul/github/sonos-mcp-server/helm/soniq/templates)
- Runtime files under [src/soniq_mcp/](/Users/paul/github/sonos-mcp-server/src/soniq_mcp)

### Testing Requirements

- Cross-check every documented env var, mode name, and troubleshooting statement against the implementation files before marking the story done.
- Verify all docs links and anchors referenced by the new auth guide actually exist.
- If commands or behavior are documented, verify them against the current docs and runtime surfaces instead of copying older planning text.
- Keep validation lightweight and appropriate for a docs story:
  - repo text search / consistency checks
  - markdown link and path verification where practical
  - targeted manual checks against current code and docs
- Do not claim support for a client flow unless it is backed by current implementation evidence or current official vendor documentation.

### Latest Technical Information

- The current MCP authorization spec states that MCP servers must expose OAuth 2.0 Protected Resource Metadata and that clients use resource indicators (`resource`) tied to the canonical MCP server URI. Docs should avoid contradicting this when summarizing OIDC/resource URL behavior. [Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization]
- The current MCP Python SDK authorization docs describe server auth as OAuth 2.1 resource-server behavior via `TokenVerifier` and `AuthSettings`. That is consistent with SoniqMCP’s current implementation approach and should be reflected in high-level wording. [Source: https://py.sdk.modelcontextprotocol.io/authorization/]
- Anthropic’s current Claude support docs for custom remote connectors say:
  - remote custom connectors are available in Claude and Claude Desktop
  - the remote MCP server must be reachable from Anthropic’s cloud infrastructure
  - local `claude_desktop_config.json` servers remain a separate local mechanism
  This means Story 4.1 should document remote Claude Desktop auth/deployment constraints carefully for private home-lab deployments. [Source: https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp]

### Project Structure Notes

- User-facing setup and integration docs belong under `docs/setup/`, `docs/integrations/`, and `README.md`.
- Setup overview pages should route users to specialized guides rather than absorb all auth detail directly.
- Story 4.1 should create one clear auth landing page and then link to it from the existing setup surface.
- Deployment-specific examples and scaffolding changes remain in the Epic 4 follow-on stories.

### References

- Story source and ACs: [Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Story-41-Document-Optional-Auth-Setup-and-Constraints`]
- Epic 4 scope and boundaries: [Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Epic-4-Operator-Adoption-Deployment-and-Release-Readiness`]
- Product requirements for optional auth docs and client constraints: [Source: `_bmad-output/planning-artifacts/prd-optional-auth.md#User-Journeys`] [Source: `_bmad-output/planning-artifacts/prd-optional-auth.md#Success-Criteria`] [Source: `_bmad-output/planning-artifacts/prd-optional-auth.md#Functional-Requirements`]
- Architecture trust model and transport boundaries: [Source: `_bmad-output/planning-artifacts/architecture.md#Authentication--Security`] [Source: `_bmad-output/planning-artifacts/architecture.md#API--Communication-Patterns`] [Source: `_bmad-output/planning-artifacts/architecture.md#Process-Patterns`]
- Current setup and integration docs: [Source: `docs/setup/README.md`] [Source: `docs/setup/operations.md`] [Source: `docs/setup/troubleshooting.md`] [Source: `docs/integrations/claude-desktop.md`] [Source: `README.md`]
- Current auth implementation: [Source: `src/soniq_mcp/config/loader.py`] [Source: `src/soniq_mcp/config/models.py`] [Source: `src/soniq_mcp/config/validation.py`] [Source: `src/soniq_mcp/server.py`]
- Epic 3 continuity and carry-forward risks: [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md`]
- Prior docs-story implementation pattern: [Source: `_bmad-output/implementation-artifacts/1-5-deliver-local-setup-and-troubleshooting-guidance.md`]
- Current MCP auth/server docs: [Source: `https://py.sdk.modelcontextprotocol.io/authorization/`] [Source: `https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization`]
- Current Claude remote connector guidance: [Source: `https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp`]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6

### Debug Log References

- Read all implementation source files (`models.py`, `loader.py`, `validation.py`, `server.py`) before writing docs to ensure every env var name, error message, and startup behavior matches exactly.
- Cross-checked all 7 auth env vars against `loader.py` _ENV_MAP — exact match confirmed.
- Verified `#configuration-errors-at-startup` anchor exists in `troubleshooting.md` before referencing it.
- Verified OIDC preflight error format (`OIDC JWKS preflight failed`, `Category:`, `Likely cause:`, `Docs:`) against `validation.py` lines 265-271.
- No scope boundaries were violated: no `src/` changes, no `.env.example` changes, no Helm template changes.

### Completion Notes List

- Created `docs/setup/authentication.md` as the primary auth guide covering `none`, `static`, and `oidc` modes with all required env vars, startup behavior, CA trust path, and Claude Desktop remote connector constraint.
- Updated `docs/setup/README.md`: corrected "no built-in end-user authentication" statement, added auth guide link in Setup guides section.
- Updated `docs/setup/operations.md`: updated trust model section to reflect optional HTTP auth without overselling it; preserved boundary protection guidance.
- Updated `docs/setup/troubleshooting.md`: added auth startup failure example and category table under the existing `#configuration-errors-at-startup` section.
- Updated `docs/integrations/claude-desktop.md`: added "Private home-lab deployment constraint" section explaining Anthropic cloud routing and home-lab reachability implications.
- Updated `README.md`: added `SONIQ_MCP_AUTH_MODE` to configuration table, added auth guide to Docs section.
- Updated `docs/setup/docker.md`: minimal security note update only — changed "no built-in authentication" to accurately reflect optional auth, added link to authentication guide.
- All docs verified against implementation: env var names, error message text, troubleshooting anchors.

### File List

- [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md) (new)
- [docs/setup/README.md](/Users/paul/github/sonos-mcp-server/docs/setup/README.md) (modified)
- [docs/setup/operations.md](/Users/paul/github/sonos-mcp-server/docs/setup/operations.md) (modified)
- [docs/setup/troubleshooting.md](/Users/paul/github/sonos-mcp-server/docs/setup/troubleshooting.md) (modified)
- [docs/integrations/claude-desktop.md](/Users/paul/github/sonos-mcp-server/docs/integrations/claude-desktop.md) (modified)
- [README.md](/Users/paul/github/sonos-mcp-server/README.md) (modified)
- [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md) (modified — minimal security note only)

### Change Log

- Added optional auth documentation suite (Date: 2026-05-07)
