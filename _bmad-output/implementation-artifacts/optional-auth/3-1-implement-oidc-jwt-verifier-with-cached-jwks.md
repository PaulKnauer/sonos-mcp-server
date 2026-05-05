# Story 3.1: Implement OIDC JWT Verifier with Cached JWKS

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a homelab operator,
I want SoniqMCP to validate OIDC Bearer JWTs using a configured JWKS endpoint,
so that existing identity-provider tokens can protect HTTP MCP access.

## Acceptance Criteria

1. Given `auth_mode=oidc` and valid OIDC configuration, when `build_token_verifier(config)` is called, then it returns an `OIDCVerifier`.
2. Given `OIDCVerifier` is constructed, when it initializes, then it creates a `PyJWKClient` once and keeps it for the verifier lifetime.
3. Given a valid RS256 JWT with expected issuer, audience, and non-expired `exp`, when `verify_token(token)` runs, then it returns a FastMCP-compatible `AccessToken`.
4. Given the JWT includes `client_id`, `sub`, `scope`, `scp`, or `exp` claims, when `AccessToken` is created, then client id, scopes, and expiry are mapped consistently.
5. Given a missing, expired, tampered, wrongly issued, or wrong-audience token, when `verify_token(token)` runs, then it returns `None`.
6. Given JWT validation raises a PyJWT or unexpected exception, when `verify_token(token)` handles it, then it fails closed by returning `None` without leaking token content.

## Tasks / Subtasks

- [x] Add the OIDC verifier production dependency and public auth-module surface (AC: 1, 2, 6)
  - [x] Add direct `PyJWT` production dependency to [pyproject.toml](/Users/paul/github/sonos-mcp-server/pyproject.toml) and refresh [uv.lock](/Users/paul/github/sonos-mcp-server/uv.lock) so the OIDC verifier does not rely on a transitive dependency.
  - [x] Update [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py) so `build_token_verifier(config)` returns `OIDCVerifier` for `AuthMode.OIDC`.
  - [x] Export `OIDCVerifier` alongside the existing public auth module surface if needed by tests or local imports.
  - [x] Preserve current behavior for `AuthMode.STATIC` and keep unsupported-mode behavior explicit for `AuthMode.NONE`.

- [x] Implement `OIDCVerifier` as the runtime JWT verification primitive (AC: 2, 3, 4, 5, 6)
  - [x] Extend [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) with `OIDCVerifier`.
  - [x] Construct one `PyJWKClient` in `OIDCVerifier.__init__` and keep it on the verifier instance for its lifetime.
  - [x] Use the configured JWKS endpoint as the verifier input; do not add live OIDC discovery, custom CA handling, or refresh-retry logic in this story.
  - [x] In `verify_token(token)`, resolve the signing key from the JWT, decode with fixed `algorithms=["RS256"]`, and validate `iss`, `aud`, and `exp`.
  - [x] Map claims into `AccessToken` consistently:
    - [x] `client_id` from `client_id`, falling back to `sub`
    - [x] `scopes` from `scp` or whitespace-split `scope`
    - [x] `expires_at` from `exp`
    - [x] `resource` only if that mapping is already coherent with existing config use
  - [x] Return `None` for invalid or unusable tokens and catch `PyJWTError` plus unexpected exceptions without leaking token contents to logs or exceptions.

- [x] Add focused, implementation-level OIDC verifier coverage without external identity-provider dependencies (AC: 1, 2, 3, 4, 5, 6)
  - [x] Extend [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) for `AuthMode.OIDC`.
  - [x] Add a focused factory test proving `build_token_verifier()` returns `OIDCVerifier` for valid OIDC config.
  - [x] Add a constructor test proving `PyJWKClient` is created once with the expected JWKS URI.
  - [x] Add focused verification tests that mock `PyJWKClient` and `jwt.decode` to prove valid-token success and invalid-token fail-closed behavior.
  - [x] Add coverage for claim-to-`AccessToken` mapping (`client_id` fallback, `scope` vs `scp`, `exp` passthrough).
  - [x] Preserve the existing static-auth and secret-access regression assertions.

- [x] Keep Story 3.1 tightly scoped to verifier construction and verification logic (AC: 1, 2, 3, 4, 5, 6)
  - [x] Do not change [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) to wire OIDC into FastMCP yet; Story 3.3 owns OIDC auth-settings and startup-path behavior.
  - [x] Do not add JWKS refresh-on-rotation, HTTPS-enforcement helpers, or custom CA `ssl_context` handling here; Story 3.2 owns those behaviors.
  - [x] Do not add OIDC startup preflight checks, docs-link diagnostics, or JWKS discovery network calls here; Story 3.3 owns startup validation and actionable errors.
  - [x] Do not introduce Authelia, live JWKS, or network-bound smoke coverage in this story; Story 3.4 owns the fuller OIDC verifier coverage matrix.
  - [x] Do not weaken the disabled-auth and stdio no-op protections established in Epics 1 and 2.

### Review Findings

- [x] [Review][Patch] Fail closed when OIDC verifier config cannot enforce `iss`/`aud` validation [src/soniq_mcp/auth/verifiers.py:53]
- [x] [Review][Patch] Accept string-valued `scp` claims instead of dropping scopes [src/soniq_mcp/auth/verifiers.py:99]

## Dev Notes

### Story Intent

Story 3.1 is the first OIDC runtime story. Its job is to establish the OIDC verifier primitive and the factory branch that selects it.

This story is not the place to finish the entire OIDC feature. In particular:
- no OIDC startup preflight
- no custom CA bundle wiring
- no JWKS refresh-on-rotation retry path
- no server wiring changes for HTTP OIDC requests
- no live-provider or network-bound coverage

The implementation should be narrow and verifiable: one verifier class, one factory branch, focused tests, no boundary leakage.

### What Already Exists

Current repo state relevant to Story 3.1:

- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py) currently supports only `AuthMode.STATIC` and raises `NotImplementedError` for other modes.
- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) currently contains only `StaticBearerVerifier`.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) currently wires auth only when `transport == HTTP` and `auth_mode == STATIC`. HTTP OIDC is still intentionally ignored.
- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) already defines `AuthMode.OIDC` and the config fields `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, and `oidc_resource_url`.
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) currently has no OIDC startup preflight logic beyond existing model-level issuer consistency.
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) already locks down the static-auth verifier contract and the `get_secret_value()` confinement rule.
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) explicitly asserts that stdio OIDC is ignored and that HTTP OIDC is not yet wired into server construction.
- [pyproject.toml](/Users/paul/github/sonos-mcp-server/pyproject.toml) declares `mcp[cli]>=1.26.0` and `cryptography>=46.0.7`, but not direct `PyJWT`, even though [uv.lock](/Users/paul/github/sonos-mcp-server/uv.lock) already contains `pyjwt` 2.12.1.

### Previous Story Intelligence

Relevant learnings from Story 2.3 and the Epic 2 retrospective:

- Story 2.3 reinforced that focused auth convenience targets are useful, but they do not replace broader regression validation. Keep Story 3.1’s tests focused and local; do not weaken the broader suite expectations. [Source: _bmad-output/implementation-artifacts/optional-auth/2-3-add-static-auth-regression-coverage.md#Completion-Notes-List]
- Epic 2 explicitly carried forward that disabled-auth and stdio protections are first-class acceptance concerns whenever auth expands. Story 3.1 must preserve that contract even though it is only adding an OIDC verifier. [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#Lessons-Learned]
- Epic 2 also flagged validation-ownership clarity as still somewhat soft. Do not shift startup validation into the verifier constructor just because OIDC adds more config fields. [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#Previous-Retro-Follow-Through]

### Git Intelligence Summary

Recent auth work sequence:

- `905686c` implemented the static bearer verifier runtime primitive
- `a97cf21` completed static auth server wiring and review fixes
- `6fd6256` added static auth regression coverage and marked Story 2.3 done

The pattern to preserve is:
- story-scoped runtime increments
- review-driven hardening
- explicit regression coverage for no-op paths

### Architecture Guardrails

- Auth remains a server/transport concern only. No auth logic may enter `tools/`, `services/`, `adapters/`, or transport runners. [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- `build_token_verifier(config: SoniqConfig) -> TokenVerifier` is the only public factory surface of the auth module. [Source: _bmad-output/planning-artifacts/architecture.md#Naming-Patterns]
- `OIDCVerifier` belongs in `src/soniq_mcp/auth/verifiers.py`, not in `server.py` or `config/`. [Source: _bmad-output/planning-artifacts/architecture.md#Structure-Patterns]
- `PyJWKClient` should be an instance variable initialized once in `OIDCVerifier.__init__`, not recreated per request. [Source: _bmad-output/planning-artifacts/architecture.md#Communication-Patterns]
- `verify_token()` must return `None`, not raise, for invalid tokens. [Source: _bmad-output/planning-artifacts/architecture.md#Format-Patterns]
- `jwt.decode()` should validate signature, `iss`, `aud`, and `exp` atomically. [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]
- OIDC startup preflight belongs in `run_preflight()` later, not in verifier constructors here. [Source: _bmad-output/planning-artifacts/architecture.md#Important-Decisions-Shape-Architecture]
- Story 3.2 owns HTTPS enforcement, custom CA `ssl_context`, and refresh-on-rotation behavior; Story 3.3 owns startup validation and resource-url behavior; Story 3.4 owns the broader unit-coverage matrix. [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-32-Support-JWKS-Refresh-HTTPS-and-Custom-CA-Trust] [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-33-Add-OIDC-Startup-Preflight-and-Actionable-Errors] [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-34-Add-OIDC-Verifier-Unit-Coverage]

### Current File Analysis

#### [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)

Current state:
- exports `StaticBearerVerifier` and `build_token_verifier`
- returns `StaticBearerVerifier` for `AuthMode.STATIC`
- raises `NotImplementedError` for all non-static modes

What this story changes:
- add the `AuthMode.OIDC` branch
- optionally export `OIDCVerifier` if tests or local imports need it

What must be preserved:
- `AuthMode.STATIC` behavior unchanged
- `AuthMode.NONE` remains unsupported at the factory level
- factory stays narrow and does not absorb startup validation duties

#### [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)

Current state:
- contains `StaticBearerVerifier` only
- handles token comparison with `secrets.compare_digest`
- keeps `get_secret_value()` confined to `StaticBearerVerifier.verify_token()`

What this story changes:
- add `OIDCVerifier` in the same module
- introduce `PyJWKClient` and `jwt.decode` usage
- add claim-to-`AccessToken` mapping logic

What must be preserved:
- existing static verifier behavior and tests
- secret-unwrapping confinement to the static verifier
- fail-closed behavior for any OIDC decode or key-resolution problem

#### [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)

Current state:
- HTTP auth kwargs are built only for `auth_mode == STATIC`
- stdio auth is ignored
- HTTP OIDC is intentionally ignored and tested as such

What this story changes:
- nothing

What must be preserved:
- `test_http_oidc_auth_is_ignored_until_oidc_is_implemented` remains valid after this story
- no OIDC auth wiring enters `create_server()` yet
- no eager OIDC imports are added to the default or stdio path

#### [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)

Current state:
- already contains all OIDC config fields
- already requires `oidc_issuer` when `auth_mode=oidc` on non-stdio transport

What this story changes:
- usually nothing

What must be preserved:
- config ownership remains in `config/`
- no verifier-specific runtime logic gets pushed into the model

#### [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)

Current state:
- handles only static-token preflight blocking

What this story changes:
- nothing

What must be preserved:
- OIDC startup preflight remains a later story concern
- verifier construction is not used as a substitute startup validator

### Technical Requirements

- Add direct `PyJWT` dependency to the production dependency set because OIDC runtime code will import `jwt` directly. Do not rely on a transitive lockfile entry. [Source: _bmad-output/planning-artifacts/architecture.md#Decision-Impact-Analysis] [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- Use `PyJWKClient` from PyJWT for JWKS-backed key resolution. Current docs show the constructor accepts `uri`, `cache_keys`, `cache_jwk_set`, `lifespan`, `timeout`, and `ssl_context`; Story 3.1 should use the simple constructor path and leave `ssl_context` for Story 3.2. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- Use `jwt.decode()` with fixed `algorithms=["RS256"]`; do not derive algorithms from token headers. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- The local MCP SDK contract requires `async verify_token(token: str) -> AccessToken | None`, where `AccessToken` contains `token`, `client_id`, `scopes`, optional `expires_at`, and optional `resource`. [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/provider.py]

### Architecture Compliance

- Keep the OIDC verifier self-contained under `src/soniq_mcp/auth/`.
- Do not add FastMCP auth wiring changes in this story.
- Do not perform live OIDC discovery over `.well-known/openid-configuration` here; Story 3.3 owns missing-`oidc_jwks_uri` discovery/derivation behavior.
- Do not add custom CA handling or refresh-on-rotation retry logic here; those are separate acceptance surfaces with separate stories.

### Library / Framework Requirements

- `mcp[cli]>=1.26.0` is already present and provides the `TokenVerifier` protocol and `AccessToken` model used by the verifier. [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml] [Source: https://github.com/modelcontextprotocol/python-sdk]
- `cryptography>=46.0.7` is already present and can support later in-process RSA test generation without adding a new crypto backend. [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- `PyJWT` is already locked at 2.12.1 in [uv.lock](/Users/paul/github/sonos-mcp-server/uv.lock), and current docs show:
  - `PyJWKClient(..., ssl_context=None)` constructor support
  - `get_signing_key_from_jwt(token)` lookup by `kid`
  - `jwt.decode(..., audience=..., issuer=..., algorithms=[...])` validation API
  [Source: /Users/paul/github/sonos-mcp-server/uv.lock] [Source: https://pyjwt.readthedocs.io/en/stable/api.html] [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]

### File Structure Requirements

Expected touched files for Story 3.1:

- [pyproject.toml](/Users/paul/github/sonos-mcp-server/pyproject.toml)
- [uv.lock](/Users/paul/github/sonos-mcp-server/uv.lock)
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)
- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)

Files this story should not modify unless a narrow test helper forces it:

- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)
- [tests/smoke/streamable_http/test_streamable_http_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/streamable_http/test_streamable_http_smoke.py)

### Testing Requirements

- Keep all OIDC tests network-free and provider-free.
- For Story 3.1, focused mocking is acceptable and preferred: patch `PyJWKClient.get_signing_key_from_jwt()` and `jwt.decode()` to validate the runtime contract without pulling in the full RSA/JWKS matrix yet.
- Preserve the static-auth tests in [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py); do not split them into a separate file unless there is a compelling reuse need.
- Validate at least:
  - factory returns `OIDCVerifier`
  - constructor builds one `PyJWKClient`
  - valid token yields `AccessToken`
  - `client_id` fallback and `scope`/`scp` mapping are correct
  - PyJWT errors return `None`
  - unexpected exceptions also return `None`
- Story 3.4 will expand into real RSA/JWT generation, rotation behavior, and CA-bundle coverage; do not try to swallow that whole here.

### Latest Technical Information

- The official MCP Python SDK’s current stable README shows authentication is supplied by passing a `TokenVerifier` implementation plus `AuthSettings` to `FastMCP`, and the verifier method is `async verify_token(self, token: str) -> AccessToken | None`. Story 3.1 should implement the verifier contract only, not the `FastMCP` wiring change. [Source: https://github.com/modelcontextprotocol/python-sdk]
- PyJWT 2.12.1 documents `PyJWKClient(uri, ..., ssl_context=None)` and demonstrates `get_signing_key_from_jwt(token)` followed by `jwt.decode(token, signing_key, audience=..., algorithms=["RS256"])`. [Source: https://pyjwt.readthedocs.io/en/stable/api.html] [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- Pydantic’s `SecretStr` continues to mask values in repr, `model_dump()`, and `model_dump_json()`. This remains the baseline secret-handling expectation that OIDC work must not accidentally weaken through logging or config debugging. [Source: https://pydantic.dev/docs/validation/2.2/usage/types/secrets/]

### Project Structure Notes

- This story belongs in the optional-auth track, not the main Phase 2 tracker.
- Story file location should stay under `_bmad-output/implementation-artifacts/optional-auth/`.
- Sprint-state updates should target [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml), not `_bmad-output/implementation-artifacts/sprint-status.yaml`.
- Epic 3 is the next active epic and should move from `backlog` to `in-progress` when this story is created.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-31-Implement-OIDC-JWT-Verifier-with-Cached-JWKS]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-32-Support-JWKS-Refresh-HTTPS-and-Custom-CA-Trust]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-33-Add-OIDC-Startup-Preflight-and-Actionable-Errors]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-34-Add-OIDC-Verifier-Unit-Coverage]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: _bmad-output/implementation-artifacts/optional-auth/2-3-add-static-auth-regression-coverage.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md]
- [Source: src/soniq_mcp/auth/__init__.py]
- [Source: src/soniq_mcp/auth/verifiers.py]
- [Source: src/soniq_mcp/server.py]
- [Source: src/soniq_mcp/config/models.py]
- [Source: src/soniq_mcp/config/validation.py]
- [Source: tests/unit/auth/test_verifiers.py]
- [Source: tests/unit/test_server.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/provider.py]
- [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- [Source: /Users/paul/github/sonos-mcp-server/uv.lock]
- [Source: https://github.com/modelcontextprotocol/python-sdk]
- [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- [Source: https://pydantic.dev/docs/validation/2.2/usage/types/secrets/]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest -q tests/unit/auth/test_verifiers.py`
- `uv lock`
- `uv run pytest -q tests/unit/auth/test_verifiers.py tests/unit/test_server.py::TestDisabledAuthNoOp::test_stdio_oidc_auth_is_ignored tests/unit/test_server.py::TestDisabledAuthNoOp::test_http_oidc_auth_is_ignored_until_oidc_is_implemented`
- `uv run ruff check src/soniq_mcp/auth tests/unit/auth/test_verifiers.py`

### Completion Notes List

- Added `pyjwt[crypto]` as a direct production dependency and refreshed `uv.lock` so OIDC verification no longer depends on the MCP SDK's transitive install graph.
- Implemented `OIDCVerifier` with one cached `PyJWKClient`, fixed-algorithm `jwt.decode(..., algorithms=["RS256"])`, claim mapping for `client_id`/`sub`, `scope`/`scp`, and `exp`, and fail-closed handling for both `PyJWTError` and unexpected exceptions.
- Updated `build_token_verifier(config)` to return `OIDCVerifier` for `AuthMode.OIDC` while preserving the existing static branch and explicit unsupported-mode behavior for `AuthMode.NONE`.
- Kept Story 3.1 scoped to verifier construction only: `server.py`, startup preflight, CA-bundle handling, and JWKS refresh behavior were intentionally left untouched.
- Validation passed:
  - `uv run pytest -q tests/unit/auth/test_verifiers.py` -> `16 passed`
  - `uv run pytest -q tests/unit/auth/test_verifiers.py tests/unit/test_server.py::TestDisabledAuthNoOp::test_stdio_oidc_auth_is_ignored tests/unit/test_server.py::TestDisabledAuthNoOp::test_http_oidc_auth_is_ignored_until_oidc_is_implemented` -> `18 passed`
  - `uv run ruff check src/soniq_mcp/auth tests/unit/auth/test_verifiers.py` -> `All checks passed`

### File List

- [pyproject.toml](/Users/paul/github/sonos-mcp-server/pyproject.toml)
- [uv.lock](/Users/paul/github/sonos-mcp-server/uv.lock)
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)
- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)

## Change Log

- 2026-05-05: Created Story 3.1 with comprehensive OIDC verifier context, architecture guardrails, prior-story intelligence, and tracker activation for Epic 3.
- 2026-05-05: Implemented the OIDC JWT verifier, added focused unit coverage, refreshed the direct `PyJWT` dependency, and moved the story to review.
