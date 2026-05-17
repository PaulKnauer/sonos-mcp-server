# Helm Chart Deployment Guide

This guide covers deploying SoniqMCP to a Kubernetes or k3s cluster using the included Helm chart.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Helm 3 | `helm version` to check |
| kubectl | `kubectl version --client` to check; configured for your cluster |
| k3s or Kubernetes cluster | Running and accessible via `kubectl get nodes` |
| SoniqMCP image in an accessible registry | Build with `make docker-build` and push to a registry your cluster can pull from, or load directly into k3s |
| SoniqMCP source | `git clone <repo-url> sonos-mcp-server` |

---

## 1. Validate and preview the chart

Before deploying, validate the chart and preview the rendered manifests:

```bash
make helm-lint
# Equivalent: helm lint helm/soniq
```

```bash
make helm-template
# Equivalent: helm template soniq helm/soniq
```

`helm-lint` catches chart structure errors. `helm-template` renders the full manifest set so you can inspect what will be applied to your cluster.

---

## 2. Deploy to the cluster

```bash
make helm-install
# Equivalent: helm upgrade --install soniq helm/soniq
```

`helm upgrade --install` is idempotent — it installs on first run and upgrades on subsequent runs using the same command.

To verify the deployment:

```bash
kubectl get pods
kubectl get svc
```

---

## 3. Configuration

### Override values at deploy time

Pass `--set` flags to override individual values:

```bash
helm upgrade --install soniq helm/soniq \
  --set image.repository=registry.example.com/soniq-mcp \
  --set image.tag=1.0.0 \
  --set secret.defaultRoom="Living Room" \
  --set config.logLevel=DEBUG
```

### Override values using a file

Create a `my-values.yaml` file:

```yaml
image:
  repository: registry.example.com/soniq-mcp
  tag: 1.0.0

config:
  logLevel: DEBUG
  maxVolumePct: "90"

secret:
  defaultRoom: "Living Room"
```

Then deploy with:

```bash
helm upgrade --install soniq helm/soniq -f my-values.yaml
```

### Full values reference

| values.yaml key | Env var | Default | Notes |
|---|---|---|---|
| `config.transport` | `SONIQ_MCP_TRANSPORT` | `http` | Must be `http` for cluster |
| `config.httpHost` | `SONIQ_MCP_HTTP_HOST` | `0.0.0.0` | Bind address inside pod |
| `config.httpPort` | `SONIQ_MCP_HTTP_PORT` | `8000` | Port inside pod |
| `config.exposure` | `SONIQ_MCP_EXPOSURE` | `home-network` | Use `home-network` for remote access |
| `config.logLevel` | `SONIQ_MCP_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `config.maxVolumePct` | `SONIQ_MCP_MAX_VOLUME_PCT` | `80` | Integer 0–100 |
| `config.toolsDisabled` | `SONIQ_MCP_TOOLS_DISABLED` | `""` | Comma-separated tool names |
| `config.configFile` | `SONIQ_MCP_CONFIG_FILE` | `""` | Reserved for future use |
| `config.authMode` | `SONIQ_MCP_AUTH_MODE` | `""` | `"none"`, `"static"`, or `"oidc"`; empty uses runtime default (`none`) |
| `config.oidcIssuer` | `SONIQ_MCP_OIDC_ISSUER` | `""` | OIDC issuer URL (`oidc` mode only) |
| `config.oidcAudience` | `SONIQ_MCP_OIDC_AUDIENCE` | `""` | Expected JWT `aud` claim (`oidc` mode only) |
| `config.oidcJwksUri` | `SONIQ_MCP_OIDC_JWKS_URI` | `""` | Explicit JWKS endpoint; auto-discovered if unset |
| `config.oidcResourceUrl` | `SONIQ_MCP_OIDC_RESOURCE_URL` | `""` | Optional resource server URL |
| `secret.defaultRoom` | `SONIQ_MCP_DEFAULT_ROOM` | `""` | Stored in a Kubernetes Secret |
| `secret.authToken` | `SONIQ_MCP_AUTH_TOKEN` | `""` | Bearer token for `static` mode (stored in a Kubernetes Secret) |
| `caBundle.enabled` | — | `false` | Mount an operator-provided CA bundle into the pod |
| `caBundle.configMapName` | — | `""` | Name of an existing ConfigMap containing the CA bundle file |
| `caBundle.configMapKey` | — | `ca.crt` | Key within the ConfigMap that holds the PEM data |
| `caBundle.mountPath` | — | `/etc/soniq/ca.crt` | Container path where the CA bundle is mounted |
| `image.repository` | — | `soniq-mcp` | Container image repository |
| `image.tag` | — | `local` | Container image tag |
| `service.type` | — | `ClusterIP` | `ClusterIP` or `NodePort` |
| `ingress.enabled` | — | `false` | Enable to expose via ingress |

`config.*` values are stored in a ConfigMap. `secret.*` values are stored in a Kubernetes Secret. Auth values are only included in rendered manifests when explicitly set; omitting them preserves the default no-auth behavior.

---

## 4. SSDP / Sonos network considerations

SoniqMCP uses SoCo, which relies on SSDP (UDP multicast on `239.255.255.250:1900`) to discover Sonos devices. Pod network isolation in Kubernetes/k3s breaks multicast routing by default.

### Symptom

SoniqMCP starts successfully but reports no Sonos rooms found. Sonos discovery times out.

### Fix: `hostNetwork: true`

Adding `hostNetwork: true` to the Deployment spec puts the pod on the node's network stack, allowing SSDP multicast to reach the physical network interface. This is the reliable path for k3s on Linux running on the same network segment as your Sonos system.

**The current chart does not include a `hostNetwork` value.** To apply it, edit the Deployment manifest directly after templating, or add it via a post-render hook. This is a known limitation of the current chart; a `hostNetwork` chart value is planned for a future update.

**Manual workaround** — patch the Deployment after install:

```bash
kubectl patch deployment soniq -p '{"spec":{"template":{"spec":{"hostNetwork":true}}}}'
```

With `hostNetwork: true`, the pod uses the node's network interfaces. The service port mapping still applies; the container listens on port 8000 of the node.

### Practical guidance

For k3s on Linux running on the same network as your Sonos devices, `hostNetwork: true` is the reliable path. Without it, Sonos discovery will likely fail. For managed Kubernetes clusters (cloud providers), the node is not typically on the same network as your home Sonos system, making container-based deployment impractical for device discovery.

---

## 5. Ingress

By default, `ingress.enabled` is `false`. The service is only reachable within the cluster (ClusterIP).

To expose the MCP endpoint externally via an ingress controller:

```bash
helm upgrade --install soniq helm/soniq \
  --set ingress.enabled=true \
  --set "ingress.hosts[0].host=soniq.example.com" \
  --set "ingress.hosts[0].paths[0].path=/" \
  --set "ingress.hosts[0].paths[0].pathType=Prefix"
```

> **Security note:** The MCP endpoint defaults to no authentication (`auth_mode=none`). Optional static or OIDC auth is available via `config.authMode` — see [Section 6](#6-authentication-optional) below. When ingress is enabled, the endpoint is reachable from outside the cluster without credentials unless you configure runtime auth or add ingress-layer protection. Apply authentication at the ingress layer (e.g., `nginx.ingress.kubernetes.io/auth-*` annotations, an OAuth2 proxy, or mTLS) before exposing to untrusted networks. See [authentication.md](authentication.md) for the full runtime auth model.

---

## 6. Authentication (optional)

Authentication is disabled by default (`auth_mode=none`) and is an HTTP transport concern only.

Auth values are conditional: they appear in the rendered manifests only when set. Omitting them leaves the default no-auth path unchanged.

### Static bearer token

```bash
helm upgrade --install soniq helm/soniq \
  --set config.authMode=static \
  --set secret.authToken=change-me-to-a-strong-secret
```

Or in a values file:

```yaml
config:
  authMode: static

secret:
  authToken: change-me-to-a-strong-secret
```

`config.authMode` is stored in the ConfigMap. `secret.authToken` is stored in the Kubernetes Secret.

### OIDC JWT auth (e.g. Authelia)

```yaml
config:
  authMode: oidc
  oidcIssuer: https://auth.example.com
  oidcAudience: https://soniq.example.com
  # Optional: override JWKS endpoint if auto-discovery does not work for your IdP.
  # oidcJwksUri: https://auth.example.com/.well-known/jwks.json
```

For Authelia on k3s, register SoniqMCP under Authelia's OIDC client configuration (`identity_providers.oidc.clients`) and use the audience issued for that client as `oidcAudience`. If your homelab manages Authelia through Terraform or GitOps, make that client registration in `iot-edge-k3s` or your infra repo; this chart only supplies the SoniqMCP-side values and template hooks.

See [authentication.md](authentication.md) for startup preflight behavior and OIDC error categories.

### CA bundle for OIDC with a private CA

If your JWKS endpoint uses a private CA, mount the certificate into the pod using `caBundle`. The CA bundle must already exist as a ConfigMap in your cluster — this chart mounts it but does not create it.

```yaml
config:
  authMode: oidc
  oidcIssuer: https://auth.example.com
  oidcAudience: https://soniq.example.com

caBundle:
  enabled: true
  configMapName: my-private-ca    # name of an existing ConfigMap in the cluster
  configMapKey: ca.crt
  mountPath: /etc/soniq/ca.crt
```

The chart mounts the ConfigMap key as a single file at `mountPath` using `subPath`, and sets `SONIQ_MCP_OIDC_CA_BUNDLE` to that path automatically.

> **Restart note:** Kubernetes does not propagate live updates to `subPath` volume mounts. After rotating the CA bundle in the backing ConfigMap, trigger a rollout to pick up the new certificate:
> ```bash
> kubectl rollout restart deployment/soniq
> ```

---

## 7. Connect a remote MCP client

Once the pod is running and the service is reachable, connect Claude Desktop or another MCP client.

**Port-forward to test locally** (without ingress):

```bash
kubectl port-forward svc/soniq 8000:8000
```

Then add a Claude Desktop connector in **Settings > Connectors** using `http://localhost:8000/mcp` as the server URL.

**With ingress enabled:** add a Claude Desktop connector in **Settings > Connectors** using `http://soniq.example.com/mcp` as the server URL.

See [Claude Desktop integration guide](../integrations/claude-desktop.md) for full details on local stdio config vs. remote connector setup.

Once the endpoint is reachable, use the same diagnostics-first flow as every other deployment: `ping`, `server_info`, then `list_rooms` before playback or lifecycle mutations. For phase-2 scenarios such as play modes, seek and sleep timer, room EQ, inputs, group audio, alarms, playlists, and local library browsing, use [../prompts/example-uses.md](../prompts/example-uses.md) and keep [../prompts/command-reference.md](../prompts/command-reference.md) as the canonical tool reference. Helm changes deployment mechanics, not business semantics.

---

## 8. Troubleshooting

### Pod can't reach Sonos devices

**Symptom:** Pod starts but SoniqMCP reports no rooms found; Sonos discovery times out.

**What's happening:** Pod network is isolated from the host network. SSDP multicast does not reach the physical NIC.

**Fix:** Apply `hostNetwork: true` to the Deployment (see [Section 4](#4-ssdp--sonos-network-considerations)).

---

### Image pull errors (`ImagePullBackOff` or `ErrImagePull`)

**Symptom:** `kubectl get pods` shows `ImagePullBackOff` or `ErrImagePull`.

**Checks:**

1. Confirm the image is available in a registry your cluster can reach:
   ```bash
   helm upgrade --install soniq helm/soniq \
     --set image.repository=registry.example.com/soniq-mcp \
     --set image.tag=1.0.0
   ```

2. For k3s, you can import a locally built image directly:
   ```bash
   docker save soniq-mcp:local | sudo k3s ctr images import -
   ```
   Then deploy without changing the `image.repository` default.

3. Check image pull secrets if your registry requires authentication.

---

### Pod fails to start or CrashLoopBackOff

**Symptom:** `kubectl get pods` shows `CrashLoopBackOff` or the pod restarts immediately.

**Diagnosis:**

```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
```

Common causes:
- **Configuration error:** SoniqMCP exits cleanly on invalid config with a message naming the field. Check the log for `configuration error:`.
- **Port conflict:** If using `hostNetwork: true`, port 8000 must be free on the node.
- **Missing env var:** Check the ConfigMap and Secret are correctly mounted by inspecting `kubectl describe pod`.

---

### Port-forward to test without ingress

If you do not have ingress configured, use port-forward to test connectivity from your local machine:

```bash
kubectl port-forward svc/soniq 8000:8000
```

Then connect an MCP client to `http://localhost:8000/mcp` on your local machine.

---

### Enabling debug logging

```bash
helm upgrade --install soniq helm/soniq --set config.logLevel=DEBUG
```

Logs are visible via:

```bash
kubectl logs -f <pod-name>
```
