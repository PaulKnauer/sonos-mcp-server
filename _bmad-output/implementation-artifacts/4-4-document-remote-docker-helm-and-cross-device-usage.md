# Story 4.4: Document Remote, Docker, Helm, and Cross-Device Usage

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want deployment guides for remote and self-hosted use,
so that I can choose the right runtime model for my environment.

## Acceptance Criteria

1. Given the remote and deployment features exist, when a user reads the documentation, then they can follow separate guides for Docker, Helm, and cross-device/home-network usage.
2. Given a user wants to connect an MCP client to the remote server, when they read the docs, then MCP client configuration examples are provided for the supported remote patterns.
3. Given a user reads the docs, when comparing local and remote operation, then the docs explain the difference between local `stdio` and remote `Streamable HTTP`.
4. Given a remote deployment problem, when a user reads the troubleshooting section, then the docs include representative networking and troubleshooting guidance for remote scenarios.

## Tasks / Subtasks

- [x] Create `docs/setup/docker.md` — Docker deployment guide (AC: 1, 3, 4)
  - [x] Prerequisites table: Docker, docker-compose, Sonos network access
  - [x] Build: `make docker-build`
  - [x] Run single container: `make docker-run` with env var configuration table
  - [x] Run via Compose: `make docker-compose-up` / `make docker-compose-down`
  - [x] SSDP/Sonos network section: explain multicast limitation, `--network=host` on Linux, macOS/Windows caveat
  - [x] Remote MCP client connection example: Claude Desktop `url`-based config (AC: 2)
  - [x] Troubleshooting: container can't reach Sonos, port conflicts, env var validation errors

- [x] Create `docs/setup/helm.md` — Helm chart deployment guide (AC: 1, 3, 4)
  - [x] Prerequisites table: Helm 3, kubectl, k3s/k8s cluster, image available in accessible registry
  - [x] Validate chart: `make helm-lint`, preview: `make helm-template`
  - [x] Deploy: `make helm-install` (equivalent to `helm upgrade --install soniq helm/soniq`)
  - [x] Configuration: values override via `--set` flags and values file snippet (config.* and secret.* keys)
  - [x] SSDP/network section: pod network isolation, `hostNetwork: true` workaround (manual override, not in chart by default)
  - [x] Ingress: enabling `ingress.enabled=true`, security note (no built-in auth, apply at ingress layer)
  - [x] Remote MCP client connection example (AC: 2)
  - [x] Troubleshooting: pod can't reach Sonos, image pull issues, port-forward to test

- [x] Replace `docs/setup/README.md` — Overview and cross-device guide (AC: 1, 3)
  - [x] Replace placeholder ("Story 1.1 placeholder") entirely
  - [x] Transport comparison table: local stdio vs Docker/HTTP vs Helm/HTTP
  - [x] When-to-use guidance for each deployment model
  - [x] Links to stdio.md, docker.md, helm.md, troubleshooting.md

- [x] Create `docs/integrations/claude-desktop.md` — Claude Desktop config for stdio and remote (AC: 2, 3)
  - [x] Cross-reference to `docs/setup/stdio.md` for local stdio setup
  - [x] Remote HTTP config example: `url` field pointing to `http://<host>:8000/mcp`
  - [x] Difference between local (`command`) and remote (`url`) config fields
  - [x] Restart requirement after config change

- [x] Update `docs/integrations/README.md` — Replace placeholder with links (AC: 2)
  - [x] Replace placeholder ("Story 1.1 placeholder") with navigation links
  - [x] Link to claude-desktop.md; note other integration guides planned for Epic 5

- [x] Extend `docs/setup/troubleshooting.md` — Add remote/Docker/Helm sections (AC: 4)
  - [x] Append new sections at end (do not rewrite existing local/stdio content)
  - [x] Docker: container can't discover Sonos rooms (SSDP/multicast)
  - [x] Docker: port not reachable from remote client
  - [x] Helm: pod fails to start or CrashLoopBackOff
  - [x] Remote: MCP client can't connect to server URL

## Dev Notes

### What This Story Is (and Is Not)

**Pure documentation work.** No changes to `src/`, `helm/`, `tests/`, or `Makefile`. All underlying features (HTTP transport: Story 4.1; Docker packaging: Story 4.2; Helm chart: Story 4.3) are complete. This story adds user-facing guides for the deployment paths that now exist.

### Existing Documentation State

| File | State | Action |
|---|---|---|
| `docs/setup/stdio.md` | Complete ✅ | Do NOT modify — use as quality template |
| `docs/setup/troubleshooting.md` | Complete for local ✅ | Extend (append remote sections) |
| `docs/setup/README.md` | Placeholder ❌ | Replace entirely |
| `docs/integrations/README.md` | Placeholder ❌ | Replace with navigation links |
| `docs/integrations/claude-desktop.md` | Missing ❌ | Create |
| `docs/setup/docker.md` | Missing ❌ | Create |
| `docs/setup/helm.md` | Missing ❌ | Create |

### Key Technical Facts (Canonical Sources)

**Server endpoint (HTTP transport):**
- MCP endpoint path: `/mcp`
- Default URL: `http://<host>:8000/mcp`
- Port configurable via `SONIQ_MCP_HTTP_PORT`

**Environment variables** (source of truth: `docker-compose.yml` and `.env.example`):

| Env var | Docker/remote default | Notes |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `http` | Must be `http` for Docker/Helm; `stdio` for local |
| `SONIQ_MCP_HTTP_HOST` | `0.0.0.0` | Must be `0.0.0.0` for container port-mapping |
| `SONIQ_MCP_HTTP_PORT` | `8000` | Port inside container; map to host with `-p 8000:8000` |
| `SONIQ_MCP_EXPOSURE` | `home-network` | Use `home-network` for remote; `local` for stdio |
| `SONIQ_MCP_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SONIQ_MCP_MAX_VOLUME_PCT` | `80` | Integer 0–100 |
| `SONIQ_MCP_DEFAULT_ROOM` | (empty) | Optional; put in Secret for Helm |
| `SONIQ_MCP_TOOLS_DISABLED` | (empty) | Comma-separated tool names |
| `SONIQ_MCP_CONFIG_FILE` | (empty) | Reserved — document as reserved for future use |

**Makefile targets for docs to reference** (source: `Makefile` — do not invent new targets):

| Target | Command | Description |
|---|---|---|
| `make docker-build` | `docker build -t soniq-mcp:local .` | Build local image |
| `make docker-run` | `docker run --rm -p 8000:8000 -e ...` | Run with HTTP transport |
| `make docker-compose-up` | `docker compose up --build -d` | Build and start detached |
| `make docker-compose-down` | `docker compose down` | Stop and remove containers |
| `make helm-lint` | `helm lint helm/soniq` | Validate chart |
| `make helm-template` | `helm template soniq helm/soniq` | Preview rendered manifests |
| `make helm-install` | `helm upgrade --install soniq helm/soniq` | Deploy/upgrade |

**Helm chart configurable surface** (source: `helm/soniq/values.yaml` from Story 4.3):

| values.yaml key | Maps to env var | Default |
|---|---|---|
| `config.transport` | `SONIQ_MCP_TRANSPORT` | `http` |
| `config.httpHost` | `SONIQ_MCP_HTTP_HOST` | `0.0.0.0` |
| `config.httpPort` | `SONIQ_MCP_HTTP_PORT` | `8000` |
| `config.exposure` | `SONIQ_MCP_EXPOSURE` | `home-network` |
| `config.logLevel` | `SONIQ_MCP_LOG_LEVEL` | `INFO` |
| `config.maxVolumePct` | `SONIQ_MCP_MAX_VOLUME_PCT` | `80` |
| `config.toolsDisabled` | `SONIQ_MCP_TOOLS_DISABLED` | `""` |
| `secret.defaultRoom` | `SONIQ_MCP_DEFAULT_ROOM` | `""` |
| `image.repository` | — | `soniq-mcp` |
| `image.tag` | — | `local` |
| `service.type` | — | `ClusterIP` |
| `ingress.enabled` | — | `false` |

Override example:
```bash
helm upgrade --install soniq helm/soniq \
  --set image.repository=registry.example.com/soniq-mcp \
  --set image.tag=1.0.0 \
  --set secret.defaultRoom="Living Room" \
  --set config.logLevel=DEBUG
```

### SSDP / Sonos Network Limitations — Critical for Docker and Helm Docs

SoCo uses SSDP (UDP multicast `239.255.255.250:1900`) to discover Sonos devices. Container network isolation breaks multicast by default. Document clearly:

**Docker:**
- Default bridge network: multicast not forwarded to host → SoCo discovery may fail
- **Linux fix:** `docker run --network=host ...` puts container on host network stack; SSDP works
- **macOS/Windows Docker Desktop:** `--network=host` maps to the VM, not the physical host → SSDP still fails. No simple fix; practically, this means Docker is best for Linux home-lab deployment
- `docker-compose.yml` does not set `network_mode: host`. Users on Linux who need discovery can add it manually

**Helm/k3s:**
- Pod network is isolated from node network by default → SoCo discovery will likely fail
- Fix: add `hostNetwork: true` to Deployment spec so pod uses node network stack
- The current chart (`helm/soniq/templates/deployment.yaml`) does **NOT** include `hostNetwork: true` — document as a manual override: `helm upgrade --install soniq helm/soniq --set ... ` but note that `hostNetwork` is not a chart value yet (it requires editing deployment.yaml directly or a future chart update)
- Practical guidance: for k3s on Linux running on the same network as Sonos, `hostNetwork: true` is the reliable path; document as a known limitation of the current chart

### stdio vs Streamable HTTP Comparison

| | Local `stdio` | Remote `Streamable HTTP` |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `stdio` | `http` |
| `SONIQ_MCP_EXPOSURE` | `local` | `home-network` |
| Port opened | None | 8000 (configurable) |
| Client location | Same machine only | Any network client |
| MCP client config | `command` field | `url` field |
| MCP endpoint | stdin/stdout pipes | `http://<host>:8000/mcp` |
| Sonos network access | Direct from machine | Container/pod must reach Sonos subnet |
| Deployment model | Process launched by client | Long-running service |

### Remote MCP Client Configuration

Claude Desktop config for remote HTTP connection:
```json
{
  "mcpServers": {
    "soniq-mcp": {
      "url": "http://soniq-host:8000/mcp"
    }
  }
}
```
Replace `soniq-host` with the IP or hostname running the container/pod.

**Important note for developer:** Verify this config syntax against current Claude Desktop documentation before publishing. MCP remote transport support in Claude Desktop is actively evolving. Test against a running server instance to confirm the `url` field format is current.

### Documentation Quality Standard

Follow the same pattern as `docs/setup/stdio.md` (complete, production-quality reference):
- Prerequisites as a table
- Numbered step sections
- All commands shown using `make` targets where available, with inline equivalents
- Configuration shown as a table with field names, valid values, and defaults
- Troubleshooting entries use Symptom / What's happening / Fix structure
- No placeholder content; no "will be added later" sections

### Anti-Patterns to Avoid

- **Do not** invent new `make` targets — only reference targets that exist in `Makefile`
- **Do not** document TLS or authentication — not implemented; ingress-layer protection is the architecture approach
- **Do not** claim `--network=host` works on macOS Docker Desktop (routes to VM, not physical host)
- **Do not** modify `docs/setup/stdio.md` — already complete
- **Do not** modify files under `src/`, `helm/`, `tests/`, or `Makefile`
- **Do not** add `hostNetwork` support to the Helm chart — chart is out of scope; document as known limitation
- **Do not** leave placeholder sections in newly created docs — if content is truly out of scope for 4.4 (e.g., n8n integration), link to the planned Epic 5 story rather than writing "TBD"

### Project Structure Notes

Files to create/modify (all paths relative to project root):

| File | Action |
|---|---|
| `docs/setup/docker.md` | Create |
| `docs/setup/helm.md` | Create |
| `docs/setup/README.md` | Replace placeholder |
| `docs/setup/troubleshooting.md` | Extend (append remote sections) |
| `docs/integrations/claude-desktop.md` | Create |
| `docs/integrations/README.md` | Replace placeholder |

No files under `src/`, `helm/soniq/`, `tests/`, or `Makefile` are modified.

### Previous Story Intelligence (Story 4.3)

From Story 4.3 completion notes:
- Helm chart fully implemented: `Chart.yaml`, `values.yaml`, `templates/` (configmap, secret, deployment, service, ingress)
- `SONIQ_MCP_CONFIG_FILE` is surfaced in the chart (added in 4.3 review follow-up)
- `containerPort`/`targetPort` are wired to `config.httpPort` (not hardcoded to 8000)
- `ingress.enabled: false` by default — ingress exposes MCP endpoint to the network; security note required in docs
- Smoke tests (`tests/smoke/helm/`) validate `helm lint` and `helm template` pass — docs should mention these

From Story 4.2 completion notes:
- Docker image: `soniq-mcp:local`, built with `make docker-build`
- `docker-compose.yml` is the reference for canonical env var defaults
- Smoke tests (`tests/smoke/docker/`) validate Docker runtime — reference in troubleshooting

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md#Infrastructure-and-Deployment`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Authentication-Security`]
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-4.4`]
- [Source: `_bmad-output/implementation-artifacts/4-3-provide-a-helm-chart-for-self-hosted-deployment.md#Dev-Notes`]
- [Source: `docker-compose.yml`] — canonical env var names and container defaults
- [Source: `.env.example`] — env var descriptions and valid values
- [Source: `Makefile`] — all available command targets
- [Source: `docs/setup/stdio.md`] — quality template for new setup docs
- [Source: `helm/soniq/values.yaml`] — Helm configurable surface

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes List

- Created `docs/setup/docker.md`: full Docker deployment guide covering build, single-container run, Compose, SSDP/network limitations (Linux `--network=host` vs macOS/Windows caveat), remote MCP client config, and troubleshooting.
- Created `docs/setup/helm.md`: full Helm chart deployment guide covering prerequisites, lint/template/install, full values reference, SSDP/`hostNetwork` limitation and manual workaround, ingress security note, remote client config, and troubleshooting.
- Replaced `docs/setup/README.md`: replaced Story 1.1 placeholder with deployment model comparison table, when-to-use guidance, and links to all setup/integration guides.
- Created `docs/integrations/claude-desktop.md`: covers local stdio (`command` field) setup, remote HTTP connector setup via Claude Desktop Settings, differences table, and restart requirement.
- Updated `docs/integrations/README.md`: replaced Story 1.1 placeholder with link to claude-desktop.md and note on planned Epic 5 integrations.
- Extended `docs/setup/troubleshooting.md`: appended four new troubleshooting sections (Docker SSDP, Docker port, Helm CrashLoopBackOff, remote MCP client) without modifying existing local/stdio content.
- No source, Helm chart, test, or Makefile changes — pure documentation story as specified.
- 2026-03-29 review follow-up: corrected Claude Desktop remote setup guidance to use Settings > Connectors instead of unsupported `claude_desktop_config.json` `url` entries; updated Docker, Helm, and troubleshooting docs to match current Anthropic guidance.

### File List

- `docs/setup/docker.md` (created)
- `docs/setup/helm.md` (created)
- `docs/setup/README.md` (replaced)
- `docs/setup/troubleshooting.md` (extended)
- `docs/integrations/claude-desktop.md` (created)
- `docs/integrations/README.md` (replaced)
- `_bmad-output/implementation-artifacts/4-4-document-remote-docker-helm-and-cross-device-usage.md` (story file updated)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (status updated)

## Change Log

- 2026-03-29: Story 4.4 implemented — created Docker and Helm deployment guides, replaced setup/integrations README placeholders, created Claude Desktop integration guide, extended troubleshooting with remote/Docker/Helm sections. Status → review.
- 2026-03-29: Addressed code review finding by updating Claude Desktop remote connection guidance to the supported Connectors flow.
- 2026-03-29: Story status updated from review → done after review follow-up completion.
