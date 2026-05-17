# Docker Deployment Guide

This guide walks you through building and running SoniqMCP as a Docker container, connecting a remote MCP client, and troubleshooting network issues.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Docker 24+ | `docker --version` to check |
| docker compose v2 | Bundled with Docker Desktop; `docker compose version` to verify |
| SoniqMCP source | `git clone <repo-url> sonos-mcp-server` |
| Sonos system on the same network as the Docker host | Required for Sonos device discovery |

---

## 1. Build the image

```bash
make docker-build
# Equivalent: docker build -t soniq-mcp:local .
```

This creates a local image tagged `soniq-mcp:local`.

---

## 2. Run a single container

```bash
make docker-run
# Equivalent:
docker run --rm -p 8000:8000 \
  -e SONIQ_MCP_TRANSPORT=http \
  -e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
  -e SONIQ_MCP_HTTP_PORT=8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  soniq-mcp:local
```

The server listens on `http://0.0.0.0:8000/mcp` inside the container, mapped to `http://<docker-host>:8000/mcp` on the host.

### Environment variable reference

| Variable | Default | Notes |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `http` | Must be `http` for Docker |
| `SONIQ_MCP_HTTP_HOST` | `0.0.0.0` | Must be `0.0.0.0` for container port-mapping |
| `SONIQ_MCP_HTTP_PORT` | `8000` | Port inside container; mapped to host with `-p 8000:8000` |
| `SONIQ_MCP_EXPOSURE` | `home-network` | Use `home-network` for remote access |
| `SONIQ_MCP_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SONIQ_MCP_MAX_VOLUME_PCT` | `80` | Integer 0–100; AI agents cannot exceed this |
| `SONIQ_MCP_DEFAULT_ROOM` | _(empty)_ | Optional; name of your main Sonos room |
| `SONIQ_MCP_TOOLS_DISABLED` | _(empty)_ | Comma-separated tool names to disable |
| `SONIQ_MCP_CONFIG_FILE` | _(empty)_ | Reserved for future use; leave unset |
| `SONIQ_MCP_AUTH_MODE` | `none` | `none`, `static`, or `oidc` — see [authentication.md](authentication.md) |
| `SONIQ_MCP_AUTH_TOKEN` | _(empty)_ | Bearer token for `static` mode |
| `SONIQ_MCP_OIDC_ISSUER` | _(empty)_ | OIDC issuer URL for `oidc` mode |
| `SONIQ_MCP_OIDC_AUDIENCE` | _(empty)_ | Expected JWT `aud` claim for `oidc` mode |
| `SONIQ_MCP_OIDC_JWKS_URI` | _(empty)_ | Explicit JWKS endpoint; auto-discovered if unset |
| `SONIQ_MCP_OIDC_CA_BUNDLE` | _(empty)_ | Path inside the container to a private CA bundle file |
| `SONIQ_MCP_OIDC_RESOURCE_URL` | _(empty)_ | Optional OIDC resource server URL |

Pass additional variables using `-e KEY=VALUE` flags:

```bash
docker run --rm -p 8000:8000 \
  -e SONIQ_MCP_TRANSPORT=http \
  -e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
  -e SONIQ_MCP_HTTP_PORT=8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  -e SONIQ_MCP_DEFAULT_ROOM="Living Room" \
  -e SONIQ_MCP_LOG_LEVEL=DEBUG \
  soniq-mcp:local
```

---

## 3. Run via Docker Compose

Docker Compose is the recommended approach for persistent deployments.

```bash
make docker-compose-up
# Equivalent: docker compose up --build -d
```

This builds the image (if needed) and starts the container detached.

To stop and remove the container:

```bash
make docker-compose-down
# Equivalent: docker compose down
```

The `docker-compose.yml` at the project root reads environment variables from your shell or from a `.env` file in the project directory. Copy `.env.example` to `.env` and set your values:

```bash
cp .env.example .env
# Edit .env: set SONIQ_MCP_TRANSPORT=http, SONIQ_MCP_HTTP_HOST=0.0.0.0, etc.
```

---

## 4. Authentication (optional)

Authentication is disabled by default (`auth_mode=none`). It is an HTTP transport concern only — `stdio` deployments ignore all auth settings.

The `docker-compose.yml` already passes through the auth env vars. Set the values in your `.env` file and run `docker compose config` to verify the interpolation before restarting the stack.

### Static bearer token

Add the following to your `.env` file:

```dotenv
SONIQ_MCP_AUTH_MODE=static
SONIQ_MCP_AUTH_TOKEN=change-me-to-a-strong-secret
```

Verify the resolved config before restarting:

```bash
docker compose config
# Look for SONIQ_MCP_AUTH_MODE and SONIQ_MCP_AUTH_TOKEN in the output
# to confirm your .env values are interpolated correctly.
```

Then restart:

```bash
docker compose up --build -d
```

Every client request must include `Authorization: Bearer <token>`. Startup blocks with an actionable error if `auth_mode=static` is set but `SONIQ_MCP_AUTH_TOKEN` is absent.

### OIDC JWT auth (e.g. Authelia)

Add the following to your `.env` file:

```dotenv
SONIQ_MCP_AUTH_MODE=oidc
SONIQ_MCP_OIDC_ISSUER=https://auth.example.com
SONIQ_MCP_OIDC_AUDIENCE=https://soniq.example.com
# Optional: override JWKS endpoint if auto-discovery does not work for your IdP.
# SONIQ_MCP_OIDC_JWKS_URI=https://auth.example.com/.well-known/jwks.json
```

For Authelia, register SoniqMCP as an OIDC client in your Authelia configuration and use the resulting client `audience` value for `SONIQ_MCP_OIDC_AUDIENCE`. Authelia client registration is an `iot-edge-k3s` or infra-repo concern; this repo supplies only the SoniqMCP-side env vars.

See [authentication.md](authentication.md) for startup preflight behavior and error categories.

### CA trust for OIDC with a private CA

If your JWKS endpoint uses a private CA certificate, mount the CA bundle into the container and point `SONIQ_MCP_OIDC_CA_BUNDLE` at the mounted path.

Add a volume bind-mount and the env var to your `.env`:

```dotenv
SONIQ_MCP_OIDC_CA_BUNDLE=/etc/soniq/ca.crt
```

And add the volume to your `docker-compose.yml` override or a `docker-compose.override.yml`:

```yaml
services:
  soniq-mcp:
    volumes:
      - /path/on/host/private-ca.pem:/etc/soniq/ca.crt:ro
```

`SONIQ_MCP_OIDC_CA_BUNDLE` is scoped to the OIDC verifier only. To augment the default Python TLS trust store for the entire process, use `SSL_CERT_FILE` instead (pass it as an additional `-e` flag or `.env` entry).

---

## 5. SSDP / Sonos network considerations

SoniqMCP uses SoCo, which relies on SSDP (UDP multicast on `239.255.255.250:1900`) to discover Sonos devices. Container network isolation breaks multicast routing by default.

### Linux

Add `--network=host` to put the container on the host network stack. SSDP multicast reaches the physical network interface:

```bash
docker run --rm --network=host \
  -e SONIQ_MCP_TRANSPORT=http \
  -e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
  -e SONIQ_MCP_HTTP_PORT=8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  soniq-mcp:local
```

With `--network=host`, the `-p` flag is not needed; the container's port is directly on the host.

### macOS and Windows (Docker Desktop)

`--network=host` on Docker Desktop routes to the Linux VM, not the physical host. SSDP multicast still does not reach the physical network interface. There is no simple workaround.

**Practical guidance:** Docker is best suited for Linux home-lab deployments where `--network=host` works as expected. For macOS or Windows, the local stdio setup is more reliable for same-machine use.

### Docker Compose and `network_mode: host`

The provided `docker-compose.yml` does not set `network_mode: host`. If you are on Linux and need Sonos discovery via Compose, add this to the service in your local `docker-compose.yml`:

```yaml
services:
  soniq-mcp:
    network_mode: host
```

Remove the `ports` mapping when using `network_mode: host` (ports are not needed; the container uses the host network directly).

---

## 6. Connect a remote MCP client

Once the container is running, connect an MCP client to the HTTP endpoint.

**Claude Desktop:** add the server through **Settings > Connectors** and use `http://soniq-host:8000/mcp` as the server URL.

Replace `soniq-host` with the IP address or hostname of the machine running the container (for example, `my-server.local` or the host's LAN IP).

> **Security note:** The MCP endpoint defaults to no authentication (`auth_mode=none`). Optional static or OIDC auth is available — see [authentication.md](authentication.md). The Docker deployment is intended for trusted home-network use. If you need to reach SoniqMCP from outside your local network, add boundary protection at the deployment edge (e.g., reverse proxy with authentication, network ACL, or VPN-only access) before exposing port 8000 beyond a trusted network segment. See [SECURITY.md](../../SECURITY.md) for the full security policy.

See [Claude Desktop integration guide](../integrations/claude-desktop.md) for the current local-vs-remote setup flow.

Once the connector is up, start with `ping`, `server_info`, and `list_rooms` before mutation. Then use [../prompts/example-uses.md](../prompts/example-uses.md) for phase-2 scenarios such as play modes, seek and sleep timer, room EQ, inputs, group audio, alarms, playlists, and library browsing, and keep [../prompts/command-reference.md](../prompts/command-reference.md) as the canonical named tool surface. Docker changes deployment mechanics only; the tool semantics stay transport-neutral.

---

## 7. Troubleshooting

### Container starts but cannot discover Sonos rooms

**What's happening:** SSDP multicast is not reaching the container's network interface. The default bridge network does not forward multicast traffic from the host.

**Fix (Linux):** Restart the container with `--network=host`:

```bash
docker run --rm --network=host \
  -e SONIQ_MCP_TRANSPORT=http \
  -e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
  -e SONIQ_MCP_HTTP_PORT=8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  soniq-mcp:local
```

**macOS/Windows:** `--network=host` does not solve this on Docker Desktop (routes to VM, not physical host). Use local stdio setup instead for these platforms.

---

### Port not reachable from remote client

**Symptom:** The MCP client reports a connection refused or timeout connecting to `http://<host>:8000/mcp`.

**Checks:**

1. Confirm the container is running: `docker ps`
2. Confirm the port is mapped: the `PORTS` column should show `0.0.0.0:8000->8000/tcp`
3. Check the host firewall: the Docker host must allow inbound TCP on port 8000
4. Confirm you are using `SONIQ_MCP_HTTP_HOST=0.0.0.0` (not `127.0.0.1`) — binding to `127.0.0.1` restricts connections to the container itself

---

### Environment variable validation errors

**Symptom:** Container exits immediately with a message like:

```
[soniq-mcp] configuration error: transport: Input should be 'http'
[soniq-mcp] fix the above errors and restart.
```

**Fix:** Check the environment variable values passed to the container. For Docker, use `docker inspect <container>` to see the resolved env. For Compose, run `docker compose config` to preview expanded variable substitution. Correct the offending variable and restart.

---

### Enabling debug logging

```bash
docker run --rm -p 8000:8000 \
  -e SONIQ_MCP_TRANSPORT=http \
  -e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
  -e SONIQ_MCP_HTTP_PORT=8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  -e SONIQ_MCP_LOG_LEVEL=DEBUG \
  soniq-mcp:local
```

Logs go to stdout/stderr, visible via `docker logs <container-id>` or directly in the terminal when not running detached.
