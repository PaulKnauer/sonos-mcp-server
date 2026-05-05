# Story 2.3: Add Static Auth Regression Coverage

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want automated coverage for static auth behavior,
so that the simplest auth path and disabled-auth compatibility do not regress.

## Acceptance Criteria

1. Given static auth unit tests run, when valid and invalid token cases are exercised, then they pass without network or Authelia dependencies.
2. Given static auth HTTP smoke tests run, when no token is provided, then the test observes HTTP 401.
3. Given static auth HTTP smoke tests run, when the valid token is provided, then the test observes normal MCP behavior.
4. Given disabled-auth regression tests run, when `auth_mode=none`, then no auth verifier is created.
5. Given all static auth tests run in CI, when the tests execute, then they do not require real Sonos hardware or an external identity provider.

## Tasks / Subtasks

- [x] Extend `tests/unit/auth/test_verifiers.py` with missing edge cases (AC: 1)
  - [x] Add test: `build_token_verifier(config)` with `auth_mode=none` raises `NotImplementedError`
  - [x] Add test: `StaticBearerVerifier` when `config.auth_token=None` returns `None` for any presented token
  - [x] Add test: presented token with only whitespace around valid content returns `None` (i.e., `"  shared-secret  "` is rejected by constant-time compare, not stripped)
  - [x] Add test: configured token with only whitespace content always returns `None` regardless of presented value
  - [x] Confirm all 7 existing tests in `tests/unit/auth/test_verifiers.py` continue to pass

- [x] Extend `tests/smoke/streamable_http/test_streamable_http_smoke.py` with additional auth 401 cases (AC: 2)
  - [x] Add test: request with wrong Authorization scheme (e.g., `Authorization: Token test-smoke-bearer-token`) → HTTP 401
  - [x] Confirm existing `test_no_auth_header_returns_401` and `test_wrong_token_returns_401` still pass

- [x] Verify disabled-auth regression baseline (AC: 4)
  - [x] Confirm all 7 `TestDisabledAuthNoOp` tests in `tests/unit/test_server.py` pass without modification
  - [x] Confirm `TestStreamableHTTPSmoke` (unauthenticated server) still connects and calls `ping` successfully as the regression baseline for the no-auth path

- [x] Add optional Makefile convenience targets (AC: 5, recommended non-blocking)
  - [x] Add `make test-auth` to `Makefile` that runs `$(UV) run pytest tests/unit/auth/ tests/unit/test_server.py::TestDisabledAuthNoOp tests/unit/test_server.py::TestStaticAuthWiring`
  - [x] Add `make smoke-auth` to `Makefile` that runs `$(UV) run pytest tests/smoke/streamable_http/test_streamable_http_smoke.py::TestStreamableHTTPAuthSmoke`

- [x] Validate implementation (AC: 1–5)
  - [x] Run `make test` — full suite must pass, no tests skipped or weakened
  - [x] Run `make lint` — no lint failures

## Dev Notes

### Story Intent

Story 2.3 closes the coverage gap that Stories 2.1 and 2.2 deliberately deferred: the wider regression matrix for the static auth path. Stories 2.1 and 2.2 established minimum viability; this story hardens it.

The implementation is test-only. No source files in `src/` require changes unless a gap in the existing implementation is discovered while writing tests. If such a gap is found, surface it in dev notes and fix it narrowly — do not expand scope.

### What Already Exists (Do Not Duplicate)

**`tests/unit/auth/test_verifiers.py`** — established in Story 2.1:
- `test_build_token_verifier_returns_static_verifier_for_static_auth`
- `test_matching_token_returns_access_token`
- `test_missing_empty_whitespace_and_incorrect_tokens_return_none` (covers `None`, `""`, `"   "`, `"wrong-secret"`, `"é"` presented tokens)
- `test_non_ascii_configured_token_returns_none`
- `test_static_verifier_uses_compare_digest`
- `test_secret_unwrapping_is_confined_to_static_verify_token`

**`tests/unit/test_server.py`** — established in Stories 1.3 and 2.2:
- `TestDisabledAuthNoOp` (7 tests covering `auth_mode=none`, stdio ignoring auth, `settings.auth is None`, `_token_verifier is None`, `_build_auth_kwargs` not called)
- `TestStaticAuthWiring` (5 tests covering settings.auth, _token_verifier, issuer_url, IPv6 host, tool registration)
- `TestDiagnosticSafety` (3 tests covering SecretStr masking)

**`tests/smoke/streamable_http/test_streamable_http_smoke.py`** — established in Story 2.2:
- `TestStreamableHTTPAuthSmoke` with 3 tests: no header → 401, wrong token → 401, correct token → MCP handling

### Coverage Gaps This Story Fills

#### 1. `build_token_verifier` error path for unsupported auth mode

`src/soniq_mcp/auth/__init__.py:build_token_verifier()` raises `NotImplementedError` for any `auth_mode` that is not `AuthMode.STATIC`. The server guard in `server.py` prevents this branch from being reachable at runtime for `auth_mode=none`, but the error path is untested. Verify the contract with:

```python
def test_build_token_verifier_raises_for_none_auth_mode() -> None:
    cfg = SoniqConfig(auth_mode=AuthMode.NONE)
    with pytest.raises(NotImplementedError):
        build_token_verifier(cfg)
```

#### 2. `StaticBearerVerifier` with unconfigured token

`src/soniq_mcp/auth/verifiers.py:StaticBearerVerifier.verify_token()` guards `self._auth_token is None` and returns `None`. This branch is only reachable if someone constructs `StaticBearerVerifier(config)` with `config.auth_token=None`, which cannot happen through normal server construction (preflight blocks it), but the code path exists and should be exercised. Use `SoniqConfig(auth_mode=AuthMode.STATIC)` without an `auth_token` to construct the verifier directly, bypassing preflight.

#### 3. Whitespace semantics for presented tokens

The existing test covers `run_verify(verifier, "   ")` (whitespace-only presented token returns `None`). What is NOT tested: a presented token with surrounding whitespace that wraps a valid value — `"  shared-secret  "` — should fail because `secrets.compare_digest` is used on the raw bytes (no strip), making it a different byte sequence from the configured `"shared-secret"`. Add a test to confirm this behavior is preserved.

#### 4. Configured token with whitespace-only content

If `config.auth_token` is set to `SecretStr("   ")` (whitespace-only), the verifier's `configured_token.strip() == ""` guard returns `None`. This is tested by having a `StaticBearerVerifier` whose underlying token is whitespace. Construct verifier directly with `SoniqConfig(auth_mode=AuthMode.STATIC, auth_token=SecretStr("   "))`.

#### 5. Wrong Authorization scheme in smoke tests

Stories 2.2 smoke tests cover no header and wrong token value. A client sending `Authorization: Token abc` (wrong scheme, not `Bearer`) is a common real-world mistake. The FastMCP auth middleware should reject it with 401. Add:

```python
def test_wrong_auth_scheme_returns_401(self, http_server_proc_with_auth) -> None:
    _, test_port = http_server_proc_with_auth
    url = f"http://{_TEST_HOST}:{test_port}{_MCP_PATH}"
    response = httpx.post(
        url,
        json={"jsonrpc": "2.0", "method": "initialize", "id": 1},
        headers={"Authorization": f"Token {_SMOKE_AUTH_TOKEN}"},
    )
    assert response.status_code == 401
```

### Source Files Being Read (Not Modified)

- `src/soniq_mcp/auth/__init__.py` — `build_token_verifier(config)` raises `NotImplementedError` for non-STATIC modes
- `src/soniq_mcp/auth/verifiers.py` — `StaticBearerVerifier.verify_token()` guard sequence: `token is None`, `token.strip() == ""`, `self._auth_token is None`, `configured_token.strip() == ""`, encode-to-ASCII, `secrets.compare_digest`
- `src/soniq_mcp/server.py` — `create_server()` guard: `config.transport == TransportMode.HTTP and config.auth_mode == AuthMode.STATIC` before calling `_build_auth_kwargs(config)`

### Current `test_verifiers.py` Structure to Follow

All new tests must follow the established patterns in `tests/unit/auth/test_verifiers.py`:
- Use the `config_with_static_token()` helper for the standard config
- Use `run_verify(verifier, token)` for calling `verify_token` synchronously
- Import `StaticBearerVerifier` directly when constructing with edge-case configs
- Do not mock filesystem or network in these tests — they are pure in-process tests

### Makefile Targets (Recommended, Non-Blocking)

If adding Makefile targets, follow the existing target style in `Makefile` (lines immediately following the `test:` and `lint:` targets). The targets should use `$(UV)` and be added to the `.PHONY` list at the top of the file. Place them after the `coverage:` target and before `audit:`:

```makefile
test-auth: ensure-uv
	$(UV) run pytest tests/unit/auth/ tests/unit/test_server.py::TestDisabledAuthNoOp tests/unit/test_server.py::TestStaticAuthWiring

smoke-auth: ensure-uv
	$(UV) run pytest tests/smoke/streamable_http/test_streamable_http_smoke.py::TestStreamableHTTPAuthSmoke
```

### Architecture Guardrails

- Auth is a server/transport concern only; no auth code may enter tools, services, adapters, or transport runners. [Source: architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- All tests must run without Authelia, external OIDC infrastructure, or Sonos hardware. [Source: epics-optional-auth.md#Story-23-Add-Static-Auth-Regression-Coverage]
- `get_secret_value()` must remain confined to `StaticBearerVerifier.verify_token()` — the existing AST-scan test in `test_verifiers.py` enforces this and must not be weakened.
- Do not update `sprint-status.yaml` in the main Phase 2 tracker; only `optional-auth-sprint-status.yaml` is relevant to this story.

### Anti-Patterns To Avoid

- Do not re-implement or duplicate tests that already exist in `test_verifiers.py` or `TestDisabledAuthNoOp`.
- Do not add OIDC, JWKS, JWT, or PyJWT test infrastructure in this story — Story 3.4 owns OIDC coverage.
- Do not start a second subprocess smoke server if `http_server_proc_with_auth` fixture already exists.
- Do not strip the `.PHONY` list or remove existing Makefile targets.
- Do not lower or skip existing tests to make new tests pass.
- Do not add a conftest.py to `tests/unit/auth/` unless fixtures genuinely shared between multiple test files require it.

### Previous Story Intelligence

From Story 2.2 completion notes:
- Full suite was 1506 passed, 3 skipped (pre-existing discovery skips). The 3 skips are expected and must not change.
- The `http_server_proc_with_auth` fixture is `scope="module"` and starts the server once for `TestStreamableHTTPAuthSmoke`. New smoke tests in this class will reuse the same server instance — do not add a new fixture.
- `streamable_http_client(url, http_client=auth_client)` is the correct SDK call for passing auth headers.

From Story 2.1 completion notes:
- `tests/unit/auth/__init__.py` exists — no need to create it.
- The `STATIC_TOKEN_CLIENT_ID = "static-token-client"` constant is importable from `soniq_mcp.auth.verifiers` if needed in assertions.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-23-Add-Static-Auth-Regression-Coverage]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#NonFunctional-Requirements NFR4, NFR5, NFR12]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- [Source: src/soniq_mcp/auth/__init__.py]
- [Source: src/soniq_mcp/auth/verifiers.py]
- [Source: src/soniq_mcp/server.py]
- [Source: tests/unit/auth/test_verifiers.py]
- [Source: tests/unit/test_server.py]
- [Source: tests/smoke/streamable_http/test_streamable_http_smoke.py]
- [Source: Makefile]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was test-only and straightforward; no blocking issues.

### Completion Notes List

- Added 4 new edge-case unit tests to `tests/unit/auth/test_verifiers.py`: `build_token_verifier` raises `NotImplementedError` for `AuthMode.NONE`; `StaticBearerVerifier` with `auth_token=None` returns `None`; presented token with surrounding whitespace is rejected by raw-bytes `compare_digest`; whitespace-only configured token always returns `None`.
- Added `test_wrong_auth_scheme_returns_401` to `TestStreamableHTTPAuthSmoke` in the smoke file — reuses the existing `http_server_proc_with_auth` fixture, no new subprocess.
- Fixed lint E501 (line too long) in a comment during implementation.
- Added `make test-auth` and `make smoke-auth` convenience targets to `Makefile`; updated `.PHONY` list accordingly.
- Full suite: 1512 passed, 3 skipped (3 pre-existing discovery skips unchanged). Lint clean.
- Code review completed with no actionable findings; focused Story 2.3 auth suite revalidated at 27 passed.

### File List

- tests/unit/auth/test_verifiers.py
- tests/smoke/streamable_http/test_streamable_http_smoke.py
- Makefile
- _bmad-output/implementation-artifacts/optional-auth/2-3-add-static-auth-regression-coverage.md
- _bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml

## Change Log

- 2026-05-05: Implemented Story 2.3 — added verifier edge-case unit tests, wrong-scheme smoke test, and Makefile auth convenience targets.
- 2026-05-05: Marked Story 2.3 done after clean code review and tracker sync.
