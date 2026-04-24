---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd-optional-auth.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/architecture.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/oidc-authelia-integration-assessment-2026-04-22.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/research/technical-oidc-fastmcp-authelia-research-2026-04-22.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/implementation-readiness-report-2026-04-23.md'
workflowType: 'epics-and-stories'
project_name: 'sonos-mcp-server'
feature: 'Optional Authentication v0.6.0'
user_name: 'Paul'
date: '2026-04-23'
---

# sonos-mcp-server Optional Authentication - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the SoniqMCP Optional Authentication v0.6.0 feature, decomposing the requirements from the optional-auth PRD, Phase 3 architecture decisions, and OIDC/Authelia research context into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: An operator can configure the server's authentication mode by setting an environment variable with one of three values: disabled, static token, or OIDC.

FR2: An operator can configure a static Bearer token secret via environment variable for use in static auth mode.

FR3: An operator can configure an OIDC issuer URL, audience, and optional JWKS URI override via environment variables for use in OIDC auth mode.

FR4: The server can validate its authentication configuration at startup and report missing required fields with a clear, actionable error message before accepting any connections.

FR5: The server can extract a Bearer token from an incoming HTTP request's `Authorization` header.

FR6: The server can validate a Bearer token against the configured static secret using a constant-time comparison.

FR7: The server can reject requests with a missing or incorrect Bearer token with an HTTP 401 response in static auth mode.

FR8: The server can fetch a JSON Web Key Set from a configured OIDC provider's JWKS endpoint at startup.

FR9: The server can cache a fetched JWKS in memory to avoid per-request network calls.

FR10: The server can validate an RS256-signed JWT Bearer token against the cached JWKS, verifying issuer, audience, and expiry claims.

FR11: The server can reject requests with a missing, expired, or invalid JWT with an HTTP 401 response in OIDC auth mode.

FR12: The server can refresh the JWKS cache and retry validation once when a token fails validation, to handle OIDC provider key rotation.

FR13: The server can support a custom CA certificate trust chain for JWKS endpoint HTTPS connections via standard environment variable configuration.

FR14: The server can verify connectivity to the configured OIDC JWKS endpoint at startup and abort with a clear error message if the endpoint is unreachable.

FR15: The server can report the specific JWKS endpoint URL, the network or TLS error encountered, and the likely cause when startup OIDC validation fails.

FR16: The server can detect when OIDC auth mode is configured without a required issuer URL and abort with a clear error message at startup.

FR17: The server can operate with all existing behaviour unchanged when authentication mode is set to disabled, the default.

FR18: The server can ignore any configured authentication mode when running on the stdio transport, without error or warning.

FR19: An operator can upgrade to this version without making any configuration changes and observe identical behaviour to the previous version.

FR20: The server can prevent the static authentication token value from appearing in log output, error messages, tracebacks, or configuration dumps.

FR21: An operator can find a complete setup guide for all three authentication modes in the project documentation.

FR22: An operator can find a step-by-step Authelia OIDC client registration walkthrough in the project documentation.

FR23: An operator can find guidance on configuring a custom CA certificate for OIDC JWKS fetching in the project documentation.

FR24: An operator can find a documented explanation of the Claude Desktop Bearer token limitation and which deployment patterns are most appropriate for each auth mode.

FR25: An operator can find commented authentication environment variable examples in the project's `.env.example` file.

FR26: An operator can configure authentication for Docker deployments using environment variables in a `docker-compose.yml` file.

FR27: An operator can configure authentication for k3s Helm deployments using Helm chart values, including CA certificate ConfigMap mounting.

### NonFunctional Requirements

NFR1: Bearer token validation, static or OIDC, must add less than 5ms to request processing time under normal conditions.

NFR2: JWKS caching must ensure token validation makes no outbound network call on every request, only on cache miss or rotation retry.

NFR3: `AUTH_MODE=none` must introduce zero measurable overhead versus the current unauthenticated path, with no conditional branches entered and no additional memory allocated.

NFR4: Static token comparison must be constant-time using `secrets.compare_digest`, so timing-based token enumeration is not possible.

NFR5: The static auth token value must not appear in any log output, exception tracebacks, error responses, or Pydantic model serialisation.

NFR6: JWT validation must fail closed; any exception during verification must produce a 401, never a pass-through.

NFR7: JWKS must be fetched over HTTPS; plaintext HTTP JWKS endpoints must not be supported.

NFR8: JWT expiry through the `exp` claim must be validated on every request; tokens with elapsed expiry must be rejected regardless of signature validity.

NFR9: OIDC token validation must be provider-agnostic; any issuer that exposes a standard JWKS endpoint and issues RS256 JWTs must work without code changes.

NFR10: The implementation must use the FastMCP `TokenVerifier` protocol as the integration point, with no ASGI middleware bypass and no Uvicorn transport replacement.

NFR11: CA certificate trust must be configurable via the standard `SSL_CERT_FILE` environment variable, with no proprietary cert-loading mechanism required.

NFR12: The `TokenVerifier` implementation must return `None`, not raise, for invalid tokens, as required by the FastMCP `BearerAuthBackend` contract.

### Additional Requirements

- This is a bounded brownfield feature addition; no project re-initialisation or platform reset is required.
- Add `PyJWT>=2.8` as the sole new production dependency; `cryptography>=46.0.7` already exists and supplies RSA support.
- Keep auth as a transport/server concern only. No auth logic may enter `tools/`, `services/`, `adapters/`, or Sonos domain logic.
- Add `AuthMode` to `src/soniq_mcp/config/models.py` with values `none`, `static`, and `oidc`; keep the default as `none`.
- Add config fields: `auth_mode`, `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, and `oidc_resource_url`.
- Map env vars: `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, `SONIQ_MCP_OIDC_JWKS_URI`, `SONIQ_MCP_OIDC_CA_BUNDLE`, and `SONIQ_MCP_OIDC_RESOURCE_URL`.
- Store the static token as Pydantic `SecretStr`; `get_secret_value()` may be called only inside `StaticBearerVerifier.verify_token()`.
- Add `src/soniq_mcp/auth/__init__.py` exporting `build_token_verifier(config) -> TokenVerifier`.
- Add `src/soniq_mcp/auth/verifiers.py` with `StaticBearerVerifier` and `OIDCVerifier`.
- Wire auth only in `create_server()` via `_build_auth_settings(config)` and `build_token_verifier(config)` behind an `auth_mode != AuthMode.NONE` guard.
- `AUTH_MODE=none` must leave the FastMCP constructor call structurally identical to the current implementation.
- `AuthSettings` is required whenever `token_verifier` is passed to FastMCP.
- For static auth, derive `issuer_url` from the server HTTP base URL rather than using a fake external issuer.
- For OIDC auth, use `oidc_issuer` as `issuer_url`; `required_scopes` remains `None`.
- Verify story-level behavior for `oidc_resource_url` default and Authelia audience/resource binding.
- Implement OIDC with `PyJWKClient` and cached JWKS; do not use the separate `fastmcp` package or a generic auth framework.
- Support custom CA trust through standard `SSL_CERT_FILE` and optional `oidc_ca_bundle`.
- Add auth preflight checks to `config/validation.py` `run_preflight()`; verifier constructors must not become preflight validators.
- OIDC startup preflight performs live JWKS connectivity validation and reports endpoint URL, network/TLS error, likely cause, and docs reference.
- Static auth preflight requires `auth_token` when `auth_mode=static`.
- Stdio transport remains unaffected; configured auth in stdio mode must not block local use.
- Unit verifier tests live in `tests/unit/auth/test_verifiers.py`; config validation tests extend `tests/unit/config/test_validation.py`.
- Smoke tests use `auth_mode=static` only; CI must not depend on Authelia.
- Extend existing streamable HTTP smoke tests for missing-token 401 and valid-token success.
- Add `docs/setup/authentication.md` covering none/static/OIDC modes, Authelia, CA certificates, Docker, Helm, and Claude Desktop scope limitations.
- Update `.env.example` with commented auth examples.
- Update Helm values for auth env vars and CA cert ConfigMap mounting.
- Keep Docker support env-var driven; Docker Compose may be documented rather than structurally changed if no compose file exists or is not part of release assets.
- Recommended but non-blocking: add `make test-auth` and `make smoke-auth` targets.

### UX Design Requirements

No UX design document exists and no first-party UI changes are required. Operator experience requirements are represented through configuration behavior, startup diagnostics, deployment examples, and documentation.

### FR Coverage Map

FR1: Epic 1 - Auth mode environment variable belongs to the safe opt-in configuration foundation.

FR2: Epic 1 - Static token configuration is part of the validated auth configuration surface.

FR3: Epic 1 - OIDC issuer, audience, and JWKS configuration are part of the validated auth configuration surface.

FR4: Epic 1 - Startup validation for missing auth configuration belongs to the safe opt-in foundation.

FR5: Epic 2 - Bearer token extraction is required for static HTTP protection.

FR6: Epic 2 - Constant-time static token comparison is required for static HTTP protection.

FR7: Epic 2 - Static mode must reject missing or incorrect credentials with HTTP 401.

FR8: Epic 3 - OIDC mode must fetch JWKS at startup.

FR9: Epic 3 - OIDC mode must cache JWKS in memory.

FR10: Epic 3 - OIDC mode must validate RS256 JWT issuer, audience, and expiry.

FR11: Epic 3 - OIDC mode must reject missing, expired, or invalid JWTs with HTTP 401.

FR12: Epic 3 - OIDC mode must refresh JWKS once on token validation failure to handle key rotation.

FR13: Epic 3 - OIDC mode must support custom CA trust for JWKS HTTPS connections.

FR14: Epic 3 - OIDC mode must verify JWKS connectivity at startup.

FR15: Epic 3 - OIDC startup failures must report endpoint URL, network/TLS error, and likely cause.

FR16: Epic 1 - OIDC mode without a required issuer must fail startup configuration validation.

FR17: Epic 1 - Disabled auth mode must preserve existing behavior.

FR18: Epic 1 - Stdio transport must ignore auth configuration without error or warning.

FR19: Epic 1 - Existing deployments must upgrade without configuration changes or behavior changes.

FR20: Epic 1 - Static auth token secrecy is a configuration and logging safety requirement.

FR21: Epic 4 - Operators need a complete setup guide for all auth modes.

FR22: Epic 4 - Operators need an Authelia OIDC client registration walkthrough.

FR23: Epic 4 - Operators need custom CA certificate guidance.

FR24: Epic 4 - Operators need Claude Desktop Bearer token limitation guidance.

FR25: Epic 4 - Operators need commented auth examples in `.env.example`.

FR26: Epic 4 - Operators need Docker authentication configuration guidance.

FR27: Epic 4 - Operators need Helm/k3s auth values and CA certificate mounting support.

## Epic List

### Epic 1: Safe Opt-In Auth Configuration

Operators can upgrade to v0.6.0 with no behavior change by default, while gaining a validated configuration surface for optional HTTP authentication.

**FRs covered:** FR1, FR2, FR3, FR4, FR16, FR17, FR18, FR19, FR20

### Epic 2: Static Bearer Token Protection for HTTP

Shared-LAN and Docker users can enable a simple Bearer token gate for HTTP transport and receive 401 responses for missing or incorrect credentials.

**FRs covered:** FR5, FR6, FR7

### Epic 3: OIDC and JWKS Validation for Homelab Operators

Homelab operators can configure SoniqMCP to validate RS256 OIDC JWTs against a cached JWKS endpoint, including custom CA support and key-rotation behavior.

**FRs covered:** FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15

### Epic 4: Operator Adoption, Deployment, and Release Readiness

Operators can configure and verify optional auth across local, Docker, and Helm/k3s deployments using complete docs, examples, smoke coverage, and release-safe defaults.

**FRs covered:** FR21, FR22, FR23, FR24, FR25, FR26, FR27

## Epic 1: Safe Opt-In Auth Configuration

Operators can upgrade to v0.6.0 with no behavior change by default, while gaining a validated configuration surface for optional HTTP authentication.

### Story 1.1: Add Optional Auth Configuration Model

As an operator,
I want SoniqMCP to expose optional authentication settings through validated configuration,
So that I can choose `none`, `static`, or `oidc` auth without changing existing deployments.

**Acceptance Criteria:**

**Given** no auth environment variables are configured
**When** configuration is loaded
**Then** `auth_mode` defaults to `none`.

**Given** `SONIQ_MCP_AUTH_MODE` is set to `none`, `static`, or `oidc`
**When** configuration is loaded
**Then** the value is parsed into an `AuthMode` enum.

**Given** static token, OIDC issuer, audience, JWKS URI, CA bundle, or resource URL env vars are set
**When** configuration is loaded
**Then** the corresponding `SoniqConfig` fields are populated.

**Given** a static auth token is configured
**When** the config model is represented or serialized
**Then** the raw token value is masked.

**Given** an unsupported auth mode is configured
**When** configuration is loaded or validated
**Then** startup fails with a clear validation error.

### Story 1.2: Validate Auth Configuration During Preflight

As an operator,
I want invalid auth configuration to fail before the server accepts requests,
So that setup errors are caught early with actionable feedback.

**Acceptance Criteria:**

**Given** `auth_mode=static` and no auth token is configured
**When** preflight runs
**Then** it fails with a clear missing-token error.

**Given** `auth_mode=oidc` and no issuer is configured
**When** preflight runs
**Then** it fails with a clear missing-issuer error.

**Given** `auth_mode=none`
**When** preflight runs
**Then** no auth-specific validation failure occurs.

**Given** auth is configured while running stdio transport
**When** preflight runs
**Then** stdio startup is not blocked.

**Given** a validation failure occurs
**When** the error is reported
**Then** it does not include the raw static token.

### Story 1.3: Preserve Backward Compatibility for Disabled Auth

As an existing SoniqMCP user,
I want upgrading to v0.6.0 to preserve current behavior unless I opt into auth,
So that local and existing HTTP deployments continue working without migration.

**Acceptance Criteria:**

**Given** `auth_mode=none`
**When** `create_server()` builds the FastMCP app
**Then** no `auth` or `token_verifier` argument is passed.

**Given** existing env vars from a pre-auth deployment
**When** the server starts
**Then** startup behavior remains unchanged.

**Given** stdio transport is used
**When** auth fields are absent
**Then** tool registration and server startup remain unchanged.

**Given** tests inspect the disabled-auth path
**When** compared to current server construction behavior
**Then** no auth module is imported or invoked.

**Given** the default config is serialized for diagnostics
**When** diagnostics output is produced
**Then** no auth token field leaks a secret value.

## Epic 2: Static Bearer Token Protection for HTTP

Shared-LAN and Docker users can enable a simple Bearer token gate for HTTP transport and receive 401 responses for missing or incorrect credentials.

### Story 2.1: Implement Static Bearer Token Verifier

As a shared-LAN HTTP operator,
I want SoniqMCP to validate a configured static Bearer token,
So that only clients with the shared token can use HTTP tools.

**Acceptance Criteria:**

**Given** `auth_mode=static` and a configured `auth_token`
**When** `build_token_verifier(config)` is called
**Then** it returns a `StaticBearerVerifier`.

**Given** a request token matching the configured secret
**When** `verify_token(token)` runs
**Then** it returns a FastMCP-compatible `AccessToken`.

**Given** a missing, empty, or incorrect token
**When** `verify_token(token)` runs
**Then** it returns `None`.

**Given** static token comparison occurs
**When** implementation is inspected or tested
**Then** it uses `secrets.compare_digest`.

**Given** static token verification runs
**When** logs or errors are emitted
**Then** the raw configured token and presented token are never included.

**Given** `get_secret_value()` is used
**When** the codebase is inspected
**Then** it appears only inside `StaticBearerVerifier.verify_token()`.

### Story 2.2: Wire Static Auth into HTTP Server Construction

As an HTTP operator,
I want static auth to be enforced by FastMCP before tool handlers run,
So that unauthorized clients receive 401 responses without touching Sonos tools or services.

**Acceptance Criteria:**

**Given** `auth_mode=static`
**When** `create_server(config)` builds the FastMCP app
**Then** it passes both `auth` and `token_verifier`.

**Given** `auth_mode=static`
**When** auth settings are built
**Then** `issuer_url` is derived from the configured HTTP host and port.

**Given** `auth_mode=static`
**When** the app starts
**Then** no auth code is added to tools, services, adapters, or transport runners.

**Given** a client calls the HTTP MCP endpoint without an Authorization header
**When** static auth is enabled
**Then** the response is HTTP 401.

**Given** a client calls the HTTP MCP endpoint with an incorrect Bearer token
**When** static auth is enabled
**Then** the response is HTTP 401.

**Given** a client calls the HTTP MCP endpoint with the correct Bearer token
**When** static auth is enabled
**Then** the request reaches normal MCP handling.

### Story 2.3: Add Static Auth Regression Coverage

As a maintainer,
I want automated coverage for static auth behavior,
So that the simplest auth path and disabled-auth compatibility do not regress.

**Acceptance Criteria:**

**Given** static auth unit tests run
**When** valid and invalid token cases are exercised
**Then** they pass without network or Authelia dependencies.

**Given** static auth HTTP smoke tests run
**When** no token is provided
**Then** the test observes HTTP 401.

**Given** static auth HTTP smoke tests run
**When** the valid token is provided
**Then** the test observes normal MCP behavior.

**Given** disabled-auth regression tests run
**When** `auth_mode=none`
**Then** no auth verifier is created.

**Given** all static auth tests run in CI
**When** the tests execute
**Then** they do not require real Sonos hardware or an external identity provider.

## Epic 3: OIDC and JWKS Validation for Homelab Operators

Homelab operators can configure SoniqMCP to validate RS256 OIDC JWTs against a cached JWKS endpoint, including custom CA support and key-rotation behavior.

### Story 3.1: Implement OIDC JWT Verifier with Cached JWKS

As a homelab operator,
I want SoniqMCP to validate OIDC Bearer JWTs using a configured JWKS endpoint,
So that existing identity-provider tokens can protect HTTP MCP access.

**Acceptance Criteria:**

**Given** `auth_mode=oidc` and valid OIDC configuration
**When** `build_token_verifier(config)` is called
**Then** it returns an `OIDCVerifier`.

**Given** `OIDCVerifier` is constructed
**When** it initializes
**Then** it creates a `PyJWKClient` once and keeps it for the verifier lifetime.

**Given** a valid RS256 JWT with expected issuer, audience, and non-expired `exp`
**When** `verify_token(token)` runs
**Then** it returns a FastMCP-compatible `AccessToken`.

**Given** the JWT includes `client_id`, `sub`, `scope`, `scp`, or `exp` claims
**When** `AccessToken` is created
**Then** client id, scopes, and expiry are mapped consistently.

**Given** a missing, expired, tampered, wrongly issued, or wrong-audience token
**When** `verify_token(token)` runs
**Then** it returns `None`.

**Given** JWT validation raises a PyJWT or unexpected exception
**When** `verify_token(token)` handles it
**Then** it fails closed by returning `None` without leaking token content.

### Story 3.2: Support JWKS Refresh, HTTPS, and Custom CA Trust

As a homelab operator with a self-signed CA,
I want SoniqMCP to fetch and refresh OIDC signing keys safely,
So that token validation works with my provider without per-request network calls.

**Acceptance Criteria:**

**Given** an OIDC JWKS URI is configured
**When** the verifier fetches keys
**Then** it uses HTTPS and rejects plaintext HTTP JWKS endpoints.

**Given** `SSL_CERT_FILE` is set
**When** JWKS is fetched
**Then** standard Python TLS trust behavior can use that certificate bundle.

**Given** `oidc_ca_bundle` is configured
**When** `OIDCVerifier` initializes
**Then** it builds an SSL context from that CA bundle for JWKS fetching.

**Given** JWKS has already been fetched
**When** multiple valid tokens are verified
**Then** validation does not make an outbound network call for every request.

**Given** token validation fails because a signing key is unknown or rotated
**When** `verify_token(token)` handles the failure
**Then** it refreshes JWKS once and retries validation before returning `None`.

**Given** JWKS refresh still fails
**When** `verify_token(token)` completes
**Then** the token is rejected with `None` and no exception escapes.

### Story 3.3: Add OIDC Startup Preflight and Actionable Errors

As a homelab operator,
I want OIDC misconfiguration to fail at startup with actionable diagnostics,
So that TLS, issuer, and JWKS problems are fixed before clients see confusing 401s.

**Acceptance Criteria:**

**Given** `auth_mode=oidc` and a reachable JWKS endpoint
**When** preflight runs
**Then** startup validation succeeds.

**Given** `auth_mode=oidc` and the JWKS endpoint is unreachable
**When** preflight runs
**Then** startup fails before accepting requests.

**Given** JWKS startup validation fails due to TLS trust
**When** the error is reported
**Then** it includes the JWKS URL, the network or TLS error category, likely cause, and authentication docs reference.

**Given** `oidc_jwks_uri` is not configured
**When** preflight runs
**Then** it derives or discovers the JWKS endpoint according to the documented OIDC configuration behavior.

**Given** `oidc_resource_url` is not configured
**When** OIDC auth settings are built
**Then** the implementation verifies whether `resource_server_url=None` works with FastMCP `AuthSettings` and Authelia audience validation.

**Given** the verification shows `resource_server_url` must be explicit
**When** preflight validates OIDC config
**Then** it requires or derives a stable resource URL with a clear error or default.

**Given** OIDC preflight logs configuration context
**When** logs are emitted
**Then** they never include presented JWTs or static auth secrets.

### Story 3.4: Add OIDC Verifier Unit Coverage

As a maintainer,
I want OIDC validation covered without external identity-provider dependencies,
So that provider-agnostic JWT behavior remains reliable in CI.

**Acceptance Criteria:**

**Given** OIDC verifier unit tests run
**When** RSA key pairs and JWTs are generated in-process
**Then** tests do not require Authelia or network access.

**Given** a valid RS256 JWT test case
**When** `verify_token(token)` runs
**Then** it returns an `AccessToken`.

**Given** expired, tampered, wrong-issuer, wrong-audience, and missing-claim token cases
**When** tests run
**Then** each case returns `None`.

**Given** key rotation behavior is tested
**When** the initial signing key is unavailable
**Then** JWKS refresh is attempted once.

**Given** custom CA bundle behavior is tested
**When** `oidc_ca_bundle` is configured
**Then** SSL context construction is verified without making a live network call.

**Given** `TokenVerifier` compatibility is tested
**When** the verifier class is inspected or type-checked
**Then** its signature matches FastMCP’s expected `verify_token(token: str) -> AccessToken | None` contract.

## Epic 4: Operator Adoption, Deployment, and Release Readiness

Operators can configure and verify optional auth across local, Docker, and Helm/k3s deployments using complete docs, examples, smoke coverage, and release-safe defaults.

### Story 4.1: Document Optional Auth Setup and Constraints

As an operator,
I want a complete authentication guide for none, static, and OIDC modes,
So that I can choose and configure the right auth path without reading source code.

**Acceptance Criteria:**

**Given** the auth documentation is added
**When** operators read it
**Then** it explains `none`, `static`, and `oidc` modes and when to use each.

**Given** an operator wants static auth
**When** they follow the guide
**Then** they can configure the required env vars and understand the expected 401 and authorized behavior.

**Given** an operator wants OIDC auth
**When** they follow the guide
**Then** they can configure issuer, audience, JWKS, and CA trust inputs.

**Given** Claude Desktop limitations apply
**When** the guide discusses client support
**Then** it explicitly documents the Bearer token limitation and appropriate deployment patterns.

**Given** the guide documents CA certificate handling
**When** operators troubleshoot TLS trust
**Then** it references `SSL_CERT_FILE` and the supported CA bundle approach.

**Given** the guide is published
**When** maintainers review it
**Then** it matches the implemented config names and startup behavior.

### Story 4.2: Add Deployment Examples for Docker and Helm

As an operator running SoniqMCP in containers or k3s,
I want auth-specific deployment examples,
So that I can enable authentication without inventing my own config patterns.

**Acceptance Criteria:**

**Given** `.env.example` is updated
**When** operators inspect it
**Then** it contains commented examples for static and OIDC auth env vars.

**Given** Helm values are updated
**When** operators configure auth in k3s
**Then** auth env vars and CA certificate mount scaffolding are represented in chart values or templates as required by the release scope.

**Given** Docker deployment guidance is updated
**When** operators follow it
**Then** they can configure auth env vars and CA trust mounting using documented container patterns.

**Given** Authelia is the reference OIDC provider
**When** the documentation covers Helm or k3s deployment
**Then** it includes an operator-facing walkthrough or pointer for the Authelia client registration path.

**Given** cross-repo Terraform or Authelia work is not implemented in this repo
**When** documentation mentions it
**Then** the boundary between `sonos-mcp-server` and `iot-edge-k3s` responsibilities is explicit.

**Given** deployment examples are reviewed
**When** compared to actual config fields and chart values
**Then** names and defaults are consistent.

### Story 4.3: Add Auth Smoke Coverage and Release Validation

As a maintainer,
I want release-facing validation for optional auth adoption paths,
So that docs, examples, and the simplest protected runtime path stay accurate.

**Acceptance Criteria:**

**Given** auth smoke tests run
**When** static auth is enabled and no token is sent
**Then** the test observes HTTP 401.

**Given** auth smoke tests run
**When** static auth is enabled and the correct token is sent
**Then** the test observes successful MCP handling.

**Given** release validation covers disabled auth
**When** `auth_mode=none`
**Then** the existing startup path remains unchanged.

**Given** documentation and examples are updated
**When** reviewed against implementation
**Then** auth env var names and setup steps match shipped behavior.

**Given** CI executes auth-related validation
**When** the pipeline runs
**Then** it does not require Authelia, external OIDC infrastructure, or Sonos hardware.

**Given** the release is prepared
**When** maintainers assess optional auth readiness
**Then** the docs, examples, and smoke coverage together support shipping the feature without hidden setup gaps.
