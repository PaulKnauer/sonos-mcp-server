---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd.md'
  - '/Users/paul/github/sonos-mcp-server/docs/sonos-mcp-research.md'
workflowType: 'architecture'
project_name: 'sonos-mcp-server'
user_name: 'Paul'
date: '2026-03-23'
lastStep: 8
status: 'complete'
completedAt: '2026-03-23'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The product must support a broad Sonos control surface including playback, volume, queue operations, grouping, favourites, playlists, and system visibility. It must expose those capabilities consistently across direct MCP client use and agent-driven integrations. It must also support installation, configuration, permission-aware operation, and rich documentation as first-class capabilities rather than secondary support material.

**Non-Functional Requirements:**
Architecture is strongly shaped by reliability, setup responsiveness, safe default security posture, stable integration semantics, maintainability, and bounded home-use scalability. The system must behave predictably in a trust-sensitive home environment, fail gracefully, and preserve user trust through actionable diagnostics and controlled behavior.

**Scale & Complexity:**
This is a medium-complexity greenfield architecture for a self-hosted developer tool and integration service. The complexity comes from combining protocol integration, multi-transport MCP delivery, Sonos network constraints, deployment packaging, and strong experience-quality expectations in one coherent product.

- Primary domain: developer tool / MCP integration service
- Complexity level: medium
- Estimated architectural components: 6-8 major components

### Technical Constraints & Dependencies

The architecture depends on Python as the implementation language, `SoCo` as the Sonos control library, and MCP-compatible transports for both local and deployed use cases. The system is explicitly scoped to a single Sonos household and should default to local or trusted home-network exposure. SSDP discovery limitations in containerized or Kubernetes-like deployments mean the architecture should support static speaker configuration as the primary deployment-friendly model. Packaging and deployment are mandatory concerns, including PyPI distribution, Docker images, and Helm support.

### Cross-Cutting Concerns Identified

Cross-cutting concerns include transport abstraction, configuration and preflight validation, permission-aware tool exposure, safe control semantics for room and volume actions, deterministic error handling, deployment portability, and documentation-driven onboarding. These concerns affect nearly every architectural decision and will need explicit design treatment rather than being left implicit.

## Starter Template Evaluation

### Primary Technology Domain

Python backend / CLI integration service based on project requirements analysis

### Starter Options Considered

1. Official Python application scaffold using `uv init` plus the official MCP Python SDK
2. Standalone `fastmcp` package scaffold approach
3. Third-party MCP scaffolding tools

### Selected Starter: uv application scaffold + official MCP Python SDK

**Rationale for Selection:**
This project is a self-hosted Python MCP server with both CLI-like local usage and deployed HTTP transport. It does not benefit from a heavy opinionated web starter. The safest foundation is a minimal Python application scaffold created with `uv`, then layering in the official MCP SDK and project-specific structure deliberately. This keeps the architecture aligned with the MCP specification, avoids unnecessary framework decisions, and gives us clean control over packaging, transport abstraction, SoCo integration, and deployment assets.

**Initialization Command:**

```bash
uv init --app soniq
cd soniq
uv add "mcp[cli]" soco
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python project managed with `uv`, suitable for application-style execution.

**Styling Solution:**
Not applicable. This product has no primary frontend/UI starter requirement.

**Build Tooling:**
Standard Python packaging and dependency management through `uv` and `pyproject.toml`.

**Testing Framework:**
Not provided by default; architecture should add explicit testing decisions separately.

**Code Organization:**
Minimal Python application structure, allowing custom organization around server, tools, config, and Sonos integration.

**Development Experience:**
Fast local project initialization, dependency management, reproducible environments, and alignment with current MCP Python SDK guidance.

**Note:** Project initialization using this command should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Python application architecture using `uv` and the official MCP Python SDK
- `SoCo` as the Sonos control integration library
- `stdio` for local transport and `Streamable HTTP` for remote transport
- Configuration-driven, stateless service architecture
- No database in MVP
- Docker and Helm as primary deployment outputs

**Important Decisions (Shape Architecture):**
- Validation through Python data models and startup preflight checks
- Reverse-proxy or ingress-layer protection for remote exposure rather than built-in end-user auth
- Explicit separation between transport layer, Sonos service layer, configuration layer, and deployment assets
- Structured logging and deterministic domain error handling

**Deferred Decisions (Post-MVP):**
- Persistent storage for advanced features
- Built-in auth models beyond MCP/client/proxy controls
- Discovery-first network model beyond static speaker configuration
- Event subscription architecture and advanced asynchronous workflows

### Data Architecture

The MVP architecture will not include an application database. The system will operate as a stateless service whose authoritative runtime state comes from Sonos devices and validated application configuration. Configuration should be represented through explicit typed models and may be sourced from environment variables, config files, or deployment values.

**Rationale:**
This keeps the architecture aligned with the MVP feature set and avoids inventing persistence needs before they exist. It also reduces operational complexity for home users and keeps deployment simple.

### Authentication & Security

The MVP will not implement a built-in end-user authentication system. Security will be based on safe default exposure, MCP-compatible permission controls where supported by clients, and optional reverse-proxy or ingress protections for remote deployments. The default operating model assumes local or trusted home-network use.

**Rationale:**
This matches the product scope, avoids overbuilding for a home-use trust model, and keeps security controls close to deployment boundaries where remote exposure is actually managed.

### API & Communication Patterns

The architecture will support two primary MCP transport modes:
- `stdio` for same-machine local client use
- `Streamable HTTP` for remote or deployed use

The product will expose a consistent MCP tool surface across both modes. Internal communication should be organized around clear service boundaries and explicit error translation rather than transport-specific branching throughout the codebase.

**Verified Technology Direction:**
- Official MCP Python SDK package: `mcp` (current PyPI release found: `1.26.0`)
- Transport direction: modern MCP remote support should center on `Streamable HTTP`, not legacy SSE-first designs

### Frontend Architecture

No dedicated frontend architecture is required for MVP because the product is not a primary GUI application. However, user experience remains architecturally significant through setup flows, configuration UX, examples, diagnostics, and troubleshooting content.

**Rationale:**
The main product experience is delivered through MCP clients, deployment flows, CLI/runtime behavior, and documentation rather than a first-party web interface.

### Infrastructure & Deployment

The deployable unit will be a stateless single-process Python service packaged as a Docker image. Helm will be the primary deployment abstraction for home-lab and k3s use. Configuration should be injected at runtime and remain compatible with both direct container execution and Helm-managed deployment.

**Rationale:**
This supports both local and self-hosted use cases while keeping the deployment model simple, repeatable, and private-registry friendly.

### Decision Impact Analysis

**Implementation Sequence:**
1. Initialize the Python application with `uv`
2. Add official MCP SDK and `SoCo`
3. Define configuration and validation models
4. Implement transport bootstrap for `stdio` and `Streamable HTTP`
5. Implement Sonos service layer and tool handlers
6. Add structured logging and domain error handling
7. Package into Docker and Helm outputs

**Cross-Component Dependencies:**
Transport decisions affect server bootstrap and deployment shape. Configuration decisions affect startup flow, validation, and documentation. Security posture affects deployment guidance and tool exposure. The stateless service decision simplifies deployment but means advanced future capabilities that require persistence must be introduced deliberately later.

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
7 major areas where AI agents could make incompatible choices:
- MCP tool naming and parameter conventions
- transport bootstrapping and separation
- configuration model shape
- Sonos service abstraction boundaries
- error and result formatting
- file and module organization
- test placement and scope

### Naming Patterns

**Configuration and Data Naming Conventions:**
- Python internal names use `snake_case`
- Environment variables use `UPPER_SNAKE_CASE`
- Public MCP tool names use clear verb-oriented `snake_case`
- Configuration fields should align closely with Python model names unless environment-variable formatting requires transformation

**API and Tool Naming Conventions:**
- Tool names are action-oriented and explicit, for example `play`, `pause`, `set_volume`, `list_rooms`
- Parameter names use `snake_case`
- Room-targeting parameters use `room` consistently
- Group coordination parameters use `coordinator` consistently where relevant

**Code Naming Conventions:**
- Python modules and files use `snake_case`
- Classes use `PascalCase`
- Functions and variables use `snake_case`
- Abstract interfaces should use clear role-based names such as `SonosService`, `TransportConfig`, `ConfigLoader`

### Structure Patterns

**Project Organization:**
- Transport concerns live separately from Sonos domain logic
- Configuration loading and validation live separately from runtime tool handlers
- MCP tool definitions are grouped by capability area, not mixed into one large file
- Shared utility code should only exist when used across multiple modules; avoid premature helper sprawl

**File Structure Patterns:**
- `server` layer owns MCP bootstrap and transport wiring
- `tools` layer owns tool registration and thin request handling
- `services` or equivalent domain layer owns Sonos operations and business rules
- `config` layer owns configuration schema, loading, normalization, and validation
- Deploy assets such as Docker and Helm stay outside the application source tree

### Format Patterns

**Tool Response Formats:**
- Successful tool responses should be structured and predictable rather than ad hoc strings
- Error responses should distinguish user-correctable configuration or input issues from operational failures
- Domain errors should be translated into MCP-safe response payloads consistently

**Data Exchange Formats:**
- Internal and tool-facing structured fields use `snake_case`
- Date/time values use ISO 8601 strings when exposed
- Optional values should use explicit nullability patterns rather than sentinel magic values
- Collections should use consistent list structures for rooms, groups, queue items, favourites, and playlists

### Communication Patterns

**Transport and Service Boundaries:**
- MCP transport handlers should not call `SoCo` directly
- Tool handlers should delegate to a service layer
- The service layer should be transport-agnostic
- Transport-specific concerns must remain at the boundary

**Logging Patterns:**
- Use structured logs with consistent event names and contextual fields
- Distinguish user-facing messages from diagnostic logs
- Avoid leaking sensitive config or network details unless explicitly needed for diagnostics

### Process Patterns

**Error Handling Patterns:**
- Validate config at startup before normal operation
- Validate tool inputs before invoking Sonos operations
- Map errors into a small, consistent set of categories such as configuration error, validation error, Sonos connectivity error, and unexpected internal error
- Risk-sensitive actions such as volume changes should use explicit validation and safe guards

**Testing Patterns:**
- Unit tests should focus on configuration validation, service-layer logic, and error translation
- Integration tests should focus on transport wiring and tool/service behavior boundaries
- Avoid requiring real Sonos hardware for the majority of automated tests
- Hardware-dependent validation should be isolated from core automated test suites

### Enforcement Guidelines

**All AI Agents MUST:**
- Keep transport, config, and Sonos domain logic separated
- Use `snake_case` consistently for Python code, config fields, and tool parameters
- Add new tools within the existing capability-area structure rather than creating parallel patterns
- Reuse the shared error model and response conventions
- Place tests according to the agreed structure instead of inventing local conventions

**Pattern Enforcement:**
- Architecture and code review should reject direct `SoCo` calls from transport/bootstrap layers
- New modules should be checked for naming and placement consistency
- Pattern violations should be corrected before new conventions are allowed to spread

### Pattern Examples

**Good Examples:**
- `tools/playback.py` defines thin MCP tool handlers and delegates to `SonosService`
- `config/models.py` defines typed config schemas and validation rules
- `services/sonos_service.py` owns operational logic such as room lookup, volume validation, and queue actions

**Anti-Patterns:**
- Putting MCP bootstrap, config parsing, and Sonos control logic in one file
- Mixing `camelCase` and `snake_case` across config, tools, and code
- Returning arbitrary free-form error strings with no consistent structure
- Writing tests only around transport entry points while leaving service logic untested

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
soniq/
├── README.md
├── Makefile
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── src/
│   └── soniq_mcp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── server.py
│       ├── logging_config.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── loader.py
│       │   ├── defaults.py
│       │   └── validation.py
│       ├── transports/
│       │   ├── __init__.py
│       │   ├── stdio.py
│       │   ├── streamable_http.py
│       │   └── bootstrap.py
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── playback.py
│       │   ├── volume.py
│       │   ├── queue.py
│       │   ├── groups.py
│       │   ├── favourites.py
│       │   ├── playlists.py
│       │   ├── system.py
│       │   └── setup_support.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── sonos_service.py
│       │   ├── room_service.py
│       │   ├── queue_service.py
│       │   ├── group_service.py
│       │   ├── favourites_service.py
│       │   └── diagnostics_service.py
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── soco_adapter.py
│       │   └── discovery_adapter.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── requests.py
│       │   ├── responses.py
│       │   └── errors.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── exceptions.py
│       │   ├── models.py
│       │   └── safety.py
│       └── utils/
│           ├── __init__.py
│           ├── network.py
│           ├── formatting.py
│           └── version.py
├── tests/
│   ├── unit/
│   │   ├── config/
│   │   ├── tools/
│   │   ├── services/
│   │   ├── domain/
│   │   └── utils/
│   ├── integration/
│   │   ├── transports/
│   │   ├── server/
│   │   ├── adapters/
│   │   └── config/
│   ├── contract/
│   │   ├── tool_schemas/
│   │   ├── response_formats/
│   │   └── error_mapping/
│   ├── smoke/
│   │   ├── stdio/
│   │   └── streamable_http/
│   ├── fixtures/
│   │   ├── configs/
│   │   ├── payloads/
│   │   └── sonos/
│   ├── fakes/
│   │   ├── fake_soco.py
│   │   └── fake_transport_clients.py
│   └── conftest.py
├── helm/
│   └── soniq/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── ingress.yaml
│           ├── configmap.yaml
│           └── secret.yaml
├── docs/
│   ├── architecture.md
│   ├── setup/
│   │   ├── stdio.md
│   │   ├── docker.md
│   │   ├── helm.md
│   │   └── troubleshooting.md
│   ├── integrations/
│   │   ├── claude-desktop.md
│   │   ├── chatgpt-mcp.md
│   │   ├── home-assistant.md
│   │   └── n8n.md
│   └── prompts/
│       └── example-uses.md
└── .github/
    └── workflows/
        ├── ci.yml
        └── publish.yml
```

### Architectural Boundaries

**API Boundaries:**
- MCP transport entry points live in `transports/` and `server.py`
- Tool registration and tool-facing request handling live in `tools/`
- No transport module calls `SoCo` directly

**Component Boundaries:**
- `tools/` handles MCP-facing inputs and outputs
- `services/` owns business logic and orchestration
- `adapters/` owns external library integration with `SoCo`
- `config/` owns configuration lifecycle from load to validation
- `domain/` owns internal models, safety rules, and exception taxonomy

**Service Boundaries:**
- `SonosService` is the main orchestration boundary for core Sonos operations
- Capability-specific services may support it, but they should not create parallel transport or config logic
- Diagnostics and setup support stay separate from playback logic

**Data Boundaries:**
- No application database in MVP
- Authoritative runtime state comes from Sonos devices plus validated application config
- Request/response schemas are separated from domain models

### Requirements to Structure Mapping

**Feature Mapping:**
- Core Sonos control → `tools/playback.py`, `tools/volume.py`, `services/sonos_service.py`, `adapters/soco_adapter.py`
- Queue, playlists, favourites → `tools/queue.py`, `tools/playlists.py`, `tools/favourites.py`, related services
- Grouping and topology → `tools/groups.py`, `services/group_service.py`, `services/room_service.py`
- MCP integration and transport modes → `server.py`, `transports/stdio.py`, `transports/streamable_http.py`
- Setup and onboarding support → `config/`, `tools/setup_support.py`, `services/diagnostics_service.py`, `docs/setup/`
- Safety and permission boundaries → `domain/safety.py`, `schemas/errors.py`, transport/bootstrap config surfaces
- Documentation and examples → `docs/setup/`, `docs/integrations/`, `docs/prompts/`

**Cross-Cutting Concerns:**
- Structured logging → `logging_config.py`
- Error taxonomy and translation → `domain/exceptions.py`, `schemas/errors.py`
- Request/response consistency → `schemas/requests.py`, `schemas/responses.py`
- Environment defaults and validation → `config/defaults.py`, `config/validation.py`

### Integration Points

**Internal Communication:**
- Transport → tools → services → adapters
- Config is loaded at startup, validated once, then injected downward
- Domain exceptions move upward and are translated into consistent MCP-safe responses

**External Integrations:**
- Sonos devices via `SoCo`
- MCP clients via `stdio` and `Streamable HTTP`
- Deployment environment via env vars, Helm values, and container runtime config

**Data Flow:**
- Client request enters through transport
- Tool handler validates request shape
- Service applies business logic and safety checks
- Adapter performs Sonos interaction
- Result is normalized into response schema
- Response returns through the MCP transport boundary

### File Organization Patterns

**Configuration Files:**
- Root-level packaging and runtime config files stay at the repository root
- Application config code lives only in `src/soniq_mcp/config/`
- Deployment config lives only in `helm/` and container files

**Source Organization:**
- Source code is organized by boundary and capability, not by arbitrary utility buckets
- Tools are thin, services are authoritative, adapters isolate third-party specifics

**Test Organization:**
- Unit tests validate config parsing, defaults, validation rules, service-layer business logic, safety rules, and utility behavior
- Integration tests validate MCP server bootstrap for `stdio` and `Streamable HTTP`, tool-to-service-to-adapter flow, config loading in realistic runtime scenarios, and diagnostics behavior where practical
- Contract tests validate tool names, parameter schemas, response formats, and error mappings remain stable across transports
- Smoke tests prove `stdio` mode, `Streamable HTTP` mode, and containerized runtime boot and respond as expected
- Most tests must run without real Sonos hardware; hardware-dependent tests must be isolated and never block core automated validation

**Asset Organization:**
- Documentation is treated as part of the product surface
- No frontend asset tree is needed in MVP

### Development Workflow Integration

**Developer Command Surface:**
- `Makefile` is the canonical quick-reference for lint, test, smoke, Docker, Helm, and validation commands
- Common targets should include unit, integration, contract, smoke, and full test runs
- Commands should wrap `uv`, Docker, and Helm consistently so humans and agents use the same entry points

**Development Server Structure:**
- Local developers can run the application directly from `src/soniq_mcp/__main__.py` or `server.py`
- Transport bootstrap remains explicit and environment-driven

**Build Process Structure:**
- `uv` and `pyproject.toml` define package and dependency flow
- Docker build packages the same application structure used locally

**Deployment Structure:**
- Docker is the deployable artifact
- Helm templates wrap the containerized application for self-hosted deployment
- Docs and config examples mirror supported deployment paths

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
The architecture is internally coherent. Python, `uv`, the official MCP Python SDK, and `SoCo` fit the project scope and support the required local and remote MCP modes. The decision to use `stdio` plus `Streamable HTTP`, remain stateless in MVP, and package via Docker and Helm is compatible with the single-household home-use deployment model.

**Pattern Consistency:**
The implementation patterns support the architectural decisions well. Naming, structure, transport boundaries, config handling, error translation, and test placement all align with the chosen stack and reduce the risk of agent divergence.

**Structure Alignment:**
The project structure reflects the chosen boundaries clearly. Transport, tools, services, adapters, config, domain, tests, docs, and deployment assets each have a distinct place. The structure supports both maintainability and multi-agent consistency.

### Requirements Coverage Validation ✅

**Feature Coverage:**
All major FR categories have an architectural home:
- Sonos control, queueing, grouping, favourites, and playlists are supported through tools, services, and adapters
- MCP local and remote integration is supported through transport and bootstrap boundaries
- Setup, validation, diagnostics, and documentation are reflected as first-class architecture concerns
- Permission and safety constraints are reflected through config, domain, and response/error boundaries

**Functional Requirements Coverage:**
All 55 functional requirements are architecturally supported at the boundary level. No FR category appears orphaned or structurally unsupported.

**Non-Functional Requirements Coverage:**
The architecture addresses the major NFR themes:
- Performance through a lightweight stateless design
- Reliability through validation, explicit boundaries, and deterministic error handling
- Security through safe default exposure and boundary-layer controls
- Maintainability through strict module separation
- Integration through consistent transport and tool contracts
- Home-scale scalability through stateless deployment assumptions

### Implementation Readiness Validation ✅

**Decision Completeness:**
The core implementation-blocking decisions are present: runtime, transport, packaging, service boundaries, validation strategy, security posture, and deployment approach.

**Structure Completeness:**
The structure is sufficiently concrete for implementation. Files and directories are specific enough that future stories can map into them without inventing new architecture.

**Pattern Completeness:**
The major conflict points for AI agents are covered: naming, module boundaries, response/error consistency, config shape, and testing boundaries.

### Gap Analysis Results

**Critical Gaps:** None for MVP architecture definition.

**Important Gaps:**
- CI workflow behavior is named but not yet specified in operational detail
- Hardware-dependent testing policy will need explicit implementation-time conventions
- Remote exposure guidance will still need to be translated into concrete deployment documentation and examples

**Nice-to-Have Gaps:**
- Optional contributor guidelines document for humans and agents
- More explicit conventions for versioning and release packaging
- A dedicated architecture decision record section for future changes

### Validation Issues Addressed

The architecture intentionally avoids over-designing persistence, multi-household support, and advanced discovery features in MVP. These are not omissions; they are deferred decisions aligned with the PRD scope.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**
- [x] Critical decisions documented
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Deployment model specified

**✅ Implementation Patterns**
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION PLANNING

**Confidence Level:** High

**Key Strengths:**
- Strong alignment with the PRD and product differentiator
- Clear separation of concerns for transport, domain logic, config, and deployment
- Implementation patterns designed to prevent agent drift
- Testing strategy considered as part of architecture, not as an afterthought
- Setup, diagnostics, and docs treated as part of the product architecture

**Areas for Future Enhancement:**
- Persistence strategy for post-MVP features
- Discovery architecture for broader network modes
- Advanced async/event-driven capabilities
- Explicit release and versioning conventions

### Implementation Handoff

**AI Agent Guidelines:**
- Follow architectural boundaries exactly as documented
- Do not bypass service boundaries from transport or tool layers
- Preserve naming, config, and response conventions
- Treat docs, setup, and diagnostics as product-critical work

**First Implementation Priority:**
Initialize the project with the agreed starter foundation:

```bash
uv init --app soniq
cd soniq
uv add "mcp[cli]" soco
```
