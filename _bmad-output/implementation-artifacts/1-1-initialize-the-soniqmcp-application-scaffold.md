# Story 1.1: Initialize the SoniqMCP Application Scaffold

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want the project initialized with the agreed Python and MCP foundation,
so that all future work starts from a consistent, production-ready baseline.

## Acceptance Criteria

1. Given a new repository state for the implementation, when the project scaffold is created, then the application is initialized using `uv` with the agreed Python application structure.
2. Given the scaffold is created, when dependencies are installed, then the official MCP Python SDK and `SoCo` are added as dependencies.
3. Given the scaffold is complete, when the repository root is inspected, then it includes `pyproject.toml`, `Makefile`, `src/soniq_mcp/`, `tests/`, `helm/`, and `docs/`.
4. Given the scaffold is complete, when the codebase is reviewed against the architecture, then the structure matches the agreed architectural boundaries.

## Tasks / Subtasks

- [x] Initialize the Python application scaffold with `uv` (AC: 1)
  - [x] Create the application package rooted at `src/soniq_mcp/`
  - [x] Ensure `pyproject.toml`, `uv.lock`, and standard Python app entry points are present
  - [x] Add `.python-version` if the scaffold does not produce one
- [x] Add and record baseline dependencies (AC: 2)
  - [x] Add `mcp[cli]`
  - [x] Add `soco`
  - [x] Confirm dependency declarations land in `pyproject.toml`
- [x] Establish the agreed repository skeleton (AC: 3, 4)
  - [x] Add root `Makefile`
  - [x] Add placeholder app subpackages under `src/soniq_mcp/` for `config`, `transports`, `tools`, `services`, `adapters`, `schemas`, `domain`, and `utils`
  - [x] Add `tests/` layout with unit, integration, contract, smoke, fixtures, and fakes directories
  - [x] Add `helm/soniq/` and `docs/setup/`, `docs/integrations/`, `docs/prompts/` directories
- [x] Add minimal bootstrap placeholders that preserve boundaries without over-implementing later stories (AC: 4)
  - [x] Keep transport bootstrapping separate from business logic
  - [x] Do not implement real Sonos control, config validation, or transport behavior beyond placeholder wiring
- [x] Verify scaffold integrity (AC: 1, 2, 3, 4)
  - [x] Run a lightweight tree/package verification
  - [x] Ensure the created layout matches the architecture document before moving to Story 1.2

## Dev Notes

- This story is the hard dependency for the rest of Epic 1. Do not parallelize implementation of Stories 1.2 to 1.5 until the scaffold is in place.
- The selected foundation is `uv init --app soniq` plus `uv add "mcp[cli]" soco`. The repo package name remains `soniq_mcp` even if the app scaffold starts from the product name `soniq`.
- Preserve the agreed separation of concerns from day one:
  - transport/bootstrap code in `server.py` and `transports/`
  - thin MCP tool handlers in `tools/`
  - business logic in `services/`
  - external integration with Sonos in `adapters/`
  - config lifecycle in `config/`
- Do not add a database, auth system, or discovery-first runtime in this story.
- Add a root `Makefile` as the canonical command surface. It can start minimal, but it should be the place later stories extend for lint, test, smoke, Docker, Helm, and validation commands.
- Prefer placeholders and package boundaries over speculative implementation. Story 1.2 owns real config models and validation.
- Testing for this story should focus on scaffold sanity, importability, and command entry point viability, not business behavior.

### Project Structure Notes

- Target structure for this story starts the following top-level layout:
  - `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `.env.example`, `Makefile`
  - `src/soniq_mcp/`
  - `tests/`
  - `helm/soniq/`
  - `docs/setup/`, `docs/integrations/`, `docs/prompts/`
- Alignment with architecture matters more than file count. Create boundaries that later stories can fill without moving files around.
- Detected variance to watch: the architecture example uses `uv init --app soniq`, which may create paths named after `soniq`; normalize to the agreed Python package path `src/soniq_mcp/`.

### References

- Story source and acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#epic-1-project-foundation-and-safe-local-operation]
- Starter selection and initialization command: [Source: _bmad-output/planning-artifacts/architecture.md#selected-starter-uv-application-scaffold--official-mcp-python-sdk]
- Core decisions and implementation order: [Source: _bmad-output/planning-artifacts/architecture.md#core-architectural-decisions]
- Required structure and boundaries: [Source: _bmad-output/planning-artifacts/architecture.md#project-structure--boundaries]
- Packaging, installation, and developer-tool constraints: [Source: _bmad-output/planning-artifacts/prd.md#developer-tool-specific-requirements]

## Dev Agent Record

### Agent Model Used

gpt-5-codex

### Debug Log References

- `uv init --app --package --name soniq_mcp --description "Sonos MCP server" --vcs none --author-from none --python 3.12 --no-readme --no-workspace .`
- `uv add "mcp[cli]" soco`
- `uv add --dev pytest`
- `uv run python -m soniq_mcp`
- `uv run pytest`
- `uv run python -m compileall src tests`

### Completion Notes List

- Initialized the repository as a `uv`-managed Python application and normalized the package layout to `src/soniq_mcp`.
- Added the baseline MCP SDK and `SoCo` dependencies plus `pytest` as a development dependency for scaffold verification.
- Created the initial package boundaries for config, transports, tools, services, adapters, schemas, domain, and utils.
- Added the root `Makefile`, `.env.example`, `.gitignore`, tracked docs and Helm placeholders, and the initial tests layout.
- Implemented a minimal composition boundary in `server.py` and placeholder stdio transport modules without adding real Sonos or config behavior.
- Verified the scaffold through `uv run python -m soniq_mcp`, `uv run pytest`, and `uv run python -m compileall src tests`.

### File List

- .env.example
- .gitignore
- Makefile
- _bmad-output/implementation-artifacts/1-1-initialize-the-soniqmcp-application-scaffold.md
- docs/integrations/README.md
- docs/prompts/README.md
- docs/setup/README.md
- helm/soniq/README.md
- pyproject.toml
- src/soniq_mcp/__init__.py
- src/soniq_mcp/__main__.py
- src/soniq_mcp/adapters/__init__.py
- src/soniq_mcp/config/__init__.py
- src/soniq_mcp/domain/__init__.py
- src/soniq_mcp/schemas/__init__.py
- src/soniq_mcp/server.py
- src/soniq_mcp/services/__init__.py
- src/soniq_mcp/tools/__init__.py
- src/soniq_mcp/transports/__init__.py
- src/soniq_mcp/transports/bootstrap.py
- src/soniq_mcp/transports/stdio.py
- src/soniq_mcp/utils/__init__.py
- tests/__init__.py
- tests/contract/__init__.py
- tests/fakes/sonos/.gitkeep
- tests/fixtures/configs/.gitkeep
- tests/integration/__init__.py
- tests/smoke/__init__.py
- tests/unit/__init__.py
- tests/unit/test_scaffold_smoke.py
- uv.lock

### Change Log

- 2026-03-23: Implemented the Story 1.1 uv-based scaffold, placeholder package boundaries, and initial verification coverage; status set to review.
