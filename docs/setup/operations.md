# Operations and Release Guidance

This page covers the trust model, supported exposure boundaries, release artifacts, upgrade expectations, and compatibility baseline for SoniqMCP.

For the security reporting policy and coordinated disclosure process, see [SECURITY.md](../../SECURITY.md). For the full threat model — assets, threat actors, STRIDE analysis, and mitigations — see [docs/security/threat-model.md](../security/threat-model.md).

---

## Trust model and exposure boundaries

SoniqMCP has **no built-in end-user authentication**. The product is scoped to a single Sonos household and is designed for local or trusted home-network deployment only.

### Supported exposure postures

| Deployment | Supported posture | Notes |
|---|---|---|
| Local stdio | Same machine only | No port opened; AI client launches server as subprocess |
| Docker HTTP | Trusted home network | Bind to LAN; do not expose port 8000 to untrusted networks without boundary protection |
| Helm / k3s HTTP | Trusted home network | Same constraint; ingress requires boundary-layer auth |

### Adding boundary protection for remote access

If you need to reach SoniqMCP from outside a trusted home network, add protection at the deployment edge before exposing the endpoint. Options include:

- **Reverse proxy with authentication** — e.g., Nginx or Caddy with basic auth, OAuth2 proxy, or mutual TLS
- **Ingress authentication** — e.g., `nginx.ingress.kubernetes.io/auth-*` annotations, an OAuth2 proxy sidecar, or mTLS termination
- **Network ACL or firewall rule** — restrict inbound access to specific source IPs
- **VPN-only access** — place the server behind WireGuard or another VPN; only VPN peers can reach port 8000

The product does not include built-in user accounts, OAuth flows, or remote authorisation features. Remote protection is the operator's responsibility.

---

## Release artifacts

SoniqMCP is released via GitHub Actions when a version tag matching `v*.*.*` is pushed.

### Maintainer semver workflow

SoniqMCP now uses the `project.version` field in `pyproject.toml` as the single release version source. Maintainers should treat that value as strict semver (`MAJOR.MINOR.PATCH`) and use the helper targets below to keep version, tag, and GitHub Release creation aligned.

| Step | Command | Result |
|---|---|---|
| Inspect current version | `make release-version` | Prints the current `pyproject.toml` version |
| Bump a release | `make release-bump-patch` | Updates `project.version` to the next patch version |
|  | `make release-bump-minor` | Updates `project.version` to the next minor version |
|  | `make release-bump-major` | Updates `project.version` to the next major version |
| Create annotated git tag | `make release-tag` | Creates `vX.Y.Z` from the current version |
| Create GitHub Release manually | `make release-gh` | Runs `gh release create vX.Y.Z --generate-notes` |

Recommended maintainer flow:

```bash
make release-bump-patch
git add pyproject.toml
git commit -m "Release v0.1.1"
git push origin main
make release-tag
git push origin v0.1.1
```

Pushing the tag triggers the publish workflow. That workflow publishes PyPI and GHCR artifacts, then creates the GitHub Release entry with generated notes if one does not already exist.

Use `make release-gh` only if you need to create the Release object yourself after the tag already exists, or if the workflow-created Release needs to be bootstrapped manually.

### PyPI package

The `.github/workflows/publish.yml` workflow publishes a PyPI package using GitHub Actions OIDC trusted publishing (`id-token: write`). No manual token rotation is required once the repository is configured as a trusted publisher on PyPI.

Operators who install from PyPI receive the published wheel:

```bash
pip install soniq-mcp
```

### GHCR container image

The same `publish.yml` workflow publishes a container image to the GitHub Container Registry (GHCR) using `docker/metadata-action` to produce three tags per release:

| Tag | Example | Meaning |
|---|---|---|
| Full semver | `v1.2.3` | Exact release version |
| Major.minor | `1.2` | Latest patch in this minor series |
| `latest` | `latest` | Latest stable release overall |

Pull the image from GHCR:

```bash
docker pull ghcr.io/<owner>/sonos-mcp-server:latest
# or pin to a specific version:
docker pull ghcr.io/<owner>/sonos-mcp-server:1.2.3
```

Replace `<owner>` with the GitHub organisation or username that owns the repository.

---

## Upgrade expectations

### Local Python environments and checked-out repo installs

The repository's documented local workflow uses a checked-out repo plus `uv sync`. To upgrade that style of local install:

```bash
git pull
uv sync
```

If you installed the published package directly into a Python environment instead:

```bash
pip install --upgrade soniq-mcp
```

After upgrading, restart any running server process. There is no automatic migration of `.env` configuration; review the release notes for any new or changed configuration variables before restarting.

### Docker image refresh

To upgrade a Docker deployment to the latest image:

```bash
docker pull ghcr.io/<owner>/sonos-mcp-server:latest
docker compose down && docker compose up -d
```

Or, for a pinned version:

```bash
docker pull ghcr.io/<owner>/sonos-mcp-server:1.2.3
# Update your docker-compose.yml or run command to reference the new tag, then restart.
```

When using `docker-compose.yml`, update the `image:` tag to the new version before running `docker compose up --build -d`.

### Helm upgrade

To upgrade a Helm deployment to a new image tag:

```bash
helm upgrade soniq helm/soniq --set image.tag=1.2.3
```

Or to use `latest`:

```bash
helm upgrade soniq helm/soniq --set image.tag=latest
```

Helm manages the release lifecycle. `helm upgrade` is safe to re-run; it is idempotent for the same values. If you have a custom `my-values.yaml`, pass it on each upgrade:

```bash
helm upgrade soniq helm/soniq -f my-values.yaml --set image.tag=1.2.3
```

If you applied the `hostNetwork: true` patch manually after the initial install, re-apply it after each Helm upgrade:

```bash
kubectl patch deployment soniq -p '{"spec":{"template":{"spec":{"hostNetwork":true}}}}'
```

---

## Compatibility expectations

| Dimension | Current baseline |
|---|---|
| Python | 3.12 or later |
| Transports | `stdio` (local), `Streamable HTTP` (remote) |
| Sonos discovery | SSDP via SoCo; requires direct host-network access |
| Docker platform | Linux host with `--network=host` for Sonos discovery |
| Helm / k3s | `hostNetwork: true` required for Sonos discovery (manual patch; not a chart default) |
| macOS / Windows Docker | `--network=host` does not reach the physical NIC; use local stdio instead |

### What a version tag represents

A `v*.*.*` tag on the GitHub repository triggers the publish workflow:

- A PyPI package and GHCR container image were published automatically by `publish.yml`

The repository also runs CI quality gates on pushes to `main` and on pull requests, but a version tag by itself should not be treated as an extra compatibility or support guarantee beyond the published artifacts.

There is currently no automated changelog or release notes generator in the repository. To review what changed between releases, inspect the git log between the relevant tags:

```bash
git log v1.2.2..v1.2.3 --oneline
```

GitHub Release notes are generated from merged pull requests and commits by `gh release create --generate-notes`. Treat those notes as the primary human-readable release summary unless and until a dedicated changelog file is introduced.

### Assumptions that are unsafe until a stronger policy exists

- **No guaranteed backward compatibility** — configuration variable names and defaults may change between releases. Review the diff before upgrading in production.
- **No zero-downtime upgrade guarantee** — the server process must be restarted to pick up a new version; in-flight MCP connections will be dropped.
- **No managed Kubernetes support** — the Helm chart is designed for k3s on Linux home-lab hardware on the same network as the Sonos system. Cloud Kubernetes clusters are not a supported deployment target for device discovery.

---

## CI quality gates

Every push and pull request runs `.github/workflows/ci.yml`, which enforces:

| Gate | Command |
|---|---|
| Linting | `make lint` |
| Type checking | `make type-check` |
| Tests with coverage | `make coverage` |
| Package build verification | `make build-check` |
| Helm chart lint | `make helm-lint` |

Operators can run the same gates locally before upgrading a local checkout:

```bash
make ci
```
