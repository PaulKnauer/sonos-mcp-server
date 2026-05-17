# Story 4.3: Add Auth Smoke Coverage and Release Validation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want release-facing validation for optional auth adoption paths,
so that docs, examples, and the simplest protected runtime path stay accurate.

## Acceptance Criteria

1. Given auth smoke tests run, when static auth is enabled and no token is sent, then the test observes HTTP 401.
2. Given auth smoke tests run, when static auth is enabled and the correct token is sent, then the test observes successful MCP handling.
3. Given release validation covers disabled auth, when `auth_mode=none`, then the existing startup path remains unchanged.
4. Given documentation and examples are updated, when reviewed against implementation, then auth env var names and setup steps match shipped behavior.
5. Given CI executes auth-related validation, when the pipeline runs, then it does not require Authelia, external OIDC infrastructure, or Sonos hardware.
6. Given the release is prepared, when maintainers assess optional auth readiness, then the docs, examples, and smoke coverage together support shipping the feature without hidden setup gaps.

## Tasks / Subtasks

- [x] Audit existing auth release-validation coverage before adding new code (AC: 1, 2, 3, 5, 6)
  - [x] Read `tests/smoke/streamable_http/test_streamable_http_smoke.py`, `tests/smoke/docker/test_docker_smoke.py`, `tests/smoke/helm/test_helm_smoke.py`, `tests/unit/test_server.py`, `tests/unit/auth/test_verifiers.py`, `tests/unit/test_integration_docs.py`, `.github/workflows/ci.yml`, `Makefile`, `docs/setup/authentication.md`, `docs/setup/docker.md`, `docs/setup/helm.md`, `docs/setup/operations.md`, and `docs/setup/releasing.md` before editing.
  - [x] Inventory the current status of static-auth smoke tests, disabled-auth/no-op tests, Helm auth render tests, docs assertions, and CI gates.
  - [x] Preserve existing passing tests where they already satisfy the ACs; do not duplicate weaker checks just to add volume.

- [x] Harden static HTTP auth smoke coverage where the current suite is incomplete (AC: 1, 2, 5)
  - [x] Ensure `tests/smoke/streamable_http/test_streamable_http_smoke.py` proves missing `Authorization` header returns `401`.
  - [x] Ensure the same suite proves an incorrect Bearer token returns `401`.
  - [x] Ensure the same suite proves the correct `Authorization: Bearer <token>` header reaches real MCP handling by initializing a session and calling `ping`.
  - [x] Keep the auth smoke fixture provider-free: `SONIQ_MCP_AUTH_MODE=static` and `SONIQ_MCP_AUTH_TOKEN=<test token>` only.
  - [x] Do not add OIDC smoke tests that depend on Authelia, Authentik, Keycloak, network JWKS endpoints, or external IdP containers.

- [x] Lock disabled-auth and stdio no-op release behavior (AC: 3, 5)
  - [x] Ensure `tests/unit/test_server.py` continues to assert `auth_mode=none` leaves `FastMCP.settings.auth` and `_token_verifier` unset.
  - [x] Ensure the auth-builder seam is not invoked for `auth_mode=none`.
  - [x] Ensure `transport=stdio` ignores `auth_mode=static` and `auth_mode=oidc` without wiring FastMCP auth.
  - [x] If any runtime path changes are needed, keep auth wiring in `src/soniq_mcp/server.py` only and preserve the strict guard around HTTP auth modes.

- [x] Add release-facing docs and example drift checks (AC: 4, 6)
  - [x] Extend `tests/unit/test_integration_docs.py` or an existing docs regression seam to assert the shipped env var names are present where operators need them: `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, `SONIQ_MCP_OIDC_JWKS_URI`, `SONIQ_MCP_OIDC_CA_BUNDLE`, and `SONIQ_MCP_OIDC_RESOURCE_URL`.
  - [x] Assert the docs route operators consistently across `docs/setup/authentication.md`, `docs/setup/docker.md`, `docs/setup/helm.md`, `docs/setup/operations.md`, and `docs/setup/releasing.md` without stale "Helm auth not exposed" or "no built-in auth" language.
  - [x] Assert Docker guidance still includes a concrete config verification step using `docker compose config` or equivalent.
  - [x] Assert Helm guidance still documents auth values, CA-bundle mounting, and the operator-owned Authelia/infra boundary.
  - [x] Keep docs assertions focused on user-visible release promises, not on brittle prose phrasing.

- [x] Make CI/release validation explicit and provider-free (AC: 5, 6)
  - [x] Confirm `.github/workflows/ci.yml` runs the relevant unit and smoke coverage through existing `make coverage`, `make helm-lint`, and package build gates, or update CI minimally if the auth smoke target is not exercised anywhere.
  - [x] Prefer existing Makefile targets: `make test-auth` for auth unit/server wiring checks and `make smoke-auth` for static HTTP smoke checks.
  - [x] If CI is changed, keep it on GitHub-hosted Ubuntu and avoid Docker service containers unless there is a concrete need; the current static-auth subprocess smoke path should not require service containers.
  - [x] Do not introduce Sonos hardware, Authelia, OIDC provider services, or private network assumptions into CI.

- [x] Close release-readiness documentation gaps only if the audit finds real drift (AC: 4, 6)
  - [x] Update `docs/setup/releasing.md` or `docs/setup/operations.md` if release instructions do not mention the auth validation commands maintainers should run before cutting optional-auth v0.6.0.
  - [x] Update `docs/setup/authentication.md`, `docs/setup/docker.md`, or `docs/setup/helm.md` only to correct mismatches with implemented behavior.
  - [x] Preserve the existing product stance: built-in HTTP auth is optional, `stdio` remains unaffected, and boundary-layer protection is still recommended for broader exposure.

- [x] Run targeted and release-facing validation (AC: 1, 2, 3, 4, 5, 6)
  - [x] Run `uv run pytest -q tests/smoke/streamable_http/test_streamable_http_smoke.py::TestStreamableHTTPAuthSmoke`.
  - [x] Run `uv run pytest -q tests/unit/test_server.py::TestDisabledAuthNoOp tests/unit/test_server.py::TestStaticAuthWiring`.
  - [x] Run `uv run pytest -q tests/unit/auth/ tests/unit/test_integration_docs.py`.
  - [x] Run `uv run pytest -q tests/smoke/helm/test_helm_smoke.py` when Helm is available locally; record if skipped because the CLI is absent.
  - [x] Run `make test-auth` and `make smoke-auth`.
  - [x] Run `make lint` and `make type-check`; run broader `make coverage` or `make ci` if changes touch shared runtime or CI behavior.

- [x] Close story and tracker hygiene cleanly (AC: 6)
  - [x] Update this story's Dev Agent Record with exact validation commands and outcomes.
  - [x] Keep `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml` synchronized when implementation reaches review/done.
  - [x] Do not mark this story done unless the story file, sprint tracker, and validation evidence agree.

### Review Findings

- [x] [Review][Patch] Auth release checklist claims docs validation but does not run docs tests [docs/setup/releasing.md:48]
- [x] [Review][Patch] Docs regression tests hard-code auth names instead of comparing against shipped config surfaces [tests/unit/test_integration_docs.py:440]

## Dev Notes

### Story Intent

Story 4.3 is the optional-auth release validation pass. The runtime implementation, operator guide, and deployment examples already exist. This story should prove that the simplest protected HTTP path works, that the disabled path stays unchanged, and that docs/examples/CI give maintainers enough confidence to ship optional auth without hidden setup gaps.

This is not an OIDC provider integration story. OIDC behavior already has provider-free verifier, preflight, and server wiring coverage. The release-facing smoke path must use static auth so CI remains independent of Authelia, external JWKS endpoints, Sonos hardware, and private network services.

[Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Story-43-Add-Auth-Smoke-Coverage-and-Release-Validation`]
[Source: `_bmad-output/planning-artifacts/prd-optional-auth.md#Success-Criteria`]
[Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#Next-Epic-Preparation`]

### Epic Context

Epic 4 is about operator adoption, deployment, and release readiness. Story 4.1 delivered the authentication guide. Story 4.2 delivered `.env.example`, Docker examples, Helm values, chart CA-bundle scaffolding, and deployment docs. Story 4.3 should now verify those adoption paths through automated smoke and documentation regression checks.

Key Epic 4 release promise:

- Operators can configure and verify optional auth across local, Docker, and Helm/k3s deployment paths.
- Static auth is the primary smoke-test path.
- OIDC is documented and unit-tested provider-free, but CI must not require an IdP.
- Disabled auth remains the default and must stay a strict no-op.

[Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Epic-4-Operator-Adoption-Deployment-and-Release-Readiness`]
[Source: `_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md`]
[Source: `_bmad-output/implementation-artifacts/optional-auth/4-2-add-deployment-examples-for-docker-and-helm.md`]

### Previous Story Intelligence

From Story 4.2:

- Deployment examples and Helm auth scaffolding were recently added in commit `c53f04e`.
- `Makefile` already includes `test-auth` and `smoke-auth` targets.
- `tests/smoke/helm/test_helm_smoke.py` already checks auth env rendering, secret/config split, CA bundle mount behavior, config/secret checksums, and disabled-default rendering.
- The review loop for Story 4.2 found real release-readiness issues around pod restarts, invalid CA-bundle rendering, Docker Compose `SSL_CERT_FILE`, stale setup/operations docs, and overly generic Authelia pointers. Story 4.3 should keep those areas under regression coverage.
- Story 4.2 explicitly left provider-dependent smoke coverage to Story 4.3, but the architecture says Story 4.3 must remain provider-free. Interpret this as static-auth smoke plus release validation, not Authelia-in-CI.

[Source: `_bmad-output/implementation-artifacts/optional-auth/4-2-add-deployment-examples-for-docker-and-helm.md#Review-Findings`]
[Source: `_bmad-output/implementation-artifacts/optional-auth/4-2-add-deployment-examples-for-docker-and-helm.md#Testing-Requirements`]
[Source: `git show --stat c53f04e`]

From the Epic 3 retrospective:

- Documentation accuracy and deployment examples are the main remaining release risk.
- Provider-free validation remains mandatory.
- Tracker/story status synchronization has drifted repeatedly and should be treated as an engineering-quality requirement for this close-out.

[Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#What-Didnt-Go-Well`]
[Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md#Action-Items`]

### Current Repo State To Build On

Current relevant implementation and coverage:

- `src/soniq_mcp/server.py` wires auth only when `transport=http` and `auth_mode` is `static` or `oidc`; `stdio` and `auth_mode=none` leave `auth_kwargs` empty.
- `tests/unit/test_server.py` already contains `TestDisabledAuthNoOp`, `TestStaticAuthWiring`, and `TestOIDCAuthWiring`.
- `tests/smoke/streamable_http/test_streamable_http_smoke.py` already starts a real local HTTP subprocess and has a `TestStreamableHTTPAuthSmoke` class for static auth.
- The current auth smoke class already covers missing token, wrong token, wrong scheme, and correct token MCP handling. Verify and extend only if needed.
- `tests/smoke/docker/test_docker_smoke.py` validates unauthenticated Docker runtime behavior, not auth.
- `tests/smoke/helm/test_helm_smoke.py` validates Helm render/lint plus auth env and CA-bundle rendering behavior.
- `.github/workflows/ci.yml` currently runs lint, type check, coverage, dependency audit, build check, and Helm lint. It does not explicitly run `make smoke-auth`.
- `docs/setup/authentication.md`, `docs/setup/docker.md`, `docs/setup/helm.md`, and `docs/setup/operations.md` already describe optional auth as shipped behavior.

[Source: `src/soniq_mcp/server.py`]
[Source: `tests/unit/test_server.py`]
[Source: `tests/smoke/streamable_http/test_streamable_http_smoke.py`]
[Source: `tests/smoke/docker/test_docker_smoke.py`]
[Source: `tests/smoke/helm/test_helm_smoke.py`]
[Source: `.github/workflows/ci.yml`]
[Source: `docs/setup/authentication.md`]

### Files To Read Before Implementing

Read these files completely before editing:

- `tests/smoke/streamable_http/test_streamable_http_smoke.py`
- `tests/smoke/docker/test_docker_smoke.py`
- `tests/smoke/helm/test_helm_smoke.py`
- `tests/unit/test_server.py`
- `tests/unit/auth/test_verifiers.py`
- `tests/unit/test_integration_docs.py`
- `src/soniq_mcp/server.py`
- `src/soniq_mcp/config/models.py`
- `src/soniq_mcp/config/loader.py`
- `src/soniq_mcp/config/validation.py`
- `Makefile`
- `.github/workflows/ci.yml`
- `.github/workflows/publish.yml`
- `docs/setup/authentication.md`
- `docs/setup/docker.md`
- `docs/setup/helm.md`
- `docs/setup/operations.md`
- `docs/setup/releasing.md`
- `_bmad-output/implementation-artifacts/optional-auth/4-2-add-deployment-examples-for-docker-and-helm.md`
- `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md`

### Architecture Guardrails

- Auth remains an HTTP/server/deployment concern. Do not add auth behavior to `tools/`, `services/`, `adapters/`, or transport runner modules.
- Preserve the exact public env var names:
  - `SONIQ_MCP_AUTH_MODE`
  - `SONIQ_MCP_AUTH_TOKEN`
  - `SONIQ_MCP_OIDC_ISSUER`
  - `SONIQ_MCP_OIDC_AUDIENCE`
  - `SONIQ_MCP_OIDC_JWKS_URI`
  - `SONIQ_MCP_OIDC_CA_BUNDLE`
  - `SONIQ_MCP_OIDC_RESOURCE_URL`
- Preserve `auth_mode=none` as the default and a strict no-op in server construction.
- Preserve `stdio` auth no-op behavior even if auth variables are present in `.env`.
- Use `auth_mode=static` for CI smoke tests. Do not use `auth_mode=oidc` in CI smoke tests with mocked or real providers.
- Do not add a new auth framework, ASGI middleware bypass, Uvicorn wrapper, or alternate FastMCP integration.

[Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth`]
[Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth`]

### Technical Requirements

- Static auth smoke tests must exercise the real Streamable HTTP transport and FastMCP auth middleware, not only `StaticBearerVerifier` unit logic.
- A missing token and wrong token must produce HTTP `401` before tool handlers run.
- A valid token must reach MCP handling and successfully call a low-risk tool such as `ping`.
- Disabled auth validation must prove no auth settings or token verifier are attached.
- Documentation checks must compare docs/examples against implementation names and behavior, especially around Docker/Helm and CA-bundle setup.
- CI/release validation must be reproducible on a normal GitHub-hosted Ubuntu runner.
- Hardware-dependent Sonos validation remains out of scope for automated auth release checks.

[Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Story-43-Add-Auth-Smoke-Coverage-and-Release-Validation`]
[Source: `_bmad-output/planning-artifacts/prd-optional-auth.md#Technical-Success`]
[Source: `tests/smoke/streamable_http/test_streamable_http_smoke.py`]
[Source: `tests/unit/test_server.py`]

### Latest Technical Information

- The latest MCP authorization specification page available during story creation was version `2025-11-25`. It keeps authorization scoped to HTTP-based transports, says stdio should not follow the HTTP authorization flow, and requires Bearer tokens in the `Authorization` header for HTTP resource requests. Inference: Story 4.3 should keep testing HTTP Bearer behavior and stdio no-op behavior separately.
- The same MCP spec says invalid or expired tokens should receive HTTP `401 Unauthorized`, and protected-resource metadata/`WWW-Authenticate` details are part of modern MCP authorization. SoniqMCP's current static-auth smoke acceptance focuses on status behavior and successful MCP handling; do not overfit the story to a spec feature that FastMCP owns unless the implemented runtime exposes a stable assertion seam.
- Docker Compose documentation still recommends using `docker compose config --environment` to inspect interpolated values. Inference: docs drift checks should keep a Compose config verification step in Docker guidance.
- GitHub Actions service-container docs confirm service containers are fresh per job, require Linux runners, and are useful when tests need dependent services. Inference: this story should avoid service containers unless a concrete need appears, because static auth smoke can run as a local subprocess without external services.

[Source: `https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization`]
[Source: `https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/`]
[Source: `https://docs.github.com/en/actions/tutorials/use-containerized-services/use-docker-service-containers?learn=continuous_integration`]

### Likely Files To Update

Update only if the audit finds gaps:

- `tests/smoke/streamable_http/test_streamable_http_smoke.py` - static-auth HTTP smoke gaps.
- `tests/unit/test_server.py` - disabled/no-op or static wiring gaps.
- `tests/unit/test_integration_docs.py` - docs drift checks for auth env names, Docker/Helm/release guidance, and stale security language.
- `.github/workflows/ci.yml` - only if auth release validation is not covered by existing gates and should run in CI explicitly.
- `docs/setup/releasing.md` and `docs/setup/operations.md` - release checklist/auth validation command gaps.
- `docs/setup/authentication.md`, `docs/setup/docker.md`, `docs/setup/helm.md` - only for real mismatches with shipped behavior.

Do not update:

- `src/soniq_mcp/auth/verifiers.py` unless a verified auth bug is found.
- `src/soniq_mcp/tools/`, `src/soniq_mcp/services/`, or `src/soniq_mcp/adapters/`.
- OIDC provider setup, Terraform, Authelia, or `iot-edge-k3s` resources.

### Testing Guidance

Minimum targeted validation after implementation:

```bash
uv run pytest -q tests/smoke/streamable_http/test_streamable_http_smoke.py::TestStreamableHTTPAuthSmoke
uv run pytest -q tests/unit/test_server.py::TestDisabledAuthNoOp tests/unit/test_server.py::TestStaticAuthWiring
uv run pytest -q tests/unit/auth/ tests/unit/test_integration_docs.py
make test-auth
make smoke-auth
make lint
make type-check
```

Run when available:

```bash
uv run pytest -q tests/smoke/helm/test_helm_smoke.py
make coverage
make ci
```

If Docker, Helm, or broader CI checks are unavailable locally, record the skip/blocker explicitly in the Dev Agent Record.

### Project Structure Notes

- Optional-auth story files live under `_bmad-output/implementation-artifacts/optional-auth/`.
- The optional-auth sprint tracker is `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml`.
- The default Phase 2 tracker at `_bmad-output/implementation-artifacts/sprint-status.yaml` is not authoritative for optional-auth work.
- No `project-context.md` file was found during activation; planning artifacts, prior story records, current code, and current tests are the source of truth.

### References

- [Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Story-43-Add-Auth-Smoke-Coverage-and-Release-Validation`]
- [Source: `_bmad-output/planning-artifacts/prd-optional-auth.md#Success-Criteria`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Context-Analysis--Phase-3-Optional-Auth`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth`]
- [Source: `_bmad-output/implementation-artifacts/optional-auth/4-1-document-optional-auth-setup-and-constraints.md`]
- [Source: `_bmad-output/implementation-artifacts/optional-auth/4-2-add-deployment-examples-for-docker-and-helm.md`]
- [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-3-retro-2026-05-07.md`]
- [Source: `src/soniq_mcp/server.py`]
- [Source: `src/soniq_mcp/config/models.py`]
- [Source: `src/soniq_mcp/config/loader.py`]
- [Source: `src/soniq_mcp/config/validation.py`]
- [Source: `tests/smoke/streamable_http/test_streamable_http_smoke.py`]
- [Source: `tests/smoke/docker/test_docker_smoke.py`]
- [Source: `tests/smoke/helm/test_helm_smoke.py`]
- [Source: `tests/unit/test_server.py`]
- [Source: `tests/unit/auth/test_verifiers.py`]
- [Source: `tests/unit/test_integration_docs.py`]
- [Source: `.github/workflows/ci.yml`]
- [Source: `.github/workflows/publish.yml`]
- [Source: `Makefile`]
- [Source: `docs/setup/authentication.md`]
- [Source: `docs/setup/docker.md`]
- [Source: `docs/setup/helm.md`]
- [Source: `docs/setup/operations.md`]
- [Source: `docs/setup/releasing.md`]
- [Source: `https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization`]
- [Source: `https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/`]
- [Source: `https://docs.github.com/en/actions/tutorials/use-containerized-services/use-docker-service-containers?learn=continuous_integration`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- 2026-05-17: Story created from optional-auth sprint tracker, optional-auth epics/PRD, Phase 3 architecture, Story 4.2 record, Epic 3 retrospective, current server/test/docs/CI files, recent git history, and current official MCP/Docker/GitHub Actions docs.
- 2026-05-17: Confirmed `4-3-add-auth-smoke-coverage-and-release-validation` was the only optional-auth backlog story and Epic 4 was already `in-progress`.
- 2026-05-17: Full audit completed. AC 1/2 (smoke), AC 3 (no-op), AC 5 (verifiers) all fully satisfied by existing tests — no new test code needed for those. Gaps found: test_integration_docs.py had no auth env var or docs drift assertions; releasing.md had no auth validation commands; SECURITY.md had stale "no built-in end-user authentication" language.
- 2026-05-17: CI audit: `make coverage` runs `pytest --cov` over `testpaths = ["tests"]` which includes `tests/smoke/`. `TestStreamableHTTPAuthSmoke` IS exercised through CI's coverage step. No CI changes required.

### Completion Notes List

- Audit-first approach: confirmed all auth smoke, no-op, and verifier coverage already existed and passed; added only what was genuinely missing.
- Added `TestAuthDocsRegression` class (9 tests) to `tests/unit/test_integration_docs.py`: asserts all 7 auth env vars in authentication.md and docker.md, Helm chart auth values and CA-bundle, `docker compose config` step, Authelia/infra boundary, releasing.md auth validation commands, and no stale "Helm auth not exposed"/"no built-in auth" language.
- Updated stale `test_security_policy_states_no_builtin_auth` → `test_security_policy_states_auth_posture` to check accurate optional-auth language.
- Updated `SECURITY.md` to replace "no built-in end-user authentication" with accurate optional-auth posture description.
- Added "Optional auth validation (v0.6.0+)" section to `docs/setup/releasing.md` with `make test-auth`, `make smoke-auth`, and broader `make ci` commands.
- Validation results: `make smoke-auth` 4 passed, `make test-auth` 48 passed, targeted pytest 107 passed, `make coverage` 1582 passed / 3 skipped (93.1%), `make lint` clean, `make type-check` clean, Helm smoke 12 passed.
- Code review patches applied: release docs now explicitly run `tests/unit/test_integration_docs.py`; docs regression tests now derive runtime auth env names from `soniq_mcp.config.loader._ENV_MAP`, assert Docker Compose passthrough, assert Helm template/runtime env alignment, and check stronger stdio no-op wording.
- Post-review validation: `uv run pytest -q tests/unit/test_integration_docs.py` 56 passed; `make test-auth` 48 passed; `make smoke-auth` 4 passed; `ruff` format/check clean for `tests/unit/test_integration_docs.py`.

### File List

- `_bmad-output/implementation-artifacts/optional-auth/4-3-add-auth-smoke-coverage-and-release-validation.md`
- `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml`
- `tests/unit/test_integration_docs.py`
- `SECURITY.md`
- `docs/setup/releasing.md`

### Change Log

- 2026-05-17: Created story context and marked optional-auth Story 4.3 ready for development.
- 2026-05-17: Implementation complete. Added TestAuthDocsRegression to test_integration_docs.py (9 new tests); updated stale security policy test; updated SECURITY.md to accurate optional-auth posture; added auth validation section to releasing.md. All existing auth smoke, no-op, and verifier tests confirmed passing without modification. Status: review.
- 2026-05-17: Code review patches applied and validated. Status: done.
