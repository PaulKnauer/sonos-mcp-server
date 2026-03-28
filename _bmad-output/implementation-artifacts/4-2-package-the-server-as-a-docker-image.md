# Story 4.2: Package the Server as a Docker Image

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a home-lab user,
I want a supported Docker image,
so that I can run the server consistently in containerized environments.

## Acceptance Criteria

1. Given the application is runnable locally, when the Docker build is executed, then a container image is produced for the service.
2. Given a running container, when runtime configuration is injected as environment variables, then the application picks it up without any code changes.
3. Given a container started from the image, when it boots, then container startup behavior matches the documented deployment paths (HTTP transport on 0.0.0.0, exposure `home-network`).
4. Given the built image, it is suitable for both private-registry and public-registry publishing workflows (no hardcoded registry URLs, parameterisable base image).

## Tasks / Subtasks

- [ ] Create `.dockerignore` at project root (AC: 1, 4)
  - [ ] Exclude: `.git`, `__pycache__`, `*.pyc`, `.venv`, `_bmad-output`, `tests/`, `docs/`, `helm/`, `.claude/`, `*.md` (keep `pyproject.toml`, `uv.lock`, `src/`)

- [ ] Create `Dockerfile` at project root (AC: 1, 2, 3, 4)
  - [ ] Stage 1 base image: `ARG BASE_IMAGE=python:3.12-slim` then `FROM $BASE_IMAGE` (enables private-registry overrides)
  - [ ] Copy `uv` binary: `COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`
  - [ ] Set `WORKDIR /app`
  - [ ] Copy `pyproject.toml` and `uv.lock` first (layer caching for dependencies)
  - [ ] Copy `src/` directory
  - [ ] Install production deps only: `RUN uv sync --frozen --no-dev`
  - [ ] Set default env vars reflecting the containerized deployment path:
    - `ENV SONIQ_MCP_TRANSPORT=http`
    - `ENV SONIQ_MCP_HTTP_HOST=0.0.0.0`
    - `ENV SONIQ_MCP_HTTP_PORT=8000`
    - `ENV SONIQ_MCP_EXPOSURE=home-network`
  - [ ] `EXPOSE 8000`
  - [ ] `CMD ["/app/.venv/bin/python", "-m", "soniq_mcp"]`

- [ ] Create `docker-compose.yml` at project root (AC: 2, 3)
  - [ ] Single service `soniq-mcp` built from `.`
  - [ ] Port mapping: `"${SONIQ_MCP_HTTP_PORT:-8000}:${SONIQ_MCP_HTTP_PORT:-8000}"`
  - [ ] Pass through all `SONIQ_MCP_*` env vars with sensible `${VAR:-default}` fallbacks
  - [ ] `restart: unless-stopped`

- [ ] Update `Makefile` to add Docker targets (AC: 1, 3)
  - [ ] Add `IMAGE ?= soniq-mcp` and `TAG ?= local` variables near top
  - [ ] Add `.PHONY` declarations for all new targets
  - [ ] Add `docker-build` target: `docker build -t $(IMAGE):$(TAG) .`
  - [ ] Add `docker-run` target: `docker run --rm -p 8000:8000 -e SONIQ_MCP_TRANSPORT=http -e SONIQ_MCP_HTTP_HOST=0.0.0.0 -e SONIQ_MCP_HTTP_PORT=8000 -e SONIQ_MCP_EXPOSURE=home-network $(IMAGE):$(TAG)`
  - [ ] Add `docker-compose-up` target: `docker compose up --build -d`
  - [ ] Add `docker-compose-down` target: `docker compose down`

- [ ] Update `.env.example` to add HTTP env vars introduced in story 4.1 (AC: 2)
  - [ ] Add `SONIQ_MCP_HTTP_HOST=127.0.0.1` with comment explaining use of `0.0.0.0` for home-network/Docker
  - [ ] Add `SONIQ_MCP_HTTP_PORT=8000` with comment
  - [ ] Update `SONIQ_MCP_TRANSPORT` comment to remove "Currently only stdio is supported" note (HTTP is now supported)

- [ ] Write automated tests (AC: 1, 2, 3)
  - [ ] `tests/smoke/docker/__init__.py` — empty init file
  - [ ] `tests/smoke/docker/test_docker_smoke.py` — Docker smoke test:
    - Skip entire module if `docker` binary not in PATH: `pytest.importorskip` or `pytest.mark.skipif(not shutil.which("docker"), ...)`
    - Fixture `docker_image` (module scope): runs `docker build -t soniq-mcp-test:smoke .` from project root; yields image tag; removes image on teardown
    - Fixture `docker_container` (module scope): runs container with `docker run --rm -d -p 18432:8000 -e SONIQ_MCP_TRANSPORT=http -e SONIQ_MCP_HTTP_HOST=0.0.0.0 -e SONIQ_MCP_HTTP_PORT=8000 -e SONIQ_MCP_EXPOSURE=home-network -e SONIQ_MCP_LOG_LEVEL=WARNING <image>`; waits 3s; yields; stops container on teardown
    - Test `test_docker_mcp_endpoint_responds`: connects via `streamable_http_client` to `http://127.0.0.1:18432/mcp`, calls `ping`, asserts result `== "pong"`
    - Test `test_docker_tool_surface_populated`: connects to same URL, lists tools, asserts `len(tools) > 0`
  - [ ] Run `make test` confirming no regressions in existing 635 passed tests; Docker smoke tests can be skipped if Docker unavailable

## Dev Notes

### What This Story Is (and Is Not)

This story is **purely packaging work** — no changes to application logic, config models, tools, services, or adapters. The server already runs over HTTP (story 4.1). This story wraps that capability in a container image.

### Dockerfile Technical Details

**Base image selection:**
- Use `python:3.12-slim` (Debian slim) — smaller than full, has gcc for any native deps
- Parameterise via `ARG BASE_IMAGE=python:3.12-slim` so private registries can override
- Do NOT use `python:3.12-alpine` — `soco` has dependencies that may fail on musl libc

**`uv` in Docker:**
- Copy from `ghcr.io/astral-sh/uv:latest` (official approach)
- `COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`
- `uv sync --frozen --no-dev` installs into `.venv/` under `WORKDIR`
- Invoke the installed app via `/app/.venv/bin/python -m soniq_mcp` (avoids needing to activate venv)

**Layer caching optimisation:**
```dockerfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev  # cached unless deps change
COPY src/ ./src/
RUN uv sync --frozen --no-dev  # installs local package into .venv
```
Two-phase copy/sync: first sync installs third-party deps (cached); second sync installs the local `soniq-mcp` package after source is copied.

**Port and transport:**
- Container default transport: HTTP (`SONIQ_MCP_TRANSPORT=http`)
- Container default bind: `0.0.0.0:8000` — required for port-mapped container access
- MCP endpoint inside container: `http://0.0.0.0:8000/mcp`
- MCP endpoint from host: `http://127.0.0.1:8000/mcp` (or `http://<host-ip>:8000/mcp`)

**All config via env vars — zero code changes needed.** The existing config system (`config/loader.py`, `config/models.py`) already supports all required env vars.

### Configuration Reference for Docker

| Env Var | Container Default | Notes |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `http` | Must be `http` in container |
| `SONIQ_MCP_HTTP_HOST` | `0.0.0.0` | Bind all interfaces — required for port mapping |
| `SONIQ_MCP_HTTP_PORT` | `8000` | Container-internal port |
| `SONIQ_MCP_EXPOSURE` | `home-network` | Triggers trust-model reminder log |
| `SONIQ_MCP_LOG_LEVEL` | `INFO` | Override to `DEBUG` for troubleshooting |
| `SONIQ_MCP_DEFAULT_ROOM` | (empty) | Optional default room |
| `SONIQ_MCP_MAX_VOLUME_PCT` | `80` | Volume safety cap |
| `SONIQ_MCP_TOOLS_DISABLED` | (empty) | Comma-separated tool names |

**Typical container launch (direct):**
```bash
docker run --rm -p 8000:8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  -e SONIQ_MCP_DEFAULT_ROOM="Living Room" \
  soniq-mcp:local
```
Transport, host, port have safe defaults baked into the image — only override what you need.

### Project Structure Notes

Files created/modified by this story (all at project root unless stated):
- `Dockerfile` (create)
- `.dockerignore` (create)
- `docker-compose.yml` (create)
- `Makefile` (modify — add IMAGE, TAG vars, docker-build, docker-run, docker-compose-up, docker-compose-down targets)
- `.env.example` (modify — add SONIQ_MCP_HTTP_HOST, SONIQ_MCP_HTTP_PORT; update TRANSPORT comment)
- `tests/smoke/docker/__init__.py` (create)
- `tests/smoke/docker/test_docker_smoke.py` (create)

No files under `src/` are modified.

### Previous Story Intelligence (Story 4.1)

- HTTP transport is fully implemented. `SONIQ_MCP_TRANSPORT=http` + `SONIQ_MCP_HTTP_HOST` + `SONIQ_MCP_HTTP_PORT` + `SONIQ_MCP_EXPOSURE` are all wired and tested.
- `uvicorn` is already a transitive dep via `mcp[cli]` — no extra deps needed.
- `streamable_http_client` from `mcp.client.streamable_http` is the right client for smoke tests — see existing pattern in `tests/smoke/streamable_http/test_streamable_http_smoke.py`.
- `streamable_http_client` yields a 3-tuple `(read_stream, write_stream, get_session_id_callback)` — unpack the third as `_`.
- MCP endpoint path is `/mcp` (FastMCP default).
- Smoke test port `18431` is taken by the HTTP smoke test — use `18432` for Docker smoke tests to avoid conflicts.
- The `HOME_NETWORK` exposure posture emits a log warning about binding — this is expected, not an error.

### Testing Notes

- Docker smoke tests **must** be skipped when `docker` CLI is unavailable (e.g., most CI environments without Docker-in-Docker).
- Use `shutil.which("docker")` for the skip check.
- Docker build in test context: use `subprocess.run(["docker", "build", "-t", IMAGE, str(PROJECT_ROOT)], check=True)` where `PROJECT_ROOT = Path(__file__).parents[3]` (3 levels up from `tests/smoke/docker/`).
- Container teardown: `docker stop <container_id>` then `docker rm <container_id>` — or just `docker rm -f`.
- Image teardown: `docker rmi <image_tag> --force` — suppress errors in case image was already removed.
- Existing 635 tests must remain green. Docker smoke tests add on top of them.

### Architecture Compliance

- Source: `_bmad-output/planning-artifacts/architecture.md#Infrastructure-and-Deployment`
  - "The deployable unit will be a stateless single-process Python service packaged as a Docker image."
  - "Configuration should be injected at runtime and remain compatible with both direct container execution and Helm-managed deployment."
  - "Docker build packages the same application structure used locally."
- Dockerfile lives at project root per the architecture directory structure.
- `docker-compose.yml` lives at project root per the architecture directory structure.
- `Makefile` is "the canonical quick-reference for lint, test, smoke, Docker, Helm, and validation commands".
  - Add `docker-build`, `docker-run` (and compose equivalents) to `PHONY` list.

### Anti-Patterns to Avoid

- **Do not** use `python:3.12-alpine` — native lib compatibility risk with `soco`/`SoCo` deps.
- **Do not** hardcode registry URLs in `FROM` or `COPY --from` without `ARG` parameterisation.
- **Do not** include test/dev files in the image (use `.dockerignore`).
- **Do not** use `uv run` as the CMD — it adds overhead and `uv sync --no-dev` already installs the venv.
- **Do not** change any files under `src/` — this story is packaging only.
- **Do not** set `SONIQ_MCP_HTTP_HOST=127.0.0.1` in the container defaults — the container must bind `0.0.0.0` to be reachable via port mapping.

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md#Infrastructure-and-Deployment`]
- [Source: `_bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure`]
- [Source: `_bmad-output/implementation-artifacts/4-1-run-soniqmcp-over-streamable-http.md#Dev-Notes`]
- [Source: `src/soniq_mcp/config/models.py`] — `SoniqConfig` fields and env var names
- [Source: `src/soniq_mcp/config/loader.py`] — env var to config field mapping
- [Source: `tests/smoke/streamable_http/test_streamable_http_smoke.py`] — smoke test pattern to follow
- [Source: `Makefile`] — existing target structure and `UV` variable pattern to extend

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Debug Log References

### Completion Notes List

### File List
