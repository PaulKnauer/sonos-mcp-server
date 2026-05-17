# Story 4.2: Add Deployment Examples for Docker and Helm

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator running SoniqMCP in containers or k3s,
I want auth-specific deployment examples,
so that I can enable authentication without inventing my own config patterns.

## Acceptance Criteria

1. Given `.env.example` is updated, when operators inspect it, then it contains commented examples for static and OIDC auth env vars.
2. Given Helm values are updated, when operators configure auth in k3s, then auth env vars and CA certificate mount scaffolding are represented in chart values or templates as required by the release scope.
3. Given Docker deployment guidance is updated, when operators follow it, then they can configure auth env vars and CA trust mounting using documented container patterns.
4. Given Authelia is the reference OIDC provider, when the documentation covers Helm or k3s deployment, then it includes an operator-facing walkthrough or pointer for the Authelia client registration path.
5. Given cross-repo Terraform or Authelia work is not implemented in this repo, when documentation mentions it, then the boundary between `sonos-mcp-server` and `iot-edge-k3s` responsibilities is explicit.
6. Given deployment examples are reviewed, when compared to actual config fields and chart values, then names and defaults are consistent.

## Tasks / Subtasks

- [x] Update `.env.example` to expose auth configuration patterns without breaking the default local path (AC: 1, 6)
  - [x] Add commented static-auth examples for `SONIQ_MCP_AUTH_MODE=static` and `SONIQ_MCP_AUTH_TOKEN`.
  - [x] Add commented OIDC examples for `SONIQ_MCP_AUTH_MODE=oidc`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, optional `SONIQ_MCP_OIDC_JWKS_URI`, optional `SONIQ_MCP_OIDC_CA_BUNDLE`, and optional `SONIQ_MCP_OIDC_RESOURCE_URL`.
  - [x] Keep the active defaults unchanged for the stdio-first experience; auth examples should remain opt-in comments, not enabled defaults.
  - [x] If you document `SSL_CERT_FILE`, do it as a comment that clearly distinguishes process-wide trust from the verifier-scoped `SONIQ_MCP_OIDC_CA_BUNDLE`.

- [x] Bring Docker deployment assets and docs up to parity with the shipped auth surface (AC: 1, 3, 6)
  - [x] Update [docker-compose.yml](/Users/paul/github/sonos-mcp-server/docker-compose.yml) to pass through the auth env vars already supported by the runtime so Compose users do not need to fork the file just to enable auth.
  - [x] Decide deliberately whether CA trust stays docs-only for Compose or whether the Compose file gains an optional bind-mount/example path for a CA bundle. Do not add fake defaults or a mount that breaks the current zero-config path.
  - [x] Update [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md) with static-auth and OIDC examples that match the real env names and current startup behavior.
  - [x] Include a concrete verification step using `docker compose config` or equivalent so operators can confirm their env interpolation before restart.

- [x] Extend the Helm chart with auth values and CA-bundle mounting scaffolding that matches the runtime model (AC: 2, 4, 5, 6)
  - [x] Update [helm/soniq/values.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/values.yaml) with chart values for HTTP auth mode and OIDC inputs that operators can override cleanly with `-f` or `--set`.
  - [x] Route non-secret auth settings through [helm/soniq/templates/configmap.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/templates/configmap.yaml).
  - [x] Route sensitive values such as `SONIQ_MCP_AUTH_TOKEN` through [helm/soniq/templates/secret.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/templates/secret.yaml), preserving the existing split between ConfigMap and Secret responsibilities.
  - [x] Update [helm/soniq/templates/deployment.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/templates/deployment.yaml) to mount an optional CA bundle into the container and set the matching env var path only when the CA-bundle values are supplied.
  - [x] Keep the CA-bundle design scoped to mount scaffolding for an operator-provided ConfigMap or equivalent input. This repo does not own creating or Terraform-managing the external Authelia or `iot-edge-k3s` resources.
  - [x] Preserve the existing chart behavior when auth values are omitted: no auth envs should be required, and the current no-auth deployment path must still render cleanly.

- [x] Update Helm and auth docs so operators understand both the happy path and the repo boundary (AC: 2, 3, 4, 5, 6)
  - [x] Update [docs/setup/helm.md](/Users/paul/github/sonos-mcp-server/docs/setup/helm.md) with concrete values-file examples for static auth and OIDC auth.
  - [x] Document how to provide the CA bundle to the chart and the operational consequence that a mounted single-file `subPath` bundle requires a rollout/restart to pick up changes.
  - [x] Add a clear note that Authelia client registration, Terraform modules, and cluster-specific ConfigMap creation may live in `iot-edge-k3s` or another infra repo; this repo only supplies the SoniqMCP-side values/template hooks and docs.
  - [x] Update [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md) only as needed to point readers to the new Docker/Helm deployment examples rather than duplicating them.

- [x] Add or update verification so deployment examples cannot silently drift again (AC: 2, 3, 6)
  - [x] Extend [tests/unit/test_integration_docs.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_integration_docs.py) assertions that currently still describe the Helm auth gap.
  - [x] Extend [tests/smoke/helm/test_helm_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/helm/test_helm_smoke.py) to assert the rendered chart surfaces the new auth env vars and any optional CA-bundle mount/env wiring.
  - [x] Run the relevant docs/unit tests plus Helm render validation (`helm template`, `helm lint`) after implementation.
  - [x] Do not add provider-dependent smoke coverage here; Story 4.3 owns release-facing auth smoke validation.

### Review Findings

- [x] [Review][Patch] Helm auth upgrades do not restart existing pods [helm/soniq/templates/deployment.yaml:13]
- [x] [Review][Patch] CA bundle can render an invalid Deployment when enabled without a ConfigMap name [helm/soniq/templates/deployment.yaml:21]
- [x] [Review][Patch] `SSL_CERT_FILE` `.env` guidance is not wired for Docker Compose [docker-compose.yml:6]
- [x] [Review][Patch] Setup and operations docs still say Helm auth is not exposed [docs/setup/README.md:25]
- [x] [Review][Patch] Authelia client registration pointer is too generic for AC4 [docs/setup/helm.md:207]
- [x] [Review][Patch] Helm CA bundle smoke test does not verify the actual mount contract [tests/smoke/helm/test_helm_smoke.py:176]
- [x] [Review][Patch] Sprint status marks story 4-2 as current completed while its status is still review [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml:53]

## Dev Notes

### Story Intent

Story 4.2 is the deployment-surface story for optional auth. Epic 3 shipped the runtime. Story 4.1 shipped the core operator guide and explicitly deferred `.env.example`, Docker/Helm examples, and chart scaffolding to this story. This story closes that gap without widening into cross-repo infrastructure automation or provider-dependent validation.

### Epic Context

Epic 4 is about operator adoption, deployment, and release readiness. Story 4.2 specifically owns:

- deployment-ready examples for Docker and Helm
- `.env.example` parity with the shipped auth env surface
- chart scaffolding for Helm operators, including optional CA bundle mounting
- truthful boundaries between this repo and external homelab infra repos

Story 4.3 still owns release-facing smoke coverage and broader validation. Do not turn Story 4.2 into the smoke-test story.

### Current State Summary

What exists today:

- [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md) already documents the auth modes, runtime env vars, OIDC preflight behavior, CA trust model, and Claude Desktop caveats.
- [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md) mentions optional auth, but it does not yet show full static/OIDC deployment examples or CA-bundle container patterns.
- [docs/setup/helm.md](/Users/paul/github/sonos-mcp-server/docs/setup/helm.md) still says the Helm chart does not expose the auth env vars.
- [.env.example](/Users/paul/github/sonos-mcp-server/.env.example) currently ends at the transport/logging/tool settings and contains no auth examples.
- [docker-compose.yml](/Users/paul/github/sonos-mcp-server/docker-compose.yml) currently passes only transport/logging/default-room/tool env vars.
- The Helm chart currently exposes only the existing config set plus `secret.defaultRoom`; it has no auth values and no CA-bundle mount support.

### Files To Read Before Implementing

Read these files completely before editing:

- [.env.example](/Users/paul/github/sonos-mcp-server/.env.example)
- [docker-compose.yml](/Users/paul/github/sonos-mcp-server/docker-compose.yml)
- [docs/setup/docker.md](/Users/paul/github/sonos-mcp-server/docs/setup/docker.md)
- [docs/setup/helm.md](/Users/paul/github/sonos-mcp-server/docs/setup/helm.md)
- [docs/setup/authentication.md](/Users/paul/github/sonos-mcp-server/docs/setup/authentication.md)
- [helm/soniq/values.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/values.yaml)
- [helm/soniq/templates/configmap.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/templates/configmap.yaml)
- [helm/soniq/templates/deployment.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/templates/deployment.yaml)
- [helm/soniq/templates/secret.yaml](/Users/paul/github/sonos-mcp-server/helm/soniq/templates/secret.yaml)
- [tests/unit/test_integration_docs.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_integration_docs.py)
- [tests/smoke/helm/test_helm_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/helm/test_helm_smoke.py)
- [_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md)
- [_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md)

### Current-State Guardrails For Update Files

#### `.env.example`

Current state:

- Contains only the transport, exposure, logging, default room, volume cap, disabled-tools, and config-file settings. [Source: `.env.example:1-32`]

What this story changes:

- Add commented auth examples for static and OIDC modes.
- Keep stdio-safe defaults as the active defaults.

What must be preserved:

- The file remains safe to copy for a first-time local stdio user.
- No raw secret example should look like a production token; use obvious placeholders.

#### `docker-compose.yml`

Current state:

- Passes through only the existing non-auth env vars and has no volume mount support. [Source: `docker-compose.yml:1-15`]

What this story changes:

- Surface the auth env vars already implemented in runtime config.
- Optionally add a CA-bundle mounting pattern if it can be done without harming the base path.

What must be preserved:

- `docker compose up` with no auth envs must still work.
- Do not force users into OIDC-only or CA-bundle-only structure.

#### `docs/setup/docker.md`

Current state:

- Covers HTTP Docker deployment, Compose usage, Sonos networking caveats, and a high-level security note.
- Does not yet provide full auth-specific Compose/run examples or explicit CA-bundle mount guidance.

What this story changes:

- Add copy-pasteable static-auth and OIDC examples.
- Show how operators validate interpolated Compose config before restart.
- Explain CA trust mounting in container terms.

What must be preserved:

- Linux host-network discovery caveats remain intact.
- The guide stays honest about trusted-home-network assumptions and Claude connector constraints.

#### `helm/soniq/values.yaml`

Current state:

- Exposes only `config.transport`, `config.httpHost`, `config.httpPort`, `config.exposure`, `config.logLevel`, `config.maxVolumePct`, `config.toolsDisabled`, `config.configFile`, and `secret.defaultRoom`. [Source: `helm/soniq/values.yaml:1-31`]

What this story changes:

- Introduce auth-related values that map cleanly onto the shipped env vars.
- Make the CA-bundle scaffolding operator-overridable via values files.

What must be preserved:

- Existing overrides remain valid.
- Values should stay easy to override with `-f` or `--set`; avoid a deeply awkward structure for routine fields.

#### `helm/soniq/templates/configmap.yaml`

Current state:

- Renders only the existing non-secret config env vars. [Source: `helm/soniq/templates/configmap.yaml:1-15`]

What this story changes:

- Add non-secret auth envs here (`SONIQ_MCP_AUTH_MODE`, OIDC URLs/audience, optional CA-bundle path if mounted, optional resource URL).

What must be preserved:

- Do not move secret material into ConfigMap data.

#### `helm/soniq/templates/secret.yaml`

Current state:

- Renders only `SONIQ_MCP_DEFAULT_ROOM`. [Source: `helm/soniq/templates/secret.yaml:1-9`]

What this story changes:

- Add secret-bearing auth fields here if chart values include them, most importantly `SONIQ_MCP_AUTH_TOKEN`.

What must be preserved:

- Secrets stay optional and absent/empty values do not break chart rendering.

#### `helm/soniq/templates/deployment.yaml`

Current state:

- Uses `envFrom` for the chart ConfigMap and Secret and exposes the configured HTTP port, but has no volume mounts or volumes. [Source: `helm/soniq/templates/deployment.yaml:1-29`]

What this story changes:

- Add optional volume/volumeMount wiring for a CA bundle when values request it.

What must be preserved:

- Base rendering remains valid when the CA bundle is not configured.
- The container and service port relationship remains unchanged.

#### `docs/setup/helm.md`

Current state:

- Correctly explains `hostNetwork: true` limitations and ingress caveats.
- Incorrectly states that the chart does not expose auth env vars.

What this story changes:

- Replace that gap statement with actual supported chart values/examples.
- Add the Authelia/infra-repo boundary note.

What must be preserved:

- `hostNetwork: true` remains documented as a separate concern from auth.
- Do not imply this repo provisions Authelia, Terraform, or cluster ConfigMaps for the operator.

### Implementation Guidance

Preferred value split for Helm:

- Non-sensitive fields in ConfigMap-backed values:
  - `authMode`
  - `oidcIssuer`
  - `oidcAudience`
  - `oidcJwksUri`
  - `oidcResourceUrl`
  - `oidcCaBundlePath` only if the chart mounts a file there
- Sensitive fields in Secret-backed values:
  - `authToken`

Preferred CA-bundle scaffolding direction:

- Support mounting an operator-provided ConfigMap by name and key into a predictable in-container file path.
- Set `SONIQ_MCP_OIDC_CA_BUNDLE` to that mounted file path when the mount is enabled.
- Keep ConfigMap creation for homelab-specific CA material outside this repo’s scope unless the implementation can do so without inventing cross-repo ownership.

Why this direction:

- The PRD and journey docs expect Helm/k3s operators to mount a CA-certificate ConfigMap, not paste infrastructure automation into this repo.
- It keeps the runtime env model aligned with the shipped verifier/preflight behavior.
- It avoids pretending SoniqMCP owns the operator’s IdP lifecycle.

### Previous Story Intelligence

From Story 4.1:

- Story 4.1 intentionally stopped before `.env.example`, Docker/Helm examples, and Helm auth scaffolding. This story owns those surfaces; do not leave them half-finished again. [Source: `_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md#Story-Foundation`]
- The auth guide already documents the actual runtime env names and current OIDC/trust behavior; deployment examples must reuse those names exactly rather than rephrasing them. [Source: `_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md#What-Already-Exists`]
- Story 4.1 review findings corrected several documentation accuracy issues; treat deployment docs as implementation-sensitive, not marketing copy. [Source: `_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md#Review-Findings`]

From the Epic 3 retrospective:

- Docs accuracy and deployment examples are now the main release risk. This story is not optional polish. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#What-Didnt-Go-Well`]
- Epic 4 should begin by inventorying auth env var names, doc links, and deployment examples against the shipped implementation before drafting. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#Next-Epic-Preparation`]
- Provider-free validation remains a release requirement; no Authelia dependency should creep into automated tests. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#Next-Epic-Preparation`]

### Git Intelligence

Recent relevant commit history:

- `68a77f4 Complete optional auth story 4.1: document auth setup and constraints`
- `0773197 Complete optional auth epic 3`
- `b1fad53 Fix mypy type errors for AuthSettings URL arguments`

Actionable takeaways:

- The latest optional-auth work already tightened docs for truthfulness. Keep that tone and avoid speculative claims.
- Runtime auth behavior has already been stabilized and reviewed; this story should extend deployment surfaces to match it, not reopen the runtime design.

### Architecture Compliance

- Auth remains an HTTP/server/deployment concern only. Do not add auth logic to `tools/`, domain services, or Sonos adapters.
- Preserve the strict no-op path when auth is omitted. Deployment examples and chart values must not change the default `auth_mode=none` experience accidentally.
- Keep Docker and Helm changes bounded to deployment assets, docs, and chart templates unless a small test adjustment is required.

### Testing Requirements

- Update docs assertions in [tests/unit/test_integration_docs.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_integration_docs.py) so they reflect the new Helm capability instead of the current “chart does not expose auth env vars” statement.
- Expand [tests/smoke/helm/test_helm_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/helm/test_helm_smoke.py) to assert:
  - auth env vars render when set
  - secret/config split remains correct
  - optional CA-bundle mount/env wiring renders only when configured
- Re-run Helm smoke validation and any touched docs tests.
- If you change Compose behavior materially, add focused validation if there is an existing test seam; otherwise verify with `docker compose config` manually and record it in completion notes.

### Latest Technical Information

- Docker Compose still supports project-root `.env` interpolation, and `docker compose config` is the right way to inspect resolved values before running the stack. This supports adding explicit verification steps to the Docker docs rather than asking operators to guess whether interpolation worked. Source: Docker Docs, "Set, use, and manage variables in a Compose file with interpolation" — <https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/>
- Kubernetes still documents that ConfigMap and Secret `subPath` mounts do not receive live updates. If the Helm chart mounts a CA bundle as a single file via `subPath`, the docs must tell operators that they need a rollout/restart after changing the backing ConfigMap or Secret. Source: Kubernetes Docs, "Volumes" — <https://kubernetes.io/docs/concepts/storage/volumes/?q=configmap>
- Helm chart best practices still emphasize values structures that are easy to override with `-f` or `--set`. Keep auth values straightforward for operators rather than burying routine fields in a deeply nested structure. Source: Helm Docs, "Values" — <https://docs.helm.sh/docs/chart_best_practices/values/>

### Project Structure Notes

- No `project-context.md` file was found in the repo during activation, so this story relies on the planning artifacts, prior story records, current deployment assets, and current tests as the authoritative context.
- Optional-auth story files live under `_bmad-output/implementation-artifacts/optional-auth/`.
- The optional-auth sprint tracker is `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml`, not the older phase-2 tracker.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-42-Add-Deployment-Examples-for-Docker-and-Helm]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Journey-2-Priya--The-Homelab-Operator-OIDC-Path]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#MVP-Feature-Set]
- [Source: _bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md]
- [Source: .env.example]
- [Source: docker-compose.yml]
- [Source: docs/setup/docker.md]
- [Source: docs/setup/helm.md]
- [Source: docs/setup/authentication.md]
- [Source: helm/soniq/values.yaml]
- [Source: helm/soniq/templates/configmap.yaml]
- [Source: helm/soniq/templates/deployment.yaml]
- [Source: helm/soniq/templates/secret.yaml]
- [Source: tests/unit/test_integration_docs.py]
- [Source: tests/smoke/helm/test_helm_smoke.py]
- [Source: https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/]
- [Source: https://kubernetes.io/docs/concepts/storage/volumes/?q=configmap]
- [Source: https://docs.helm.sh/docs/chart_best_practices/values/]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- All five task groups implemented in a single session; 1571 tests pass (10 Helm smoke, 1561 unit/integration)
- CA trust approach for Docker: pass-through env var + docs-only bind-mount override (no default volume added to compose file)
- Helm conditional rendering used throughout to preserve the default no-auth rendering path

### Completion Notes List

- `.env.example`: added opt-in auth section (static + OIDC + SSL_CERT_FILE boundary note); stdio defaults unchanged
- `docker-compose.yml`: added all 7 auth env vars as pass-through with `none` default; no CA volume mount in base file (docs-only pattern)
- `docs/setup/docker.md`: new section 4 "Authentication (optional)" — static, OIDC, and CA-bundle mounting patterns with `docker compose config` verification step; sections 4–6 renumbered to 5–7
- `helm/soniq/values.yaml`: added `config.authMode/oidcIssuer/oidcAudience/oidcJwksUri/oidcResourceUrl`, `secret.authToken`, `caBundle.*` scaffolding
- `helm/soniq/templates/configmap.yaml`: conditional auth env rendering (absent by default)
- `helm/soniq/templates/secret.yaml`: conditional `SONIQ_MCP_AUTH_TOKEN` (absent when empty)
- `helm/soniq/templates/deployment.yaml`: conditional CA bundle `volumes` + `volumeMounts` blocks using `subPath` single-file mount
- `docs/setup/helm.md`: extended values table; updated ingress security note; added section 6 "Authentication (optional)" with static, OIDC, CA-bundle examples, Authelia/infra boundary note, and subPath restart caveat; sections 6–7 renumbered to 7–8
- `docs/setup/authentication.md`: added "Deployment examples" section linking to docker.md and helm.md
- `tests/unit/test_integration_docs.py`: replaced stale "chart does not expose" assertion with `config.authMode` presence check
- `tests/smoke/helm/test_helm_smoke.py`: added 6 new auth render tests (default no-auth, static vars, token-in-secret split, OIDC vars, CA-bundle volume, CA-bundle absent by default)

### File List

- _bmad-output/implementation-artifacts/optional-auth/4-2-add-deployment-examples-for-docker-and-helm.md
- _bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml
- .env.example
- docker-compose.yml
- docs/setup/docker.md
- docs/setup/helm.md
- docs/setup/authentication.md
- helm/soniq/values.yaml
- helm/soniq/templates/configmap.yaml
- helm/soniq/templates/secret.yaml
- helm/soniq/templates/deployment.yaml
- tests/unit/test_integration_docs.py
- tests/smoke/helm/test_helm_smoke.py
