# Story 2.1: Implement Static Bearer Token Verifier

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a shared-LAN HTTP operator,
I want SoniqMCP to validate a configured static Bearer token,
so that only clients with the shared token can use HTTP tools.

## Acceptance Criteria

1. Given `auth_mode=static` and a configured `auth_token`, when `build_token_verifier(config)` is called, then it returns a `StaticBearerVerifier`.
2. Given a request token matching the configured secret, when `verify_token(token)` runs, then it returns a FastMCP-compatible `AccessToken`.
3. Given a missing, empty, or incorrect token, when `verify_token(token)` runs, then it returns `None`.
4. Given static token comparison occurs, when implementation is inspected or tested, then it uses `secrets.compare_digest`.
5. Given static token verification runs, when logs or errors are emitted, then the raw configured token and presented token are never included.
6. Given `get_secret_value()` is used, when the codebase is inspected, then it appears only inside `StaticBearerVerifier.verify_token()`.

## Tasks / Subtasks

- [x] Create the auth module public surface for verifier construction (AC: 1)
  - [x] Add [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py) exporting `build_token_verifier(config: SoniqConfig) -> TokenVerifier`.
  - [x] Make `build_token_verifier()` dispatch on `config.auth_mode` and return `StaticBearerVerifier` for `AuthMode.STATIC`.
  - [x] Keep the factory intentionally narrow in this story: support `static`, tolerate `none` only if needed by tests, and do not implement OIDC runtime behavior yet.

- [x] Implement the static verifier itself in the planned runtime location (AC: 1, 2, 3, 4, 5, 6)
  - [x] Add [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py) with a `StaticBearerVerifier` class implementing FastMCP's `TokenVerifier` protocol.
  - [x] Accept `SoniqConfig` or the needed secret-bearing config fields in the verifier constructor; keep the config lifetime small and explicit.
  - [x] Implement `async verify_token(token: str) -> AccessToken | None`.
  - [x] Use `secrets.compare_digest` for the token comparison.
  - [x] Build a valid `AccessToken` result with the presented token and a stable `client_id` / empty `scopes` shape that matches the local SDK contract.
  - [x] Confine `config.auth_token.get_secret_value()` to the comparison path inside `verify_token()` only.

- [x] Preserve secret safety and fail-closed behavior (AC: 3, 5, 6)
  - [x] Return `None` for missing, empty, or wrong tokens; do not raise into FastMCP for invalid credentials.
  - [x] If logging is added, keep it token-free and low-noise; never include the configured secret or presented token.
  - [x] Do not add token unwrapping anywhere in config loading, preflight, tests, or server wiring.

- [x] Add focused unit coverage for the new runtime contract (AC: 1, 2, 3, 4, 5, 6)
  - [x] Create [tests/unit/auth/__init__.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/__init__.py).
  - [x] Create [tests/unit/auth/test_verifiers.py](/Users/paul/github/sonos-mcp-server/tests/unit/auth/test_verifiers.py).
  - [x] Verify `build_token_verifier()` returns `StaticBearerVerifier` for `auth_mode=static`.
  - [x] Verify matching token returns an `AccessToken` with the expected shape.
  - [x] Verify missing, empty, whitespace-only, and incorrect tokens return `None`.
  - [x] Verify the implementation path uses `secrets.compare_digest` rather than `==`.
  - [x] Add a regression assertion that `get_secret_value()` is not used outside `StaticBearerVerifier.verify_token()`.

- [x] Keep Story 2.1 scoped to verifier implementation only (AC: 1, 2, 3, 4, 5, 6)
  - [x] Do not wire `auth` or `token_verifier` into `FastMCP` here; that belongs to Story 2.2.
  - [x] Do not add HTTP 401 transport assertions here; those belong to Story 2.2 and Story 2.3.
  - [x] Do not implement `OIDCVerifier`, JWKS fetching, CA-bundle handling, or `PyJWT` runtime use in this story.
  - [x] Do not modify `tools/`, `services/`, `adapters/`, or transport runner modules.

### Review Findings

- [x] [Review][Patch] Split Docker smoke prerequisite cleanup out of Story 2.1 tracking — User chose to split this infrastructure fix from Story 2.1, so Docker smoke file references were removed from this story's File List and completion notes.
- [x] [Review][Patch] Non-ASCII tokens can raise instead of failing closed [src/soniq_mcp/auth/verifiers.py:30]
- [x] [Review][Patch] Docker daemon availability check can hang pytest collection [tests/smoke/docker/test_docker_smoke.py:31]

## Dev Notes

### Story Intent

Story 2.1 is the first runtime auth story for optional auth, but it is still deliberately narrow.

Epic 1 already established:

- the `AuthMode` enum and auth config fields,
- startup preflight for static-token presence on HTTP,
- and regression coverage proving `auth_mode=none` remains a no-op.

This story should add only the verifier runtime primitive that later stories will plug into FastMCP. If the implementation starts wiring the server, changing transport behavior, or adding request/response auth handling, it has crossed into Story 2.2.

### What Already Exists

Current repo state relevant to Story 2.1:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) already defines `AuthMode` with `NONE`, `STATIC`, and `OIDC`, plus `auth_token: SecretStr | None`.
- [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py) already maps `SONIQ_MCP_AUTH_MODE` and `SONIQ_MCP_AUTH_TOKEN`.
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) already blocks `auth_mode=static` without a token for HTTP transport.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) currently has an `_build_auth_kwargs()` placeholder seam but does not yet construct `AuthSettings` or a token verifier.
- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) already asserts the disabled-auth path remains clean: `settings.auth is None`, `_token_verifier is None`, and `_build_auth_kwargs()` is not called for `auth_mode=none`.
- No `src/soniq_mcp/auth/` package exists yet, so Story 2.1 will establish that runtime boundary.

### Previous Story Intelligence

Relevant learnings from optional-auth Epic 1:

- Story 1.1 locked in `SecretStr` for `auth_token` and explicitly corrected tests so `get_secret_value()` is not used outside verifier code.
- Story 1.2 kept auth validation ownership in `run_preflight()` rather than pushing operator-facing failures into runtime constructors.
- Story 1.3 added the `_build_auth_kwargs()` seam and protected the disabled-auth path with tests; Epic 2 must preserve that no-op contract.
- The Epic 1 retrospective calls out one high-priority carry-forward action: keep auth imports and construction lazy/guarded so stdio and `AUTH_MODE=none` remain clean.

Recent work pattern:

- `05f9f16` completed Story 1.3 and introduced the current auth seam in `server.py`.
- `8c88125` fixed a mypy issue around that seam rather than expanding runtime auth scope.
- `91a7cbb` recorded the Epic 1 retrospective and explicitly recommended Story `2-1-implement-static-bearer-token-verifier` as the next step.

### Architecture Guardrails

- Auth remains a server/transport concern only. Do not place auth logic into `tools/`, `services/`, `adapters/`, or `transports/`. [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- `StaticBearerVerifier` lives in `src/soniq_mcp/auth/verifiers.py`; the public factory lives in `src/soniq_mcp/auth/__init__.py`. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- Both verifiers must implement `async verify_token(token: str) -> AccessToken | None`. Invalid tokens return `None`, not exceptions. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- Static token comparison must use `secrets.compare_digest` for constant-time comparison. [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- `config.auth_token.get_secret_value()` is allowed only inside `StaticBearerVerifier.verify_token()`. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- `AUTH_MODE=none` must remain structurally unchanged in server construction. Story 2.1 must not weaken the disabled-path tests or force eager auth imports into the default path. [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]

### Current File Analysis

#### [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)

Current state:

- Imports `AuthMode` and exposes `_build_auth_kwargs(config)` as a placeholder seam.
- Calls `_build_auth_kwargs(config)` only when `config.auth_mode != AuthMode.NONE`.
- Still constructs `FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)` with no auth kwargs.

What Story 2.1 changes:

- Nothing in this file needs to change unless a minimal import-safe seam adjustment is required for future factory use.

What must be preserved:

- `auth_mode=none` must remain the exact clean path.
- No eager import of runtime auth code should be introduced if it makes the disabled path do work unnecessarily.
- Tool registration and startup logging behavior must remain unchanged.

#### [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)

Current state:

- Holds the canonical `AuthMode` enum and `auth_token: SecretStr | None`.
- Model validation already distinguishes OIDC requirements and preserves stdio behavior.

What Story 2.1 changes:

- Usually none. The config shape is already in place.

What must be preserved:

- `SecretStr` masking semantics.
- No additional model-level secret unwrapping or verifier behavior leaking into config.

#### [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)

Current state:

- Static HTTP without `auth_token` fails preflight with a safe, actionable error.

What Story 2.1 changes:

- None. Runtime verifier logic is not preflight logic.

What must be preserved:

- Preflight remains the only startup gate for static-token presence.
- The verifier constructor should not become a second startup validator.

#### [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py)

Current state:

- Locks down the disabled-auth no-op contract and secret-masking behavior.

What Story 2.1 changes:

- Ideally none. Add new verifier-specific tests in `tests/unit/auth/` rather than bloating server tests.

What must be preserved:

- Disabled-auth assertions must continue passing after Story 2.1 lands.

### Implementation Guidance

Preferred implementation shape:

- Add `src/soniq_mcp/auth/__init__.py` with a small factory:
  - import `AuthMode` and `SoniqConfig`
  - return `StaticBearerVerifier(config)` for `AuthMode.STATIC`
  - leave OIDC support unimplemented in this story, but fail clearly if the factory is called with unsupported modes in tests or future misuse
- Add `src/soniq_mcp/auth/verifiers.py` with `StaticBearerVerifier`
  - keep the class small and self-contained
  - only unwrap the configured secret inside `verify_token()`
  - compare the incoming token with `secrets.compare_digest`
  - return `None` for any invalid or unusable input
  - return an `AccessToken` for a valid token

For the returned `AccessToken`, the local SDK shape requires:

- `token: str`
- `client_id: str`
- `scopes: list[str]`
- optional `expires_at`
- optional `resource`

Pragmatic recommendation for static mode:

- `token=token`
- `client_id="static-token-client"` or similarly stable internal identifier
- `scopes=[]`
- `expires_at=None`
- `resource=config.oidc_resource_url` only if the implementation chooses to thread it through consistently

This `client_id` choice is an implementation detail inferred from the local SDK contract. The critical requirement is that the object be a valid FastMCP `AccessToken`, not that static mode invent a richer identity model than the feature needs.

### Testing Guidance

Minimum unit coverage for Story 2.1:

- `build_token_verifier(SoniqConfig(auth_mode="static", auth_token="secret"))` returns `StaticBearerVerifier`.
- `verify_token("secret")` returns an `AccessToken` with the expected fields populated.
- `verify_token("")`, `verify_token("wrong")`, and a missing-value equivalent path all return `None`.
- `secrets.compare_digest` is the comparison primitive used by the verifier.
- No secret value appears in any raised error or log assertion introduced by these tests.

Recommended test patterns:

- Use `pytest.mark.anyio` or `asyncio.run()` patterns already accepted by the repo to call the async verifier.
- Patch `secrets.compare_digest` in one focused unit test to prove the verifier goes through it.
- Keep the secret-access regression targeted: assert `get_secret_value()` usage remains verifier-local rather than trying to scan arbitrary strings in every file.

Do not add in Story 2.1:

- Streamable HTTP smoke tests
- transport bootstrap assertions
- 401 response assertions
- OIDC/JWKS unit fixtures

Those belong to Stories 2.2, 2.3, and Epic 3.

### Anti-Patterns To Avoid

- Do not wire `build_token_verifier()` into `server.py` yet.
- Do not add `AuthSettings` construction yet.
- Do not implement `OIDCVerifier` as a placeholder with dead code just to “finish the module”.
- Do not use plain `==` for bearer-token comparison.
- Do not cache or log the raw configured token in instance state beyond what `SecretStr` already encapsulates.
- Do not unwrap `SecretStr` in tests, config loaders, or debug helpers.
- Do not add `PyJWT` to runtime code or dependencies for this static-only story unless there is a concrete immediate need.

### Latest Technical Notes

- The local installed MCP SDK in this repo defines `TokenVerifier.verify_token()` as `async` and expects an `AccessToken | None` result. `AccessToken` currently requires `token`, `client_id`, and `scopes`, with optional `expires_at` and `resource`. [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/provider.py]
- The local installed MCP SDK also enforces that `token_verifier` cannot be supplied to `FastMCP` without `auth`, which confirms why verifier implementation and server wiring are split across Story 2.1 and Story 2.2. [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- The official MCP Python SDK README currently documents the v1.x line as the stable release and shows server auth integration through `TokenVerifier` plus `AuthSettings`. [Source: https://github.com/modelcontextprotocol/python-sdk]
- As of the current PyJWT documentation, `PyJWKClient` exists with built-in JWK set caching and SSL-context support, but that is Epic 3 material and should not be pulled into this story's runtime path. [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- Pydantic `SecretStr` masks values in repr/JSON output by default, which is the existing secret-safety baseline this story must preserve. [Source: https://docs.pydantic.dev/2.2/usage/types/secrets/]

### Project Structure Notes

- Optional-auth implementation artifacts live under [`_bmad-output/implementation-artifacts/optional-auth`](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth:1); keep this story and subsequent implementation work on that track rather than the Phase 2 tracker.
- The repo currently has no `src/soniq_mcp/auth/` package. Story 2.1 introduces that boundary for the first time, so keep it clean and minimal.
- The repo already separates config tests, server composition tests, transport integration tests, and smoke tests. Follow that structure instead of adding verifier assertions to unrelated suites.
- No `project-context.md` file was present during story creation, so this story relies on the optional-auth PRD, architecture, prior stories, retrospective, current code, local package inspection, and current upstream docs.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-21-Implement-Static-Bearer-Token-Verifier]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Additional-Requirements]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Executive-Summary]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Technical-Success]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Journey-1-Alex--The-Shared-LAN-HTTP-Deployer-Happy-Path]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- [Source: _bmad-output/implementation-artifacts/optional-auth/1-1-add-optional-auth-configuration-model.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/1-2-validate-auth-configuration-during-preflight.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/1-3-preserve-backward-compatibility-for-disabled-auth.md]
- [Source: _bmad-output/implementation-artifacts/optional-auth/epic-1-retro-2026-04-24.md]
- [Source: src/soniq_mcp/server.py]
- [Source: src/soniq_mcp/config/models.py]
- [Source: src/soniq_mcp/config/validation.py]
- [Source: src/soniq_mcp/config/loader.py]
- [Source: tests/unit/test_server.py]
- [Source: tests/unit/config/test_loader.py]
- [Source: tests/unit/config/test_validation.py]
- [Source: tests/smoke/streamable_http/test_streamable_http_smoke.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/provider.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/settings.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- [Source: pyproject.toml]
- [Source: https://github.com/modelcontextprotocol/python-sdk]
- [Source: https://pyjwt.readthedocs.io/en/stable/api.html]
- [Source: https://docs.pydantic.dev/2.2/usage/types/secrets/]

## Dev Agent Record

### Agent Model Used

GPT-5

### Debug Log References

- Story created from the optional-auth sprint tracker, the Epic 2 story definition, the optional-auth PRD and architecture, Epic 1 story records and retrospective, current config/server/test code, local MCP SDK package inspection, and current upstream MCP / PyJWT / Pydantic documentation.
- Red test run: `uv run pytest tests/unit/auth/test_verifiers.py` failed with missing `soniq_mcp.auth`, confirming the new runtime package was not yet implemented.
- Green verifier run: `uv run pytest tests/unit/auth/test_verifiers.py` passed.
- Scoped quality checks: `uv run ruff check src/soniq_mcp/auth tests/unit/auth` and `uv run mypy src/soniq_mcp/auth tests/unit/auth` passed.
- Regression checks: `uv run pytest tests/unit/auth/test_verifiers.py tests/unit/test_server.py tests/integration/transports/test_http_bootstrap.py tests/integration/transports/test_server_bootstrap.py` passed.
- Full non-Docker suite: `uv run pytest --ignore=tests/smoke/docker` passed with 1493 passed and 3 skipped.
- Lint note: `uv run ruff check .` is blocked by unrelated generated skill and BMad asset lint violations outside `src` and `tests`; `uv run ruff check src tests` passed.
- Mypy note: `uv run mypy src tests` is blocked by existing typing violations in older tests; scoped auth mypy passed.
- Code review fix validation: non-ASCII token handling was added and Docker smoke daemon probing was bounded with a timeout.
- Code review final validation: `uv run pytest tests/unit/auth/test_verifiers.py tests/smoke/docker/test_docker_smoke.py -rs` passed with 8 passed; `uv run mypy src/soniq_mcp/auth tests/unit/auth` passed; `make test` passed with 1496 passed and 3 skipped; `make lint` passed.

### Completion Notes List

- Created a dedicated implementation-ready story for optional-auth Story 2.1 with concrete runtime boundaries, file targets, and test expectations.
- Pulled forward Epic 1 learnings around `SecretStr`, preflight ownership, and disabled-auth no-op discipline.
- Separated verifier creation scope from later server wiring and HTTP 401 behavior so Story 2.1 does not bleed into Stories 2.2 or 2.3.
- Included current SDK contract details for `TokenVerifier`, `AccessToken`, and `FastMCP` auth configuration to prevent incompatible implementations.
- Ultimate context engine analysis completed - comprehensive developer guide created.
- Implemented `build_token_verifier()` for `AuthMode.STATIC` only, returning `StaticBearerVerifier` and leaving OIDC/runtime server wiring out of scope.
- Implemented `StaticBearerVerifier.verify_token()` with fail-closed handling for missing, empty, whitespace-only, wrong, or unconfigured tokens.
- Used `secrets.compare_digest` for static token comparison and kept `get_secret_value()` confined to `StaticBearerVerifier.verify_token()`.
- Returned FastMCP-compatible `AccessToken(token=<presented>, client_id="static-token-client", scopes=[])` for valid tokens.
- Added focused auth unit coverage for factory dispatch, valid token shape, invalid tokens, `compare_digest` usage, and verifier-local secret unwrapping.
- Addressed code review findings by making static token verification fail closed for non-ASCII configured or presented tokens.
- Split Docker smoke prerequisite cleanup out of Story 2.1 tracking per user decision.

### File List

- `_bmad-output/implementation-artifacts/optional-auth/2-1-implement-static-bearer-token-verifier.md`
- `_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml`
- `src/soniq_mcp/auth/__init__.py`
- `src/soniq_mcp/auth/verifiers.py`
- `tests/unit/auth/__init__.py`
- `tests/unit/auth/test_verifiers.py`

## Change Log

- 2026-05-04: Implemented optional-auth Story 2.1 static bearer verifier runtime primitive and focused tests.
- 2026-05-04: Addressed code review finding for non-ASCII token fail-closed behavior.
