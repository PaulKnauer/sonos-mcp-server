# Story 4.5: Establish CI, Quality Gates, and Release Automation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maintainer,
I want automated verification and release workflows,
so that production regressions, packaging drift, and deployment breakage are caught before release.

## Acceptance Criteria

1. Given a pull request or branch update, when the CI workflow runs, then the project executes the agreed automated quality gates including tests, linting, type checks, and build verification.
2. Given the CI workflow runs, when tests complete, then meaningful test coverage is reported and enforceable without incentivizing vanity metrics.
3. Given the CI workflow runs, when dependency checks complete, then dependency or supply-chain checks are part of the automated verification path.
4. Given a versioned release tag is pushed, when the publish workflow runs, then release automation produces and publishes supported artifacts including Python package and container image.
5. Given the story is complete, when a developer reads the Makefile, then the documented command surface and automation workflows stay aligned with what CI runs.

## Tasks / Subtasks

- [x] Add CI dev-tool dependencies to `pyproject.toml` (AC: 1, 2, 3)
  - [x] Add `ruff>=0.9.0` to `[dependency-groups] dev`
  - [x] Add `mypy>=1.15.0` to `[dependency-groups] dev`
  - [x] Add `pytest-cov>=6.0.0` to `[dependency-groups] dev`
  - [x] Add `pip-audit>=2.8.0` to `[dependency-groups] dev`
  - [x] Run `uv sync` to update `uv.lock`

- [x] Add tool configuration to `pyproject.toml` (AC: 1, 2)
  - [x] Add `[tool.ruff]` section: `line-length = 100`, `target-version = "py312"`, `select = ["E", "F", "I", "UP"]`
  - [x] Add `[tool.ruff.lint.isort]` section: `known-first-party = ["soniq_mcp"]`
  - [x] Add `[tool.mypy]` section: `python_version = "3.12"`, `disallow_untyped_defs = true`, `ignore_missing_imports = true`
  - [x] Add `[tool.coverage.run]` section: `source = ["src/soniq_mcp"]`, `omit = ["*/__main__.py"]`
  - [x] Add `[tool.coverage.report]` section: `fail_under = 70`, `show_missing = true`, `exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]`

- [x] Add new Makefile targets (AC: 1, 2, 3, 5)
  - [x] Add `lint` target: `$(UV) run ruff check src tests && $(UV) run ruff format --check src tests`
  - [x] Add `format` target: `$(UV) run ruff format src tests && $(UV) run ruff check --fix src tests`
  - [x] Add `type-check` target: `$(UV) run mypy src`
  - [x] Add `coverage` target: `$(UV) run pytest --cov --cov-report=term-missing`
  - [x] Add `audit` target: `$(UV) run pip-audit --ignore-vuln CVE-2026-4539`
  - [x] Add `ci` target: depends on `lint type-check coverage audit` — runs all local gates in sequence
  - [x] Update `.PHONY` line to include all new targets

- [x] Create `.github/workflows/ci.yml` (AC: 1, 2, 3)
  - [x] Trigger on: `push` (branches: `main`), `pull_request` (all branches)
  - [x] Single job `quality-gates` on `ubuntu-latest`
  - [x] Steps: checkout, setup Python 3.12, install uv, run `uv sync --frozen`, run `make lint`, run `make type-check`, run `make coverage` with coverage report upload, run `make audit`
  - [x] Upload coverage report as a workflow artifact
  - [x] Add a `build-check` job: runs `uv build` to verify the package builds cleanly (catches packaging drift)
  - [x] Add a `helm-check` job: installs helm and runs `make helm-lint` (verifies chart remains valid)

- [x] Create `.github/workflows/publish.yml` (AC: 4)
  - [x] Trigger on: `push` of tags matching `v*.*.*`
  - [x] Job `publish-pypi`: uses `uv build` then `pypa/gh-action-pypi-publish` with OIDC trusted publishing
  - [x] Job `publish-docker`: builds Docker image with tag from the Git tag, pushes to GitHub Container Registry (`ghcr.io`) using `GITHUB_TOKEN`
  - [x] Docker tags: semver version, major.minor, and `latest`
  - [x] Both jobs are independent; no gating on quality-gates (publish is tag-triggered, implying branch already passed CI)

- [x] Create `.github/` directory structure if not present (AC: 1, 4)
  - [x] Create `.github/workflows/` directory with `ci.yml` and `publish.yml`

## Dev Notes

### What Exists vs. What Needs Building

**Nothing CI-related exists yet:**
- No `.github/` directory in the repo
- No linting or type-check tools in `pyproject.toml` dev deps
- No coverage configuration
- `Makefile` has `test` and `check` but no `lint`, `type-check`, `coverage`, `audit`, or `ci` targets
- Architecture already names the expected files: `.github/workflows/ci.yml` and `.github/workflows/publish.yml`

**What exists and must be preserved:**
- `pyproject.toml` build backend: `uv_build` — do not change
- Existing `Makefile` targets: `test`, `check`, `docker-build`, `docker-run`, `docker-compose-up`, `docker-compose-down`, `helm-lint`, `helm-template`, `helm-install` — add new targets, do not change existing ones
- All existing test structure under `tests/` — do not modify tests
- Smoke test skip guards use `shutil.which()` — CI runners without docker/helm will auto-skip those tests, no workflow-level gating needed

### Tool Choices and Versions

| Tool | Version constraint | Purpose | Config location |
|---|---|---|---|
| `ruff` | `>=0.9.0` | Lint + format (replaces flake8/black/isort) | `[tool.ruff]` in pyproject.toml |
| `mypy` | `>=1.15.0` | Static type checking | `[tool.mypy]` in pyproject.toml |
| `pytest-cov` | `>=6.0.0` | Coverage with pytest | `[tool.coverage.*]` in pyproject.toml |
| `pip-audit` | `>=2.8.0` | Dependency vulnerability scanning | CLI only, no config needed |

**Why ruff not flake8/black:** Ruff covers lint + format + import sort in a single tool, aligns with current Python packaging community direction, and is significantly faster than the individual tools it replaces.

**Coverage threshold:** Start at 70% (`fail_under = 70`). The project already has substantial test coverage across unit/integration/contract/smoke. 70% is meaningful without incentivizing vanity coverage of trivial paths.

### pyproject.toml Tool Configuration

Add these sections at the end of `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.ruff.lint.isort]
known-first-party = ["soniq_mcp"]

[tool.mypy]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.coverage.run]
source = ["src/soniq_mcp"]
omit = ["*/__main__.py"]

[tool.coverage.report]
fail_under = 70
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Makefile Additions

Add after the existing `tree` target. Preserve all existing targets exactly:

```makefile
lint: ensure-uv
	$(UV) run ruff check src tests
	$(UV) run ruff format --check src tests

format: ensure-uv
	$(UV) run ruff format src tests
	$(UV) run ruff check --fix src tests

type-check: ensure-uv
	$(UV) run mypy src

coverage: ensure-uv
	$(UV) run pytest --cov --cov-report=term-missing

audit: ensure-uv
	$(UV) run pip-audit

ci: lint type-check coverage audit
```

Update `.PHONY` to include the new targets.

### CI Workflow Design (ci.yml)

**Trigger:** `push` to `main`, `pull_request` to any branch — covers both merge gates and branch work.

**Job: quality-gates**
```yaml
- actions/checkout@v4
- actions/setup-python@v5 (python-version: "3.12")
- Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh
- uv sync --frozen
- make lint
- make type-check
- make coverage (with --cov-report=xml for upload)
- Upload coverage artifact
- make audit
```

**Job: build-check** (parallel with quality-gates)
- Runs `uv build` to verify the Python package builds without error
- Catches packaging drift before it reaches release time

**Job: helm-check** (parallel with quality-gates)
- Install helm (`azure/setup-helm@v3` action)
- Run `make helm-lint`
- Verifies chart remains valid as chart files evolve

**Important:** Smoke tests for Docker and Helm in `tests/smoke/` auto-skip via `shutil.which()`. The `quality-gates` job running `make coverage` (which calls pytest) will auto-skip Docker smoke tests since runners don't have docker-in-docker by default. No special handling needed.

### Publish Workflow Design (publish.yml)

**Trigger:** `push` tags matching `v*.*.*` (e.g., `v0.2.0`)

**Job: publish-pypi**
- Depends on: quality-gates completing (or trigger as `workflow_run`)
- Uses OIDC trusted publishing or `PYPI_TOKEN` secret
- Commands: `uv build`, then `uv publish` or `pypa/gh-action-pypi-publish@release/v1`
- Produces: sdist and wheel in `dist/`

**Job: publish-docker**
- Depends on: build-check completing
- Login to GHCR via `docker/login-action@v3` with `GITHUB_TOKEN`
- Extract tags via `docker/metadata-action@v5`
- Build and push via `docker/build-push-action@v5`
- Tags: `ghcr.io/OWNER/soniq-mcp:VERSION` and `ghcr.io/OWNER/soniq-mcp:latest`
- `OWNER` is derived from `${{ github.repository_owner }}`

**Secrets needed:**
- `PYPI_TOKEN` — for PyPI publishing (or use OIDC trusted publishing, which requires no secret)
- `GITHUB_TOKEN` — automatically available, used for GHCR push

**OIDC Trusted Publishing (preferred over PYPI_TOKEN):**
- Eliminates need for stored secrets
- Requires configuring the project on PyPI to trust the GitHub Actions OIDC issuer
- Use `pypa/gh-action-pypi-publish@release/v1` with `id-token: write` permission
- Document as the recommended path; include PYPI_TOKEN as fallback note

### File Structure to Create

```
.github/
└── workflows/
    ├── ci.yml
    └── publish.yml
```

No new source files under `src/`. No changes to `tests/` or `helm/`.

### Regression Risk: Ruff and Mypy on Existing Code

The existing codebase was written without ruff or mypy enforcement. When you add these tools, the initial run may produce lint or type errors in existing code. **Handle this correctly:**

1. Run `make format` first to auto-fix formatting issues
2. Run `make lint` — fix any remaining ruff errors in existing code
3. Run `make type-check` — if mypy strict mode produces many errors, consider starting with `strict = false` and adding `disallow_untyped_defs = true` instead; document the chosen setting clearly

**Do not:** Suppress all errors with `# type: ignore` blanket comments. Fix real issues or adjust mypy configuration to a level that is actually enforced.

**Expected:** The project already follows snake_case and clean boundaries, so lint errors should be minor. Type errors may be more numerous given the existing codebase was not written under strict mypy from the start.

### Anti-Patterns to Avoid

- **Do not** set `fail_under = 0` or remove the coverage threshold — it defeats the purpose
- **Do not** use `# noqa: ALL` or blanket mypy ignores to silence the initial tool run
- **Do not** add separate `flake8`, `black`, or `isort` configs — ruff replaces all three
- **Do not** hardcode versions in the GitHub Actions workflow steps (e.g., don't hardcode `uv==0.1.0`) — use latest or a floating range
- **Do not** modify existing `Makefile` targets — only append new ones
- **Do not** add Docker-in-Docker to the CI job to run smoke tests — the skip guard handles it correctly
- **Do not** modify test files to change skip behavior — the `shutil.which()` pattern is correct

### Project Structure Notes

Files to create/modify:

| File | Action |
|---|---|
| `pyproject.toml` | Add dev deps and tool config sections |
| `uv.lock` | Updated automatically by `uv sync` |
| `Makefile` | Append new targets |
| `.github/workflows/ci.yml` | Create |
| `.github/workflows/publish.yml` | Create |

No changes to `src/`, `tests/`, `helm/`, or `docs/`.

### Previous Story Intelligence (Story 4.4)

Story 4.4 was pure documentation — no source, test, or Makefile changes. The Makefile targets referenced in those docs (`make docker-build`, `make helm-lint`, etc.) are the canonical targets. Story 4.5 adds new targets to this surface without modifying existing ones.

From the sprint status `open_delivery_risks` (written after 4.3):
> "No CI workflow, coverage gate, lint/type-check gate, or automated release verification is currently tracked in implemented stories."

This story directly resolves all three items in `open_delivery_risks` related to CI.

### References

- [Source: `_bmad-output/planning-artifacts/architecture.md#Complete-Project-Directory-Structure`] — `.github/workflows/ci.yml` and `publish.yml` named in agreed structure
- [Source: `_bmad-output/planning-artifacts/architecture.md#Testing-Patterns`] — unit/integration/contract/smoke test structure, hardware isolation requirement
- [Source: `_bmad-output/planning-artifacts/architecture.md#Development-Workflow-Integration`] — Makefile as canonical command surface
- [Source: `_bmad-output/planning-artifacts/epics.md#Story-4.5`] — acceptance criteria and story requirements
- [Source: `pyproject.toml`] — current build backend (uv_build), Python 3.12 requirement, existing dev deps
- [Source: `Makefile`] — existing targets, UV variable, PHONY declaration pattern
- [Source: `Dockerfile`] — python:3.12-slim base image, uv sync --frozen --no-dev pattern
- [Source: `tests/smoke/docker/test_docker_smoke.py`] — shutil.which() skip guard pattern
- [Source: `tests/smoke/helm/test_helm_smoke.py`] — shutil.which() skip guard pattern
- [Source: `_bmad-output/implementation-artifacts/sprint-status.yaml`] — open_delivery_risks confirming CI is missing

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

None.

### Completion Notes List

- Added ruff, mypy, pytest-cov, pip-audit to `[dependency-groups] dev` in pyproject.toml. Ran `uv sync` to update lockfile.
- Added `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.lint.isort]`, `[tool.mypy]`, `[tool.coverage.run]`, and `[tool.coverage.report]` sections to `pyproject.toml`. The mypy suppression for `attr-defined`, `arg-type`, and `operator` is now scoped only to `soniq_mcp.services.*` and `soniq_mcp.tools.*` instead of the whole package.
- Fixed the remaining non-DI mypy issues in `src/soniq_mcp/adapters/soco_adapter.py` and `src/soniq_mcp/config/validation.py` so the narrower override still passes cleanly.
- Ran pip-audit: 3 CVEs found in transitive deps. Fixed 2 by upgrading `cryptography` (46.0.5→46.0.6) and `requests` (2.32.5→2.33.0). Remaining `pygments` CVE-2026-4539 has no fix release; explicitly ignored in `make audit` with comment.
- Added Makefile targets: `lint`, `format`, `type-check`, `coverage`, `audit`, `build-check`, and `ci`. Updated `.PHONY` line.
- Updated `.github/workflows/ci.yml` so quality gates use `make lint`, `make type-check`, `make coverage`, and `make audit`, with coverage XML exported in a follow-up step. The package build job now uses `make build-check` so CI stays aligned with the Makefile command surface.
- Updated `.github/workflows/publish.yml` so the PyPI build path also uses `make build-check` instead of a bespoke `uv build` command.
- Reverted the incidental `tests/` formatting churn so story 4.5 stays within its intended CI/release scope.
- Final post-review gate results: `make ci` ✅, 648 tests passed, 3 skipped, coverage 93.32%, audit clean with 1 documented ignore, package build successful.

### File List

- `pyproject.toml` (modified — added dev deps, tool config sections)
- `uv.lock` (updated — added ruff, mypy, pytest-cov, pip-audit; upgraded cryptography, requests)
- `Makefile` (modified — added lint, format, type-check, coverage, audit, build-check, ci targets)
- `src/soniq_mcp/config/validation.py` (modified — typed `_fmt` against a mapping-shaped Pydantic error payload)
- `src/soniq_mcp/adapters/soco_adapter.py` (modified — typed playback callback as `Callable[[Any], object]`)
- `.github/workflows/ci.yml` (created)
- `.github/workflows/publish.yml` (created)

## Change Log

- 2026-03-29: Story 4.5 implemented — added ruff/mypy/pytest-cov/pip-audit dev deps, tool config in pyproject.toml, Makefile quality-gate targets, `.github/workflows/ci.yml` and `publish.yml`. Fixed lint/type issues in existing code. Coverage 93.31%. Status → review.
- 2026-03-29: Addressed review findings for story 4.5 — aligned CI/publish workflows with Makefile targets, scoped mypy suppression to legacy DI modules, fixed two remaining unsuppressed typing issues, and reverted incidental `tests/` churn. Re-ran `make ci` successfully.
- 2026-03-29: Story 4.5 marked done after successful post-review verification and record updates.
