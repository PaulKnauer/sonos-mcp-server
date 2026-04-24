---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments:
  - _bmad-output/planning-artifacts/oidc-authelia-integration-assessment-2026-04-22.md
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'OIDC authentication feasibility for SoniqMCP with FastMCP 1.26.0 and Authelia homelab OIDC'
research_goals: >
  1. Determine if FastMCP 1.26.0 exposes get_app() or an ASGI hook enabling JWT middleware injection
  2. Identify how a homelab self-signed CA cert should be supplied to SoniqMCP for JWKS fetching
  3. Validate the chosen architecture (in-app JWT validation, client_credentials grant) as feasible and appropriate
  4. Assess available Python JWT/OIDC libraries for this use case
  5. Evaluate whether OIDC auth is appropriate for this project at all — does it serve real home users,
     does it align with the "simple and pleasant installation" vision, and what is the actual threat model
     for a home-LAN Sonos MCP server? Is complexity justified?
user_name: 'Paul'
date: '2026-04-22'
web_research_enabled: true
source_verification: true
---

# Research Report: OIDC Authentication Feasibility for SoniqMCP

**Date:** 2026-04-22
**Author:** Paul
**Research Type:** Technical

---

## Technical Research Scope Confirmation

**Research Topic:** OIDC authentication feasibility for SoniqMCP with FastMCP 1.26.0 and Authelia homelab OIDC

**Research Goals:**
1. Determine if FastMCP 1.26.0 exposes `get_app()` or an ASGI hook enabling JWT middleware injection
2. Identify how a homelab self-signed CA cert should be supplied to SoniqMCP for JWKS fetching
3. Validate the chosen architecture (in-app JWT validation, client_credentials grant) as feasible
4. Assess available Python JWT/OIDC libraries for this use case
5. Evaluate whether OIDC auth is appropriate for this project at all — vision alignment, real threat model, complexity vs. benefit for home users

**Technical Research Scope:**
- Architecture Analysis — FastMCP internals, ASGI middleware layering, MCP transport design
- Implementation Approaches — JWT validation patterns, JWKS caching, Python library options
- Technology Stack — FastMCP 1.26.0, Uvicorn, Starlette, Authelia OIDC, python-jose / PyJWT / authlib
- Integration Patterns — client_credentials flow, JWKS discovery, self-signed TLS trust
- Performance Considerations — JWKS cache TTL, token expiry, no-op passthrough
- Vision Alignment & Threat Model — is OIDC appropriate for home users, simpler alternatives

**Research Methodology:**
- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Direct codebase inspection of installed FastMCP package

**Scope Confirmed:** 2026-04-22

---

## Research Overview

This document investigates whether OIDC authentication is technically feasible and strategically appropriate for SoniqMCP — a home Sonos control MCP server. The research covers five areas: FastMCP 1.26.0 internals, Python JWT/OIDC libraries, Authelia OIDC integration patterns, SoniqMCP architectural fit, and vision alignment.

**The short answer:** OIDC auth is feasible, simpler than initially assessed, and well-supported by the MCP spec. FastMCP has first-class built-in auth infrastructure. However, it must remain strictly opt-in — the "simple install" vision requires that default behaviour be unchanged. A two-tier approach (static Bearer token + OIDC) serves the full user spectrum without compromising simplicity for the majority.

See the **Research Synthesis** section at the end of this document for the full executive summary, go/no-go recommendation, and story breakdown.

---

<!-- Content will be appended sequentially through research workflow steps -->

---

## Technology Stack Analysis

### CRITICAL FINDING: FastMCP 1.26.0 Built-in Auth Support

> **The assessment's "critical constraint" was incorrect.** FastMCP 1.26.0 does NOT require bypassing `app.run()` or wrapping Uvicorn manually. It has a first-class, built-in auth extensibility API.

**Verified by inspecting installed package:**
`.venv/lib/python3.12/site-packages/mcp/server/fastmcp/server.py`

FastMCP exposes a `TokenVerifier` Protocol (a single async method) that integrates directly with the `FastMCP()` constructor:

```python
# mcp/server/auth/provider.py
class TokenVerifier(Protocol):
    async def verify_token(self, token: str) -> AccessToken | None:
        """Verify a bearer token and return access info if valid."""

class AccessToken(BaseModel):
    token: str
    client_id: str
    scopes: list[str]
    expires_at: int | None = None
    resource: str | None = None  # RFC 8707 resource indicator
```

**How it wires up** (lines 978–1024 of server.py):

```python
# When token_verifier is provided, FastMCP adds BearerAuthBackend + middleware automatically
middleware = [
    Middleware(AuthenticationMiddleware, backend=BearerAuthBackend(self._token_verifier)),
    Middleware(AuthContextMiddleware),
]
# And wraps the MCP endpoint with RequireAuthMiddleware
Route("/mcp", endpoint=RequireAuthMiddleware(streamable_http_app, required_scopes, ...))
```

**Constructor usage:**
```python
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp import FastMCP

class OIDCTokenVerifier:
    async def verify_token(self, token: str) -> AccessToken | None:
        # decode JWT from Authelia, validate claims, return AccessToken or None
        ...

app = FastMCP(
    "soniq-mcp",
    auth=SomeAuthSettings(issuer_url=..., required_scopes=[]),
    token_verifier=OIDCTokenVerifier(),
)
```

`streamable_http_app()` also supports passing middleware directly via `http_app(middleware=[...])` for other customization needs.
_Source: installed package inspection, gofastmcp.com/deployment/http_

---

### Python JWT/OIDC Library Comparison

Three candidate libraries for RS256 JWT + JWKS validation:

| Library | JWKS Support | RS256 | Auto Claims Validation | Maintenance | Verdict |
|---------|-------------|-------|----------------------|-------------|---------|
| **PyJWT** | `PyJWKClient` (built-in, auto-caches) | ✅ | ✅ `jwt.decode(algorithms=["RS256"])` validates `exp`, `aud`, `iss` | Active | **Recommended** |
| **authlib** | Auto via `JsonWebKey` | ✅ | ⚠️ Manual `claims.validate()` required | Active | Viable, more verbose |
| **python-jose** | Complex x509 path | ✅ | ✅ | Slow updates | Not recommended |

**PyJWT recommended** — `PyJWKClient` fetches the JWKS endpoint, selects the correct key by `kid` header, and caches results. `jwt.decode()` validates signature, expiry, and audience atomically.

```python
from jwt import PyJWKClient
import jwt

jwks_client = PyJWKClient("https://authelia.home.lab:30443/api/oidc/jwks")
signing_key = jwks_client.get_signing_key_from_jwt(token)
payload = jwt.decode(
    token,
    signing_key.key,
    algorithms=["RS256"],
    audience="soniq-mcp",
    issuer="https://authelia.home.lab:30443",
)
```
_Source: pyjwt.readthedocs.io, renzolucioni.com/verifying-jwts-with-jwks-and-pyjwt_

---

### Self-Signed CA Certificate for JWKS Fetch

Authelia uses a self-signed homelab CA (`homelab-tls`). Python's default TLS trust store will reject the connection.

**Options (ranked by simplicity):**

1. **`SSL_CERT_FILE` env var** — Python's `ssl` and `httpx` respect this automatically. Mount the CA cert as a k3s secret, set `SSL_CERT_FILE=/path/to/ca.crt`. Zero code change.
2. **`SONIQ_MCP_OIDC_CA_BUNDLE` config field** — Pass path to `PyJWKClient(jwks_uri, ssl_context=ssl.create_default_context(cafile=ca_path))`. More explicit, avoids system-wide trust changes.
3. **`REQUESTS_CA_BUNDLE` env var** — Same as option 1 but for the `requests` library (not used here).
4. **Disable TLS verification** (`ssl_context=False`) — Never do this in production.

**Recommendation**: Option 1 for k3s deployment (standard k8s pattern), Option 2 for Docker Compose (explicit config). Add `SONIQ_MCP_OIDC_CA_BUNDLE` as an optional config field; fall back to system trust store if not set.

---

### MCP Protocol Authorization Specification

The MCP specification (draft, April 2026) now has an **official authorization framework**:

- Authorization is **OPTIONAL** per spec but SHOULD conform when implemented
- STDIO transport: **SHOULD NOT** use this spec (credentials from environment only)
- HTTP transport: **SHOULD** implement OAuth 2.1
- MCP server acts as **OAuth 2.1 resource server** accepting Bearer tokens
- Clients MUST send `Authorization: Bearer <token>` on every HTTP request
- Servers MUST validate audience claim (RFC 8707 resource indicators)
- Servers MUST return `401` for invalid/expired tokens

FastMCP's built-in auth system (`TokenVerifier`, `RequireAuthMiddleware`) is explicitly designed for this spec. Authelia + OIDC maps cleanly to the "external authorization server" model.
_Source: modelcontextprotocol.io/specification/draft/basic/authorization_

---

### Vision Alignment & Threat Model Assessment

**Threat model for home Sonos MCP:**

| Scenario | Real Risk | Auth Needed? |
|----------|-----------|-------------|
| stdio on local machine | None — process-isolated | No |
| HTTP on home LAN (192.168.x.x) | Very low — requires LAN access | Optional |
| HTTP exposed via homelab ingress (internet-facing) | Medium — anyone with URL can reach it | **Yes** |
| HTTP behind VPN-only access | Low — VPN acts as auth layer | No |

**Key insight from MCP security research:**
> "Local MCP servers running on trusted networks have a different threat model than remote servers. Authentication is primarily needed when the server is exposed beyond a trusted perimeter."
_Source: redhat.com MCP security, corgea.com MCP threats_

**Home Assistant MCP comparison:** The popular `ha-mcp` server uses a long-lived API token (static Bearer token), not OIDC. This pattern is common in home automation.

**Verdict on vision alignment:**

OIDC authentication is:
- ✅ **Technically feasible** — FastMCP has first-class support, simpler than originally assessed
- ✅ **Spec-aligned** — matches the MCP OAuth 2.1 authorization spec
- ✅ **Appropriate for homelab power users** (like Paul's k3s + Authelia setup)
- ⚠️ **NOT appropriate as a default** — contradicts the "simple and pleasant" install vision
- ⚠️ **Overkill for 95% of users** — home LAN stdio or HTTP with no auth is perfectly safe
- ✅ **Safe to add as an optional advanced feature** — `SONIQ_MCP_OIDC_ENABLED=false` default, zero impact on normal users

**Recommendation: Implement as opt-in advanced feature.** The complexity is hidden behind 3 env vars. Default behavior is unchanged. Document it in a dedicated "Advanced: OIDC Authentication" section, separate from the primary setup guide. This preserves the simple-install vision while serving advanced homelab users.

**Simpler alternative worth noting:**
FastMCP also supports `BearerTokenAuth(token="static-secret")` — a static shared secret. For users who want *some* protection without OIDC infrastructure overhead, this is a lower-friction option that could also be added. Consider offering both: static token (simple) and OIDC (enterprise/homelab).

---

### Technology Adoption Summary

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| FastMCP | 1.26.0 | ✅ Installed | `TokenVerifier` protocol available |
| PyJWT | ≥2.8 | To be added | `PyJWKClient` for JWKS |
| Authelia OIDC | Live | ✅ Running | `https://authelia.home.lab:30443` |
| MCP Auth Spec | Draft 2026 | ✅ Aligned | OPTIONAL, OAuth 2.1 |
| Python cryptography | ≥46.0.7 | ✅ Installed | Already a dep; PyJWT uses it |

---

## Integration Patterns Analysis

### IMPORTANT CLARIFICATION: `mcp` vs `fastmcp` Package Distinction

> The `gofastmcp.com` docs reference a **separate `fastmcp` package** (jlowin/fastmcp). SoniqMCP uses `mcp[cli]` (the official Anthropic/modelcontextprotocol SDK). These are **different packages** with different APIs.

| Feature | `mcp[cli]` 1.26.0 (installed) | `fastmcp` (separate package) |
|---------|-------------------------------|-------------------------------|
| `TokenVerifier` Protocol | ✅ | ✅ |
| Built-in `JWTVerifier` | ❌ (not present) | ✅ |
| `StaticTokenVerifier` | ❌ (not present) | ✅ |
| `BearerAuthBackend` | ✅ | ✅ |
| `RequireAuthMiddleware` | ✅ | ✅ |
| `AuthSettings` model | ✅ | ✅ |

**Decision**: Stay with `mcp[cli]` and implement `TokenVerifier` manually using PyJWT. This avoids introducing a new primary dependency and keeps the implementation self-contained.

---

### API Design Pattern: FastMCP Resource Server

The `mcp[cli]` 1.26.0 `TokenVerifier` is a simple Protocol:

```python
# mcp/server/auth/provider.py
class TokenVerifier(Protocol):
    async def verify_token(self, token: str) -> AccessToken | None:
        ...

class AccessToken(BaseModel):
    token: str
    client_id: str         # from JWT 'client_id' or 'sub' claim
    scopes: list[str]      # from JWT 'scp' or 'scope' claim
    expires_at: int | None # from JWT 'exp' claim (Unix timestamp)
    resource: str | None   # from JWT 'aud' claim (RFC 8707)
```

**Full wiring pattern** (where complexity actually lives — in `AuthSettings`):

```python
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

verifier = AutheliaOIDCVerifier(config)  # custom class

app = FastMCP(
    "soniq-mcp",
    auth=AuthSettings(
        issuer_url="https://authelia.home.lab:30443",
        resource_server_url="https://soniq.home.lab:30443",  # MCP server's own URL
        required_scopes=[],  # enforce at route level if needed
    ),
    token_verifier=verifier,
)
```

When `token_verifier` is set, FastMCP automatically:
1. Adds `BearerAuthBackend` + `AuthenticationMiddleware` to the Starlette app
2. Wraps the `/mcp` endpoint with `RequireAuthMiddleware`
3. Returns `401 Unauthorized` with `WWW-Authenticate` header on missing/invalid tokens
_Source: installed package source inspection, gofastmcp.com/servers/auth/token-verification_

---

### Custom TokenVerifier Implementation: Authelia OIDC

```python
import ssl
import jwt
from jwt import PyJWKClient, PyJWTError
from mcp.server.auth.provider import AccessToken, TokenVerifier

class AutheliaOIDCVerifier:
    """TokenVerifier that validates RS256 JWTs from Authelia via JWKS."""

    def __init__(self, jwks_uri: str, issuer: str, audience: str, ca_bundle: str | None = None):
        ssl_ctx = None
        if ca_bundle:
            ssl_ctx = ssl.create_default_context(cafile=ca_bundle)
        # PyJWKClient caches keys; ssl_context supported since PyJWT 2.8.0
        self._jwks_client = PyJWKClient(jwks_uri, ssl_context=ssl_ctx)
        self._issuer = issuer
        self._audience = audience

    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
            )
            # Extract scopes from Authelia's 'scp' claim (space-sep string or list)
            raw_scopes = payload.get("scp", payload.get("scope", ""))
            scopes = raw_scopes.split() if isinstance(raw_scopes, str) else raw_scopes
            return AccessToken(
                token=token,
                client_id=payload.get("client_id", payload.get("sub", "unknown")),
                scopes=scopes,
                expires_at=payload.get("exp"),
            )
        except PyJWTError:
            return None  # invalid/expired/tampered → 401
```

**Key notes:**
- `PyJWKClient` auto-selects the correct key by `kid` header; auto-caches; refreshes on rotation
- `jwt.decode()` validates signature, `exp`, `aud`, `iss` atomically — one call does everything
- Custom `ssl_context` required for Authelia's self-signed homelab CA
- Returning `None` from `verify_token` → FastMCP returns `401 Unauthorized`
- No state stored; verifier is safe for async concurrent use
_Source: pyjwt.readthedocs.io, github.com/jpadilla/pyjwt/pull/891_

---

### Authelia client_credentials Flow: Exact Integration

**Client registration requirement** (Authelia-specific):
Authelia's bearer token usage requires the special scope `authelia.bearer.authz`. The audience must exactly match the resource server URL.

```yaml
# Authelia client config (in Terraform/Helm values)
- client_id: soniq-mcp
  client_name: SoniqMCP
  grant_types: ['client_credentials']
  scopes:
    - 'authelia.bearer.authz'
    - 'openid'
    - 'profile'
  audience:
    - 'https://soniq.home.lab:30443'   # must match resource_server_url
  token_endpoint_auth_method: 'client_secret_basic'
  authorization_policy: 'one_factor'
```

**Token acquisition by AI agent client:**
```bash
curl -s -X POST https://authelia.home.lab:30443/api/oidc/token \
  --cacert /path/to/homelab-ca.crt \
  -H "Authorization: Basic $(echo -n 'soniq-mcp:CLIENT_SECRET' | base64)" \
  -d "grant_type=client_credentials" \
  -d "scope=authelia.bearer.authz" \
  -d "audience=https://soniq.home.lab:30443"
# → {"access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600}
```

**Subsequent MCP request with Bearer token:**
```bash
curl -X POST https://soniq.home.lab:30443/mcp \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

**Authelia JWT claims** (relevant to validation):
- `iss`: `https://authelia.home.lab:30443`
- `aud`: `["https://soniq.home.lab:30443"]`
- `sub`: Authelia client ID (`soniq-mcp`)
- `client_id`: `soniq-mcp`
- `scp`: space-separated scopes
- `exp`: Unix timestamp (default: 1 hour for client_credentials)
_Source: authelia.com/integration/openid-connect/oauth-2.0-bearer-token-usage/_

---

### SSL/TLS Integration Pattern for Homelab CA

PyJWT's `PyJWKClient` supports custom SSL contexts since version 2.8.0 (PR #891). Three patterns:

**Pattern 1 — Config field `SONIQ_MCP_OIDC_CA_BUNDLE` (recommended for k8s):**
```python
# In verifier init
if ca_bundle_path := config.oidc_ca_bundle:
    ssl_ctx = ssl.create_default_context(cafile=ca_bundle_path)
    jwks_client = PyJWKClient(jwks_uri, ssl_context=ssl_ctx)
```
Mount the homelab CA cert as a k8s ConfigMap, set `SSL_CERT_FILE` env var or custom config var.

**Pattern 2 — `SSL_CERT_FILE` env var (simplest, zero code change):**
```bash
# Kubernetes deployment env
- name: SSL_CERT_FILE
  value: /etc/ssl/certs/homelab-ca.crt
```
Python's `ssl` module and most HTTP clients check this automatically.

**Pattern 3 — Docker Compose `volumes` mount:**
```yaml
volumes:
  - ./certs/homelab-ca.crt:/etc/ssl/certs/homelab-ca.crt:ro
environment:
  SSL_CERT_FILE: /etc/ssl/certs/homelab-ca.crt
```
_Source: github.com/jpadilla/pyjwt/pull/891_

---

### Static Bearer Token as Simpler Alternative

For the 95% of users who don't need OIDC, FastMCP's architecture supports a much simpler auth option. The same `TokenVerifier` protocol can back a static shared-secret pattern:

```python
class StaticBearerVerifier:
    def __init__(self, expected_token: str):
        self._token = expected_token

    async def verify_token(self, token: str) -> AccessToken | None:
        if token == self._token:
            return AccessToken(token=token, client_id="static-client", scopes=[])
        return None
```

This is a `5-minute` implementation vs OIDC's multi-component setup. Recommendation: **offer both as options** in SoniqMCP, selectable via config:
- `SONIQ_MCP_AUTH_MODE=none` (default) — no auth
- `SONIQ_MCP_AUTH_MODE=static` — static Bearer token (`SONIQ_MCP_AUTH_TOKEN=<secret>`)
- `SONIQ_MCP_AUTH_MODE=oidc` — full OIDC JWT validation (`SONIQ_MCP_OIDC_*` vars)
_Source: mcpplaygroundonline.com/blog/mcp-server-oauth-authentication-guide, github.com/modelcontextprotocol/modelcontextprotocol/discussions/1247_

---

### Integration Security Patterns Summary

| Pattern | Complexity | Use Case | Home User Fit |
|---------|-----------|----------|---------------|
| No auth (current) | None | Trusted LAN / stdio | ✅ Default for home |
| Static Bearer token | Very low | Single trusted client | ✅ Good for basic protection |
| OIDC `client_credentials` | Medium | Homelab / multi-client | ✅ Opt-in for advanced users |
| OAuth2 PKCE flow | High | Multi-user browser apps | ❌ Overkill for Sonos MCP |
| mTLS | Very high | Enterprise / zero-trust | ❌ Not appropriate |

---

## Architectural Patterns and Design

### System Architecture: Where Auth Lives in SoniqMCP

Auth must slot cleanly into SoniqMCP's existing layered architecture without touching the tool or service layers. The key principle: **auth is a transport concern, not a domain concern**.

```
Current SoniqMCP layers:
┌─────────────────────────────────┐
│  MCP Tools (17 modules)         │  ← domain layer, no change
├─────────────────────────────────┤
│  Services (12 modules)          │  ← business logic, no change
├─────────────────────────────────┤
│  SoniqConfig (Pydantic)         │  ← ADD auth_mode + oidc_* fields
├─────────────────────────────────┤
│  create_server() in server.py   │  ← ADD TokenVerifier wiring here
├─────────────────────────────────┤
│  FastMCP (mcp[cli] 1.26.0)      │  ← handles middleware internally
├─────────────────────────────────┤
│  HTTP Transport / stdio         │  ← no change to transport runner
└─────────────────────────────────┘
```

**The only files that change** for auth feature delivery:

| File | Change |
|------|--------|
| `src/soniq_mcp/config/models.py` | Add `auth_mode`, `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle` fields |
| `src/soniq_mcp/config/loader.py` | Add `SONIQ_MCP_AUTH_*` env-var mappings |
| `src/soniq_mcp/config/validation.py` | Add preflight checks for auth config consistency |
| `src/soniq_mcp/server.py` | Wire `TokenVerifier` + `AuthSettings` into `FastMCP()` constructor |
| `src/soniq_mcp/auth/` | New module: `verifiers.py` (StaticBearerVerifier + OIDCVerifier) |
| `pyproject.toml` | Add `PyJWT[cryptography]>=2.8` dep |
| `.env.example` | Document new env vars |

**No changes needed to**: transport runners, tool modules, service layer, adapters, smoke tests structure.
_Source: github.com/modelcontextprotocol/python-sdk/issues/194, starlette.io/middleware/_

---

### Design Principles

**1. Backward Compatibility as Invariant**

`auth_mode=none` is the hardcoded default. All existing behavior is fully preserved. The auth code path is only entered when explicitly opted in. This satisfies the "simple install" vision: users who don't set auth env vars notice nothing.

```python
# server.py create_server() — clean branch
def create_server(config: SoniqConfig) -> FastMCP:
    kwargs = {"host": config.http_host, "port": config.http_port}
    if config.auth_mode != AuthMode.NONE:
        kwargs["auth"] = _build_auth_settings(config)
        kwargs["token_verifier"] = _build_token_verifier(config)
    app = FastMCP("soniq-mcp", **kwargs)
    register_all(app, config)
    return app
```

**2. Single Responsibility: Config Validates Itself**

Auth config validation belongs in `SoniqConfig`'s `@model_validator`, keeping the server factory clean:

```python
@model_validator(mode="after")
def validate_auth_config(self) -> "SoniqConfig":
    if self.auth_mode == AuthMode.STATIC and not self.auth_token:
        raise ValueError("SONIQ_MCP_AUTH_TOKEN required when auth_mode=static")
    if self.auth_mode == AuthMode.OIDC and not self.oidc_issuer:
        raise ValueError("SONIQ_MCP_OIDC_ISSUER required when auth_mode=oidc")
    if self.auth_mode == AuthMode.OIDC and not self.oidc_audience:
        raise ValueError("SONIQ_MCP_OIDC_AUDIENCE required when auth_mode=oidc")
    return self
```

**3. Transport Parity**

Auth is only meaningful on HTTP transport. When `transport=stdio`, the auth verifier is never constructed regardless of config. This is already implied by FastMCP's design (auth applies to `streamable_http_app()` only), but should be explicitly validated: warn if `auth_mode != none` and `transport == stdio`.
_Source: modelcontextprotocol.io/specification/draft/basic/authorization — "STDIO transport SHOULD NOT follow this specification"_

---

### Scalability and Performance Patterns

**JWKS Caching Architecture**

`PyJWKClient` maintains an in-memory JWKS cache keyed by `kid`. Cache is refreshed when a token arrives with an unknown `kid` (handles Authelia key rotation). For a single-instance SoniqMCP server (typical homelab deployment), this is fully sufficient — no Redis or external cache needed.

```
Request → BearerAuthBackend.authenticate()
              ↓
          PyJWKClient.get_signing_key_from_jwt(token)
              ↓ (cache hit, ~0.1ms)         ↓ (cache miss, ~50ms network)
          jwt.decode()                  fetch JWKS from Authelia
              ↓                              ↓
          AccessToken returned          update cache, then decode
```

**Token Expiry**: Authelia default for `client_credentials` access tokens is 1 hour. AI agent clients should cache their Bearer token and refresh proactively (e.g., at 50% of `expires_in`). This is out-of-scope for SoniqMCP itself but should be documented.

**Performance impact of auth (estimated)**:
- `auth_mode=none`: zero overhead (no code path entered)
- `auth_mode=static`: ~0.1ms (string comparison)
- `auth_mode=oidc` (cache hit): ~0.5ms (JWKS lookup + RS256 verify)
- `auth_mode=oidc` (cache miss): ~50-100ms one-time per key rotation

All well within acceptable latency for an MCP tool call over HTTP.

---

### Deployment Architecture

**k3s / Helm Deployment (Paul's homelab)**

```yaml
# Helm values additions
env:
  SONIQ_MCP_AUTH_MODE: oidc
  SONIQ_MCP_OIDC_ISSUER: https://authelia.home.lab:30443
  SONIQ_MCP_OIDC_AUDIENCE: https://soniq.home.lab:30443
  SSL_CERT_FILE: /etc/ssl/certs/homelab-ca.crt

volumes:
  - name: homelab-ca
    configMap:
      name: homelab-ca-cert   # created from homelab-tls secret

volumeMounts:
  - name: homelab-ca
    mountPath: /etc/ssl/certs/homelab-ca.crt
    subPath: ca.crt           # subPath avoids overwriting existing /etc/ssl/certs/
    readOnly: true
```

**ConfigMap creation** (from existing `homelab-tls` secret):
```bash
kubectl get secret homelab-tls -n cert-manager -o jsonpath='{.data.ca\.crt}' | \
  base64 -d > /tmp/homelab-ca.crt
kubectl create configmap homelab-ca-cert --from-file=ca.crt=/tmp/homelab-ca.crt \
  -n sonos-mcp
```
_Source: paraspatidar.medium.com (k8s CA cert mount pattern), kubernetes.io/docs/tasks/tls/_

**Docker Compose Deployment (community users)**

```yaml
environment:
  SONIQ_MCP_AUTH_MODE: oidc
  SONIQ_MCP_OIDC_ISSUER: https://authelia.example.com
  SONIQ_MCP_OIDC_AUDIENCE: https://mcp.example.com
  SONIQ_MCP_OIDC_CA_BUNDLE: /certs/ca.crt   # explicit path override
volumes:
  - ./certs/ca.crt:/certs/ca.crt:ro
```

**stdio Deployment (most home users — unchanged)**
```bash
SONIQ_MCP_TRANSPORT=stdio  # no auth env vars needed; auth_mode defaults to none
```

---

### Security Architecture Patterns

**Defence in Depth for Homelab Exposure**

For Paul's specific deployment (Authelia + k3s + Nginx ingress), the security stack layering is:

```
Internet
    ↓
Nginx Ingress (TLS termination, rate limiting)
    ↓
[Optional: Authelia forward_auth for browser clients]
    ↓
SoniqMCP HTTP endpoint
    ↓
Bearer JWT validation (in-app, TokenVerifier)
    ↓
Tool execution
```

The in-app JWT validation is the correct layer for AI agent clients (Bearer token, not browser cookie). The Nginx ingress handles TLS and can provide rate limiting as a complementary control.

**Token Audience Binding (RFC 8707)**

`AuthSettings.resource_server_url` must be set to SoniqMCP's own URL. This binds issued tokens to this specific resource server — tokens issued for other services can't be reused against SoniqMCP. The MCP spec mandates this validation.

**Secret Management**

- OIDC client secret lives in Authelia's k8s Secret (`authelia-secrets`) — never in SoniqMCP
- SoniqMCP is a pure resource server: it only needs the `issuer` URL and its own audience string (both non-sensitive)
- The static token (if `auth_mode=static`) should be treated as a secret and injected via k8s Secret + env var, not hardcoded

---

### SDK Stability Risk

The `mcp` Python SDK is evolving rapidly. The v2 roadmap may change `mcp.server.auth` interfaces. The custom `TokenVerifier` implementation should be isolated in `src/soniq_mcp/auth/verifiers.py` with a thin adapter to the MCP protocol — making future interface changes a one-file update rather than a broad refactor.

**Mitigation**: Pin `mcp[cli]` to a specific version (already done: `>=1.26.0`), add a lower-bound floor to prevent accidental breaking upgrades. Consider `mcp[cli]>=1.26.0,<2.0.0` once v2 ships.
_Source: dev.to/peytongreen_dev/mcp-dev-summit-2026, workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026_

---

## Implementation Approaches and Technology Adoption

### Dependency Changes

**`pyproject.toml` addition** (one line):
```toml
dependencies = [
    "cryptography>=46.0.7",   # already present — PyJWT uses this for RS256
    "mcp[cli]>=1.26.0",
    "PyJWT>=2.8",             # ADD: JWKS client + RS256 decode; ssl_context since 2.8.0
    "python-dotenv>=1.2.2",
    "soco>=0.30.14",
]
```

`cryptography` is already a production dependency — `PyJWT` finds it automatically and enables RSA algorithms. No `PyJWT[cryptography]` extras syntax needed; the dep is already satisfied.

**No new dev dependencies** — `anyio` (already transitive from `mcp[cli]`) covers async test execution via `@pytest.mark.anyio`.
_Source: pyjwt.readthedocs.io/en/latest/installation.html_

---

### Adoption Strategy: Gradual Opt-In

The feature is introduced as strictly additive. Three phases:

| Phase | Scope | Risk |
|-------|-------|------|
| 1 — Config + validation | Add `auth_mode` enum + new fields to `SoniqConfig`; preflight checks | Zero runtime risk; config-only |
| 2 — Verifier module | `src/soniq_mcp/auth/verifiers.py` + unit tests; wiring in `server.py` | Isolated to new module; `auth_mode=none` path untouched |
| 3 — iot-edge-k3s | Authelia client registration + Helm values | Infrastructure only; SoniqMCP unchanged |

**Feature flag**: `SONIQ_MCP_AUTH_MODE` defaults to `none`. All existing tests, Docker images, and deployment configs continue working without modification.

---

### Development Workflows and Tooling

**Auth module structure** (new files only):
```
src/soniq_mcp/
└── auth/
    ├── __init__.py          # exports: build_token_verifier()
    └── verifiers.py         # StaticBearerVerifier, OIDCVerifier classes
```

**`server.py` change** (addition only, ~10 lines):
```python
from soniq_mcp.auth import build_token_verifier
from mcp.server.auth.settings import AuthSettings

def create_server(config: SoniqConfig) -> FastMCP:
    kwargs: dict = {"host": config.http_host, "port": config.http_port}
    if config.auth_mode.value != "none":
        kwargs["token_verifier"] = build_token_verifier(config)
        kwargs["auth"] = AuthSettings(
            issuer_url=config.oidc_issuer or "https://placeholder.local",
            resource_server_url=config.oidc_resource_url,
        )
    app = FastMCP("soniq-mcp", **kwargs)
    register_all(app, config)
    return app
```

**Existing `make lint`** (`ruff + mypy`) will catch type errors in new code automatically. No CI changes needed.

---

### Testing and Quality Assurance

**Unit test approach** — mock JWKS, no network calls:

```python
# tests/unit/auth/test_verifiers.py
from __future__ import annotations
import time
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import jwt
from unittest.mock import MagicMock, patch
from soniq_mcp.auth.verifiers import OIDCVerifier

ISSUER = "https://authelia.home.lab:30443"
AUDIENCE = "soniq-mcp"

@pytest.fixture
def rsa_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    return private_key, private_key.public_key()

@pytest.fixture
def valid_token(rsa_key_pair):
    private_key, _ = rsa_key_pair
    return jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "sub": "soniq-mcp",
         "client_id": "soniq-mcp", "scp": "authelia.bearer.authz",
         "exp": int(time.time()) + 3600},
        private_key, algorithm="RS256"
    )

class TestOIDCVerifier:
    @pytest.mark.anyio
    async def test_valid_token_returns_access_token(self, rsa_key_pair, valid_token):
        _, public_key = rsa_key_pair
        mock_signing_key = MagicMock()
        mock_signing_key.key = public_key
        with patch.object(OIDCVerifier, "_jwks_client") as mock_client:
            mock_client.get_signing_key_from_jwt.return_value = mock_signing_key
            verifier = OIDCVerifier(jwks_uri="...", issuer=ISSUER, audience=AUDIENCE)
            result = await verifier.verify_token(valid_token)
        assert result is not None
        assert result.client_id == "soniq-mcp"

    @pytest.mark.anyio
    async def test_missing_token_returns_none(self):
        verifier = OIDCVerifier(jwks_uri="...", issuer=ISSUER, audience=AUDIENCE)
        result = await verifier.verify_token("not-a-jwt")
        assert result is None

    @pytest.mark.anyio
    async def test_expired_token_returns_none(self, rsa_key_pair):
        private_key, public_key = rsa_key_pair
        expired = jwt.encode(
            {"iss": ISSUER, "aud": AUDIENCE, "exp": int(time.time()) - 60},
            private_key, algorithm="RS256"
        )
        # ... mock and verify returns None
```

**Smoke test extension** — subprocess server with `SONIQ_MCP_AUTH_MODE=static`:
```python
# Extend tests/smoke/streamable_http/test_streamable_http_smoke.py
def test_missing_auth_header_returns_401(http_server_proc_with_auth):
    resp = requests.post(f"http://{_TEST_HOST}:{port}/mcp", json={...})
    assert resp.status_code == 401

def test_valid_bearer_token_succeeds(http_server_proc_with_auth, test_token):
    resp = requests.post(..., headers={"Authorization": f"Bearer {test_token}"})
    assert resp.status_code == 200
```

For smoke tests, use `auth_mode=static` with a known test token — no Authelia dependency in CI.
_Source: fmpm.dev/mocking-auth0-tokens, pyjwt.readthedocs.io_

---

### Deployment and Operations Practices

**iot-edge-k3s changes** (Authelia dynamic registration is NOT supported — must pre-configure):

```hcl
# infra/live/home/authelia/terragrunt.hcl — add to oidc_clients list
{
  client_id   = "soniq-mcp"
  client_name = "SoniqMCP"
  grant_types = ["client_credentials"]
  scopes      = ["authelia.bearer.authz", "openid", "profile"]
  audience    = ["https://soniq.home.lab:30443"]
  token_endpoint_auth_method = "client_secret_basic"
  authorization_policy = "one_factor"
}
```

Client secret is **hashed** in Authelia config and stored as a k8s Secret. The AI agent client needs the plain secret; SoniqMCP itself never needs it.

**Secret rotation**: Authelia client secrets can be rotated without SoniqMCP changes — only the AI agent client config needs updating.

**Observability**: When `auth_mode=oidc`, log auth failures at `WARNING` level with token prefix (never full token). Successful auth at `DEBUG`. Invalid tokens never leak claims into logs.

---

### Risk Assessment and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `mcp.server.auth` API changes in v2 | Medium | Medium | Isolate in `auth/verifiers.py`; cap dep `<2.0.0` once v2 ships |
| JWKS fetch fails (Authelia down) | Low | High when OIDC enabled | Cache last valid JWKS; add startup preflight check; document fallback |
| Self-signed CA cert not trusted | Medium | High | Test with `curl --cacert` before deployment; document `SSL_CERT_FILE` clearly |
| `authelia.bearer.authz` scope missing | Medium | High | Document exact client config; include in BMAD story AC |
| Token replay between services | Low | Medium | Audience binding enforced; tokens are resource-specific |
| Accidental auth bypass in tests | Low | Low | `auth_mode=none` is default; smoke tests explicitly opt-in |

---

## Technical Research Recommendations

### Implementation Roadmap

**Phase 1 — SoniqMCP changes** (sonos-mcp-server repo):

1. **Story A: Auth config fields** — `SoniqConfig` model + env-var mappings + preflight validation
   - New fields: `auth_mode` (enum: none/static/oidc), `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, `oidc_resource_url`
   - New env vars: `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_*`
   - Validator: warn if `auth_mode != none` and `transport == stdio`

2. **Story B: Auth verifiers + server wiring** — `src/soniq_mcp/auth/` module + `server.py` update
   - `StaticBearerVerifier`: token string comparison
   - `OIDCVerifier`: PyJWT JWKS + RS256
   - `build_token_verifier(config)` factory
   - `create_server()` wiring with `TokenVerifier` + `AuthSettings`
   - Unit tests + smoke test extension
   - Update `.env.example` and `docs/setup/operations.md`

**Phase 2 — Infrastructure changes** (iot-edge-k3s repo):

3. **Story C: Authelia client registration** — parameterize Terraform module
   - Add `oidc_clients` variable to `infra/modules/authelia/variables.tf`
   - Update `infra/modules/authelia/main.tf` to iterate clients
   - Register `soniq-mcp` client in `infra/live/home/authelia/terragrunt.hcl`
   - Store client secret as k8s Secret

4. **Story D: SoniqMCP k8s deployment update** — Helm chart + CA cert
   - Add `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_OIDC_*` env vars to Helm chart values
   - Create `homelab-ca-cert` ConfigMap from existing `homelab-tls` secret
   - Mount CA cert with `subPath`, set `SSL_CERT_FILE`

---

### Technology Stack Recommendations

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| JWT library | `PyJWT>=2.8` | JWKS client built-in, ssl_context support, RS256, already has `cryptography` dep |
| Auth mode config | `AuthMode` enum (none/static/oidc) | Clean validation, explicit, extensible |
| CA cert delivery | `SSL_CERT_FILE` env + ConfigMap | Standard Python pattern, zero code for k8s |
| Test token generation | `cryptography` + `jwt.encode()` inline | No new test dep; `cryptography` already present |
| Authelia client config | Pre-registered via Terraform | Dynamic registration not supported in Authelia |

---

### Success Metrics

- `SONIQ_MCP_AUTH_MODE` not set → zero behavioural change (regression tests pass)
- `auth_mode=static` with wrong token → `401` within 1ms
- `auth_mode=oidc` with valid Authelia JWT → tool call succeeds, JWKS cache hit < 1ms
- `auth_mode=oidc` with expired token → `401`
- `make lint` passes (`ruff`, `mypy`) on all new auth code
- All existing unit + smoke tests green
- New auth unit tests achieve 100% branch coverage of `verifiers.py`
- `SONIQ_MCP_OIDC_ENABLED=true` without issuer → clear preflight error message (not a crash)

---

## Research Synthesis

### Executive Summary

SoniqMCP currently has no authentication — by design, scoped to trusted home LAN deployment. This research investigated whether adding Authelia OIDC authentication is feasible and whether doing so is consistent with the project's vision of a "simple and pleasant" install experience.

**Finding 1: Technically feasible, and simpler than anticipated.**
The original assessment identified a "critical constraint" — that FastMCP's `app.run()` doesn't expose ASGI middleware hooks. This was incorrect. `mcp[cli]` 1.26.0 has a first-class `TokenVerifier` Protocol that integrates directly with the `FastMCP()` constructor. No transport-layer bypass, no Uvicorn wrapping. The entire implementation is ~30 lines in one new module, one new field in `server.py`, and a dependency addition (`PyJWT>=2.8`). The `cryptography` package, already a production dependency, handles RS256 natively.

**Finding 2: Vision alignment requires opt-in architecture.**
The MCP specification (April 2026 draft) confirms that authorization is **OPTIONAL** for HTTP transports and **not applicable** for stdio. For the overwhelming majority of SoniqMCP users — running stdio on a single machine or HTTP on a trusted home LAN — authentication adds zero value and meaningful friction. Adding it as a default would directly contradict the project's install philosophy. As a strictly opt-in feature (off by default, three env vars to enable), it serves the advanced homelab segment without impacting anyone else.

**Finding 3: A two-tier auth model better serves the user spectrum.**
Beyond OIDC, FastMCP's `TokenVerifier` protocol also enables a much simpler static Bearer token option (~5 lines of code). Offering both `auth_mode=static` and `auth_mode=oidc` allows home users who want basic protection to avoid running a full OIDC stack, while homelab users with Authelia can use the full JWT flow. The default remains `auth_mode=none`.

---

### Go / No-Go Recommendation

**✅ GO — with the opt-in constraint as a non-negotiable**

Implement auth as a new Phase 3 epic across both repos. The work is well-scoped, the risk is low (backward-compatible by design), and it directly serves the homelab use case Paul has running. The implementation is materially simpler than the original assessment suggested.

**Hard constraints:**
- `SONIQ_MCP_AUTH_MODE` defaults to `none` — all current behaviour unchanged
- Auth is meaningless on stdio transport; emit a preflight warning (not error) if misconfigured
- Docs must clearly position auth as an "Advanced" topic, not a standard setup step
- CI/smoke tests use `auth_mode=static` only — no Authelia dependency in the test environment

---

### Corrected Assessment vs. Original

| Item | Original Assessment | Research Finding |
|------|---------------------|-----------------|
| FastMCP ASGI hooks | ❌ "Not exposed — must bypass `app.run()`" | ✅ `TokenVerifier` Protocol + `FastMCP(token_verifier=...)` constructor — no bypass needed |
| Implementation complexity | High — custom Uvicorn + middleware wrapping | Low — 30-line verifier class, ~10 lines in `server.py` |
| JWT library | `python-jose` suggested | `PyJWT>=2.8` recommended (`PyJWKClient` + `ssl_context` built-in) |
| Self-signed CA | Unknown | `PyJWKClient(ssl_context=...)` since PyJWT 2.8.0; k8s: ConfigMap + `SSL_CERT_FILE` |
| Auth appropriateness | Assumed yes | Conditional — appropriate as opt-in advanced feature only |

---

### Key Technical Facts (verified)

| Fact | Confidence | Source |
|------|-----------|--------|
| FastMCP `TokenVerifier` Protocol exists in `mcp` 1.26.0 | ✅ High | Package source inspection |
| `JWTVerifier` class is NOT in `mcp` 1.26.0 (it's in separate `fastmcp` package) | ✅ High | Package source inspection |
| `PyJWKClient` supports custom `ssl_context` since PyJWT 2.8.0 | ✅ High | GitHub PR #891 |
| MCP spec: authorization is OPTIONAL for HTTP, not applicable for stdio | ✅ High | modelcontextprotocol.io |
| Authelia dynamic client registration: NOT supported (must pre-configure) | ✅ High | Authelia GitHub discussions |
| Authelia `client_credentials` requires `authelia.bearer.authz` scope | ✅ High | Authelia docs |
| `cryptography>=46.0.7` already in SoniqMCP prod deps | ✅ High | pyproject.toml |
| `@pytest.mark.anyio` is the existing async test pattern | ✅ High | Tests source inspection |

---

### Story Breakdown (BMAD-ready)

**Epic: Optional Authentication for SoniqMCP HTTP Transport**

**Repo: `sonos-mcp-server`**

| Story | Title | Key Deliverable |
|-------|-------|----------------|
| A | Auth config fields | `auth_mode` enum + `auth_token`/`oidc_*` fields in `SoniqConfig`; env-var mappings; preflight validation |
| B | Auth verifiers + server wiring | `src/soniq_mcp/auth/verifiers.py` (Static + OIDC); `server.py` wiring; unit tests; smoke test extension; docs |

**Repo: `iot-edge-k3s`**

| Story | Title | Key Deliverable |
|-------|-------|----------------|
| C | Authelia client registration | `var.oidc_clients` in Terraform module; `soniq-mcp` client registered; k8s Secret for client secret |
| D | SoniqMCP k8s deployment update | Helm chart env vars; CA cert ConfigMap + `subPath` mount; `SSL_CERT_FILE` env var |

---

### Source Bibliography

- [Authorization — Model Context Protocol](https://modelcontextprotocol.io/specification/draft/basic/authorization)
- [HTTP Deployment — FastMCP (gofastmcp.com)](https://gofastmcp.com/deployment/http)
- [Token Verification — FastMCP (gofastmcp.com)](https://gofastmcp.com/servers/auth/token-verification)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/en/latest/)
- [PyJWT ssl_context PR #891](https://github.com/jpadilla/pyjwt/pull/891)
- [OAuth 2.0 Bearer Token Usage — Authelia](https://www.authelia.com/integration/openid-connect/oauth-2.0-bearer-token-usage/)
- [OpenID Connect 1.0 Clients — Authelia](https://www.authelia.com/configuration/identity-providers/openid-connect/clients/)
- [Authelia OIDC dynamic client registration discussion](https://github.com/authelia/authelia/discussions/7304)
- [MCP server OAuth 2.1 guide (2026)](https://mcpplaygroundonline.com/blog/mcp-server-oauth-authentication-guide)
- [MCP security risks and controls — Red Hat](https://www.redhat.com/en/blog/model-context-protocol-mcp-understanding-security-risks-and-controls)
- [Add SSL/TLS Certificate to Kubernetes Pod trusted CA store](https://paraspatidar.medium.com/add-ssl-tls-certificate-or-pem-file-to-kubernetes-pod-s-trusted-root-ca-store-7bed5cd683d)
- [Mocking Auth0 Tokens in Python](https://fmpm.dev/mocking-auth0-tokens)
- [Best Practices for remote MCP bearer token auth (modelcontextprotocol discussions)](https://github.com/modelcontextprotocol/modelcontextprotocol/discussions/1247)

---

**Research Completion Date:** 2026-04-23
**Research Period:** 2026-04-22 — 2026-04-23
**Source Verification:** All technical facts cited with current sources or direct package inspection
**Confidence Level:** High — key claims verified by direct `mcp[cli]` 1.26.0 source inspection

_This document is authoritative for SoniqMCP Phase 3 planning. Feed into BMAD epic creation as primary context document._
