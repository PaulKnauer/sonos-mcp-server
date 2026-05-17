# Authentication Guide

SoniqMCP supports optional HTTP authentication for operators who want to protect the MCP endpoint beyond network-layer isolation. Authentication is always optional — `auth_mode=none` is the default and requires no additional configuration.

**Authentication is an HTTP transport concern only.** The `stdio` transport ignores all auth settings. If you run SoniqMCP locally via `stdio` (the default), no auth configuration is needed or applied.

---

## Auth modes at a glance

| Mode | When to use | Required env vars |
|---|---|---|
| `none` | Local stdio; trusted home-network deployments with network-layer isolation | _(none)_ |
| `static` | Simple HTTP deployments where a shared bearer token is sufficient | `SONIQ_MCP_AUTH_TOKEN` |
| `oidc` | Homelab IdP setups (e.g., Authelia, Authentik, Keycloak) with JWKS-capable issuers | `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE` |

Set the mode with:

```dotenv
SONIQ_MCP_AUTH_MODE=none     # default — no authentication
SONIQ_MCP_AUTH_MODE=static   # static bearer token
SONIQ_MCP_AUTH_MODE=oidc     # OIDC JWT validation
```

---

## `auth_mode=none` (default)

No authentication. The MCP endpoint accepts all connections without token validation.

This is the correct setting for:

- Local stdio deployments (auth is always a no-op on stdio regardless of this setting)
- Docker or Helm deployments that rely on reverse proxy authentication, network ACLs, VPN, or ingress auth for boundary protection

If you are exposing port 8000 on a home-lab server and network isolation is your protection layer, `auth_mode=none` is appropriate. See [operations.md](operations.md) for boundary protection options.

---

## `auth_mode=static`

Protects the HTTP endpoint with a shared bearer token. The server checks the `Authorization: Bearer <token>` header on every request and rejects requests with a missing or incorrect token with `401 Unauthorized`.

### Required configuration

```dotenv
SONIQ_MCP_AUTH_MODE=static
SONIQ_MCP_AUTH_TOKEN=your-secret-token-here
```

`SONIQ_MCP_AUTH_TOKEN` must be a non-empty string. Startup blocks with an actionable error if `auth_mode=static` is set but `SONIQ_MCP_AUTH_TOKEN` is absent.

### What startup does

SoniqMCP checks during startup preflight that `auth_token` is present when `auth_mode=static` is configured on an HTTP transport. If the token is missing, startup exits with:

```
auth_mode=static requires auth_token to be set.
Set SONIQ_MCP_AUTH_TOKEN to a non-empty bearer token value.
```

### What clients must send

Every MCP request to the HTTP endpoint must include:

```
Authorization: Bearer your-secret-token-here
```

Requests without this header, or with a different token value, receive `401 Unauthorized`.

### Practical constraints

Static auth uses a single shared token. There is no per-client identity, no token rotation, and no revocation mechanism beyond changing the token and restarting the server.

For a home-lab deployment where you control both the server and the client, static auth is a straightforward step up from no auth. For multi-client or externally-exposed scenarios, OIDC is better suited.

---

## `auth_mode=oidc`

Validates incoming requests against JWTs issued by an OIDC-compatible identity provider. The server fetches the provider's JWKS (public keys) and validates token signatures, audience, and expiry on each request.

### Required configuration

```dotenv
SONIQ_MCP_AUTH_MODE=oidc
SONIQ_MCP_OIDC_ISSUER=https://auth.example.com
SONIQ_MCP_OIDC_AUDIENCE=https://soniq.example.com
```

| Variable | Required | Description |
|---|---|---|
| `SONIQ_MCP_OIDC_ISSUER` | Yes | OIDC issuer URL. Must be an absolute `http://` or `https://` URL with no query string or fragment. |
| `SONIQ_MCP_OIDC_AUDIENCE` | Yes | Audience value expected in incoming JWTs. Must match what your IdP puts in the `aud` claim. |
| `SONIQ_MCP_OIDC_JWKS_URI` | No | Explicit JWKS endpoint URL. Must be HTTPS. If unset, SoniqMCP discovers it through the issuer's OpenID discovery document using the issuer path rules implemented by the server. |
| `SONIQ_MCP_OIDC_CA_BUNDLE` | No | Path to a CA certificate bundle file. Use when your JWKS endpoint uses a private CA that is not in the default trust store. |
| `SONIQ_MCP_OIDC_RESOURCE_URL` | No | OIDC resource server URL passed into the FastMCP auth settings. Leave unset unless your IdP or client flow needs an explicit resource server URL. |

### What startup does

SoniqMCP runs OIDC preflight validation before starting the HTTP server:

1. Validates the issuer URL shape (absolute `http://` or `https://`, no query or fragment)
2. Validates the optional resource URL shape if set
3. Loads the CA bundle if `SONIQ_MCP_OIDC_CA_BUNDLE` is set and validates it is a readable certificate file
4. If `SONIQ_MCP_OIDC_JWKS_URI` is absent, fetches the issuer's OpenID discovery document using the same issuer-path rules as the implementation and reads the `jwks_uri` field from the response
5. Validates that the resolved JWKS URI is an HTTPS URL
6. Probes the JWKS endpoint with a GET request and validates that the response is a valid JWKS document (JSON object with a `keys` list)

If any step fails, startup exits with actionable diagnostics. Startup does not proceed to the transport layer until the OIDC preflight passes.

### Startup error categories

OIDC preflight errors include a `Category` field that identifies the class of failure:

| Category | Meaning |
|---|---|
| `configuration` | The issuer URL, resource URL, CA bundle path, or JWKS URI has an invalid shape or cannot be loaded |
| `tls` | A TLS certificate verification failure occurred when contacting the issuer or JWKS endpoint |
| `network` | The issuer or JWKS endpoint was unreachable (DNS failure, connection refused, timeout) |
| `discovery` | The discovery document was reachable but returned invalid JSON or a missing `jwks_uri` field |

Example startup error:

```
OIDC JWKS preflight failed
URL: https://auth.example.com/.well-known/openid-configuration
Category: tls
Likely cause: TLS certificate verification failed; check CA trust configuration or set SONIQ_MCP_OIDC_CA_BUNDLE
Docs: docs/setup/troubleshooting.md#configuration-errors-at-startup
```

### CA certificate trust

SoniqMCP's OIDC verifier and preflight use the standard Python TLS trust path by default. This honors the `SSL_CERT_FILE` environment variable and the system CA store.

If your JWKS endpoint uses a private CA certificate that is not in the default store:

```dotenv
SONIQ_MCP_OIDC_CA_BUNDLE=/path/to/private-ca.pem
```

This path is scoped to the OIDC verifier and preflight only; it does not affect other TLS connections made by the server or the Sonos discovery layer.

`SSL_CERT_FILE` is the broader mechanism if you want to augment the default trust store across the entire Python process:

```bash
SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt soniq-mcp
```

---

## Stdio and auth

The `stdio` transport never enforces authentication regardless of how `SONIQ_MCP_AUTH_MODE` is set. This is intentional:

- Local stdio deployments do not open a port and do not have a network-accessible endpoint
- Setting `SONIQ_MCP_AUTH_MODE=static` or `=oidc` in a `.env` file while using stdio transport is safe — it allows the same config file to be used for both local testing and HTTP deployment without removing the auth variables between modes

Startup preflight skips all auth validation when `SONIQ_MCP_TRANSPORT=stdio`.

---

## Claude Desktop and auth constraints

Claude Desktop supports two different connection models. They have different implications for authentication.

### Local stdio (the default Claude Desktop path)

Local stdio connections are configured in `claude_desktop_config.json` with a `command` key. Claude Desktop launches SoniqMCP as a subprocess; no port is opened and no auth applies.

This is the recommended setup for single-user home use:

```json
{
  "mcpServers": {
    "soniq-mcp": {
      "command": "/absolute/path/to/sonos-mcp-server/.venv/bin/soniq-mcp",
      "env": {
        "SONIQ_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

See [stdio.md](stdio.md) for the full local setup guide.

### Remote custom connectors

Claude Desktop also supports remote MCP servers via **Settings > Connectors**. When you add a remote connector, the connection **originates from Anthropic's cloud infrastructure**, not from your local machine or LAN.

This has a direct consequence for private home-lab authentication:

- **Your private SoniqMCP endpoint is unreachable from Anthropic's cloud** unless you expose it to the public internet
- Claude Desktop remote connectors do not provide a supported way to manually attach a static `Authorization: Bearer ...` header for SoniqMCP, so `auth_mode=static` is not a practical Claude Desktop remote-connector path
- Static bearer tokens and OIDC auth both work at the HTTP protocol level, but the auth setup does not help if the server itself cannot be reached from outside your network
- Exposing your home-lab SoniqMCP server to the public internet for Claude Desktop remote connector use requires reverse proxy, firewall configuration, and a public hostname or dynamic DNS — and is not a supported or recommended configuration for this product

**The practical guidance:** Use local `stdio` for Claude Desktop. If you need a remote HTTP endpoint for other MCP clients (Home Assistant, n8n, or other integrations on your home network), configure auth for those, but do not assume Claude Desktop remote connectors can reach a private home-lab server over Anthropic's cloud without additional internet exposure work.

See [claude-desktop.md](../integrations/claude-desktop.md) for the current local vs. remote connector comparison.

---

## Deployment examples

For copy-pasteable deployment examples that wire up these env vars in Docker and Helm:

- **Docker:** [docker.md — Authentication (optional)](docker.md#4-authentication-optional)
- **Helm / k3s:** [helm.md — Authentication (optional)](helm.md#6-authentication-optional)

---

## Troubleshooting auth startup failures

Auth startup failures are reported with the same mechanism as all other configuration errors. See [troubleshooting.md#configuration-errors-at-startup](troubleshooting.md#configuration-errors-at-startup) for the recovery flow.

| Symptom | Likely cause | Fix |
|---|---|---|
| `auth_mode=static requires auth_token` | `SONIQ_MCP_AUTH_TOKEN` is missing or empty | Set `SONIQ_MCP_AUTH_TOKEN` to a non-empty token value |
| `OIDC JWKS preflight failed` + `Category: tls` | JWKS or discovery endpoint uses a CA not in the default trust store | Set `SONIQ_MCP_OIDC_CA_BUNDLE` to the path of your CA bundle, or set `SSL_CERT_FILE` |
| `OIDC JWKS preflight failed` + `Category: network` | The issuer or JWKS endpoint is not reachable at startup | Verify the endpoint is up, check DNS resolution and firewall, then restart |
| `OIDC JWKS preflight failed` + `Category: discovery` | The discovery document is missing or invalid | Check the issuer URL and verify the IdP's OIDC discovery endpoint returns valid JSON with a `jwks_uri` field |
| `OIDC JWKS preflight failed` + `Category: configuration` | Issuer URL shape, resource URL, CA bundle path, or JWKS URI is invalid | Review the error message's `Likely cause` for the specific field to correct |
| `auth_mode=oidc requires oidc_issuer to be set.` | `auth_mode=oidc` is set on HTTP but `oidc_issuer` is absent | Set `SONIQ_MCP_OIDC_ISSUER` to your IdP's issuer URL |
| `auth_mode=oidc requires oidc_audience to be set.` | `auth_mode=oidc` is set on HTTP but `oidc_audience` is absent | Set `SONIQ_MCP_OIDC_AUDIENCE` to the audience value your IdP issues for this MCP server |

For all auth startup errors, correct the indicated variable in `.env` or the deployment environment and restart the server.
