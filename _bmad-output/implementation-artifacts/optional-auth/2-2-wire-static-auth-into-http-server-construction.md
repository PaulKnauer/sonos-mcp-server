# Story 2.2: Wire Static Auth into HTTP Server Construction

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an HTTP operator,
I want static auth to be enforced by FastMCP before tool handlers run,
so unauthorized clients receive 401 responses without touching Sonos tools or services.

## Acceptance Criteria

1. Given `auth_mode=static`, when `create_server(config)` builds the FastMCP app, then it passes both `auth` and `token_verifier`.
2. Given `auth_mode=static`, when auth settings are built, then `issuer_url` is derived from configured HTTP host and port.
3. Given `auth_mode=static`, when app starts, then no auth code is added to tools, services, adapters, or transport runners.
4. Given client calls HTTP MCP endpoint without Authorization header, when static auth enabled, response is HTTP 401.
5. Given client calls HTTP MCP endpoint with incorrect Bearer token, when static auth enabled, response is HTTP 401.
6. Given client calls HTTP MCP endpoint with correct Bearer token, when static auth enabled, request reaches normal MCP handling.

## Tasks / Subtasks

- [x] Replace the placeholder auth seam in server construction with real FastMCP auth kwargs (AC: 1, 2, 3)
  - [x] Update [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) so `create_server(config)` passes auth kwargs into `FastMCP(...)` only when `config.auth_mode != AuthMode.NONE`.
  - [x] Make `_build_auth_kwargs(config)` return a mapping containing both `auth` and `token_verifier` for static auth.
  - [x] Construct `token_verifier` through `build_token_verifier(config)` from [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py).
  - [x] Construct FastMCP `AuthSettings` with `issuer_url=f"http://{config.http_host}:{config.http_port}"`.
  - [x] Set `resource_server_url=config.oidc_resource_url` and `required_scopes=None`.

- [x] Preserve the disabled-auth and stdio no-op contracts (AC: 1, 3)
  - [x] Keep `auth_mode=none` structurally unchanged: no auth kwargs, `app.settings.auth is None`, `app._token_verifier is None`, and `_build_auth_kwargs()` is not called.
  - [x] Do not move auth logic into [src/soniq_mcp/tools](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/tools), [src/soniq_mcp/services](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/services), [src/soniq_mcp/adapters](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/adapters), or transport runner modules.
  - [x] Do not add auth checks inside individual MCP tools or Sonos service calls.

- [x] Add focused server construction coverage (AC: 1, 2, 3)
  - [x] Extend [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) to assert static auth sets both FastMCP `settings.auth` and `_token_verifier`.
  - [x] Assert the generated `issuer_url` uses the configured HTTP host and port.
  - [x] Assert disabled-auth tests from Story 1.3 still pass without weakening their expectations.
  - [x] Add a small guard test or code-inspection assertion if useful to prove auth wiring remains server-local.

- [x] Add minimal HTTP behavior coverage for this story's acceptance criteria (AC: 4, 5, 6)
  - [x] Extend the existing streamable HTTP smoke file [tests/smoke/streamable_http/test_streamable_http_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/streamable_http/test_streamable_http_smoke.py) rather than creating a parallel smoke suite.
  - [x] Start the server with `SONIQ_MCP_AUTH_MODE=static` and `SONIQ_MCP_AUTH_TOKEN` set to a known test value.
  - [x] Verify a request without `Authorization` receives HTTP 401.
  - [x] Verify a request with an incorrect `Authorization: Bearer ...` token receives HTTP 401.
  - [x] Verify a request with the correct bearer token reaches normal MCP handling.
  - [x] Use a preconfigured `httpx.AsyncClient` for bearer headers when using `streamable_http_client(...)`; the installed SDK accepts headers through the `http_client` argument.

- [x] Keep Story 2.2 scoped to server wiring only (AC: 1, 2, 3, 4, 5, 6)
  - [x] Do not implement OIDC, JWKS fetching, custom CA handling, or `PyJWT` runtime behavior.
  - [x] Do not change config loading, preflight requirements, or `SecretStr` masking unless a narrow bug is discovered while wiring.
  - [x] Do not broaden the full static-auth regression matrix beyond what is needed to prove this story; Story 2.3 owns the wider regression coverage.

- [x] Validate the implementation (AC: 1, 2, 3, 4, 5, 6)
  - [x] Run focused tests for server construction and streamable HTTP auth behavior.
  - [x] Run `make test`.
  - [x] Run `make lint`.
  - [x] Do not lower or skip existing tests to make the story pass.

### Review Findings

- [x] [Review][Patch] Stdio auth configs are no longer ignored [src/soniq_mcp/server.py:49]
- [x] [Review][Patch] Auth imports now affect auth-disabled startup [src/soniq_mcp/server.py:14]
- [x] [Review][Patch] IPv6 HTTP hosts produce an invalid issuer URL [src/soniq_mcp/server.py:33]
- [x] [Review][Patch] Smoke test leaks the provided async HTTP client [tests/smoke/streamable_http/test_streamable_http_smoke.py:253]
- [x] [Review][Patch] Auth smoke subprocess can leak if startup wait fails [tests/smoke/streamable_http/test_streamable_http_smoke.py:214]
- [x] [Review][Patch] Sprint tracker status contradicts story review state [_bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml:67]
- [x] [Review][Patch] HTTP OIDC branch now crashes during server construction [src/soniq_mcp/server.py:59]

## Dev Notes

### Story Intent

Story 2.2 connects the static verifier from Story 2.1 to FastMCP's native auth path.

The target is narrow: when HTTP auth is enabled, `create_server(config)` must supply FastMCP with both an `AuthSettings` object and the `StaticBearerVerifier`. FastMCP should then reject unauthenticated HTTP requests before any SoniqMCP tool, service, adapter, or transport runner logic executes.

### Current File Analysis

#### [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)

Current state:

- Imports `AuthMode`.
- Defines `_build_auth_kwargs(config) -> None` as a placeholder.
- Calls `_build_auth_kwargs(config)` only when `config.auth_mode != AuthMode.NONE`.
- Constructs `FastMCP("soniq-mcp", host=config.http_host, port=config.http_port)` without auth kwargs.

Required change:

- Change `_build_auth_kwargs(config)` into the single server-local helper that returns the kwargs needed by `FastMCP`.
- Preserve the guarded call from `create_server()` so disabled auth does not call the helper.
- Pass returned kwargs into the existing `FastMCP(...)` construction.

Preferred implementation shape:

```python
auth_kwargs: dict[str, object] = {}
if config.auth_mode != AuthMode.NONE:
    auth_kwargs = _build_auth_kwargs(config)

mcp = FastMCP(
    "soniq-mcp",
    host=config.http_host,
    port=config.http_port,
    **auth_kwargs,
)
```

The exact type annotation may be adjusted to satisfy mypy, but keep the helper small and local to server construction.

#### [src/soniq_mcp/auth/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/__init__.py)

Current state:

- Exposes `build_token_verifier(config: SoniqConfig) -> TokenVerifier`.
- Returns `StaticBearerVerifier(config)` for `AuthMode.STATIC`.
- Leaves unsupported runtime modes unimplemented.

Required change:

- Usually none. Story 2.2 should consume this factory rather than duplicating verifier construction in `server.py`.

#### [src/soniq_mcp/auth/verifiers.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/auth/verifiers.py)

Current state:

- Implements `StaticBearerVerifier`.
- Uses `secrets.compare_digest`.
- Returns `AccessToken(token=token, client_id="static-token-client", scopes=[])` for valid tokens.
- Returns `None` for missing, empty, whitespace-only, wrong, unconfigured, or non-ASCII tokens.
- Keeps `config.auth_token.get_secret_value()` inside `verify_token()` only.

Required change:

- Usually none. Do not unwrap secrets in `server.py` while wiring auth.

#### Existing Tests

- [tests/unit/test_server.py](/Users/paul/github/sonos-mcp-server/tests/unit/test_server.py) already protects the disabled-auth path: `settings.auth is None`, `_token_verifier is None`, and `_build_auth_kwargs()` is not called for `auth_mode=none`.
- [tests/integration/transports/test_http_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_http_bootstrap.py) covers HTTP transport bootstrap and disabled-auth backward compatibility.
- [tests/integration/transports/test_server_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_server_bootstrap.py) covers stdio/bootstrap behavior.
- [tests/smoke/streamable_http/test_streamable_http_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/streamable_http/test_streamable_http_smoke.py) already starts a live streamable HTTP server on a dynamic port and exercises MCP client/session behavior.

### Previous Story Intelligence

Story 2.1 completed the static verifier and established these constraints:

- Static verifier construction is already implemented in `build_token_verifier(config)`.
- Invalid verifier tokens return `None`, not exceptions.
- Static token comparison uses `secrets.compare_digest`.
- Non-ASCII presented or configured tokens fail closed.
- `get_secret_value()` is intentionally confined to `StaticBearerVerifier.verify_token()`.
- Docker smoke prerequisite cleanup was split out of optional-auth Story 2.1 tracking and must not be reintroduced as auth-story scope.

Epic 1 carry-forward still applies:

- `auth_mode=none` must remain the default and must not pay auth construction overhead.
- Stdio must ignore configured auth.
- Auth startup validation belongs to preflight, not scattered runtime checks.
- Keep auth imports and construction guarded behind the enabled-auth path where practical.

### Architecture Guardrails

- Auth is a server/transport concern only; no auth code belongs in tools, services, adapters, or transport runners. [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- FastMCP requires `AuthSettings` when `token_verifier` is supplied; providing a verifier without `auth` raises during construction. [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- Static mode's `AuthSettings.issuer_url` must be derived as `http://{config.http_host}:{config.http_port}`. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- `resource_server_url` should use `config.oidc_resource_url`; `required_scopes` stays `None`. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- `AUTH_MODE=none` must leave FastMCP construction behavior equivalent to the current no-auth path. [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- Static auth must use FastMCP's `TokenVerifier` integration point, not custom ASGI middleware. [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Non-Functional-Requirements]

### Implementation Guidance

Build auth settings in `server.py`, not inside the verifier:

- Import `AuthSettings` from `mcp.server.auth.settings`.
- Import `build_token_verifier` from `soniq_mcp.auth` only in the enabled-auth helper or in a way that does not disturb the disabled path.
- Return `{"auth": auth_settings, "token_verifier": build_token_verifier(config)}` from `_build_auth_kwargs(config)`.

Use the architecture-specified static settings:

```python
AuthSettings(
    issuer_url=f"http://{config.http_host}:{config.http_port}",
    resource_server_url=config.oidc_resource_url,
    required_scopes=None,
)
```

Do not introduce additional scopes, clients, audiences, or token parsing in this story. Static mode is a shared-secret gate, and the verifier already owns the token decision.

### Testing Guidance

Recommended focused tests:

- Unit test that `create_server()` with `auth_mode=static` produces a FastMCP instance where `settings.auth` is present and `_token_verifier` is present.
- Unit test that the auth settings `issuer_url` matches the configured `http_host` and `http_port`.
- Regression test that `auth_mode=none` still avoids `_build_auth_kwargs()` and leaves auth fields unset.
- HTTP smoke tests for missing header, wrong bearer token, and correct bearer token.

For streamable HTTP client tests, the installed SDK signature is:

```python
streamable_http_client(url: str, *, http_client: httpx.AsyncClient | None = None, terminate_on_close: bool = True)
```

To pass an auth header, create an `httpx.AsyncClient(headers={"Authorization": "Bearer ..."})` and pass it as `http_client=...`. Do not use the deprecated `streamablehttp_client(...)` wrapper unless there is a specific compatibility reason.

When testing 401 behavior, use the existing subprocess/dynamic-port pattern in `tests/smoke/streamable_http/test_streamable_http_smoke.py`. Keep the assertions focused on the HTTP auth boundary rather than Sonos device availability.

### Anti-Patterns To Avoid

- Do not add ASGI middleware or manual request-header parsing.
- Do not put auth checks into MCP tools, services, adapters, or transport runner modules.
- Do not unwrap `config.auth_token` in server construction.
- Do not weaken disabled-auth assertions because static auth needs kwargs.
- Do not implement OIDC placeholders, JWKS cache behavior, or new dependencies in this story.
- Do not create a second streamable HTTP smoke harness if the existing one can be extended.
- Do not log configured or presented bearer tokens.

### Latest Technical Notes

- The installed MCP SDK `FastMCP` constructor accepts both `auth` and `token_verifier`; it validates that a verifier is not supplied without auth settings. [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- The installed MCP SDK `AuthSettings` requires `issuer_url` and supports optional `resource_server_url` and `required_scopes`. [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/settings.py]
- The installed SDK wraps the streamable HTTP route with auth middleware when `_token_verifier` is configured, which is the desired enforcement point for this story. [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- The installed MCP client configures headers through a supplied `httpx.AsyncClient` passed to `streamable_http_client(...)`. [Source: .venv/lib/python3.12/site-packages/mcp/client/streamable_http.py]
- The official MCP Python SDK authorization documentation continues to show server auth integration through `TokenVerifier` and `AuthSettings`, matching this architecture. [Source: https://py.sdk.modelcontextprotocol.io/authorization/]

### Project Structure Notes

- Optional-auth implementation artifacts live under [_bmad-output/implementation-artifacts/optional-auth](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/optional-auth:1).
- This story should update only the optional-auth sprint tracker, not the main Phase 2 sprint tracker.
- There is no `project-context.md` file in this repo; this story was prepared from the optional-auth PRD, optional-auth epics, architecture, previous story record, current code, installed SDK source, and current MCP authorization docs.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-22-Wire-Static-Auth-into-HTTP-Server-Construction]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Functional-Requirements]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Non-Functional-Requirements]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- [Source: _bmad-output/implementation-artifacts/optional-auth/2-1-implement-static-bearer-token-verifier.md]
- [Source: src/soniq_mcp/server.py]
- [Source: src/soniq_mcp/auth/__init__.py]
- [Source: src/soniq_mcp/auth/verifiers.py]
- [Source: tests/unit/test_server.py]
- [Source: tests/integration/transports/test_http_bootstrap.py]
- [Source: tests/integration/transports/test_server_bootstrap.py]
- [Source: tests/smoke/streamable_http/test_streamable_http_smoke.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/settings.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/client/streamable_http.py]
- [Source: https://py.sdk.modelcontextprotocol.io/authorization/]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None — implementation was straightforward; no blocking issues encountered.

### Completion Notes List

- Implemented `_build_auth_kwargs(config)` in `server.py` to return `{"auth": AuthSettings(...), "token_verifier": build_token_verifier(config)}`.
- Changed `create_server()` to capture and unpack `auth_kwargs` into `FastMCP(...)` constructor only when HTTP transport auth is enabled.
- Used `dict[str, Any]` annotation to satisfy mypy for `**auth_kwargs` unpacking.
- Added `TestStaticAuthWiring` coverage for `settings.auth`, `_token_verifier`, `issuer_url` derivation including IPv6 host formatting, and tool registration.
- All existing `TestDisabledAuthNoOp` tests pass without modification.
- Added `TestStreamableHTTPAuthSmoke` (3 tests) using subprocess fixture with `SONIQ_MCP_AUTH_MODE=static`; verified 401 for no header, 401 for wrong token, and successful MCP ping with correct token via `httpx.AsyncClient` passed to `streamable_http_client`.
- Addressed code review findings by keeping stdio auth ignored for static/OIDC configs, moving auth imports behind the HTTP-auth path, bracketing IPv6 issuer hosts, closing supplied async HTTP clients, and ensuring auth smoke subprocess cleanup also runs after startup failures.
- Restricted server auth wiring to static HTTP mode so the unimplemented OIDC branch is not entered during Story 2.2.
- Full suite: 1506 passed, 3 skipped (pre-existing discovery skips). Lint clean.

### File List

- src/soniq_mcp/server.py
- tests/unit/test_server.py
- tests/smoke/streamable_http/test_streamable_http_smoke.py
- _bmad-output/implementation-artifacts/optional-auth/2-2-wire-static-auth-into-http-server-construction.md
- _bmad-output/implementation-artifacts/optional-auth-sprint-status.yaml

## Change Log

- 2026-05-04: Created optional-auth Story 2.2 for static FastMCP server auth wiring.
- 2026-05-04: Implemented Story 2.2 — wired `_build_auth_kwargs` and `FastMCP` auth kwargs; added unit and smoke test coverage for static auth enforcement.
- 2026-05-04: Addressed Story 2.2 code review findings and marked story done after `make test` and `make lint`.
