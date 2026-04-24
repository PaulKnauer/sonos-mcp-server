---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments:
  - '_bmad-output/planning-artifacts/prfaq-sonos-mcp-server.md'
  - '_bmad-output/planning-artifacts/prfaq-sonos-mcp-server-distillate.md'
  - '_bmad-output/planning-artifacts/oidc-authelia-integration-assessment-2026-04-22.md'
  - '_bmad-output/planning-artifacts/research/technical-oidc-fastmcp-authelia-research-2026-04-22.md'
  - 'docs/security/threat-model.md'
  - 'docs/setup/operations.md'
workflowType: 'prd'
classification:
  projectType: 'developer_tool'
  deploymentTargets: ['pip', 'docker', 'helm-k3s']
  domain: 'general'
  complexity: 'medium'
  projectContext: 'brownfield'
briefCount: 2
researchCount: 2
brainstormingCount: 0
projectDocsCount: 2
---

# Product Requirements Document — SoniqMCP Optional Authentication

**Author:** Paul
**Date:** 2026-04-23

## Executive Summary

SoniqMCP v0.6.0 adds optional Bearer token authentication to the HTTP transport of the existing SoniqMCP server — a production-grade, open-source MCP server for Sonos speaker control. The feature is strictly opt-in: `AUTH_MODE=none` is the default, and existing deployments are unaffected without any action. For users running SoniqMCP over HTTP on a shared LAN, in a Docker container, or in a k3s homelab, this release provides a credential gate without requiring a reverse proxy or external service.

The April 2026 MCP specification draft mandates OAuth 2.1 for HTTP transport servers. This feature aligns SoniqMCP with that direction — optional now, ecosystem-compliant from day one.

Three auth modes: `none` (current behaviour, default), `static` (shared Bearer token, two env vars, a few minutes to configure), and `oidc` (JWT validation against a JWKS endpoint, for homelab operators with an existing identity provider such as Authelia or Authentik). Implementation uses FastMCP's `TokenVerifier` protocol, present in `mcp[cli]>=1.26.0`. Stdio transport is unaffected in all modes.

### What Makes This Special

The load-bearing design decision is the opt-in architecture. Home users on a trusted network never encounter this feature. Users who need it — shared-LAN deployments, AI automation pipelines, homelab SSO stacks — get spec-compliant authentication with minimal configuration. The static token path is the primary path for the majority; OIDC is the power-user extension for operators who want SoniqMCP to be just another registered client in an existing SSO stack.

Implementation scope is bounded: one `TokenVerifier` class (~30 lines), `PyJWT>=2.8` as the only new dependency (`cryptography>=46.0.7` already present), no ASGI middleware bypass required. The documentation — `docs/setup/authentication.md` — is the largest single investment.

### Project Classification

| Dimension | Value |
|-----------|-------|
| Project Type | Developer tool — multi-deployment (pip / Docker / Helm) |
| Domain | General |
| Complexity | Medium |
| Project Context | Brownfield — feature addition to an existing production system |
| Backward Compatibility | Hard constraint — `AUTH_MODE=none` must be a strict no-op |

## Success Criteria

### User Success

- An HTTP deployer sets `AUTH_MODE=static` + `SONIQ_MCP_AUTH_TOKEN`, restarts their container, and confirms: (a) a request without the token returns `401 Unauthorized`, and (b) their AI assistant makes a tool call with the token and tools execute normally — both within a few minutes of configuration
- A homelab operator with Authelia registers the `soniq-mcp` OIDC client, sets three env vars, and SoniqMCP validates a `client_credentials` Bearer JWT and executes tools without any other changes to their setup
- A stdio user upgrades to v0.6.0 and observes zero change in behaviour — no errors, no warnings, no configuration required

### Business Success

- Zero regressions in the existing test suite on release — `make lint` and all tests green
- No breaking changes reported against existing deployments post-release
- Feature ships as a clean, self-contained release — no half-finished states, no deferred known issues

### Technical Success

- `AUTH_MODE=none` is a strict no-op: no extra imports at startup, no performance impact, no code path difference from current behaviour
- `AUTH_MODE=oidc` with an unreachable or misconfigured JWKS endpoint fails fast at startup with a clear, actionable error message (endpoint URL, HTTP/TLS error, likely cause) — never fails silently at request time
- Valid RS256 JWT (correct `iss`, `aud`, non-expired) → `200` and tool execution
- Missing, expired, or tampered token → `401 Unauthorized`
- `AUTH_MODE=oidc` without `SONIQ_MCP_OIDC_ISSUER` → preflight error with clear message before server starts

### Measurable Outcomes

- All three deployment modes (local pip, Docker, k3s/Helm) have documented setup paths in `docs/setup/authentication.md`
- Claude Desktop Bearer token limitation is explicitly documented so users understand the scope
- Authelia `client_credentials` walkthrough is complete and tested against the live homelab environment

## User Journeys

### Journey 1: Alex — The Shared-LAN HTTP Deployer (Happy Path)

Alex runs a small flat share with two housemates. He set up SoniqMCP in Docker six months ago so his Claude Desktop can control the living room Sonos system. Life was good — until he noticed his housemate's phone had accidentally triggered the "skip track" tool through some AI assistant she was experimenting with on the same Wi-Fi.

He opens the SoniqMCP docs, finds the authentication section, and reads: *Static token — a few minutes.* He sets two environment variables in his `docker-compose.yml`:

```
SONIQ_MCP_AUTH_MODE=static
SONIQ_MCP_AUTH_TOKEN=a-secret-only-alex-knows
```

He runs `docker compose up -d`. The container restarts cleanly. He fires a raw HTTP request with no Authorization header — `401 Unauthorized`. He updates his Claude Desktop MCP client config with the token, asks Claude to play something, and the track changes. His housemate's AI assistant, with no token, gets a 401 and moves on.

Alex didn't need a reverse proxy. He didn't need an identity provider. He needed a door with a lock.

**Requirements revealed:** `AUTH_MODE=static`, `SONIQ_MCP_AUTH_TOKEN` env var, 401 on missing/wrong token, 200 on valid token, Docker restart recovery, documentation for this path.

---

### Journey 2: Priya — The Homelab Operator (OIDC Path)

Priya runs a 6-node k3s cluster. Every service — Home Assistant, Grafana, Gitea — is gated through Authelia. SoniqMCP was the exception: left open because the docs said "for trusted home networks." She's been tightening things up, and her AI agent automation scripts already carry Authelia Bearer tokens for other services — SoniqMCP should be the same pattern.

She adds `soniq-mcp` to the `oidc_clients` variable in the Terraform module (parameterised in this release), runs `terragrunt apply`. She updates the Helm values with `SONIQ_MCP_AUTH_MODE=oidc`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, and mounts the homelab CA cert ConfigMap. Pod restarts — JWKS fetched and cached. Her automation script requests a token from Authelia via `client_credentials`, presents it on the next tool call, tools execute. SoniqMCP is now just another registered client — same pattern, same token flow, no special cases.

**Requirements revealed:** `AUTH_MODE=oidc`, JWKS fetching with custom CA cert (`SSL_CERT_FILE`), RS256 JWT validation (`iss`, `aud`, `exp`), startup JWKS connectivity check, Helm env var injection, CA cert ConfigMap mount, Authelia `client_credentials` flow, Terraform `oidc_clients` variable parameterisation.

---

### Journey 3: Mia — The Stdio User Upgrading to v0.6.0 (Backward Compatibility Path)

Mia runs SoniqMCP via `uvx` with Claude Desktop on her MacBook. She reads the v0.6.0 release notes: *"Optional auth for HTTP transport. Default: none. Stdio users: no change required."*

She runs `uvx mcp install sonos-mcp-server`. The upgrade completes. She asks Claude to list her Sonos groups. It works. She sets nothing, reads nothing about auth, and gets zero new errors. The release notes told the truth.

**Requirements revealed:** `AUTH_MODE=none` strict no-op, no startup changes for stdio users, no log noise when auth is unconfigured, upgrade path leaves nothing broken.

---

### Journey 4: Marcus — The Misconfigured OIDC Deployer (Error Recovery Path)

Marcus has Authelia running but his homelab uses a self-signed certificate from his own CA. He configures SoniqMCP OIDC, mounts what he thinks is the right cert, and restarts the container.

The server doesn't start. The logs show:

```
PREFLIGHT ERROR: OIDC JWKS endpoint unreachable
  URL: https://authelia.home.lab:30443/api/oidc/jwks
  Error: SSL: CERTIFICATE_VERIFY_FAILED — unable to get local issuer certificate
  Likely cause: CA certificate not trusted. Set SSL_CERT_FILE to your homelab CA bundle.
  Docs: docs/setup/authentication.md#ca-certificates
```

He checks his Helm values — the volume mount `subPath` is wrong. He fixes it, redeploys. Server starts. JWKS fetched. Preflight passes in silence.

He never saw a mysterious 401. The error told him exactly what was wrong and where to look.

**Requirements revealed:** Startup preflight JWKS connectivity check, actionable error message (URL + SSL error + likely cause + docs link), clear distinction between "server won't start" (config error) and "request rejected" (auth failure).

---

### Journey Requirements Summary

| Capability | Revealed By |
|-----------|-------------|
| `AUTH_MODE` env var with `none`/`static`/`oidc` | All journeys |
| `StaticTokenVerifier` (string comparison) | Journey 1 |
| `OIDCTokenVerifier` (PyJWT RS256, JWKS) | Journeys 2, 4 |
| 401 on missing/invalid token | Journeys 1, 2 |
| Startup preflight with actionable error messages | Journeys 2, 4 |
| Custom CA cert support (`SSL_CERT_FILE`) | Journeys 2, 4 |
| Strict no-op for `AUTH_MODE=none` and stdio | Journey 3 |
| Helm env var injection + CA cert ConfigMap | Journey 2 |
| Authelia `oidc_clients` Terraform parameterisation | Journey 2 |
| `docs/setup/authentication.md` (all three modes) | All journeys |

## Domain-Specific Requirements

### Security Constraints

Security properties required of the auth implementation itself (measurable forms in NFR4–NFR8):

- JWT validation must fail closed — exceptions during verification produce `401`, never pass-through
- Static token comparison must be constant-time to prevent timing attacks
- `SONIQ_MCP_AUTH_TOKEN` must never appear in logs, tracebacks, error responses, or config serialisation
- JWKS must be fetched over HTTPS only

### Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| `AUTH_MODE=oidc` misconfigured → silent 401s at runtime | Startup preflight — fail fast with actionable error before accepting connections |
| JWKS key rotation invalidates cached tokens | Retry JWKS fetch once on validation failure before returning 401 |
| Static token leaked in logs or error output | Mask `SONIQ_MCP_AUTH_TOKEN` in all log/debug/config output paths |

## Developer Tool Specific Requirements

### Distribution Impact

SoniqMCP is distributed via PyPI (`pip` / `uvx`), Docker Hub, and a Helm chart for k3s. The auth feature extends server-side configuration only — no client-side SDK changes, no language matrix expansion. MCP clients interact with the server at the HTTP protocol level; auth is transparent to them.

| Channel | Auth feature impact |
|---------|-------------------|
| `pip` / `uvx` | New env vars documented; no install-step changes |
| Docker | Env vars in `docker-compose.yml`; CA cert mount via volume |
| Helm (k3s) | New Helm values: auth env vars, CA cert ConfigMap mount |

### API Surface

| Surface | Detail |
|---------|--------|
| `SoniqConfig.auth_mode` | Enum: `none` \| `static` \| `oidc` |
| `SoniqConfig.auth_token` | `str \| None` — static token (masked in logs) |
| `SoniqConfig.oidc_issuer` | `str \| None` — OIDC issuer URL |
| `SoniqConfig.oidc_audience` | `str \| None` — expected JWT audience |
| `SoniqConfig.oidc_jwks_uri` | `str \| None` — optional JWKS URI override |
| `TokenVerifier` protocol | FastMCP integration point: `async verify_token(token) -> AccessToken \| None` |
| `StaticTokenVerifier` | Implementation for `auth_mode=static` |
| `OIDCTokenVerifier` | Implementation for `auth_mode=oidc` |
| New env vars (5) | `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, `SONIQ_MCP_OIDC_JWKS_URI` |

### Migration Guide

**Existing deployments:** No migration required. `AUTH_MODE` defaults to `none`. All existing env var configs are unaffected. No new required fields introduced.

**Upgrade verification:** If the server starts cleanly after upgrading with no new errors, backward compatibility is confirmed. If `AUTH_MODE` is present in the environment from a prior experiment, the server validates the config at startup and fails fast with a clear message if it's incomplete.

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Problem-solving MVP — minimum feature set to credential-gate the HTTP endpoint for users who need it, without touching anything for users who don't.

**Resource profile:** Solo maintainer, AI-assisted development. Bounded scope: 5 config fields, 2 verifier classes (~35 lines total), preflight extension, tests, documentation.

### MVP Feature Set

**Must-have capabilities:**

- `AUTH_MODE` config: `none` | `static` | `oidc` (default: `none`)
- `StaticTokenVerifier` — constant-time Bearer token comparison
- `OIDCTokenVerifier` — RS256 JWT validation via PyJWT `PyJWKClient`, JWKS caching, single retry on key rotation
- Startup preflight: OIDC JWKS connectivity check; `AUTH_MODE=static` requires `AUTH_TOKEN` set
- `SONIQ_MCP_AUTH_TOKEN` masked in all log/debug output
- 5 new env vars with mappings in `config/loader.py`
- `@model_validator` in `SoniqConfig`: require `oidc_issuer` when `auth_mode=oidc`
- Unit tests: mock JWKS, valid/expired/tampered/missing token cases
- Smoke tests: 401 without token, 200 with valid token, stdio no-op
- `docs/setup/authentication.md`: all three modes, Authelia walkthrough, CA cert pattern, Claude Desktop scope note
- `.env.example` updated with commented auth examples

### Post-MVP Features

**Phase 2:**
- Community-contributed OIDC provider examples (Authentik, Auth0, Keycloak)
- Token acquisition example scripts for AI agent clients
- Auth status in health/readiness endpoint (if one is added)

**Phase 3 (Expansion):**
- RBAC / role-based claims validation — explicitly deferred; only revisited if the MCP specification mandates it

### Risk Mitigation

| Risk type | Risk | Mitigation |
|-----------|------|-----------|
| Technical | JWKS fetch at startup fails on first cold boot | Preflight fail-fast with clear error |
| Technical | JWKS cache doesn't handle key rotation | Retry JWKS fetch once on validation failure before 401 |
| Technical | `AUTH_MODE=none` introduces overhead | No-op path: zero code executed — verified by smoke test |
| Resource | Solo maintainer support surface | Free software terms; Authelia as reference path; community for other providers |
| Regression | Existing deployments broken by upgrade | `AUTH_MODE=none` default is strict no-op; smoke test covers backward compat |

## Functional Requirements

### Authentication Configuration

- **FR1:** An operator can configure the server's authentication mode by setting an environment variable with one of three values: disabled, static token, or OIDC
- **FR2:** An operator can configure a static Bearer token secret via environment variable for use in static auth mode
- **FR3:** An operator can configure an OIDC issuer URL, audience, and optional JWKS URI override via environment variables for use in OIDC auth mode
- **FR4:** The server can validate its authentication configuration at startup and report missing required fields with a clear, actionable error message before accepting any connections

### Request Authentication — Static Mode

- **FR5:** The server can extract a Bearer token from an incoming HTTP request's `Authorization` header
- **FR6:** The server can validate a Bearer token against the configured static secret using a constant-time comparison
- **FR7:** The server can reject requests with a missing or incorrect Bearer token with an HTTP 401 response in static auth mode

### Request Authentication — OIDC Mode

- **FR8:** The server can fetch a JSON Web Key Set from a configured OIDC provider's JWKS endpoint at startup
- **FR9:** The server can cache a fetched JWKS in memory to avoid per-request network calls
- **FR10:** The server can validate an RS256-signed JWT Bearer token against the cached JWKS, verifying issuer, audience, and expiry claims
- **FR11:** The server can reject requests with a missing, expired, or invalid JWT with an HTTP 401 response in OIDC auth mode
- **FR12:** The server can refresh the JWKS cache and retry validation once when a token fails validation, to handle OIDC provider key rotation
- **FR13:** The server can support a custom CA certificate trust chain for JWKS endpoint HTTPS connections via standard environment variable configuration

### Startup Validation & Error Reporting

- **FR14:** The server can verify connectivity to the configured OIDC JWKS endpoint at startup and abort with a clear error message if the endpoint is unreachable
- **FR15:** The server can report the specific JWKS endpoint URL, the network or TLS error encountered, and the likely cause when startup OIDC validation fails
- **FR16:** The server can detect when OIDC auth mode is configured without a required issuer URL and abort with a clear error message at startup

### No-Op & Backward Compatibility

- **FR17:** The server can operate with all existing behaviour unchanged when authentication mode is set to disabled (the default)
- **FR18:** The server can ignore any configured authentication mode when running on the stdio transport, without error or warning
- **FR19:** An operator can upgrade to this version without making any configuration changes and observe identical behaviour to the previous version

### Secret Handling

- **FR20:** The server can prevent the static authentication token value from appearing in log output, error messages, tracebacks, or configuration dumps

### Documentation & Operator Guidance

- **FR21:** An operator can find a complete setup guide for all three authentication modes in the project documentation
- **FR22:** An operator can find a step-by-step Authelia OIDC client registration walkthrough in the project documentation
- **FR23:** An operator can find guidance on configuring a custom CA certificate for OIDC JWKS fetching in the project documentation
- **FR24:** An operator can find a documented explanation of the Claude Desktop Bearer token limitation and which deployment patterns are most appropriate for each auth mode
- **FR25:** An operator can find commented authentication environment variable examples in the project's `.env.example` file

### Deployment Configuration

- **FR26:** An operator can configure authentication for Docker deployments using environment variables in a `docker-compose.yml` file
- **FR27:** An operator can configure authentication for k3s Helm deployments using Helm chart values, including CA certificate ConfigMap mounting

## Non-Functional Requirements

### Performance

- **NFR1:** Bearer token validation (static or OIDC) must add less than 5ms to request processing time under normal conditions
- **NFR2:** JWKS caching must ensure token validation makes no outbound network call on every request — only on cache miss or rotation retry
- **NFR3:** `AUTH_MODE=none` must introduce zero measurable overhead versus the current unauthenticated path — no conditional branches entered, no additional memory allocated

### Security

- **NFR4:** Static token comparison must be constant-time (`secrets.compare_digest`) — timing-based token enumeration must not be possible
- **NFR5:** The static auth token value must not appear in any log output, exception tracebacks, error responses, or Pydantic model serialisation
- **NFR6:** JWT validation must fail closed — any exception during verification must produce a 401, never a pass-through
- **NFR7:** JWKS must be fetched over HTTPS; plaintext HTTP JWKS endpoints must not be supported
- **NFR8:** JWT expiry (`exp` claim) must be validated on every request; tokens with elapsed expiry must be rejected regardless of signature validity

### Integration

- **NFR9:** OIDC token validation must be provider-agnostic — any issuer that exposes a standard JWKS endpoint and issues RS256 JWTs must work without code changes
- **NFR10:** The implementation must use the FastMCP `TokenVerifier` protocol as the integration point — no ASGI middleware bypass, no Uvicorn transport replacement
- **NFR11:** CA certificate trust must be configurable via the standard `SSL_CERT_FILE` environment variable — no proprietary cert-loading mechanism
- **NFR12:** The `TokenVerifier` implementation must return `None` (not raise) for invalid tokens, as required by the FastMCP `BearerAuthBackend` contract
