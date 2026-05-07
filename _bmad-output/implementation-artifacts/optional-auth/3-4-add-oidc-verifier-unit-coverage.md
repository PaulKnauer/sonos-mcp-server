# Story 3.4: Add OIDC Verifier Unit Coverage

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want OIDC validation covered without external identity-provider dependencies,
so that provider-agnostic JWT behavior remains reliable in CI.

## Acceptance Criteria

1. Given OIDC verifier unit tests run, when RSA key pairs and JWTs are generated in-process, then tests do not require Authelia or network access.
2. Given a valid RS256 JWT test case, when `verify_token(token)` runs, then it returns an `AccessToken`.
3. Given expired, tampered, wrong-issuer, wrong-audience, and missing-claim token cases, when tests run, then each case returns `None`.
4. Given key rotation behavior is tested, when the initial signing key is unavailable, then JWKS refresh is attempted once.
5. Given custom CA bundle behavior is tested, when `oidc_ca_bundle` is configured, then SSL context construction is verified without making a live network call.
6. Given `TokenVerifier` compatibility is tested, when the verifier class is inspected or type-checked, then its signature matches FastMCP’s expected `verify_token(token: str) -> AccessToken | None` contract.

## Tasks / Subtasks

- [x] Expand OIDC verifier tests to use in-process RSA/JWT fixtures instead of decode-path-only doubles (AC: 1, 2, 3, 4)
  - [x] Extend [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) with helper fixtures/utilities that generate RSA key pairs in-process using the already-installed `cryptography` dependency.
  - [x] Generate RS256 JWTs in-process with explicit `kid` headers so tests exercise the real `PyJWKClient.get_signing_key_from_jwt()` lookup path rather than only monkeypatched `jwt.decode()` success/failure stubs.
  - [x] Supply JWKS payloads without network access by monkeypatching the JWKS fetch boundary (`PyJWKClient.fetch_data()` or equivalent narrow seam) instead of introducing a live HTTP server or external identity provider.
  - [x] Keep the runtime production path intact: tests should drive the real `OIDCVerifier.verify_token()` implementation and only fake the external JWKS transport boundary.

- [x] Add a broader invalid-token matrix around the current verifier contract (AC: 2, 3, 6)
  - [x] Add a valid-token test that proves a real RS256 JWT signed by the generated private key returns an `AccessToken` with the expected `client_id`, `scopes`, `expires_at`, and optional `resource` mapping.
  - [x] Add focused negative tests for expired signature, tampered signature, wrong issuer, wrong audience, and missing required identity/claim-shape cases that should return `None` with no exception escape.
  - [x] Keep the fail-closed assertions explicit: each invalid-token case must assert `None`, not just “no exception”.
  - [x] Preserve the fixed-algorithm contract by continuing to validate with `algorithms=[“RS256”]`; do not broaden accepted algorithms in tests or production code.

- [x] Exercise JWKS refresh and CA-bundle behavior through more realistic verifier-level coverage (AC: 1, 4, 5)
  - [x] Add a key-rotation test where the first JWKS set does not contain the token’s `kid`, the refresh JWKS set does, and verification succeeds after the built-in single refresh path.
  - [x] Add a final-refresh-failure test where the rotated key never appears and verification still returns `None`.
  - [x] Keep the custom-CA test network-free: verify that `ssl.create_default_context(cafile=...)` is called once and that the resulting `ssl_context` is passed to `PyJWKClient` construction.
  - [x] Preserve the default trust-path test proving `ssl_context=None` when `oidc_ca_bundle` is unset, so `SSL_CERT_FILE` remains the standard Python TLS mechanism.

- [x] Lock down FastMCP `TokenVerifier` compatibility without widening story scope (AC: 6)
  - [x] Add a focused compatibility assertion in [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) that checks `OIDCVerifier.verify_token` retains the `token: str` parameter and `AccessToken | None` return contract expected by `mcp.server.auth.provider.TokenVerifier`.
  - [x] If a type-check-oriented assertion is needed, keep it local to the test file and compatible with the repo’s current `mypy` settings; do not introduce a new mypy plugin, runtime protocol wrapper, or additional test module just for this check.

- [x] Preserve the story boundaries established by Stories 3.1, 3.2, and 3.3
  - [x] Do not change [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py), [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py), or deployment/docs artifacts unless a verifier-test bug forces a narrowly justified production fix.
  - [x] Do not add Authelia, a live JWKS server, Docker/Helm auth setup, or smoke/integration coverage here; Story 4.x owns operator-facing paths and Story 3.4 stays unit-test scoped.
  - [x] Do not rework startup preflight, resource-server URL behavior, or transport wiring in this story; those were settled in Story 3.3 and should only be touched if new verifier coverage proves a real defect.

## Dev Notes

### Story Intent

Story 3.4 is the verifier-confidence story for Epic 3. The production OIDC path now exists, supports HTTPS-only JWKS, custom CA trust, startup preflight, and HTTP wiring. What is still thin is the unit-test matrix around the verifier itself: much of the current suite relies on monkeypatched `jwt.decode()` and lightweight `PyJWKClient` doubles instead of exercising real RS256 tokens and JWKS content.

This story closes that gap without introducing external-provider dependencies. It is a test-depth story, not another transport or preflight story.

### Story Foundation

Epic 3 already delivered the OIDC runtime in three slices:

- Story 3.1 created the `OIDCVerifier` primitive and factory branch.
- Story 3.2 hardened JWKS behavior for HTTPS, custom CA trust, and built-in refresh/retry semantics.
- Story 3.3 added startup validation and HTTP wiring.

Story 3.4’s job is to prove those verifier behaviors with stronger provider-free unit coverage:

- real RS256 signing and verification in-process
- real `kid`-based JWKS lookup behavior
- clear fail-closed coverage for invalid-token cases
- explicit compatibility with FastMCP’s `TokenVerifier` contract

### What Already Exists

Current repo state relevant to Story 3.4:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) already contains the production `OIDCVerifier` with one verifier-owned `PyJWKClient`, HTTPS-only JWKS acceptance, optional CA-bundle `ssl_context`, and fail-closed `verify_token()`.
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py) already exports `build_token_verifier(config)` and routes `AuthMode.OIDC` to `OIDCVerifier`.
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) already covers:
  - static bearer token behavior
  - OIDC verifier construction
  - non-HTTPS JWKS rejection
  - CA-bundle `ssl_context` wiring
  - single-client reuse
  - refresh-on-rotation behavior through the `PyJWKClient` boundary
  - fail-closed behavior for decode and refresh failures
- The current OIDC tests are still heavily mock-driven: they patch `jwt.decode()` and `PyJWKClient` methods directly instead of generating real RSA keypairs, real JWTs, and JWKS payloads. That is the main quality gap this story should close.
- Story 3.3 already verified that `resource_server_url=None` is operationally acceptable in the current FastMCP runtime path and that injected configs now go through the same preflight preparation as env-loaded configs. Story 3.4 should not reopen that surface unless verifier coverage proves a bug.

### Files To Read Before Implementing

Read these files completely before editing:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)
- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)
- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [.venv/lib/python3.12/site-packages/mcp/server/auth/provider.py](/Users/paul/github/sonos-mcp-server/.venv/lib/python3.12/site-packages/mcp/server/auth/provider.py)

Read these if coverage reveals a defect rather than just a missing test:

- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)

### Current-State Guardrails For UPDATE Files

#### `src/soniq_mcp/auth/verifiers.py`

Current state:

- `OIDCVerifier.__init__` stores `_issuer`, `_audience`, `_resource`, and `_jwk_client`.
- `_build_jwk_client()` rejects missing or non-HTTPS JWKS URIs and optionally constructs one `ssl.SSLContext` for `oidc_ca_bundle`.
- `verify_token()` currently:
  - returns `None` for missing token, blank token, missing issuer, missing audience, or absent JWKS client
  - resolves a signing key via `self._jwk_client.get_signing_key_from_jwt(token)`
  - validates with `jwt.decode(..., algorithms=["RS256"], audience=self._audience, issuer=self._issuer)`
  - maps `client_id` or `sub`, scopes from `scp`/`scope`, and `exp` to `AccessToken`
  - fails closed on `PyJWTError` and any unexpected exception

What this story changes:

- ideally nothing in production behavior
- only change production code if stronger verifier tests expose a real runtime bug

What must be preserved:

- one verifier-owned `PyJWKClient`
- fixed algorithm list `["RS256"]`
- fail-closed `None` contract
- no logging or exception leaks of token content

#### `tests/unit/auth/test_verifiers.py`

Current state:

- already contains the full static-auth test set plus the current OIDC constructor/claim/fail-closed coverage
- already has helpers like `config_with_oidc()` and `run_verify(...)`
- already uses monkeypatch-based seams for `PyJWKClient`, `ssl.create_default_context`, and `jwt.decode`

What this story changes:

- raise the OIDC tests from “mocked contract checks” to “real verifier path with in-process crypto and provider-free JWKS data”
- add a clearer invalid-token matrix and signature-compatibility assertions

What must be preserved:

- existing static-auth tests
- secret-unwrapping AST guard
- network-free execution
- no external identity-provider dependency in CI

#### `src/soniq_mcp/auth/__init__.py`

Current state:

- exports `OIDCVerifier`, `StaticBearerVerifier`, and `build_token_verifier`
- factory returns `OIDCVerifier` for `AuthMode.OIDC`

What this story changes:

- probably nothing

What must be preserved:

- public auth-module surface unchanged
- unsupported `AuthMode.NONE` remains explicit

### Previous Story Intelligence

From Story 3.1:

- Story 3.1 intentionally deferred the broader OIDC verifier coverage matrix to Story 3.4. This story should now absorb that remaining test-depth work instead of pushing it again. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md`]
- The verifier shape is already established and should not be reinvented: one `OIDCVerifier`, one `PyJWKClient`, fixed `jwt.decode()` validation, fail closed on invalid tokens. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md#Completion-Notes-List`]

From Story 3.2:

- Story 3.2 already added constructor tests for HTTPS enforcement, CA-bundle SSL-context wiring, and key-rotation refresh behavior. Story 3.4 should build on those tests, not duplicate them with a second disconnected pattern. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-2-support-jwks-refresh-https-and-custom-ca-trust.md#Completion-Notes-List`]
- Epic 2’s retro carried forward that disabled-auth and stdio invariants remain first-class whenever auth expands. Even though Story 3.4 is test-focused, it should avoid “fixes” that leak auth deeper into unrelated layers. [Source: `_bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md#Lessons-Learned`]

From Story 3.3:

- Story 3.3 resolved the startup/server-path gaps and verified `resource_server_url=None` against the current FastMCP runtime path. Story 3.4 should stay verifier-local unless a newly strengthened test proves the verifier itself is wrong. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-3-add-oidc-startup-preflight-and-actionable-errors.md#Re-review-Findings`]
- The current optional-auth OIDC path now passes targeted verification with `138` focused tests. Story 3.4 should preserve that green baseline while deepening only the verifier matrix. [Source: `_bmad-output/implementation-artifacts/optional-auth/3-3-add-oidc-startup-preflight-and-actionable-errors.md#Completion-Notes-List`]

### Git Intelligence Summary

Recent auth work sequence:

- `52b394a` implemented the base OIDC verifier for Story 3.1
- `70e6802` completed Story 3.2 verifier hardening
- `b1fad53` fixed mypy type errors for `AuthSettings` URL arguments

Pattern to preserve:

- story-scoped increments
- verifier logic stays in `src/soniq_mcp/auth/`
- no-op and boundary protections are kept while auth coverage expands
- review-driven hardening is normal for auth work, so write the tests to expose real defects instead of papering over them

### Architecture Guardrails

- Auth remains a server/transport concern only. No auth logic may enter `tools/`, `services/`, `adapters/`, or transport runners. [Source: `_bmad-output/planning-artifacts/architecture.md#Structure-Patterns`]
- `OIDCVerifier` stays in [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py); do not move verifier behavior into `server.py` or `config/`. [Source: `_bmad-output/planning-artifacts/architecture.md#Structure-Patterns`]
- `build_token_verifier(config)` remains the only public auth-module factory surface. [Source: `_bmad-output/planning-artifacts/architecture.md#Naming-Patterns`]
- `verify_token()` must continue to return `None`, not raise, for invalid tokens. [Source: `_bmad-output/planning-artifacts/architecture.md#Format-Patterns`]
- `PyJWKClient` remains verifier-owned and initialized once in `__init__`, not per request. [Source: `_bmad-output/planning-artifacts/architecture.md#Communication-Patterns`]
- Story 3.4 owns the broader unit-coverage matrix. It does not own startup preflight, deployment docs, or smoke/provider integration. [Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Story-34-Add-OIDC-Verifier-Unit-Coverage`]

### Technical Requirements

- Use the existing production dependencies only: `cryptography>=46.0.7` for in-process RSA key generation and `pyjwt[crypto]>=2.12.1` for signing, JWKS parsing, and token validation. [Source: [pyproject.toml](/Users/paul/github/sonos-mcp-server/pyproject.toml)]
- Keep tests provider-free and network-free. Fake the JWKS transport boundary rather than adding a local HTTP service or live Authelia dependency. [Source: `_bmad-output/planning-artifacts/epics-optional-auth.md#Story-34-Add-OIDC-Verifier-Unit-Coverage`]
- Exercise the real `PyJWKClient` lookup path where possible. PyJWT’s docs explicitly show `get_signing_key_from_jwt()` resolving by `kid` and auto-refreshing the JWKS once when the current set does not contain the token’s key. [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- Preserve fixed-algorithm validation. PyJWT’s API docs still warn against deriving accepted algorithms from token headers; keep `algorithms=["RS256"]` hard-coded in production behavior and reflected in tests. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- The FastMCP verifier contract remains `async verify_token(self, token: str) -> AccessToken | None`. Story 3.4 should explicitly validate compatibility with that contract. [Source: https://github.com/modelcontextprotocol/python-sdk] [Source: [.venv/lib/python3.12/site-packages/mcp/server/auth/provider.py](/Users/paul/github/sonos-mcp-server/.venv/lib/python3.12/site-packages/mcp/server/auth/provider.py)]

### Architecture Compliance

- Keep Story 3.4 focused on verifier production code and verifier unit tests.
- Do not widen this story into smoke tests, startup preflight, docs, Docker, Helm, or client-setup guidance.
- Prefer strengthening [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) over creating a second auth test module unless there is a clear reuse benefit.
- If stronger tests reveal a production bug, fix the smallest production surface necessary and document why the fix belongs in Story 3.4 instead of a follow-up.

### Library / Framework Requirements

- PyJWT `2.12.1` usage docs still show in-process RS256 encode/decode and `PyJWKClient` JWKS resolution by `kid`. That matches this story’s requirement to generate real RS256 tokens while staying provider-free. [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- PyJWT API docs continue to expose `PyJWKClient`, `get_signing_key_from_jwt()`, and the `jwt.decode(..., audience=..., issuer=..., algorithms=["RS256"])` surface already used by the repo. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- The official MCP Python SDK still documents auth as `TokenVerifier` plus `AuthSettings`; Story 3.4 should validate compatibility with the verifier protocol, not invent a new abstraction. [Source: https://github.com/modelcontextprotocol/python-sdk]

### File Structure Requirements

Expected touched files for Story 3.4:

- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py)

Potentially touched only if stronger coverage exposes a real bug:

- [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)
- [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)

Files this story should not modify unless a verified defect forces it:

- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)
- docs or deployment artifacts under `docs/setup/`, `helm/`, or container config

### Testing Requirements

- Keep the suite network-free and deterministic.
- Use in-process RSA keys and JWT signing rather than static pasted tokens where practical.
- Include at least one valid-token test that does not monkeypatch `jwt.decode()`.
- Include explicit invalid-token cases for:
  - expired token
  - tampered signature
  - wrong issuer
  - wrong audience
  - missing identity/required claim shape leading to `None`
- Include a rotation-path test that proves the built-in JWKS refresh is attempted once when the first key set lacks the matching `kid`.
- Keep CA-bundle coverage focused on constructor behavior; no live TLS server is needed.
- Preserve the existing static-auth test matrix and the AST-based secret-unwrapping guard.

### Latest Technical Information

- PyJWT’s usage docs continue to demonstrate in-process RS256 token generation and decoding, which is directly relevant to Story 3.4’s “generate RSA keys and JWTs in-process” requirement. [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- The same usage docs state that `PyJWKClient.get_signing_key_from_jwt()` resolves the signing key by `kid`, and that if the `kid` is not found in the current key set, PyJWT refreshes the JWKS and retries once before raising an error. Story 3.4 should verify that actual behavior, not only a hand-built mock approximation. [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- PyJWT’s API docs still warn not to compute accepted algorithms from attacker-controlled token headers. That means tests should continue to assert the repository’s fixed `["RS256"]` validation model rather than broadening the algorithm surface. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- The official MCP Python SDK auth example still shows `TokenVerifier` as the server-side contract. Story 3.4 should validate that `OIDCVerifier.verify_token` stays compatible with that protocol and returns `AccessToken | None`. [Source: https://github.com/modelcontextprotocol/python-sdk]

### Project Structure Notes

- This story belongs in the optional-auth implementation track under [_bmad-output/implementation-artifacts/optional-auth](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth:1).
- Sprint-state updates must target [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml:1), not the main Phase 2 tracker.
- Epic 3 is already `in-progress`, so creating this story should only move `3-4-add-oidc-verifier-unit-coverage` from `backlog` to `ready-for-dev`.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-34-Add-OIDC-Verifier-Unit-Coverage]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Epic-3-OIDC-and-JWKS-Validation-for-Homelab-Operators]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: _bmad-output/implementation-artifacts/optional-auth/3-1-implement-oidc-jwt-verifier-with-cached-jwks.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/3-2-support-jwks-refresh-https-and-custom-ca-trust.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/3-3-add-oidc-startup-preflight-and-actionable-errors.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/epic-2-retro-2026-05-05.md]
- [Source: src/soniq_mcp/auth/__init__.py]
- [Source: src/soniq_mcp/auth/verifiers.py]
- [Source: tests/unit/auth/test_verifiers.py]
- [Source: src/soniq_mcp/config/models.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/provider.py]
- [Source: /Users/paul/github/sonos-mcp-server/pyproject.toml]
- [Source: https://pyjwt.readthedocs.io/en/latest/usage.html]
- [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- [Source: https://github.com/modelcontextprotocol/python-sdk]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `uv run pytest -q tests/unit/auth/test_verifiers.py`
- `uv run ruff check src/soniq_mcp/auth tests/unit/auth/test_verifiers.py`
- `uv run mypy src/soniq_mcp/auth tests/unit/auth/test_verifiers.py`

### Completion Notes List

- Story context analysis completed.
- Added 10 new tests to `tests/unit/auth/test_verifiers.py` raising total from 26 to 36 (all passing).
- Added 4 helper functions: `_make_rsa_keypair`, `_make_jwks`, `_make_rs256_jwt`, `_valid_oidc_claims`.
- Real-path tests patch `PyJWKClient.fetch_data` on the verifier's `_jwk_client` instance, letting the real JWKS key resolution chain (`get_signing_key_from_jwt` → `get_signing_key` → `get_signing_keys` → `get_jwk_set` → `fetch_data`) run against in-process RSA keys.
- The 4 pre-existing mypy errors (lines 430/482 before this story, shifted to 478/530 after import additions) were pre-existing and not introduced by this story.
- No production code changes required; no new runtime defects discovered.
- Full regression suite: 1565 passed, 3 skipped.

### File List

- [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py) (modified)
- [_bmad-output/implementation-artifacts/optional-auth/3-4-add-oidc-verifier-unit-coverage.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth/3-4-add-oidc-verifier-unit-coverage.md) (story file)
- [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml) (sprint status)

## Change Log

- 2026-05-07: Created Story 3.4 with verifier-focused test guidance, Epic 3 carry-forward context, current auth-boundary guardrails, and current PyJWT/MCP SDK references.
- 2026-05-07: Implemented Story 3.4 — added in-process RSA/JWT helper suite and 10 new verifier unit tests covering valid path, invalid-token matrix (expired, tampered, wrong issuer, wrong audience, missing identity claim), JWKS key rotation (success and failure), and FastMCP TokenVerifier contract compatibility.

### Review Findings

- [x] [Review][Patch] Valid-token real-path coverage does not assert `AccessToken.resource`, so the story’s required optional resource mapping is still unverified. [tests/unit/auth/test_verifiers.py:659]
- [x] [Review][Patch] FastMCP contract coverage is too weak to catch signature drift; it only checks that a `token` parameter exists and that the return annotation string contains `AccessToken` and `None`, instead of verifying `token: str` and `AccessToken | None` precisely. [tests/unit/auth/test_verifiers.py:848]
