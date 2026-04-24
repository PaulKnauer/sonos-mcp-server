# Story 1.1: Add Optional Auth Configuration Model

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an operator,
I want SoniqMCP to expose optional authentication settings through validated configuration,
so that I can choose `none`, `static`, or `oidc` auth without changing existing deployments.

## Acceptance Criteria

1. Given no auth environment variables are configured, when configuration is loaded, then `auth_mode` defaults to `none`.
2. Given `SONIQ_MCP_AUTH_MODE` is set to `none`, `static`, or `oidc`, when configuration is loaded, then the value is parsed into an `AuthMode` enum.
3. Given static token, OIDC issuer, audience, JWKS URI, CA bundle, or resource URL env vars are set, when configuration is loaded, then the corresponding `SoniqConfig` fields are populated.
4. Given a static auth token is configured, when the config model is represented or serialized, then the raw token value is masked.
5. Given an unsupported auth mode is configured, when configuration is loaded or validated, then startup fails with a clear validation error.

## Tasks / Subtasks

- [x] Extend the typed config model with optional-auth fields and enum support (AC: 1, 2, 3, 4, 5)
  - [x] Add `AuthMode` to [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) with exactly `NONE = "none"`, `STATIC = "static"`, and `OIDC = "oidc"`.
  - [x] Add new `SoniqConfig` fields for `auth_mode`, `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, and `oidc_resource_url`.
  - [x] Use `SecretStr | None` for `auth_token` so masking is handled at the model boundary and raw token values do not appear in repr/serialization.
  - [x] Add model-level consistency validation required for this story only: `auth_mode=oidc` requires `oidc_issuer`; unsupported enum values must fail validation cleanly.
  - [x] Keep the existing `transport`, `exposure`, and safety validators intact; auth config must be additive, not a refactor of unrelated config behavior.

- [x] Extend env-var loading and defaults without breaking existing installs (AC: 1, 2, 3)
  - [x] Update [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py) to map `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, `SONIQ_MCP_OIDC_JWKS_URI`, `SONIQ_MCP_OIDC_CA_BUNDLE`, and `SONIQ_MCP_OIDC_RESOURCE_URL`.
  - [x] Preserve the existing resolution order: defaults, `.env`, environment variables, then explicit overrides.
  - [x] Ensure whitespace-only auth-related optional strings normalize to `None` in the same way existing optional config fields do.
  - [x] Keep `AUTH_MODE=none` as the default through config defaults rather than through special-case runtime behavior elsewhere.

- [x] Export the new config surface cleanly (AC: 1, 2, 3)
  - [x] Update [src/soniq_mcp/config/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/__init__.py) to export `AuthMode` alongside the existing config types.
  - [x] Update [src/soniq_mcp/config/defaults.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/defaults.py) with the minimal auth-related defaults needed for predictable loading.

- [x] Add targeted unit coverage for model and loader behavior (AC: 1, 2, 3, 4, 5)
  - [x] Extend [tests/unit/config/test_models.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_models.py) to cover `AuthMode` parsing, default `auth_mode=none`, `SecretStr` masking behavior, and `oidc` missing-issuer validation.
  - [x] Extend [tests/unit/config/test_loader.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_loader.py) to cover auth env-var loading, override behavior, and whitespace normalization for optional auth fields.
  - [x] Extend [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py) only as needed to assert clear validation errors for unsupported auth mode values or missing issuer under `oidc`.

- [x] Preserve story boundaries so later auth stories stay meaningful (AC: 1, 3, 5)
  - [x] Do not add `src/soniq_mcp/auth/` in this story.
  - [x] Do not wire `token_verifier`, `AuthSettings`, or auth kwargs into `create_server()` in this story.
  - [x] Do not add live JWKS connectivity checks here; those belong to Story 1.2 and Epic 3.
  - [x] Do not add docs, Helm values, or smoke-test auth flows here; those belong to later stories.

### Review Findings

- [x] [Review][Patch] Model-level `oidc_issuer` enforcement blocks stdio auth configs before preflight can downgrade them to a warning [_bmad-output/planning-artifacts/epics-optional-auth.md:128]
- [x] [Review][Patch] Test suite calls `SecretStr.get_secret_value()` outside `StaticBearerVerifier.verify_token()`, violating the auth secret-handling guardrail [tests/unit/config/test_loader.py:149]

## Dev Notes

### Story Intent

This is the configuration-foundation story for optional auth. The implementation should stop at typed config modeling, env-var loading, and validation that belongs at the model/loading boundary.

The goal is to make later auth stories straightforward:

- Story 1.2 extends `run_preflight()` with auth-specific startup checks.
- Story 1.3 proves the disabled-auth no-op path remains structurally unchanged.
- Epic 2 and Epic 3 consume these config fields when wiring actual verifiers.

If this story starts touching runtime auth middleware, server constructor kwargs, or OIDC network behavior, it has gone too far.

### What Already Exists

Current repo state:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py) defines `TransportMode`, `ExposurePosture`, `LogLevel`, and `SoniqConfig`, but has no auth-specific fields yet.
- [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py) already implements the project’s canonical env-to-field mapping and whitespace normalization.
- [src/soniq_mcp/config/defaults.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/defaults.py) is the source of truth for default values consumed by `load_config()`.
- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py) currently just wraps `load_config()`/Pydantic validation into `ConfigValidationError`.
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py) builds `FastMCP("soniq-mcp", host=..., port=...)` without auth kwargs.

That means Story 1.1 should remain a bounded change in `config/` plus its tests.

### Required Architecture Guardrails

- `AuthMode` belongs in `config/models.py`, not in a future `auth/` module. This is a config concern first. [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- `auth_token` must be `SecretStr | None`, and raw secret access is reserved for `StaticBearerVerifier.verify_token()` in a later story. This story must not introduce any `get_secret_value()` usage. [Source: _bmad-output/planning-artifacts/architecture.md#Authentication--Security]
- Auth remains a transport concern. Nothing in `tools/`, `services/`, `adapters/`, or Sonos domain code should be touched here. [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Additional-Requirements]
- `AUTH_MODE=none` must remain the default and must preserve backward compatibility for existing installs. The config defaults should make that path the natural baseline. [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Technical-Success]

### Field and Validation Guidance

Use the architecture and PRD names exactly:

- `auth_mode`
- `auth_token`
- `oidc_issuer`
- `oidc_audience`
- `oidc_jwks_uri`
- `oidc_ca_bundle`
- `oidc_resource_url`

Enum values must be exactly `none`, `static`, and `oidc`.

Validation scope for this story:

- Accept valid `AuthMode` values and reject unsupported values through normal Pydantic validation.
- Require `oidc_issuer` when `auth_mode=oidc` using a model validator.
- Keep `auth_mode=static` token presence checks out of this story; that belongs to preflight in Story 1.2.
- Do not decide `oidc_resource_url` semantics yet beyond loading/storing the field. Architecture explicitly leaves its default-behavior verification for a later OIDC story.

The PRD describes OIDC URL fields as `str | None`, so avoid over-constraining the model unless the implementation need is clear. If URL-typed fields are introduced, they must not create avoidable friction for current test and env-loading patterns.

### Expected File Touches

Likely to modify:

- [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py)
- [src/soniq_mcp/config/defaults.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/defaults.py)
- [src/soniq_mcp/config/__init__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/__init__.py)
- [tests/unit/config/test_models.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_models.py)
- [tests/unit/config/test_loader.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_loader.py)
- [tests/unit/config/test_validation.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_validation.py)

Potentially inspect but avoid changing in this story:

- [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py)
- [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py)
- [tests/smoke/streamable_http/test_streamable_http_smoke.py](/Users/paul/github/sonos-mcp-server/tests/smoke/streamable_http/test_streamable_http_smoke.py)

### Testing Guidance

Follow the current config-test layering already present in the repo:

- `test_models.py` for direct `SoniqConfig(...)` behavior and validator semantics.
- `test_loader.py` for env-file/env-var/override mapping behavior.
- `test_validation.py` for user-facing `ConfigValidationError` formatting from `run_preflight()`.

Suggested test additions:

- `SoniqConfig()` defaults `auth_mode` to `AuthMode.NONE`.
- `SoniqConfig(auth_mode="static")` and `SoniqConfig(auth_mode="oidc", oidc_issuer="...")` parse correctly.
- Unsupported auth mode values raise a field-level validation error.
- `SoniqConfig(auth_mode="oidc")` fails with a clear model-validation error naming `oidc_issuer`.
- `SecretStr` masking works in repr/model dump behavior for `auth_token`.
- Loader picks up every new `SONIQ_MCP_AUTH_*` / `SONIQ_MCP_OIDC_*` variable.
- Whitespace-only values for optional OIDC strings normalize to `None`.

### Anti-Patterns To Avoid

- Do not create `src/soniq_mcp/auth/` yet.
- Do not import JWT or MCP auth classes into `config/` for this story.
- Do not make `run_preflight()` perform network checks yet.
- Do not add auth-aware logic to `server.py` in Story 1.1.
- Do not unwrap `SecretStr` anywhere in this story.
- Do not break existing non-auth config tests while adding auth defaults.

### Latest Technical Notes

- The installed MCP SDK in this repo’s project environment exposes `FastMCP.__init__(..., token_verifier: TokenVerifier | None = None, ..., auth: AuthSettings | None = None, ...)`, which confirms auth wiring is a later server-construction concern and not part of this config-only story.
- The same SDK defines `TokenVerifier.verify_token(self, token: str) -> AccessToken | None`, reinforcing the architecture rule that later verifier stories return `None`, not exceptions, for invalid tokens.
- `AuthSettings` requires `issuer_url` and `resource_server_url`, which is why the architecture keeps `oidc_resource_url` in the config surface even though its exact OIDC behavior is deferred.
- Current PyJWT docs for 2.12.1 document `PyJWKClient` with built-in JWKS-set caching and optional `ssl_context`; that matches the later-story design but does not need to be implemented here.
- Pydantic v2 documents `SecretStr` masking in repr/logging/JSON serialization unless explicitly unwrapped with a serializer, which supports using it directly at the config boundary.

### Project Structure Notes

- This repo keeps config concerns under `src/soniq_mcp/config/`; follow that pattern rather than inventing a new top-level auth config module.
- Existing defaults are centralized in `config/defaults.py`, so the auth default should be added there instead of being hardcoded elsewhere.
- `config/__init__.py` is the public config surface; export `AuthMode` there once added so later stories can import from `soniq_mcp.config`.
- No previous optional-auth story exists yet, so there are no prior-story implementation learnings to inherit.

### References

- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Story-11-Add-Optional-Auth-Configuration-Model]
- [Source: _bmad-output/planning-artifacts/epics-optional-auth.md#Additional-Requirements]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#Technical-Success]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#API-Surface]
- [Source: _bmad-output/planning-artifacts/prd-optional-auth.md#MVP-Feature-Set]
- [Source: _bmad-output/planning-artifacts/architecture.md#Core-Architectural-Decisions--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation-Patterns--Phase-3-Optional-Auth]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project-Structure--Boundaries--Phase-3-Optional-Auth]
- [Source: src/soniq_mcp/config/models.py]
- [Source: src/soniq_mcp/config/loader.py]
- [Source: src/soniq_mcp/config/defaults.py]
- [Source: src/soniq_mcp/config/__init__.py]
- [Source: src/soniq_mcp/config/validation.py]
- [Source: src/soniq_mcp/server.py]
- [Source: tests/unit/config/test_models.py]
- [Source: tests/unit/config/test_loader.py]
- [Source: tests/unit/config/test_validation.py]
- [Source: tests/smoke/streamable_http/test_streamable_http_smoke.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/fastmcp/__init__.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/provider.py]
- [Source: .venv/lib/python3.12/site-packages/mcp/server/auth/settings.py]
- [Source: https://pyjwt.readthedocs.io/en/latest/api.html]
- [Source: https://pyjwt.readthedocs.io/en/stable/changelog.html]
- [Source: https://docs.pydantic.dev/2.2/usage/types/secrets/]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- Story created from optional-auth planning artifacts, Phase 3 architecture sections, current config/server implementation, and live SDK signature inspection via `uv run python`.
- Implemented config changes and validated with `uv run pytest tests/unit/config/test_models.py tests/unit/config/test_loader.py tests/unit/config/test_validation.py`.
- Addressed code-review follow-ups by allowing stdio/OIDC configs to load without issuer at model-validation time and removing direct `SecretStr.get_secret_value()` usage from tests.
- Revalidated review fixes with `uv run pytest tests/unit/config/test_models.py tests/unit/config/test_loader.py tests/unit/config/test_validation.py` and `uv run ruff check src/soniq_mcp/config tests/unit/config`.

### Completion Notes List

- Story created with config-only scope, explicit file targets, and later-story guardrails for preflight, verifier, and server wiring work.
- Implemented `AuthMode` StrEnum (`none`, `static`, `oidc`) in `config/models.py`.
- Added 7 new `SoniqConfig` fields: `auth_mode`, `auth_token` (SecretStr|None), and 5 optional OIDC string fields.
- Added `validate_auth_config` model validator: `auth_mode=oidc` requires `oidc_issuer`; invalid enum values rejected by Pydantic.
- Updated `defaults.py` with `auth_mode="none"` and `None` defaults for all optional auth fields.
- Updated `loader.py` `_ENV_MAP` with 7 new `SONIQ_MCP_AUTH_*` / `SONIQ_MCP_OIDC_*` entries; existing whitespace normalization covers all new optional fields.
- Exported `AuthMode` from `config/__init__.py`.
- 29 new tests added (models: 18, loader: 11, validation: 4); all 1091 unit tests pass; lint clean.
- No `src/soniq_mcp/auth/` module created; no server.py changes; story boundaries preserved.
- Review fixes applied: stdio + `auth_mode=oidc` no longer hard-fails before preflight, and tests no longer unwrap `SecretStr` outside verifier code.

### File List

- `_bmad-output/implementation-artifacts/optional-auth/1-1-add-optional-auth-configuration-model.md`
- `src/soniq_mcp/config/models.py`
- `src/soniq_mcp/config/defaults.py`
- `src/soniq_mcp/config/loader.py`
- `src/soniq_mcp/config/__init__.py`
- `tests/unit/config/test_models.py`
- `tests/unit/config/test_loader.py`
- `tests/unit/config/test_validation.py`

### Change Log

- 2026-04-24: Implemented Story 1.1 — added `AuthMode` enum, optional auth fields to `SoniqConfig`, env-var loading, defaults, and unit coverage. All ACs satisfied.
- 2026-04-24: Addressed code review follow-ups, revalidated Story 1.1, and marked the story done.
