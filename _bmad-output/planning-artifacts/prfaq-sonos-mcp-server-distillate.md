---
title: "PRFAQ Distillate: sonos-mcp-server — Optional Authentication"
type: llm-distillate
source: "prfaq-sonos-mcp-server.md"
created: "2026-04-23"
purpose: "Token-efficient context for downstream PRD creation"
---

# PRFAQ Distillate: SoniqMCP Optional Authentication

## Concept Summary

SoniqMCP v0.6.0 adds optional Bearer token authentication to its HTTP transport. Three modes: `none` (default, unchanged), `static` (shared secret), `oidc` (JWT validated against a JWKS endpoint). Stdio transport is unaffected. The MCP April 2026 spec draft mandates OAuth 2.1 for HTTP transport servers — this feature is ecosystem alignment, not scope creep.

---

## Customer & Problem

- **Primary customer**: HTTP deployers who share a LAN with others, run automation pipelines, or want a credential check without running a reverse proxy
- **Secondary customer**: Homelab operators with an existing OIDC provider (Authelia, Authentik) who want SoniqMCP to be a registered client like every other service
- **Not the primary customer**: Solo home users on a locked-down home network with only their own devices — they should never see or need this feature
- **Problem**: Anyone on the same network as SoniqMCP's HTTP endpoint can reach it today. For shared LAN or homelab contexts, that's an open door. Reverse proxy is a valid workaround but adds operational complexity.

---

## Rejected Framings

- "SoniqMCP gets security" — rejected: implies it was insecure before, dishonest for the intended use case
- "Enterprise-grade auth for your home Sonos controller" — rejected: wrong audience signal
- OIDC-first framing — rejected: positions a niche feature as the headline; static token is more broadly relevant
- Making auth visible in the default install path — rejected: violates the simple-install vision

---

## Architecture Decisions

- **Auth is strictly opt-in**: `AUTH_MODE=none` is the default and must behave identically to today's behaviour (zero performance impact, no extra dependencies loaded)
- **Three modes**: `none` | `static` | `oidc`
- **Implementation**: FastMCP `TokenVerifier` protocol — one async method `verify_token(token: str) -> AccessToken | None`, passed to `FastMCP(token_verifier=...)` constructor; FastMCP wires all middleware automatically
- **Static mode**: string comparison against `SONIQ_MCP_AUTH_TOKEN` env var (~5 lines)
- **OIDC mode**: PyJWT `PyJWKClient` + RS256 + claims validation (`iss`, `aud`, `exp`) — ~30 lines
- **Dependency**: Add `PyJWT>=2.8` only; `cryptography>=46.0.7` already a prod dep; `python-jose` explicitly rejected (maintenance risk, CVE history)
- **No ASGI middleware bypass needed**: Original assessment was wrong — FastMCP's `TokenVerifier` protocol is the correct integration point; no need to extract the Starlette app and run Uvicorn manually

---

## Technical Constraints

- FastMCP version: `mcp[cli]>=1.26.0` — `TokenVerifier` protocol confirmed present at `mcp/server/auth/provider.py`
- `AccessToken` model fields: `token`, `client_id`, `scopes`, `expires_at`, `resource`
- `streamable_http_app()` method confirmed in FastMCP 1.26.0 (line ~950 of server.py) — returns Starlette app; auth middleware wired automatically when `token_verifier` provided
- `JWTVerifier` from gofastmcp.com docs is from the separate `fastmcp` (jlowin) package — NOT `mcp[cli]`. Do not use it.
- Self-signed homelab CA cert: `PyJWKClient(ssl_context=ssl.create_default_context(cafile=ca_bundle))` supported since PyJWT 2.8.0 (PR #891)
- Authelia: does NOT support dynamic client registration; must pre-configure in Terraform; `client_secret_basic` auth method; requires `authelia.bearer.authz` scope for bearer token usage
- Stdio transport: auth is silently ignored if configured — no error, no warning

---

## Key Files (sonos-mcp-server)

| File | Change |
|------|--------|
| `src/soniq_mcp/config/models.py` | Add `auth_mode`, `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri` fields |
| `src/soniq_mcp/config/loader.py` | Add `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_*` env-var mappings |
| `src/soniq_mcp/config/validation.py` | Add preflight: require `auth_token` when `auth_mode=static`; validate OIDC connectivity when `auth_mode=oidc` |
| `src/soniq_mcp/server.py` | Pass `token_verifier` to `FastMCP()` constructor when auth enabled |
| `src/soniq_mcp/auth/token_verifier.py` | New: `StaticTokenVerifier` and `OIDCTokenVerifier` implementations |
| `tests/unit/auth/test_token_verifier.py` | New: mock JWKS, valid/expired/tampered/missing token cases |
| `tests/smoke/streamable_http/test_streamable_http_smoke.py` | Extend: 401 without token, 200 with valid token |
| `docs/setup/authentication.md` | New: all three modes, Authelia walkthrough, CA cert pattern, error messages |
| `.env.example` | Add auth env var examples (commented out) |

## Key Files (iot-edge-k3s)

| File | Change |
|------|--------|
| `infra/modules/authelia/variables.tf` | Add `oidc_clients` variable |
| `infra/modules/authelia/main.tf` | Render OIDC clients dynamically from `var.oidc_clients` |
| `infra/live/home/authelia/terragrunt.hcl` | Register `soniq-mcp` client (client_credentials, scopes: openid + authelia.bearer.authz) |
| `infra/live/home/sonos-mcp/terragrunt.hcl` | Add OIDC env vars to deployment |
| `infra/modules/sonos-mcp/charts/soniq/` | Mount CA cert ConfigMap; add `SSL_CERT_FILE` env var |

---

## Hard Requirements (confirmed during PRFAQ)

1. **`AUTH_MODE=none` must be a strict no-op**: no performance impact, no extra imports at startup, identical behaviour to today
2. **Startup preflight for OIDC**: if `AUTH_MODE=oidc` and JWKS endpoint is unreachable, server must fail fast with a clear error naming the endpoint, the HTTP/TLS error, and the likely cause — no silent failures that produce mysterious 401s at request time
3. **`docs/setup/authentication.md` is a first-class deliverable**: not an afterthought; the press release points to it explicitly

---

## Scope Decisions

**In scope (MVP):**
- `AUTH_MODE`: `none` | `static` | `oidc`
- RS256 JWT validation: `iss`, `aud`, `exp` claims
- Authelia `client_credentials` flow as the reference OIDC implementation
- Startup preflight validation with actionable error messages
- Full documentation: `docs/setup/authentication.md`

**Out of scope (explicit):**
- Role/groups claim authorization (authentication only, not fine-grained RBAC)
- Token caching on the MCP client side (out of SoniqMCP's scope; document it)
- Dynamic OIDC client registration (Authelia doesn't support it)
- Browser redirect / authorization code flow (machine-to-machine only)
- Ingress-layer auth (in-app validation is the chosen architecture)

**Accepted trade-offs:**
- Static tokens don't expire — rotation is "change env var, restart container." Intentional simplicity. OIDC is the upgrade path for users who need expiry.
- Claude Desktop's built-in MCP client does not have a Bearer token config field — static token is most useful for custom/automation clients. Document this honestly; stdio users (the majority of Claude Desktop users) are unaffected.
- OIDC tested only with Authelia; provider-agnostic by design but not verified beyond Authelia. Other providers: community-contributed examples, no SLA.

---

## Open Questions (resolved)

| Question | Resolution |
|----------|------------|
| FastMCP ASGI exposure | Resolved: `TokenVerifier` protocol is the integration point; no transport bypass needed |
| Self-signed CA cert for JWKS | Resolved: `PyJWKClient(ssl_context=...)` + ConfigMap mount + `SSL_CERT_FILE` |
| PyJWT vs python-jose | Resolved: PyJWT; python-jose has CVE history and maintenance risk |
| `JWTVerifier` class from fastmcp docs | Resolved: that's jlowin/fastmcp, not `mcp[cli]`. Not available; implement manually. |
| Authelia dynamic client registration | Resolved: not supported; pre-configure in Terraform |
| MCP spec stance on auth | Resolved: April 2026 draft mandates OAuth 2.1 for HTTP transport; optional auth = spec alignment |

---

## Verdict Summary

**Ready to proceed to PRD.**

- **Forged in steel**: opt-in architecture, MCP spec alignment, technical simplicity (~30 lines OIDC path), correct primary customer framing, honest support boundary
- **Needs more heat**: `docs/setup/authentication.md` (first-class story, not afterthought); Claude Desktop scope (one explicit paragraph in docs)
- **Cracks in the foundation**: none

---

## MCP Spec References

- [MCP Authorization Specification](https://modelcontextprotocol.io/specification/draft/basic/authorization) — mandates OAuth 2.1 for HTTP transport
- [MCP Authorization Specification — OAuth 2.1 and Resource Indicators](https://dasroot.net/posts/2026/04/mcp-authorization-specification-oauth-2-1-resource-indicators/)
- [MCP OAuth: How OAuth 2.1 Works in the Model Context Protocol](https://www.prefect.io/resources/mcp-oauth)
