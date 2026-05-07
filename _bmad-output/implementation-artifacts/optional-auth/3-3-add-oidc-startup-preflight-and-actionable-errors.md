# Story 3.3: Add OIDC Startup Preflight and Actionable Errors

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a homelab operator,
I want OIDC misconfiguration to fail at startup with actionable diagnostics,
so that TLS, issuer, and JWKS problems are fixed before clients see confusing 401s.

## Acceptance Criteria

1. Given `auth_mode=oidc` and a reachable JWKS endpoint, when preflight runs, then startup validation succeeds.
2. Given `auth_mode=oidc` and the JWKS endpoint is unreachable, when preflight runs, then startup fails before accepting requests.
3. Given JWKS startup validation fails due to TLS trust, when the error is reported, then it includes the JWKS URL, the network or TLS error category, likely cause, and authentication docs reference.
4. Given `oidc_jwks_uri` is not configured, when preflight runs, then it derives or discovers the JWKS endpoint according to the documented OIDC configuration behavior.
5. Given `oidc_resource_url` is not configured, when OIDC auth settings are built, then the implementation verifies whether `resource_server_url=None` works with FastMCP `AuthSettings` and Authelia audience validation.
6. Given the verification shows `resource_server_url` must be explicit, when preflight validates OIDC config, then it requires or derives a stable resource URL with a clear error or default.
7. Given OIDC preflight logs configuration context, when logs are emitted, then they never include presented JWTs or static auth secrets.

## Tasks / Subtasks

- [x] Extend startup preflight with OIDC discovery, connectivity validation, and safe diagnostics (AC: 1, 2, 3, 4, 7)
  - [x] Update [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) so `run_preflight()` performs blocking OIDC validation only for HTTP transport with `auth_mode=oidc`.
  - [x] Keep stdio non-blocking: stdio with OIDC config must not fail startup, and any operator notice must be warning-only rather than a preflight error.
  - [x] If `config.oidc_jwks_uri` is already set, validate that URL as the preflight target rather than rediscovering it.
  - [x] If `config.oidc_jwks_uri` is missing, derive the OpenID Provider configuration URL from `config.oidc_issuer` using the OpenID Connect Discovery well-known path rules, fetch the discovery document, and extract `jwks_uri`.
  - [x] Use a temporary preflight-only JWKS client or equivalent direct fetch path to prove the JWKS endpoint is reachable; do not reuse or mutate the runtime verifier instance from [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py).
  - [x] Apply the same trust model as Story 3.2: default Python trust should continue to honor `SSL_CERT_FILE`, and `oidc_ca_bundle` should only add a verifier- or preflight-scoped `ssl.SSLContext` override.
  - [x] Fail with actionable `ConfigValidationError.messages` entries that name the JWKS URL, classify the failure (`tls`, `network`, `discovery`, or `configuration`), give the likely operator fix, and include `docs/setup/authentication.md#ca-certificates` or the most specific authentication/troubleshooting anchor available at implementation time.
  - [x] Keep logs and exceptions secret-safe: never include bearer tokens, `auth_token`, raw `SecretStr` output, or stack traces in non-debug preflight messages.

- [x] Wire HTTP OIDC into FastMCP auth settings without regressing existing auth paths (AC: 1, 5, 6, 7)
  - [x] Update [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) so HTTP `auth_mode=oidc` now uses the existing auth-construction seam instead of being silently ignored.
  - [x] For OIDC auth settings, use `issuer_url=config.oidc_issuer`; preserve the current static-auth issuer derivation from `http_host` and `http_port`.
  - [x] Verify the current MCP SDK behavior for `AuthSettings(resource_server_url=None)` against the installed stable SDK and the repo's OIDC audience expectations before changing defaults.
  - [x] If `resource_server_url=None` is acceptable, preserve that behavior when `oidc_resource_url` is unset and document the decision in the completion notes rather than inventing a derived value.
  - [x] If `resource_server_url` must be explicit for correct runtime behavior, make preflight require or derive a stable value with a clear operator-facing error message and keep the server builder consistent with that rule.
  - [x] Preserve `auth_mode=none`, static HTTP auth, and all stdio no-op behavior.

- [x] Add focused unit and integration coverage for startup OIDC validation and server wiring (AC: 1, 2, 3, 4, 5, 6, 7)
  - [x] Extend [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py) with network-free tests for:
    - [x] explicit JWKS URI success
    - [x] discovery success when `oidc_jwks_uri` is absent
    - [x] unreachable JWKS failure
    - [x] TLS trust failure with actionable message content
    - [x] stdio OIDC remains non-blocking
    - [x] no secret leakage in user-facing messages
  - [x] Extend [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) so HTTP OIDC is now wired, static auth still works, stdio OIDC is still ignored, and the `resource_server_url` decision is locked down by tests.
  - [x] Extend [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py) with startup-blocking coverage proving OIDC preflight prevents normal startup on unreachable or untrusted JWKS endpoints.
  - [x] Keep automated tests provider-free: patch discovery fetches and JWKS connectivity instead of adding a live Authelia dependency.

- [x] Preserve story boundaries established by 3.1 and 3.2
  - [x] Do not rework JWT claim validation, refresh semantics, or verifier claim mapping in [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py); Story 3.2 already owns that runtime verifier behavior.
  - [x] Do not add Docker, Helm, or auth-documentation deliverables here; Story 4.x owns operator documentation and deployment examples.
  - [x] Do not add transport-specific auth logic outside [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) and [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py).

### Review Findings

- [x] [Review][Patch] Discovered JWKS URI is not propagated into runtime auth config, so OIDC discovery can pass preflight while the runtime verifier still has no JWKS client and rejects every token. [src/soniq_mcp/config/validation.py:89]
- [x] [Review][Patch] HTTP OIDC wiring now allows startup with issuer-only config even though the runtime verifier fails closed when `oidc_audience` or JWKS client data is missing. [src/soniq_mcp/server.py:75]
- [x] [Review][Patch] Discovery URL derivation does not follow OpenID Connect well-known path rules for issuers with path components. [src/soniq_mcp/config/validation.py:136]
- [x] [Review][Patch] JWKS preflight treats any successful fetch as valid, so malformed or non-HTTPS JWKS targets can pass startup even though runtime verification will reject them. [src/soniq_mcp/config/validation.py:119]
- [x] [Review][Patch] OIDC preflight diagnostics point to `docs/setup/authentication.md#ca-certificates`, but that file does not exist in this repo, so the operator guidance link is broken. [src/soniq_mcp/config/validation.py:183]
- [x] [Review][Patch] Invalid `oidc_ca_bundle` errors label the local certificate file path as `URL`, which misidentifies the failing target and makes the message less actionable. [src/soniq_mcp/config/validation.py:80]

### Re-review Findings

- [x] [Review][Patch] `create_server(config=...)` still bypasses OIDC discovery, so injected HTTP OIDC configs with issuer+audience but no `oidc_jwks_uri` start a server whose runtime verifier has no JWKS client and rejects every token. [src/soniq_mcp/server.py:67]
- [x] [Review][Patch] Malformed `oidc_issuer` values still surface as discovery/JSON failures instead of configuration errors, producing misleading operator diagnostics such as `URL: /.well-known/openid-configurationnot-a-url`. [src/soniq_mcp/config/validation.py:70]
- [x] [Review][Patch] Invalid `oidc_ca_bundle` still reports the discovery URL even when preflight is validating an explicit `oidc_jwks_uri`, so the error names the wrong endpoint. [src/soniq_mcp/config/validation.py:75]
- [x] [Review][Patch] `oidc_resource_url` is still only validated in server wiring, which means bad values can bypass preflight and fail later as runtime URL-validation errors instead of `ConfigValidationError` startup diagnostics. [src/soniq_mcp/server.py:45]
- [x] [Review][Patch] The `resource_server_url=None` path is preserved but still not verified against actual FastMCP/Authelia runtime behavior; the tests only assert that the field stays `None`, not that the OIDC flow still works with that setting. [tests/unit/test_server.py:199]

## Dev Notes

### Story Intent

Story 3.1 created the OIDC verifier primitive. Story 3.2 hardened that verifier for HTTPS JWKS, cache refresh, and custom CA trust. Story 3.3 is the startup and server-path story:

- fail fast before the server accepts requests
- surface operator-actionable OIDC diagnostics
- stop silently ignoring HTTP OIDC auth
- resolve the `resource_server_url` decision with evidence instead of assumptions

This is not another verifier-behavior story. The verifier already exists and should remain the runtime primitive.

### Story Foundation

Epic 3 maps this story to the startup-facing requirements that were intentionally deferred earlier:

- FR14: startup JWKS connectivity validation
- FR15: actionable startup diagnostics for OIDC misconfiguration
- FR16: derive or discover JWKS details when direct config is incomplete
- NFR11: CA trust must follow standard Python mechanisms
- NFR12: fail closed without leaking secrets

Story 3.3 also closes the temporary runtime gap left by the current server tests, which still assert that HTTP OIDC auth is ignored until implemented.

### What Already Exists

Current repo state relevant to Story 3.3:

- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) currently blocks only one auth case: HTTP `auth_mode=static` without `auth_token`. There is no OIDC startup connectivity or discovery logic yet.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) already has `_build_auth_kwargs(config)`, but `create_server()` only calls it for HTTP static auth. HTTP OIDC is still intentionally ignored.
- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) already contains the runtime `OIDCVerifier`, HTTPS-only JWKS enforcement, optional `oidc_ca_bundle` support, and fail-closed `None` behavior.
- [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py) already prints each `ConfigValidationError.messages` entry line-by-line to stderr and then points operators to troubleshooting docs. Preflight messages should stay readable in that rendering model.
- [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py) and [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py) already lock down the static-auth blocking pattern and safe error-message expectations.
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) currently asserts that stdio OIDC is ignored and HTTP OIDC is ignored until implementation arrives. Story 3.3 should intentionally flip only the HTTP OIDC expectation.

### Files To Read Before Implementing

Read these files completely before editing:

- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py)
- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)
- [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py)

### Current-State Guardrails For Update Files

#### `src/soniq_mcp/config/validation.py`

Current state:

- `run_preflight()` wraps config loading and raises `ConfigValidationError(messages)`
- `_validate_auth_preflight()` returns a list of user-facing blocking messages
- stdio returns early today, with no warning or OIDC-specific handling

What this story changes:

- add OIDC startup validation to the existing preflight path
- perform discovery only when `oidc_jwks_uri` is absent
- classify discovery / TLS / network / config failures into actionable messages

What must be preserved:

- startup validation ownership remains in `run_preflight()`
- message safety: no secrets, no raw tracebacks, no noisy exception dumps
- stdio remains non-blocking

Implementation note:

- Because `__main__.py` prints each message as a separate stderr line, prefer a small list of concise messages over one newline-packed blob. Example shape:
  - headline: `OIDC JWKS preflight failed`
  - detail: `URL: https://...`
  - detail: `Category: tls`
  - detail: `Likely cause: CA certificate not trusted`
  - detail: `Docs: docs/setup/authentication.md#ca-certificates`

#### `src/soniq_mcp/server.py`

Current state:

- `_build_auth_kwargs(config)` already centralizes FastMCP auth construction
- static auth sets `issuer_url` from this server's host/port
- OIDC auth is not wired into `create_server()` yet

What this story changes:

- wire HTTP OIDC through the same auth-construction seam
- set `AuthSettings.issuer_url` correctly for OIDC
- lock down the `resource_server_url` decision in code and tests

What must be preserved:

- `auth_mode=none` stays a strict no-op
- static HTTP auth stays unchanged
- stdio still does not attach FastMCP auth

#### `tests/unit/test_server.py`

Current state:

- has explicit no-op coverage for disabled auth, stdio auth, and ignored HTTP OIDC

What this story changes:

- replace the ignored-HTTP-OIDC expectation with positive wiring assertions
- keep stdio OIDC ignored
- add tests that pin the `resource_server_url` decision

What must be preserved:

- disabled-auth behavior
- static-auth wiring
- IPv6 issuer formatting for the static path

### Previous Story Intelligence

From Story 3.2:

- Startup OIDC connectivity checks and actionable diagnostics were explicitly deferred here. Do not keep punting them. [Source: _bmad-output/implementation-artifacts/optional-auth/3-2-support-jwks-refresh-https-and-custom-ca-trust.md#Tasks--Subtasks]
- The runtime verifier already owns HTTPS-only JWKS handling, optional custom CA support, and fail-closed behavior. Reuse that contract; do not re-implement JWT verification in preflight. [Source: _bmad-output/implementation-artifacts/optional-auth/3-2-support-jwks-refresh-https-and-custom-ca-trust.md#Story-Foundation]

From Story 3.1:

- OIDC server wiring and startup validation were intentionally left untouched in 3.1. Story 3.3 is the planned place to change both. [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md#Tasks--Subtasks]
- The verifier shape is already established: one `OIDCVerifier`, one `PyJWKClient`, fail-closed `verify_token()`. Do not replace that with a transport bypass or custom auth stack. [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md#Story-Intent]

From the Epic 2 retrospective:

- Disabled-auth and stdio no-op behavior remain first-class invariants whenever auth grows. This story must add HTTP OIDC without weakening those protections. [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#Lessons-Learned]
- Validation ownership clarity matters. Keep startup validation in `config/validation.py`; keep runtime token validation in the verifier. [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#Previous-Retro-Follow-Through]

### Git Intelligence Summary

Recent auth work sequence:

- `a97cf21` completed static auth HTTP wiring
- `6fd6256` added static auth regression coverage
- `52b394a` implemented the base OIDC verifier for Story 3.1
- `70e6802` completed Story 3.2 verifier hardening

Pattern to preserve:

- story-scoped increments
- no-op path regression protection
- review-driven hardening before moving to the next auth layer

### Architecture Guardrails

- Auth remains a server/transport concern only. No auth logic may enter `tools/`, `services/`, `adapters/`, or transport runners. [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- Preflight checks belong in `config/validation.py` `run_preflight()`, not in verifier constructors and not in `server.py`. [Source: _bmad-output/planning-artifacts/architecture.md#Important-Decisions-Shape-Architecture]
- The OIDC connectivity check should construct a temporary `PyJWKClient` in preflight solely for connectivity validation; it must not share runtime verifier state. [Source: _bmad-output/planning-artifacts/architecture.md#Important-Decisions-Shape-Architecture]
- For OIDC auth wiring, `AuthSettings.issuer_url` should be `config.oidc_issuer`, while static auth continues to derive issuer URL from the server host/port. [Source: _bmad-output/planning-artifacts/architecture.md#Communication-Patterns]
- `AuthSettings.resource_server_url` is the unresolved design seam: the architecture notes explicitly call out that Story 3.3 must verify whether `None` is acceptable or whether the field must be required or derived. Do not guess. [Source: _bmad-output/planning-artifacts/architecture.md#Important-Decisions-Shape-Architecture]
- HTTPS-only JWKS and fail-closed verification are already part of the runtime verifier contract and must remain intact. [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]

### Technical Requirements

- Discovery behavior when `oidc_jwks_uri` is absent must follow the current OpenID Connect Discovery 1.0 rules: fetch `/.well-known/openid-configuration` relative to the issuer, removing a trailing slash before appending when the issuer includes a path component. [Source: https://openid.net/specs/openid-connect-discovery-1_0.html]
- Keep the implementation dependency-light. Use standard-library fetch/parsing for discovery or a narrowly justified existing dependency; do not add `requests`, `httpx`, or `authlib` just for preflight metadata retrieval. The project already chose `PyJWT` as the only JWT/JWKS dependency. [Source: _bmad-output/planning-artifacts/architecture.md#Technology-Choices]
- The installed `PyJWT` implementation still supports `PyJWKClient(..., ssl_context=...)`, in-memory JWK-set caching by default, and a single refresh-and-retry on unknown `kid`. Preflight should use that client only for connectivity proof, not as a second runtime cache. [Source: local package inspection via `uv run python` on 2026-05-05]
- The current stable MCP Python SDK still models auth via `TokenVerifier` plus `AuthSettings`, and the installed `AuthSettings` type accepts `resource_server_url: AnyHttpUrl | None`. Story 3.3 should verify runtime implications, not assume the field is always required or always ignorable. [Source: https://github.com/modelcontextprotocol/python-sdk] [Source: local package inspection via `uv run python` on 2026-05-05]
- `__main__.py` already routes preflight failures through `ConfigValidationError.messages`; prefer composing high-signal messages there instead of adding a new CLI-specific OIDC error surface. [Source: /Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py]

### Architecture Compliance

- Keep OIDC startup validation in `config/validation.py`.
- Keep FastMCP auth wiring in `server.py`.
- Do not push OIDC startup fetch logic into `auth/verifiers.py`.
- Do not create a standalone `verify_jwks_connectivity()` module detached from `run_preflight()` unless the extracted helper still remains internal to `config/validation.py` and keeps ownership obvious.

### Library / Framework Requirements

- `pyjwt[crypto]>=2.12.1` is already the repo's production JWT/JWKS dependency and remains the only production JWKS client. [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- The current installed `AuthSettings` model signature is:
  - `issuer_url: AnyHttpUrl`
  - `resource_server_url: AnyHttpUrl | None`
  This means model construction with `None` is allowed today, but Story 3.3 still needs to decide whether that is operationally correct for this project. [Source: local package inspection via `uv run python` on 2026-05-05]
- The current stable MCP SDK README continues to show `AuthSettings(resource_server_url=AnyHttpUrl(...))` in examples for protected resource metadata. Treat that as a design signal in favor of an explicit URL where the product semantics need audience binding. [Source: https://github.com/modelcontextprotocol/python-sdk]

### File Structure Requirements

Expected touched files for Story 3.3:

- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)
- [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py)

Files this story should not modify unless a narrowly justified helper extraction makes it unavoidable:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)
- `docs/setup/authentication.md`
- [tests/smoke/streamable_http/test_streamable_http_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/streamable_http/test_streamable_http_smoke.py)

### Testing Requirements

- Keep all tests network-free and provider-free.
- Patch discovery document fetches and JWKS connectivity rather than standing up a live OIDC provider.
- Add at least one unit test that proves missing `oidc_jwks_uri` causes discovery from `oidc_issuer`.
- Add at least one unit test that proves TLS trust failures are surfaced with URL, category, likely cause, and docs reference.
- Add at least one unit test that proves HTTP OIDC now attaches FastMCP auth and a token verifier.
- Add at least one unit or integration test that locks down the chosen `resource_server_url` behavior when `oidc_resource_url` is absent.
- Preserve existing disabled-auth, static-auth, and stdio behavior tests.

### Latest Technical Information

- OpenID Connect Discovery 1.0 incorporating errata set 2 still specifies that providers publish configuration at `/.well-known/openid-configuration`, with special path handling when the issuer already contains a path component. That is the correct source of truth for deriving `jwks_uri` when only `oidc_issuer` is configured. [Source: https://openid.net/specs/openid-connect-discovery-1_0.html]
- The MCP Python SDK stable README still documents server auth through a `TokenVerifier` plus `AuthSettings`, and its example continues to show an explicit `resource_server_url`. [Source: https://github.com/modelcontextprotocol/python-sdk]
- Local inspection on 2026-05-05 confirms the installed `AuthSettings` model still accepts `resource_server_url=None`, so Story 3.3 should treat this as a behavioral decision to validate, not a schema error to assume. [Source: local package inspection via `uv run python` on 2026-05-05]
- Local inspection on 2026-05-05 confirms the installed `PyJWT` `PyJWKClient` still supports `ssl_context`, JWK-set caching, and a single refresh retry on unknown `kid`. Story 3.3 should use it only for startup connectivity proof and leave runtime caching in the verifier. [Source: local package inspection via `uv run python` on 2026-05-05]
- The optional-auth PRD still specifies the operator-facing TLS failure shape as: unreachable JWKS, URL shown, TLS error identified, likely CA-trust cause, and a docs reference. Story 3.3 should make preflight messages materially match that outcome even though the dedicated auth doc file lands later. [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#User-Journey-4-Existing-OIDC-Deployment-Needs-Custom-CA]

### Project Structure Notes

- This story belongs in the optional-auth track, not the main Phase 2 tracker.
- The docs reference in the preflight message may point at `docs/setup/authentication.md#ca-certificates` before Story 4.1 lands that file. That is acceptable if the string is part of the planned contract, but do not expand this story into writing the full auth guide.

## File List

- `src/soniq_mcp/config/validation.py` — modified
- `src/soniq_mcp/server.py` — modified
- `tests/unit/config/test_validation.py` — modified
- `tests/unit/test_server.py` — modified
- `tests/integration/config/test_preflight_startup.py` — modified
- `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml` — modified

## Dev Agent Record

### Completion Notes

**OIDC preflight validation** (`validation.py`):
- Added `_validate_oidc_preflight()` which runs only for HTTP transport with `auth_mode=oidc`. Stdio is unconditionally non-blocking.
- Discovery path: when `oidc_jwks_uri` is absent, derives `/.well-known/openid-configuration` from `oidc_issuer` (OIDC Discovery 1.0 rules), fetches the document, and extracts `jwks_uri`.
- Direct path: when `oidc_jwks_uri` is set, skips discovery and probes that URL directly.
- Uses `urllib.request` (stdlib) for all preflight fetches — no new runtime dependencies.
- SSL context: `None` (Python default, honors `SSL_CERT_FILE`) unless `oidc_ca_bundle` is set, in which case a scoped `ssl.create_default_context(cafile=...)` is created for preflight only.
- Error messages follow the multi-line format that `__main__.py` renders line-by-line: headline, URL, Category, Likely cause, Docs.
- Failure categories: `tls` (SSLError or URLError wrapping SSLError), `network` (URLError), `discovery` (bad JSON or missing `jwks_uri`), `configuration` (bad CA bundle path).
- No secrets, SecretStr output, or tracebacks ever appear in user-facing messages.

**OIDC server wiring** (`server.py`):
- `_build_auth_kwargs()` now uses `config.oidc_issuer` as `issuer_url` for OIDC auth; static auth continues to derive issuer from `http_host:http_port`.
- `create_server()` now calls `_build_auth_kwargs()` for both `AuthMode.STATIC` and `AuthMode.OIDC` when transport is HTTP.
- `auth_mode=none` and all stdio paths remain strict no-ops.

**`resource_server_url` decision**: `AuthSettings` accepts `resource_server_url: AnyHttpUrl | None`. When `oidc_resource_url` is not configured, `resource_server_url=None` is passed and preserved. The static auth path already used this same behavior and all existing tests passed with it. The MCP SDK does not hard-require the field on the server side. This decision is locked down by `test_http_oidc_resource_server_url_is_none_when_not_configured`.

**Tests added**:
- `TestOIDCPreflightValidation` in `tests/unit/config/test_validation.py` — 7 network-free tests covering all AC branches.
- `TestOIDCAuthWiring` in `tests/unit/test_server.py` — 7 tests covering OIDC wiring, issuer derivation, resource_server_url decision, and regression guards.
- `TestOIDCPreflightBlocking` in `tests/integration/config/test_preflight_startup.py` — 4 integration tests covering startup-blocking behavior.

**Full suite**: 1221 passed, 3 skipped (pre-existing skips unrelated to this story).

## Change Log

- 2026-05-06: Implemented OIDC startup preflight with discovery, connectivity check, and actionable error messages in `validation.py`; wired HTTP OIDC auth through `_build_auth_kwargs()` in `server.py`; added 18 new tests across unit and integration suites.
