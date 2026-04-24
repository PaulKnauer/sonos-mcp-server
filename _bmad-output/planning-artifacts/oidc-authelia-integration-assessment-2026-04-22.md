# BMAD INPUT: SoniqMCP × Authelia OIDC Integration Assessment

> **Status**: Assessment only — not yet implemented. Created 2026-04-22.
> Use this document as source context when creating a new epic/story set for OIDC authentication.

---

## Problem Statement

SoniqMCP has no built-in authentication. The homelab k3s cluster now runs Authelia as a live OIDC provider, making it practical to gate SoniqMCP with real identity enforcement for remote/AI-agent access.

---

## Chosen Architecture

- **Auth layer**: In-app — SoniqMCP validates Bearer JWT tokens directly (no browser redirect, no ingress-layer proxy)
- **Grant type**: `client_credentials` (machine-to-machine) — matches existing Authelia `test-client` pattern; appropriate for AI agent callers
- **Validation**: RS256 JWT signature verified against Authelia JWKS endpoint; claims: `iss`, `aud`, `exp`

```
MCP Client (AI agent)
    │
    │  1. POST /api/oidc/token (client_credentials)
    │     client_id=soniq-mcp, client_secret=<secret>
    ▼
Authelia (https://authelia.home.lab:30443)
    │  → access_token (RS256 JWT)
    ▼
MCP Client holds Bearer token
    │
    │  2. POST /mcp   Authorization: Bearer <token>
    ▼
SoniqMCP validates JWT inline → tool execution or 401
```

---

## Current State: SoniqMCP (`sonos-mcp-server`)

### What exists
- No auth of any kind — plain unauthenticated HTTP
- Config: Pydantic `SoniqConfig` with `SONIQ_MCP_*` env-var mapping
- HTTP transport: `app.run(transport="streamable-http")` — a blocking Uvicorn call

### Critical constraint
FastMCP 1.26.0's `app.run()` does not expose ASGI middleware hooks. The implementation must either:
1. Use `FastMCP.get_app()` (or equivalent) to get the underlying Starlette ASGI app, wrap it with middleware, then run Uvicorn directly — **verify this method exists in 1.26.0 before writing stories**
2. Alternatively: check if `mcp.server.fastmcp.server.create_app()` is the correct API

### Key files
| File | Purpose |
|------|---------|
| `src/soniq_mcp/transports/streamable_http.py` | HTTP transport runner — where middleware wrapping goes |
| `src/soniq_mcp/config/models.py` | `SoniqConfig` Pydantic model — add OIDC fields here |
| `src/soniq_mcp/config/loader.py` | Env-var → config mapping (`_ENV_MAP` dict) |
| `src/soniq_mcp/config/validation.py` | `run_preflight()` — add OIDC validation here |
| `src/soniq_mcp/server.py` | `create_server()` app factory |
| `tests/smoke/streamable_http/test_streamable_http_smoke.py` | HTTP smoke tests — extend for auth scenarios |

---

## Current State: Authelia OIDC (`iot-edge-k3s`)

### What exists
- **OIDC live** at `https://authelia.home.lab:30443`
- Endpoints:
  - Token: `https://authelia.home.lab:30443/api/oidc/token`
  - JWKS: `https://authelia.home.lab:30443/api/oidc/jwks`
  - Discovery: `https://authelia.home.lab:30443/.well-known/openid-configuration`
- One existing client: `test-client` (client_credentials, scope: `profile`)
- Client list is **hardcoded** in Terraform — needs parameterization

### Key files
| File | Purpose |
|------|---------|
| `infra/live/home/authelia/terragrunt.hcl` | OIDC enabled flag + client list (lines 42, 45–49) |
| `infra/modules/authelia/main.tf` | Authelia Helm values + client registration (lines 206–218) |
| `infra/modules/authelia/variables.tf` | Variables — add `oidc_clients` variable here |
| `infra/live/home/sonos-mcp/terragrunt.hcl` | SoniqMCP k3s deployment |
| `infra/modules/sonos-mcp/charts/soniq/` | SoniqMCP Helm chart |

### Ingress context
- Ingress controller: **Nginx** (Traefik is disabled)
- Other services (nodered, clock-server) use `nginx.ingress.kubernetes.io/auth-url` forward_auth
- SoniqMCP does NOT use ingress-layer auth (by architecture decision — in-app validation chosen instead)
- TLS: self-signed homelab CA (`homelab-tls` secret) — SoniqMCP will need CA cert available when fetching JWKS

---

## Implementation Work Required

### Repo 1: `sonos-mcp-server`

**Story A — OIDC config fields**
- Add `oidc_enabled`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri` to `SoniqConfig`
- Add env-var mappings: `SONIQ_MCP_OIDC_ENABLED`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, `SONIQ_MCP_OIDC_JWKS_URI`
- Add preflight validator: require `oidc_issuer` when `oidc_enabled=True`
- Update `.env.example`

**Story B — JWT validation middleware**
- New dependency: `python-jose[cryptography]>=3.3` (handles JWKS + RS256)
- New module: `src/soniq_mcp/auth/oidc_middleware.py`
  - ASGI middleware: reads `Authorization: Bearer`, fetches JWKS (cached), validates RS256 + claims
  - No-op passthrough when `oidc_enabled=False`
- Modify `transports/streamable_http.py`: get ASGI app from FastMCP, wrap with middleware, run Uvicorn directly
- Unit tests: `tests/unit/auth/test_oidc_middleware.py` — mock JWKS, valid/expired/tampered/missing token cases
- Smoke tests: extend HTTP smoke test — 401 without token, 200 with valid token (locally-signed test JWT)

### Repo 2: `iot-edge-k3s`

**Story C — Authelia client registration**
- Parameterize `oidc_clients` in `infra/modules/authelia/variables.tf` and `main.tf`
- Register `soniq-mcp` client (client_credentials, scopes: `openid profile`)
- Store client secret as Kubernetes Secret following existing pattern

**Story D — SoniqMCP k3s deployment update**
- Add `SONIQ_MCP_OIDC_ENABLED`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE` env vars to Helm chart
- Mount homelab CA cert so JWKS HTTPS fetch works against self-signed Authelia TLS

---

## Open Questions / Risks for BMAD Stories

1. **FastMCP ASGI API**: Must confirm `FastMCP.get_app()` or equivalent exists in 1.26.0 before writing Story B. Check: `grep -r "get_app\|create_app" .venv/lib/python3.12/site-packages/mcp/server/fastmcp/`
2. **TLS trust**: The Authelia JWKS endpoint uses a self-signed homelab CA. Need to confirm how to supply the CA cert to SoniqMCP at runtime (env var `SSL_CERT_FILE`, mounted secret, or bundled in Docker image).
3. **Token caching on client side**: The AI agent client will need to cache the Bearer token until expiry — this is out of scope for SoniqMCP itself but should be noted in docs/examples.
4. **Scope of claims validation**: Decide if `iss + aud + exp` is sufficient or if a `groups`/`roles` claim should also be checked for authorization (not just authentication).
5. **Backward compatibility**: `oidc_enabled=False` (default) must be a strict no-op — no performance impact, no extra dependencies loaded at startup.

---

## Acceptance Criteria (high-level)

- SoniqMCP with `SONIQ_MCP_OIDC_ENABLED=false` behaves identically to today (no regression)
- `SONIQ_MCP_OIDC_ENABLED=true` without `Authorization` header → `401 Unauthorized`
- Valid JWT from Authelia → tools execute normally
- Expired or tampered JWT → `401`
- `make lint` passes; full test suite green
- `SONIQ_MCP_OIDC_ENABLED=true` without `SONIQ_MCP_OIDC_ISSUER` → preflight error with clear message
