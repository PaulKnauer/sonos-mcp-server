# Story 4.3: Provide a Helm Chart for Self-Hosted Deployment

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a home-lab operator,
I want a Helm chart for the service,
so that I can deploy it repeatably in k3s or similar environments.

## Acceptance Criteria

1. Given the Docker image is available, when the Helm chart is used for deployment, then the chart provides configurable values for transport, networking, and speaker configuration.
2. Given the chart is rendered, when templates are inspected, then chart templates include the resources needed for deployment and service exposure (Deployment, Service, ConfigMap, Secret, optional Ingress).
3. Given the chart, when its structure is inspected, then it matches the agreed architecture (`helm/soniq/Chart.yaml`, `values.yaml`, `templates/`).
4. Given the deployment, when it starts, then the deployment path remains compatible with the single-household home-use model (HTTP transport, `0.0.0.0` bind, `home-network` exposure).

## Tasks / Subtasks

- [x] Replace `helm/soniq/README.md` placeholder with the real chart files (AC: 1, 2, 3)
  - [x] Create `helm/soniq/Chart.yaml`
  - [x] Create `helm/soniq/values.yaml` with full configurable surface
  - [x] Create `helm/soniq/templates/_helpers.tpl` with common label/selector helpers
  - [x] Create `helm/soniq/templates/configmap.yaml` (non-sensitive env vars)
  - [x] Create `helm/soniq/templates/secret.yaml` (sensitive/optional env vars)
  - [x] Create `helm/soniq/templates/deployment.yaml`
  - [x] Create `helm/soniq/templates/service.yaml`
  - [x] Create `helm/soniq/templates/ingress.yaml` (disabled by default via `ingress.enabled: false`)

- [x] Add Helm targets to `Makefile` (AC: 3)
  - [x] Add `helm-lint`, `helm-template`, `helm-install` to `.PHONY`
  - [x] Add `helm-lint`: `helm lint helm/soniq`
  - [x] Add `helm-template`: `helm template soniq helm/soniq`
  - [x] Add `helm-install`: `helm upgrade --install soniq helm/soniq`

- [x] Write automated smoke tests (AC: 1, 2, 3)
  - [x] `tests/smoke/helm/__init__.py` — empty init file
  - [x] `tests/smoke/helm/test_helm_smoke.py` — skip guard for missing `helm` CLI, tests for `helm lint` and `helm template` exit cleanly

- [x] Run `make test` confirming no regressions (AC: 4)

## Dev Notes

### What This Story Is (and Is Not)

This story delivers the Helm chart assets that were a placeholder (`helm/soniq/README.md`) since story 1.1. It is **purely deployment asset work** — no changes to application logic, config models, tools, services, or adapters. The server already runs over HTTP (story 4.1) and is containerised (story 4.2). This story wraps the existing Docker image in a Helm chart for k3s/home-lab self-hosted deployment.

### Helm Chart Structure

Architecture mandates this exact file layout (replace `README.md` placeholder):

```
helm/
└── soniq/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _helpers.tpl
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        ├── configmap.yaml
        └── secret.yaml
```

### Chart.yaml

```yaml
apiVersion: v2
name: soniq
description: Helm chart for SoniqMCP — a Sonos MCP server
type: application
version: 0.1.0
appVersion: "latest"
```

- `apiVersion: v2` is required for Helm 3.
- `appVersion` is informational; set to `"latest"` to avoid coupling to a version tag that doesn't yet exist.

### values.yaml — Full Configurable Surface

All `SONIQ_MCP_*` env vars must be surfaced as values. Non-sensitive config goes into ConfigMap; sensitive/optional values go into Secret (even if empty by default — the template must exist per architecture spec).

```yaml
image:
  repository: soniq-mcp
  tag: local
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: soniq.local
      paths:
        - path: /
          pathType: Prefix

config:
  transport: http
  httpHost: "0.0.0.0"
  httpPort: "8000"
  exposure: home-network
  logLevel: INFO
  maxVolumePct: "80"
  toolsDisabled: ""

secret:
  defaultRoom: ""
```

**Why separate `config` and `secret`?** `SONIQ_MCP_DEFAULT_ROOM` is the only field that may contain personally identifiable room names. The architecture's security posture keeps sensitive material in Secrets. All others go in ConfigMap.

**`toolsDisabled` as string:** The application expects `SONIQ_MCP_TOOLS_DISABLED` as a comma-separated string (e.g., `"ping,mute"`). Helm passes it as a string value — do not use a YAML list.

**Do NOT hardcode the image registry** — `image.repository: soniq-mcp` (no registry prefix) is correct for private registries to override via `--set image.repository=registry.example.com/soniq-mcp`.

### templates/_helpers.tpl

Define reusable helpers following standard Helm conventions:
- `soniq.fullname` — `{{ include "soniq.fullname" . }}` truncated to 63 chars
- `soniq.labels` — standard `helm.sh/chart`, `app.kubernetes.io/name`, `app.kubernetes.io/instance`, `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`
- `soniq.selectorLabels` — `app.kubernetes.io/name` + `app.kubernetes.io/instance` only (used in Deployment `matchLabels` and Service `selector`)

### templates/configmap.yaml

Maps `values.yaml` `config.*` → `SONIQ_MCP_*` env var names:

| values.yaml key | Env var |
|---|---|
| `config.transport` | `SONIQ_MCP_TRANSPORT` |
| `config.httpHost` | `SONIQ_MCP_HTTP_HOST` |
| `config.httpPort` | `SONIQ_MCP_HTTP_PORT` |
| `config.exposure` | `SONIQ_MCP_EXPOSURE` |
| `config.logLevel` | `SONIQ_MCP_LOG_LEVEL` |
| `config.maxVolumePct` | `SONIQ_MCP_MAX_VOLUME_PCT` |
| `config.toolsDisabled` | `SONIQ_MCP_TOOLS_DISABLED` |

All values must be quoted strings in the ConfigMap (use `{{ .Values.config.httpPort | quote }}`).

### templates/secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "soniq.fullname" . }}
  labels: {{- include "soniq.labels" . | nindent 4 }}
type: Opaque
stringData:
  SONIQ_MCP_DEFAULT_ROOM: {{ .Values.secret.defaultRoom | default "" | quote }}
```

Using `stringData` avoids manual base64 encoding in values.

### templates/deployment.yaml

Key requirements:
- `containerPort: 8000` (matches `config.httpPort` default)
- Load env from ConfigMap via `envFrom.configMapRef`
- Load env from Secret via `envFrom.secretRef`
- Use `{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}`
- `imagePullPolicy: {{ .Values.image.pullPolicy }}`
- No `livenessProbe`/`readinessProbe` needed — the MCP endpoint `/mcp` is not a standard HTTP health endpoint and FastMCP does not expose a `/healthz`. Leave probes absent rather than use incorrect paths.
- `replicas: 1` hardcoded — single-household model, stateless but Sonos device discovery is not designed for multi-instance concurrency.

### templates/service.yaml

- `type: {{ .Values.service.type }}` (default: ClusterIP)
- `port: {{ .Values.service.port }}` → `targetPort: 8000`
- Selector uses `soniq.selectorLabels`

### templates/ingress.yaml

- Wrap entire resource in `{{- if .Values.ingress.enabled }}` ... `{{- end }}`
- Disabled by default (`ingress.enabled: false`)
- Supports optional `ingressClassName` and `annotations`
- Security note in chart comments: ingress exposes MCP endpoint to the network; users should apply auth middleware at the ingress layer (architecture decision: no built-in auth)

### Makefile Targets

Add to `.PHONY`:
```
helm-lint helm-template helm-install
```

Add targets:
```makefile
helm-lint:
	helm lint helm/soniq

helm-template:
	helm template soniq helm/soniq

helm-install:
	helm upgrade --install soniq helm/soniq
```

### Automated Tests

Follow the same pattern as `tests/smoke/docker/test_docker_smoke.py`:
- Skip guard: `pytest.mark.skipif(shutil.which("helm") is None, reason="helm CLI not found")`
- `PROJECT_ROOT = Path(__file__).parents[3]` (3 levels up from `tests/smoke/helm/`)
- `CHART_PATH = PROJECT_ROOT / "helm" / "soniq"`

Two tests:
1. `test_helm_lint_passes` — runs `helm lint <chart_path>` and asserts exit code 0
2. `test_helm_template_renders` — runs `helm template soniq <chart_path>` and asserts exit code 0 and non-empty stdout

Both use `subprocess.run(..., capture_output=True, text=True)` (not `check=True`) so we can assert on the result and provide useful error messages.

### Project Structure Notes

Files to create/modify (all paths relative to project root):
- `helm/soniq/Chart.yaml` (create)
- `helm/soniq/values.yaml` (create)
- `helm/soniq/templates/_helpers.tpl` (create)
- `helm/soniq/templates/configmap.yaml` (create)
- `helm/soniq/templates/secret.yaml` (create)
- `helm/soniq/templates/deployment.yaml` (create)
- `helm/soniq/templates/service.yaml` (create)
- `helm/soniq/templates/ingress.yaml` (create)
- `helm/soniq/README.md` (delete/replace — was story 1.1 placeholder)
- `Makefile` (modify — add `helm-lint`, `helm-template`, `helm-install` targets)
- `tests/smoke/helm/__init__.py` (create)
- `tests/smoke/helm/test_helm_smoke.py` (create)

No files under `src/` are modified.

### Previous Story Intelligence (Story 4.2)

From story 4.2 (Docker packaging):
- Docker image defaults: `SONIQ_MCP_TRANSPORT=http`, `SONIQ_MCP_HTTP_HOST=0.0.0.0`, `SONIQ_MCP_HTTP_PORT=8000`, `SONIQ_MCP_EXPOSURE=home-network`. Helm chart `values.yaml` must use the same defaults so the behaviour is consistent.
- `uv sync --frozen --no-dev --no-install-project` dependency-layer pattern is internal to Docker — no Helm concern.
- Smoke test port `18431` (HTTP) and `18432` (Docker) are taken. Helm smoke tests don't need a listening port — they only invoke the `helm` CLI.
- `tests/smoke/docker/__init__.py` and `test_docker_smoke.py` are the structural template to follow.
- Makefile pattern: `IMAGE ?= soniq-mcp`, `TAG ?= local` are existing vars. Add `helm-*` targets after the `docker-*` targets.
- `--no-install-project` in the Dockerfile is a Dockerfile concern only — not relevant to Helm templates.

### Anti-Patterns to Avoid

- **Do not** create a `helm/soniq/templates/tests/` directory with Helm-native `helm test` hooks — the architecture uses pytest smoke tests, not Helm test pods.
- **Do not** use `type: LoadBalancer` as the default service type — `ClusterIP` is correct for a home-lab (k3s) model where access is via ingress or port-forward, not a cloud load balancer.
- **Do not** add `livenessProbe` or `readinessProbe` pointing to `/mcp` — that path requires MCP handshake, not a bare HTTP health check; FastMCP does not expose `/healthz`.
- **Do not** hardcode the image registry in `values.yaml` — `image.repository: soniq-mcp` (no registry) is correct.
- **Do not** base64-encode values in `secret.yaml` — use `stringData:` to keep values human-readable in the chart.
- **Do not** use a YAML list for `SONIQ_MCP_TOOLS_DISABLED` — it is a comma-separated string env var.
- **Do not** change any files under `src/` — this story is deployment asset work only.

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md#Infrastructure-and-Deployment`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure`] — defines exact `helm/soniq/` file layout
- [Source: `_bmad-output/planning-artifacts/architecture.md#Authentication-Security`] — no built-in auth; ingress-layer protection for remote exposure
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-4.3`]
- [Source: `_bmad-output/implementation-artifacts/4-2-package-the-server-as-a-docker-image.md#Dev-Notes`] — container defaults and smoke test patterns
- [Source: `src/soniq_mcp/config/models.py`] — `SoniqConfig` fields, env var names, and valid enum values
- [Source: `docker-compose.yml`] — canonical env var names and defaults for container deployment
- [Source: `tests/smoke/docker/test_docker_smoke.py`] — smoke test structural template
- [Source: `Makefile`] — existing target structure to extend

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Replaced `helm/soniq/README.md` placeholder with full Helm chart: Chart.yaml, values.yaml, _helpers.tpl, configmap.yaml, secret.yaml, deployment.yaml, service.yaml, ingress.yaml (disabled by default).
- All `SONIQ_MCP_*` env vars surfaced in values.yaml: non-sensitive config in ConfigMap, `SONIQ_MCP_DEFAULT_ROOM` in Secret using `stringData`.
- Deployment uses `replicas: 1`, loads env via `envFrom` (ConfigMap + Secret), no probes (FastMCP exposes no `/healthz`).
- Added `helm-lint`, `helm-template`, `helm-install` targets to Makefile `.PHONY` and body.
- Added `tests/smoke/helm/test_helm_smoke.py` with skip guard and four tests covering lint, base render, env-surface coverage, and configurable port alignment.
- Full test suite after review follow-up fixes: 648 passed, 3 skipped. No regressions.
- `helm lint` passes (info-only icon recommendation, 0 failures); `helm template` renders all 4 resources (Secret, ConfigMap, Service, Deployment) correctly.
- Review follow-up fixes: surfaced `SONIQ_MCP_CONFIG_FILE` in the chart, aligned `containerPort`/`targetPort` with configurable `config.httpPort`, and expanded Helm smoke tests to assert env-var coverage and non-default port wiring.

### File List

- `helm/soniq/Chart.yaml` (created)
- `helm/soniq/values.yaml` (created)
- `helm/soniq/templates/_helpers.tpl` (created)
- `helm/soniq/templates/configmap.yaml` (created)
- `helm/soniq/templates/secret.yaml` (created)
- `helm/soniq/templates/deployment.yaml` (created)
- `helm/soniq/templates/service.yaml` (created)
- `helm/soniq/templates/ingress.yaml` (created)
- `helm/soniq/README.md` (deleted — story 1.1 placeholder)
- `Makefile` (modified — added helm-lint, helm-template, helm-install targets)
- `tests/smoke/helm/__init__.py` (created)
- `tests/smoke/helm/test_helm_smoke.py` (created, then expanded with rendered-manifest assertions)

## Change Log

- 2026-03-29: Implemented full Helm chart for soniq (Story 4.3). Created all chart templates, values.yaml, Makefile helm targets, and pytest smoke tests. 644 tests pass, no regressions.
- 2026-03-29: Addressed review follow-ups for Story 4.3 by adding `SONIQ_MCP_CONFIG_FILE` chart support, wiring Kubernetes ports to `config.httpPort`, and strengthening Helm smoke coverage for env-surface and port-alignment regressions.
