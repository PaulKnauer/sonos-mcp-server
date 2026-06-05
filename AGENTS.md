# AGENTS.md
## AI Agent Operating Contract — SoniqMCP

This document defines **strict operating rules** for any AI agent (e.g. Claude Code, Codex, Cursor) working in this repository.
The goal is **safe, predictable, and reviewable** development of the Sonos MCP server.

---

## 1. Project Intent (Read First)

This repository contains **SoniqMCP**, a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that exposes Sonos speakers as tools for AI agents.

Key architectural commitments:
- **Hexagonal architecture** — domain models (frozen dataclasses in `src/soniq_mcp/domain/`) have zero infrastructure dependencies. Adapters (`adapters/`) wrap the SoCo library. Services (`services/`) contain business logic. Tools (`tools/`) register the MCP surface.
- **Safety-first** — volume caps, tool disable lists, exposure posture validation, and preflight startup checks are not optional. All volume operations must go through `domain/safety.check_volume()`.
- **Transport-agnostic** — the same server code runs over stdio (local AI clients) or Streamable HTTP (network). Auth is a transport-layer concern.
- **Config is Pydantic-validated** at startup — every config path has preflight validation before accepting traffic.

---

## 2. Source of Truth

### Single sources of truth (DO NOT DUPLICATE)

| Concern | Location |
|---|---|
| Server entry point | `src/soniq_mcp/__main__.py` |
| Application composition | `src/soniq_mcp/server.py` — `create_server()` is the single assembly point |
| Domain models | `src/soniq_mcp/domain/models.py` — frozen dataclasses only, no infrastructure |
| Safety rules | `src/soniq_mcp/domain/safety.py` — `check_volume()`, `assert_tool_permitted()`, `validate_exposure_posture()` |
| Config schema | `src/soniq_mcp/config/models.py` — `SoniqConfig` pydantic model |
| Config validation | `src/soniq_mcp/config/validation.py` — `run_preflight()`, `ensure_preflight_ready()` |
| MCP tool registration | `src/soniq_mcp/tools/` — one file per tool category |
| Transport bootstrap | `src/soniq_mcp/transports/bootstrap.py` |
| Docker deployment | `docker-compose.yml`, `Dockerfile` |
| Helm deployment | `helm/soniq/` |
| Environment template | `.env.example` |
| Release process | `scripts/release.py` |

❌ **Never hardcode Sonos IP addresses, room names, or credentials in code.**

---

## 3. Non-Negotiable Rules

### Safety (CRITICAL)

All volume-setting tools **MUST** call `domain/safety.py::check_volume()` — never bypass this check. The function raises `VolumeCapExceeded` rather than silently clamping, so the AI agent knows why the operation was rejected.

### Tool Registration

Every MCP tool MUST be registered in `tools/register_all()` inside `src/soniq_mcp/tools/__init__.py`. The tool name MUST also appear in the `KNOWN_TOOL_NAMES` frozenset in `src/soniq_mcp/config/models.py` — otherwise the `tools_disabled` validator rejects it.

### Testing

- **Coverage floor**: `fail_under = 70` in `pyproject.toml`. Do not lower it.
- **Mypy strict mode**: `disallow_untyped_defs = true`, `disallow_incomplete_defs = true`. New code MUST be fully typed.
- **Preflight tests**: config validation and auth preflight logic MUST have tests that cover both success and failure paths.

### Config

- Never commit `.env` files. `.env` is in `.gitignore` — keep it that way.
- Secret values (`auth_token`, OIDC secrets) use `SecretStr` in the Pydantic model.
- Config validation errors must surface the specific field name — never generic "validation failed" messages.

---

## 4. Architecture Rules

### Layer Isolation

```
tools/  →  services/  →  adapters/  →  soco (external)
                ↓
         domain/models.py  (frozen dataclasses, shared across layers)
```

- **Domain** imports NOTHING from adapters, services, tools, or transports. Zero infrastructure dependencies.
- **Services** depend on adapters (via interfaces) and domain models.
- **Tools** depend on services and config. Tools must NOT call adapters directly.
- **Transports** depend on `server.py::create_server()` only.

### Adding a New Tool

1. Add the domain model to `domain/models.py` (if returning new data)
2. Add the service method to an existing service in `services/` (or create a new service)
3. Add the tool handler in `tools/` (one file per category)
4. Register the tool in `tools/__init__.py::register_all()`
5. Add the tool name to `KNOWN_TOOL_NAMES` in `config/models.py`
6. Add tests in `tests/`
7. If exposed over HTTP, add an integration test in `tests/smoke/`

### Transport Safety

- Stdio transport: no auth, local only.
- HTTP transport: auth is optional but validated at startup.
- Exposure posture `LOCAL` requires loopback bind. `HOME_NETWORK` requires non-loopback. These combinations are enforced by Pydantic model validators — do not override them.

---

## 5. BMAD Integration

This project is BMAD-aware. The `_bmad/` directory at project root (if present) contains BMAD workflow configuration. When present:

- Planning artifacts live in `_bmad-output/planning-artifacts/`
- Implementation artifacts live in `_bmad-output/implementation-artifacts/`
- BMAD agent skills (analyst, architect, dev, tech-writer) live in `.claude/skills/` and `.cursor/skills/`
- Load `project-context.md` if it exists before starting any BMAD workflow
- BMAD config (`_bmad/bmm/config.yaml`) overrides generic defaults when present

---

## 6. CI/CD & Quality Gates

Before any merge to `main`:

- [ ] `make lint` passes (ruff check + format)
- [ ] `make type-check` passes (mypy strict)
- [ ] `make test` passes (pytest)
- [ ] `make audit` passes (pip-audit, known CVEs documented in Makefile)
- [ ] `make build-check` passes (uv build)
- [ ] `make ci` passes (lint + type-check + coverage + audit + build-check)
