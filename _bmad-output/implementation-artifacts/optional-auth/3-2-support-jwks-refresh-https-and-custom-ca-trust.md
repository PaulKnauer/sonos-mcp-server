# Story 3.2: Support JWKS Refresh, HTTPS, and Custom CA Trust

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a homelab operator with a self-signed CA,
I want SoniqMCP to fetch and refresh OIDC signing keys safely,
so that token validation works with my provider without per-request network calls.

## Acceptance Criteria

1. Given an OIDC JWKS URI is configured, when the verifier fetches keys, then it uses HTTPS and rejects plaintext HTTP JWKS endpoints.
2. Given `SSL_CERT_FILE` is set, when JWKS is fetched, then standard Python TLS trust behavior can use that certificate bundle.
3. Given `oidc_ca_bundle` is configured, when `OIDCVerifier` initializes, then it builds an SSL context from that CA bundle for JWKS fetching.
4. Given JWKS has already been fetched, when multiple valid tokens are verified, then validation does not make an outbound network call for every request.
5. Given token validation fails because a signing key is unknown or rotated, when `verify_token(token)` handles the failure, then it refreshes JWKS once and retries validation before returning `None`.
6. Given JWKS refresh still fails, when `verify_token(token)` completes, then the token is rejected with `None` and no exception escapes.

## Tasks / Subtasks

- [x] Harden `OIDCVerifier` JWKS client construction for HTTPS and custom CA trust (AC: 1, 2, 3, 4)
  - [x] Update [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) so `OIDCVerifier.__init__` rejects any configured `oidc_jwks_uri` whose scheme is not `https`.
  - [x] Keep the verifier fail-closed: an invalid or non-HTTPS JWKS URI must result in `verify_token()` returning `None`, not a server crash from request-time auth handling.
  - [x] Preserve the standard-library TLS path for `SSL_CERT_FILE`; do not replace global trust handling or introduce a custom env-var parser for the default path.
  - [x] When `config.oidc_ca_bundle` is set, build one `ssl.SSLContext` with `ssl.create_default_context(cafile=...)` and pass it into `PyJWKClient(..., ssl_context=...)`.
  - [x] Keep the SSL context scoped to the verifier instance; do not create it per request.
  - [x] Continue using one long-lived `PyJWKClient` per verifier instance so the built-in JWK-set cache remains effective.

- [x] Use `PyJWT`’s existing JWKS refresh semantics correctly instead of reinventing them (AC: 4, 5, 6)
  - [x] Keep token key resolution on `PyJWKClient.get_signing_key_from_jwt(token)`.
  - [x] Rely on `PyJWT`’s built-in single refresh-and-retry behavior for unknown `kid` values rather than adding a second manual refresh layer in `verify_token()`.
  - [x] Catch final `PyJWTError` / `PyJWKClientError` outcomes and return `None` without leaking token content or stack traces.
  - [x] Do not add per-request JWKS fetches, custom cache storage, or external cache dependencies.

- [x] Add focused unit coverage for the new JWKS trust and refresh behaviors (AC: 1, 2, 3, 4, 5, 6)
  - [x] Extend [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) with a constructor test proving HTTPS JWKS URIs are accepted and plaintext HTTP URIs are rejected.
  - [x] Add a constructor test proving `oidc_ca_bundle` causes `ssl.create_default_context(cafile=...)` to be called once and that the resulting context is passed into `PyJWKClient`.
  - [x] Add a test proving the default path leaves `ssl_context=None`, so `SSL_CERT_FILE` can continue to drive trust through Python’s normal TLS behavior.
  - [x] Add a test proving repeated valid-token verification reuses the same verifier-owned `PyJWKClient` instead of reconstructing the client.
  - [x] Add a test that exercises the key-rotation path at the `PyJWT` boundary and proves the verifier accepts success after the single refresh retry.
  - [x] Add a test proving that final JWKS lookup or refresh failure still returns `None`.

- [x] Preserve story boundaries established by 3.1 and reserved for later stories
  - [x] Do not wire HTTP OIDC auth into [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py); Story 3.3 owns the runtime/server-path change.
  - [x] Do not add startup OIDC connectivity checks or actionable preflight diagnostics to [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py); Story 3.3 owns that behavior.
  - [x] Do not add smoke tests with a live OIDC provider; Story 3.4 owns the broader OIDC verifier coverage matrix.
  - [x] Do not push auth logic into `tools/`, `services/`, `adapters/`, or transport runners.

### Review Findings

- [x] [Review][Patch] Fail closed when `oidc_ca_bundle` cannot be loaded [src/soniq_mcp/auth/verifiers.py:115]
- [x] [Review][Patch] Exercise the actual JWKS refresh-and-retry path in verifier tests [tests/unit/auth/test_verifiers.py:377]

## Dev Notes

### Story Intent

Story 3.1 established the OIDC verifier primitive. Story 3.2 hardens that verifier for real homelab deployments by adding:

- HTTPS-only JWKS transport
- optional verifier-local custom CA support
- explicit preservation of the built-in JWKS cache
- verified refresh behavior for rotated signing keys

This is still a verifier-only story. It should not become a startup-validation or server-wiring story.

### Story Foundation

Epic 3 covers FR8-FR15 and NFR1-NFR12 for the OIDC path. Story 3.2 specifically implements:

- FR12: refresh JWKS once on validation failure caused by key rotation
- FR13: support custom CA trust for JWKS endpoint HTTPS connections
- NFR2: avoid per-request outbound network calls
- NFR7: do not support plaintext HTTP JWKS endpoints
- NFR12: return `None`, never raise, for invalid tokens

The later startup-facing requirements remain with Story 3.3:

- FR14: startup JWKS connectivity validation
- FR15: actionable startup error reporting

### What Already Exists

Current repo state relevant to Story 3.2:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) already implements `OIDCVerifier`, but today it constructs `PyJWKClient(config.oidc_jwks_uri or "")` with no HTTPS scheme check and no custom `ssl_context`.
- The current `OIDCVerifier.verify_token()` path already fails closed for `PyJWTError` and unexpected exceptions, and still validates `iss`, `aud`, and `exp`.
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py) already routes `AuthMode.OIDC` to `OIDCVerifier`; this story should preserve that public surface.
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) already covers the basic OIDC constructor, claim mapping, and fail-closed behavior from Story 3.1.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) still ignores HTTP OIDC wiring on purpose. That is correct for this story.
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) still has no OIDC JWKS connectivity preflight. That is also correct for this story.

### Files To Read Before Implementing

Read these files completely before editing:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)
- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)

### Current-State Guardrails For UPDATE Files

#### `src/soniq_mcp/auth/verifiers.py`

Current state:

- `StaticBearerVerifier` and `OIDCVerifier` live together in this file.
- `OIDCVerifier` stores `_issuer`, `_audience`, `_resource`, and `_jwk_client`.
- The verifier currently uses `PyJWKClient.get_signing_key_from_jwt(token)` followed by `jwt.decode(..., algorithms=["RS256"], audience=..., issuer=...)`.
- `_extract_scopes()` already normalizes `scp` and `scope`.

What this story changes:

- add JWKS URI scheme validation
- optionally create and pass one `ssl.SSLContext`
- preserve and explicitly rely on `PyJWKClient` cache/refresh behavior
- harden tests around refresh and CA behavior

What must be preserved:

- static-auth behavior and the `get_secret_value()` confinement rule
- existing claim mapping (`client_id`/`sub`, `scp`/`scope`, `exp`)
- fail-closed `None` return contract
- no token content in logs or exceptions

#### `tests/unit/auth/test_verifiers.py`

Current state:

- contains static-auth regression tests plus Story 3.1 OIDC constructor/claim/fail-closed tests
- uses local helpers (`config_with_oidc()`, `run_verify(...)`) and monkeypatch-based `PyJWKClient` doubles
- already asserts `build_token_verifier()` returns `OIDCVerifier`

What this story changes:

- add focused constructor and refresh tests
- add SSL-context coverage
- extend OIDC verifier tests without introducing network or live provider dependencies

What must be preserved:

- current static-auth tests
- AST-based secret-unwrapping guard
- no external identity provider requirement in unit tests

#### `tests/unit/test_server.py`

Current state:

- asserts stdio ignores auth and HTTP OIDC is still ignored

What this story changes:

- nothing

What must be preserved:

- HTTP OIDC still not wired in this story
- disabled-auth and stdio no-op invariants

### Previous Story Intelligence

From Story 3.1:

- Story 3.1 intentionally deferred HTTPS enforcement, custom CA handling, and refresh logic to this story. Do not re-scope them again. [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md#Tasks--Subtasks]
- The current verifier already uses one `PyJWKClient` instance and the official `jwt.decode()` path. Build on that rather than replacing the verifier shape. [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md#Completion-Notes-List]
- Server wiring and preflight were intentionally left untouched in 3.1; keep those boundaries intact here. [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md#Architecture-Compliance]

From Epic 2 retrospective:

- Disabled-auth and stdio behavior are first-class acceptance concerns whenever auth expands. Story 3.2 must not weaken those invariants while working only inside the verifier module. [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#Lessons-Learned]
- Boundary discipline mattered in Epic 2 and becomes even more important in Epic 3. Keep auth logic verifier-local and server-local only. [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#What-Went-Well]

### Git Intelligence Summary

Recent auth work sequence:

- `905686c` implemented the static bearer verifier
- `a97cf21` wired static auth into the HTTP server path
- `6fd6256` added static auth regression coverage
- `52b394a` implemented the base OIDC verifier for Story 3.1

Pattern to preserve:

- runtime behavior introduced in small story-scoped increments
- auth boundary changes verified with focused tests
- no-op paths protected continuously as auth complexity increases

### Architecture Guardrails

- Auth remains a transport/server concern only. No auth logic may enter `tools/`, `services/`, `adapters/`, or transport runners. [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- `OIDCVerifier` stays in [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py); do not move it into `server.py` or `config/`. [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- `build_token_verifier(config)` remains the only public auth-module factory surface. [Source: _bmad-output/planning-artifacts/architecture.md#Naming-Patterns]
- `verify_token()` must continue to return `None`, not raise, for invalid tokens or JWKS lookup failures. [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- `ssl_context` should be constructed once in `OIDCVerifier.__init__`, not per request. [Source: _bmad-output/planning-artifacts/architecture.md#Communication-Patterns]
- `required_scopes` remains deferred; do not introduce scope enforcement here. [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]

### Technical Requirements

- Use Python’s standard `ssl` module for custom CA support; `ssl.create_default_context(cafile=...)` is the intended shape for `oidc_ca_bundle`.
- Continue using `PyJWKClient` as the sole JWKS client implementation; do not introduce `httpx`, `requests`, `authlib`, or bespoke JWKS fetch logic.
- Preserve `jwt.decode(..., algorithms=["RS256"], audience=..., issuer=...)`; do not derive accepted algorithms from token headers.
- Explicitly reject non-HTTPS `oidc_jwks_uri` values in verifier construction or before client creation. `PyJWKClient` itself accepts an arbitrary URL string and does not enforce HTTPS for us.
- Treat `SSL_CERT_FILE` as the zero-code/default trust path. When no explicit CA bundle is configured, leave `ssl_context=None` so Python’s normal TLS behavior remains in effect.

### Architecture Compliance

- Keep this story’s changes limited to verifier internals and verifier unit tests.
- Do not add runtime OIDC auth wiring to `FastMCP` yet.
- Do not add startup connectivity probes or docs-link diagnostics yet.
- Do not create a second retry loop around `jwt.decode()` failures. Story 3.2 is about correct JWKS behavior, not repeated retries for every verification error category.

### Library / Framework Requirements

- `pyjwt[crypto]>=2.12.1` is already a direct production dependency and remains the only production JWT/JWKS dependency. [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- The installed `PyJWT` implementation already provides:
  - JWK-set caching by default
  - optional `ssl_context`
  - one refresh-and-retry on missing `kid`
  [Source: local package inspection via `uv run python` on `jwt.jwks_client.PyJWKClient`]
- The MCP Python SDK stable docs still use `TokenVerifier` plus `AuthSettings` as the server auth integration surface. This story should not bypass that model. [Source: https://github.com/modelcontextprotocol/python-sdk]

### File Structure Requirements

Expected touched files for Story 3.2:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)

Files this story should not modify unless a narrowly justified test fixture demands it:

- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)
- [tests/smoke/streamable_http/test_streamable_http_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/streamable_http/test_streamable_http_smoke.py)

### Testing Requirements

- Keep all tests network-free and provider-free.
- Prefer monkeypatching `PyJWKClient`, `ssl.create_default_context`, and `jwt.decode` rather than adding a live JWKS server.
- Add at least one test that proves the verifier passes an `ssl_context` into `PyJWKClient` only when `oidc_ca_bundle` is configured.
- Add at least one test that proves plaintext HTTP JWKS URIs are not accepted.
- Add at least one test that proves key-rotation success after the built-in refresh path still yields an `AccessToken`.
- Add at least one test that proves final refresh failure still returns `None`.
- Preserve existing static-auth, OIDC-claim-mapping, and disabled-auth tests.

### Latest Technical Information

- PyJWT 2.12.1 documents `PyJWKClient(uri, ..., ssl_context=None)` and states that the JWK-set cache is enabled by default with a 300-second lifespan. That directly supports the “no outbound network call for every request” acceptance criterion. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- The same PyJWT API docs state that `get_signing_key(kid)` refreshes the JWK set and retries once when no matching key is found, and `get_signing_key_from_jwt(token)` delegates to that method. Story 3.2 should rely on that existing behavior rather than duplicating it. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- Local inspection of the installed `jwt.jwks_client.PyJWKClient` implementation in this repo’s `uv` environment confirms the same runtime behavior: cached JWK-set lookup by default, `ssl_context` support, and a single `refresh=True` retry on unknown `kid`. [Source: local package inspection via `uv run python` on 2026-05-05]
- The MCP authorization spec current at 2025-06-18 requires HTTP clients to send `Authorization: Bearer <access-token>` on every request and requires servers to reject invalid or expired tokens with HTTP 401. This reinforces the fail-closed verifier contract and the need to preserve audience-bound validation. [Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization]
- The MCP Python SDK stable README still documents server auth through `TokenVerifier` plus `AuthSettings`; Story 3.2 should keep all OIDC work inside the verifier surface and not invent a transport bypass. [Source: https://github.com/modelcontextprotocol/python-sdk]

### Project Structure Notes

- This story belongs in the optional-auth track under `_bmad-output/implementation-artifacts/optional-auth/`.
- Sprint updates must target [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml), not the main Phase 2 tracker.
- No UX design document exists for this feature; operator experience here is expressed through config behavior and future startup diagnostics, not a UI artifact.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-32-Support-JWKS-Refresh-HTTPS-and-Custom-CA-Trust]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/research/technical-oidc-fastmcp-authelia-research-2026-04-22.md]
- [Source: _bmad-output/planning-artifacts/oidc-authelia-integration-assessment-2026-04-22.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md]
- [Source: src/soniq_mcp/auth/verifiers.py]
- [Source: src/soniq_mcp/auth/__init__.py]
- [Source: src/soniq_mcp/config/models.py]
- [Source: src/soniq_mcp/config/validation.py]
- [Source: tests/unit/auth/test_verifiers.py]
- [Source: tests/unit/test_server.py]
- [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- [Source: https://github.com/modelcontextprotocol/python-sdk]
- [Source: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest -q tests/unit/auth/test_verifiers.py` (red phase: 2 failed, then green: 24 passed)
- `uv run pytest -q tests/unit/test_server.py`
- `uv run ruff check --fix tests/unit/auth/test_verifiers.py`
- `uv run ruff check src/soniq_mcp/auth tests/unit/auth/test_verifiers.py tests/unit/test_server.py`
- `make lint`
- `make test`

### Completion Notes List

- Implemented HTTPS-only JWKS client construction in `OIDCVerifier`, so non-HTTPS or malformed `oidc_jwks_uri` values fail closed by leaving the verifier unable to authenticate tokens instead of constructing an insecure client.
- Added optional CA-bundle support with one verifier-scoped `ssl.create_default_context(cafile=...)` call passed into `PyJWKClient`, while leaving the default `ssl_context=None` path intact so `SSL_CERT_FILE` keeps working through standard Python TLS behavior.
- Preserved the single verifier-owned `PyJWKClient` instance and the existing `PyJWT` refresh semantics instead of layering a second manual retry path on top of unknown-`kid` handling.
- Added focused OIDC verifier coverage for plaintext-HTTP rejection, CA-bundle SSL-context wiring, default TLS passthrough, repeated verification client reuse, rotated-key success, and final JWKS lookup failure.
- Verified the story against focused auth tests, server no-op boundary tests, repo lint, and the full regression suite.
- Resolved code review patch findings by making CA-bundle SSL-context creation fail closed and by replacing the synthetic JWKS refresh tests with coverage that drives `PyJWKClient.get_signing_key()` through its real refresh/retry branch.

### File List

- [_bmad-output/implementation-artifacts/optional-auth/3-2-support-jwks-refresh-https-and-custom-ca-trust.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth/3-2-support-jwks-refresh-https-and-custom-ca-trust.md)
- [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml)
- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)

## Change Log

- 2026-05-05: Implemented Story 3.2 verifier hardening for HTTPS-only JWKS, optional CA-bundle TLS context, and focused JWKS trust/refresh unit coverage; validated with full lint and regression runs.
- 2026-05-05: Addressed code review findings for Story 3.2 and revalidated with full lint and regression runs.
