# CLAUDE.md — SoniqMCP

This file is loaded as persistent context by AI agents working in this repository. It supplements BMAD configuration and AGENTS.md.

## Quick Start

```bash
make install        # uv sync
make run            # run over HTTP (default)
make run-stdio      # run over stdio
make test           # pytest
make lint           # ruff check + format
make type-check     # mypy strict
make ci             # full quality gate
```

## Key Architecture

- **Python 3.12+**, managed via `uv` (not pip/poetry)
- **Hexagonal**: `domain/` (zero deps) → `services/` → `adapters/` → `tools/` → `transports/`
- **Domain models** are frozen dataclasses in `domain/models.py`
- **Safety checks** live in `domain/safety.py` — never bypass `check_volume()`
- **Config** is Pydantic v2 in `config/models.py::SoniqConfig`
- **Preflight validation** runs at startup in `config/validation.py::run_preflight()`
- **MCP tools** register in `tools/__init__.py::register_all()` — each tool name must appear in `KNOWN_TOOL_NAMES` in `config/models.py`

## Rules

1. ALL new volume-setting tools MUST call `domain/safety.check_volume()`
2. ALL new tool names MUST appear in `KNOWN_TOOL_NAMES` in `config/models.py`
3. New code MUST be fully typed (`disallow_untyped_defs = true`)
4. Never commit `.env` — it's gitignored
5. Never bypass Pydantic model validators in `config/models.py`

## BMAD Context

If planning artifacts exist under `_bmad-output/planning-artifacts/`, load:
- `project-context.md` (project overview and status)
- `sprint-status.yaml` (current sprint state)
- BMAD config from `_bmad/bmm/config.yaml`
