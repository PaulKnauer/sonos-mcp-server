# Story 4.2: Package the Server as a Docker Image

Status: review

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

- [x] Create `.dockerignore` at project root (AC: 1, 4)
  - [x] Exclude: `.git`, `__pycache__`, `*.pyc`, `.venv`, `_bmad-output`, `tests/`, `docs/`, `helm/`, `.claude/`, `*.md` (keep `pyproject.toml`, `uv.lock`, `src/`)

- [x] Create `Dockerfile` at project root (AC: 1, 2, 3, 4)
  - [x] Stage 1 base image: `ARG BASE_IMAGE=python:3.12-slim` then `FROM $BASE_IMAGE` (enables private-registry overrides)
  - [x] Copy `uv` binary: `COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv`
  - [x] Set `WORKDIR /app`
  - [x] Copy `pyproject.toml` and `uv.lock` first (layer caching for dependencies)
  - [x] Copy `src/` directory
  - [x] Install production deps only: `RUN uv sync --frozen --no-dev`
  - [x] Set default env vars reflecting the containerized deployment path:
    - `ENV SONIQ_MCP_TRANSPORT=http`
    - `ENV SONIQ_MCP_HTTP_HOST=0.0.0.0`
    - `ENV SONIQ_MCP_HTTP_PORT=8000`
    - `ENV SONIQ_MCP_EXPOSURE=home-network`
  - [x] `EXPOSE 8000`
  - [x] `CMD ["/app/.venv/bin/python", "-m", "soniq_mcp"]`

- [x] Create `docker-compose.yml` at project root (AC: 2, 3)
  - [x] Single service `soniq-mcp` built from `.`
  - [x] Port mapping: `"${SONIQ_MCP_HTTP_PORT:-8000}:${SONIQ_MCP_HTTP_PORT:-8000}"`
  - [x] Pass through all `SONIQ_MCP_*` env vars with sensible `${VAR:-default}` fallbacks
  - [x] `restart: unless-stopped`

- [x] Update `Makefile` to add Docker targets (AC: 1, 3)
  - [x] Add `IMAGE ?= soniq-mcp` and `TAG ?= local` variables near top
  - [x] Add `.PHONY` declarations for all new targets
  - [x] Add `docker-build` target: `docker build -t $(IMAGE):$(TAG) .`
  - [x] Add `docker-run` target: `docker run --rm -p 8000:8000 -e SONIQ_MCP_TRANSPORT=http -e SONIQ_MCP_HTTP_HOST=0.0.0.0 -e SONIQ_MCP_HTTP_PORT=8000 -e SONIQ_MCP_EXPOSURE=home-network $(IMAGE):$(TAG)`
  - [x] Add `docker-compose-up` target: `docker compose up --build -d`
  - [x] Add `docker-compose-down` target: `docker compose down`

- [x] Update `.env.example` to add HTTP env vars introduced in story 4.1 (AC: 2)
  - [x] Add `SONIQ_MCP_HTTP_HOST=127.0.0.1` with comment explaining use of `0.0.0.0` for home-network/Docker
  - [x] Add `SONIQ_MCP_HTTP_PORT=8000` with comment
  - [x] Update `SONIQ_MCP_TRANSPORT` comment to remove "Currently only stdio is supported" note (HTTP is now supported)

- [x] Write automated tests (AC: 1, 2, 3)
  - [x] `tests/smoke/docker/__init__.py` — empty init file
  - [x] `tests/smoke/docker/test_docker_smoke.py` — Docker smoke test with skip guard, `docker_image` and `docker_container` module-scope fixtures, `test_docker_mcp_endpoint_responds` and `test_docker_tool_surface_populated` tests
  - [x] Run `make test` confirming no regressions: 637 passed, 5 skipped (Docker smoke tests skip when docker CLI absent, as expected)

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

claude-sonnet-4-6

### Debug Log References

_No issues encountered. All files created/modified per spec without deviation._

### Completion Notes List

- Created `.dockerignore` excluding all dev/test/build artifacts; keeps only `pyproject.toml`, `uv.lock`, `src/`.
- Created `Dockerfile` with parameterisable `ARG BASE_IMAGE=python:3.12-slim`, two-phase `uv sync` for layer caching, all required `ENV` defaults for containerised HTTP deployment, `EXPOSE 8000`, and `CMD` via venv python.
- Created `docker-compose.yml` with `soniq-mcp` service, env var pass-through with fallbacks for all `SONIQ_MCP_*` vars, and `restart: unless-stopped`.
- Updated `Makefile`: added `IMAGE ?= soniq-mcp`, `TAG ?= local` vars; added `docker-build`, `docker-run`, `docker-compose-up`, `docker-compose-down` targets with `.PHONY` declarations.
- Updated `.env.example`: updated `SONIQ_MCP_TRANSPORT` comment (HTTP now supported), added `SONIQ_MCP_HTTP_HOST=127.0.0.1` and `SONIQ_MCP_HTTP_PORT=8000` with usage notes.
- Created `tests/smoke/docker/__init__.py` (empty) and `tests/smoke/docker/test_docker_smoke.py` with module-level `skipif` guard, `docker_image`/`docker_container` fixtures, and two tests (`test_docker_mcp_endpoint_responds`, `test_docker_tool_surface_populated`).
- Full test suite: **637 passed, 5 skipped** — no regressions. Docker smoke tests correctly skip when `docker` CLI is absent.
- No files under `src/` were modified — pure packaging story.

### File List

- `.dockerignore` (created)
- `Dockerfile` (created)
- `docker-compose.yml` (created)
- `Makefile` (modified)
- `.env.example` (modified)
- `tests/smoke/docker/__init__.py` (created)
- `tests/smoke/docker/test_docker_smoke.py` (created)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified)
- `_bmad-output/implementation-artifacts/4-2-package-the-server-as-a-docker-image.md` (modified)

## Change Log

- 2026-03-28: Story 4.2 implemented — Docker packaging (Dockerfile, .dockerignore, docker-compose.yml, Makefile docker targets, .env.example HTTP vars, Docker smoke tests).
