# Setup Overview

SoniqMCP supports three deployment models. Choose the one that fits your environment.

---

## Deployment model comparison

| | Local stdio | Docker (HTTP) | Helm / k3s (HTTP) |
|---|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `stdio` | `http` | `http` |
| `SONIQ_MCP_EXPOSURE` | `local` | `home-network` | `home-network` |
| Port opened | None | 8000 (configurable) | 8000 (configurable) |
| Client location | Same machine only | Any network client | Any network client |
| MCP client config | `command` field | `url` field | `url` field |
| MCP endpoint | stdin/stdout pipes | `http://<host>:8000/mcp` | `http://<host>:8000/mcp` |
| Sonos network access | Direct from machine | Container must reach Sonos subnet | Pod must reach Sonos subnet |
| Deployment model | Process launched by client | Long-running container | Long-running pod |
| Best for | Single-user local use | Linux home-lab server | Self-hosted k3s/Kubernetes |

---

## When to use each model

**Local stdio** — Start here. This is the simplest setup: the MCP client (e.g., Claude Desktop) launches SoniqMCP as a subprocess on the same machine. No ports are opened. Sonos discovery works because the process runs directly on the host network. See [stdio.md](stdio.md).

**Docker (HTTP)** — Use when you want a long-running SoniqMCP service on a Linux home-lab machine that other devices on your network can reach. The container must be on the host network (`--network=host`) for SSDP discovery to work; this works reliably on Linux, not on macOS or Windows Docker Desktop. See [docker.md](docker.md).

**Helm / k3s (HTTP)** — Use when you are already running a k3s or Kubernetes cluster on Linux at home and want SoniqMCP managed as a Helm release. Requires `hostNetwork: true` on the Deployment for Sonos SSDP discovery to work (not included in the chart by default — see the Helm guide). See [helm.md](helm.md).

---

## Setup guides

- [Local stdio setup](stdio.md) — Install, configure, and connect Claude Desktop on the same machine
- [Docker deployment](docker.md) — Build and run SoniqMCP as a Docker container
- [Helm deployment](helm.md) — Deploy SoniqMCP to a k3s or Kubernetes cluster
- [Troubleshooting](troubleshooting.md) — Common problems and fixes for all deployment models

---

## Integration guides

- [Claude Desktop](../integrations/claude-desktop.md) — Connect Claude Desktop using stdio (local) or HTTP (remote)
- [Other integrations](../integrations/README.md) — Additional MCP client integrations (planned for Epic 5)
