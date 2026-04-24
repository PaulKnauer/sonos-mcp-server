---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd.md'
  - '/Users/paul/github/sonos-mcp-server/docs/sonos-mcp-research.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd-optional-auth.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/oidc-authelia-integration-assessment-2026-04-22.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/research/technical-oidc-fastmcp-authelia-research-2026-04-22.md'
workflowType: 'architecture'
project_name: 'sonos-mcp-server'
user_name: 'Paul'
date: '2026-03-23'
lastStep: 8
status: 'in-progress-refresh-phase3'
completedAt: '2026-03-23'
updatedAt: '2026-04-23'
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

## Project Context Analysis Refresh

### Requirements Overview

**Functional Requirements:**
The updated PRD expands the Sonos control surface beyond the original MVP set. In addition to playback, volume, queue, grouping, favourites, playlists, and deployment/runtime capabilities, the architecture must now support a planned capability expansion across two follow-on bands. Tier 1 adds play modes, seek, sleep timer, audio EQ, and input switching. Tier 2 adds alarm management, playlist CRUD, group-level volume and mute control, and local music library access. Architecturally, this means the system must support more capability-specific tool groupings and service boundaries without breaking the existing transport-agnostic design.

**Non-Functional Requirements:**
The revised NFRs now place explicit architectural pressure on latency, repeatability, failure handling, safety enforcement, transport parity, and supported household scale. The architecture must support initial MCP tool responses within defined latency targets, deterministic handling of repeated actions, safe failure responses, documented deployment defaults, and testable parity between local and networked runtime modes. These NFRs make testing, schema consistency, and safety rules more central to the architecture than before.

**Scale & Complexity:**
This remains a medium-complexity brownfield architecture refresh for a self-hosted developer tool and MCP integration service. Complexity now comes less from transport and deployment uncertainty and more from expanding the control surface while preserving clean internal boundaries, maintainability, and predictable behavior.

- Primary domain: developer tool / MCP integration service
- Complexity level: medium
- Estimated architectural components: 8-10 major components

### Technical Constraints & Dependencies

The architecture remains constrained by Python as the implementation language, `SoCo` as the Sonos integration library, and MCP-compatible transports for both local and deployed use. The system is still scoped to a single Sonos household and should default to local or trusted home-network exposure. Static speaker configuration remains the deployment-friendly baseline. The updated PRD adds pressure to model more Sonos capability families explicitly, especially advanced playback controls, audio settings, input switching, alarms, and music library access, while preserving the existing adapter boundary around `SoCo`.

### Cross-Cutting Concerns Identified

Cross-cutting concerns now include transport abstraction, configuration and preflight validation, permission-aware tool exposure, safe control semantics for room and volume actions, deterministic error handling, capability-family module growth, Sonos coordinator and device guard handling, deployment portability, and documentation-driven onboarding. The architecture must also preserve parity between direct AI-client usage and agent-mediated usage as the tool surface expands.

## Starter Template Evaluation Refresh

### Primary Technology Domain

Python backend / MCP integration service based on the updated PRD and the existing brownfield architecture

### Starter Options Considered

1. Continue with the existing `uv` application scaffold + Python MCP SDK + `SoCo` foundation
2. Reframe around a different Python MCP server scaffold
3. Re-architect around a heavier web-backend starter

### Selected Starter: Continue with `uv` application scaffold + Python MCP SDK + `SoCo`

**Rationale for Selection:**
The updated PRD expands the Sonos capability surface, but it does not change the core architecture category. This remains a self-hosted Python MCP server with local `stdio` and deployed HTTP transport, packaging via `PyPI` and Docker, and a service-oriented internal structure around Sonos operations. The existing `uv` application scaffold remains the best fit because it keeps the project lightweight, packaging-friendly, and aligned with the existing architecture boundaries. A heavier starter would add complexity without solving the real phase-2 problem, which is capability expansion inside the existing `tools -> services -> adapters` model.

**Initialization Command:**

```bash
uv init --app soniq
cd soniq
uv add "mcp[cli]" soco
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
Python application project managed through `uv`, suitable for local execution, packaging, and self-hosted runtime deployment.

**Styling Solution:**
Not applicable. The product remains a backend / integration service without a first-party frontend.

**Build Tooling:**
Python packaging and dependency management through `uv` and `pyproject.toml`, consistent with the existing repository direction.

**Testing Framework:**
Not provided by default; testing remains an explicit architecture concern handled by repository conventions.

**Code Organization:**
Minimal application scaffold that supports the existing transport, tools, services, adapters, config, and domain separation already established in the architecture.

**Development Experience:**
Fast local setup, reproducible environments, dependency locking, and a clean base for phase-2 capability expansion without introducing unnecessary framework opinions.

**Phase-2 Implication:**
No starter change is required for the updated PRD. Phase 2 should be treated as an internal architecture and module-expansion exercise, not a platform reset.

**Note:** The original starter choice remains valid. Phase-2 implementation should build on the current base rather than replacing it.

## Core Architectural Decisions Refresh

### Decision Priority Analysis

**Critical Decisions (Block Phase-2 Implementation):**
- Preserve the existing `tools -> services -> adapters` boundary model
- Keep `SoCo` as the only direct Sonos integration boundary through adapters
- Expand capability-specific service boundaries for Tier 1 and Tier 2 features rather than overloading the original core services
- Preserve stateless runtime assumptions for Tier 1 and treat Tier 2 persistence needs as explicit exceptions, not silent architectural drift

**Important Decisions (Shape Architecture):**
- Introduce clearer capability-area grouping for advanced playback controls, audio settings, input switching, alarms, playlist lifecycle operations, group audio controls, and music library access
- Centralize Sonos coordinator and device-capability guards in service-layer logic rather than scattering them across tool handlers
- Preserve response-shape and parameter consistency as the tool surface expands
- Extend testing boundaries to cover the new capability families without requiring real hardware in the default automated path

**Deferred Decisions (Post-Phase-2):**
- Event subscription architecture
- Persistent storage for features that later exceed Sonos-backed state alone
- Discovery-first remote topologies beyond the current deployment model

### Data Architecture

Phase 2 should remain stateless by default. Tier 1 capabilities fit the existing model because their authoritative state remains on Sonos devices. Tier 2 capabilities such as alarms, playlist CRUD, and music library access should still default to Sonos-backed state and SoCo object models, with no new application database introduced unless a later requirement clearly exceeds that boundary.

### Authentication & Security

No architectural change from the current model. Phase-2 capabilities increase the action surface, so the existing permission-aware tool exposure and safe-default runtime posture become more important, but they do not require a new authentication architecture.

### API & Communication Patterns

The MCP surface should continue to expose the same transport-neutral capability model across `stdio` and HTTP. Phase 2 should add new tool families without changing the transport model or introducing transport-specific semantics.

### Infrastructure & Deployment

No starter or deployment reset is required. Docker, Helm, and local Python execution remain the correct deployment base for phase 2 capability expansion.

### Decision Impact Analysis

**Implementation Sequence:**
1. Add or refine capability-area tool modules for Tier 1 features
2. Introduce or extend service-layer boundaries for advanced playback and audio control
3. Add service and adapter support for Tier 2 capability families
4. Extend response schemas, error mappings, and safety rules for the new tools
5. Extend unit, integration, and contract tests for the expanded surface

**Cross-Component Dependencies:**
The new capability families increase pressure on service boundaries, adapter method organization, error-taxonomy reuse, and test coverage. The architecture must prevent phase-2 growth from collapsing back into a single oversized service or tool module.

## Implementation Patterns Refresh

### Pattern Categories Defined

**Critical Conflict Points Identified:**
Phase 2 introduces new conflict points around capability-family expansion, service ownership, Sonos guard handling, response normalization, and test placement. Without explicit rules, different AI agents could extend the codebase in incompatible ways while adding Tier 1 and Tier 2 features.

### Naming Patterns

**Tool Module Naming Conventions:**
- Keep tool modules grouped by user-facing capability area, not by low-level SoCo object names
- Use explicit module names such as `playback.py`, `audio.py`, `inputs.py`, `alarms.py`, `playlists.py`, `library.py`, and `groups.py`
- Do not create overlapping modules with ambiguous boundaries such as both `play_modes.py` and `playback_controls.py` unless one is clearly a submodule pattern adopted project-wide

**Service Naming Conventions:**
- Service names should reflect stable business capability boundaries
- Prefer `PlaybackService`, `AudioSettingsService`, `InputService`, `AlarmService`, `PlaylistService`, `LibraryService`, and `GroupService` over a single ever-growing generic service
- Shared orchestration may still exist in `SonosService`, but feature ownership should move toward narrower services as capability breadth increases

**Adapter Naming Conventions:**
- `SoCoAdapter` remains the only adapter that talks directly to `SoCo`
- New adapter-facing methods should be capability-grouped by concern within the adapter surface, not added ad hoc without organization

### Structure Patterns

**Project Organization:**
- Tier 1 and Tier 2 expansions should extend the existing `tools/`, `services/`, and `adapters/` boundaries rather than introduce parallel architecture layers
- New capabilities should be added by capability family, not by user story number or temporary epic grouping
- If a new feature area has distinct validation rules, Sonos capability guards, and response normalization, it should get its own service module

**File Structure Patterns:**
- `tools/` owns MCP-facing handlers only
- `services/` owns business rules, Sonos coordinator checks, device capability guards, safety rules, and orchestration
- `adapters/` owns all direct SoCo calls and SoCo object translations
- `schemas/` owns request, response, and error-shape consistency for new tool families
- Tests should mirror the same capability boundaries the source tree uses

### Format Patterns

**Tool Response Formats:**
- New advanced-control tools should return the same structured response style already used elsewhere
- State-changing tools should return the affected room or coordinator plus the resulting normalized state when practical
- Browsing and listing tools should return bounded list structures with explicit pagination or continuation semantics when required by the PRD

**Data Exchange Formats:**
- Preserve `snake_case` across tool parameters, response fields, config fields, and internal models
- Normalize Sonos-specific object data before it leaves the service boundary
- Raw SoCo objects or library-specific structures must not escape directly through MCP responses

### Communication Patterns

**Service-to-Adapter Communication:**
- Tools call services
- Services call adapters
- Services must own Sonos-specific eligibility checks such as coordinator-only operations, device input support, soundbar-only behavior, and group-level targeting rules
- Adapters should expose low-level capability methods but should not decide user-facing safety or permission behavior

**Capability Guard Patterns:**
- Input switching, coordinator-only play modes, alarm operations, and group-level controls should use explicit guard methods or validation paths in services
- Guard failures should map to consistent typed domain errors, not ad hoc free-form messages

**Tool Parameter Validation Convention:**
- FastMCP silently coerces tool parameter types before handlers run (e.g. `"5"` → `5`, `True` → `1`). This masks service-layer validation failures.
- For any control tool whose parameters require service-layer validation (integer ranges, enum values, boolean checks), use the following pattern to preserve raw inputs while keeping an explicit MCP-visible schema type:

  ```python
  from typing import Annotated
  from pydantic import Field

  def set_bass(room: str, level: Annotated[object, Field(json_schema_extra={"type": "integer"})]) -> dict:
      ...
  ```

- This ensures the generated MCP schema exposes `"type": "integer"` to clients while raw inputs (including invalid ones) still reach the service layer unchanged.
- **Read-only tools and tools whose parameters FastMCP can safely coerce are exempt.**
- Contract tests for setter tools MUST assert the MCP-visible schema type for each parameter (e.g. `assert schema["properties"]["level"]["type"] == "integer"`). This is the enforcement mechanism — schema drift will be caught in CI, not review.

### Process Patterns

**Error Handling Patterns:**
- Advanced capability failures should distinguish unsupported capability, invalid target state, configuration error, Sonos communication failure, and unexpected internal failure
- Music library and playlist operations should use deterministic error categories for empty results, unsupported operations, and malformed selection inputs

**Testing Patterns:**
- Unit tests should cover service-layer rules for play modes, EQ, inputs, alarms, playlists, group audio, and library pagination
- Adapter tests should verify SoCo translation logic separately from business rules
- Contract tests should cover new tool names, parameters, normalized responses, and error mappings
- Hardware-dependent behavior should stay isolated behind fakes or optional integration tests

### Enforcement Guidelines

**All AI Agents MUST:**
- Add new phase-2 capabilities within the existing `tools -> services -> adapters` model
- Keep Sonos capability guards in services, not tools or transports
- Normalize SoCo outputs before returning MCP responses
- Reuse shared schema and error conventions for every new capability family
- Extend tests in the same capability-oriented structure as the source modules

**Pattern Enforcement:**
- Reject direct `SoCo` calls from tools, transports, or bootstrap code
- Reject new capability modules that overlap existing ownership without a clear boundary
- Reject raw SoCo object leakage in MCP-facing responses

### Pattern Examples

**Good Examples:**
- `tools/audio.py` delegates bass, treble, and loudness operations to `AudioSettingsService`
- `tools/inputs.py` delegates line-in and TV switching to `InputService`, which enforces device-support guards before calling `SoCoAdapter`
- `tools/alarms.py` delegates lifecycle operations to `AlarmService`, which normalizes alarm objects into stable response schemas
- `tools/library.py` delegates browsing and selection flows to `LibraryService`, which enforces bounded result behavior

**Anti-Patterns:**
- Adding every new Tier 1 and Tier 2 feature to `tools/playback.py` and `services/sonos_service.py`
- Returning raw SoCo alarm or music-library objects through MCP responses
- Checking device capability support inside tool handlers instead of service logic
- Mixing playlist playback, playlist CRUD, and library browsing into one generic `media` module without clear ownership

## Project Structure & Boundaries Refresh

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
│       │   ├── audio.py
│       │   ├── inputs.py
│       │   ├── alarms.py
│       │   ├── library.py
│       │   ├── system.py
│       │   └── setup_support.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── sonos_service.py
│       │   ├── room_service.py
│       │   ├── queue_service.py
│       │   ├── group_service.py
│       │   ├── favourites_service.py
│       │   ├── playlist_service.py
│       │   ├── playback_service.py
│       │   ├── audio_settings_service.py
│       │   ├── input_service.py
│       │   ├── alarm_service.py
│       │   ├── library_service.py
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
├── docs/
│   ├── architecture.md
│   ├── setup/
│   ├── integrations/
│   └── prompts/
└── .github/
    └── workflows/
```

### Architectural Boundaries

**API Boundaries:**
- MCP transport entry points remain in `transports/` and `server.py`
- Tool registration and MCP-facing request handling remain in `tools/`
- No transport module calls `SoCo` directly

**Component Boundaries:**
- `playback.py` and `playback_service.py` own playback-state and coordinator-oriented playback controls
- `audio.py` and `audio_settings_service.py` own bass, treble, and loudness
- `inputs.py` and `input_service.py` own line-in and TV switching with device-support guards
- `alarms.py` and `alarm_service.py` own alarm lifecycle operations
- `playlists.py` and `playlist_service.py` own playlist playback plus playlist CRUD
- `library.py` and `library_service.py` own local music-library browsing and selection
- `groups.py` and `group_service.py` continue to own topology plus group-level audio controls

**Service Boundaries:**
- `SonosService` may remain as shared orchestration or compatibility layer, but it should not become the primary home for all new phase-2 logic
- Feature-specific services own business rules, Sonos capability guards, and normalization
- `SoCoAdapter` remains the only direct library boundary

**Data Boundaries:**
- No application database is introduced for phase 2
- Sonos devices and validated config remain the authoritative state sources
- Alarm, playlist, and library objects are normalized before they cross out of services

### Requirements to Structure Mapping

**Feature Mapping:**
- Core playback and Tier 1 play modes / seek / sleep timer → `tools/playback.py`, `services/playback_service.py`, `adapters/soco_adapter.py`
- Audio EQ → `tools/audio.py`, `services/audio_settings_service.py`
- Input switching → `tools/inputs.py`, `services/input_service.py`
- Queue, favourites, playlist playback, playlist CRUD → `tools/queue.py`, `tools/favourites.py`, `tools/playlists.py`, `services/queue_service.py`, `services/favourites_service.py`, `services/playlist_service.py`
- Grouping, topology, group volume and mute → `tools/groups.py`, `services/group_service.py`, `services/room_service.py`
- Alarm management → `tools/alarms.py`, `services/alarm_service.py`
- Local music library → `tools/library.py`, `services/library_service.py`
- Setup, diagnostics, and onboarding → `config/`, `tools/setup_support.py`, `services/diagnostics_service.py`, `docs/setup/`

**Cross-Cutting Concerns:**
- Safety and guard rules → `domain/safety.py`, service-layer validation paths
- Request/response consistency → `schemas/requests.py`, `schemas/responses.py`, `schemas/errors.py`
- Error taxonomy and translation → `domain/exceptions.py`, `schemas/errors.py`
- Tests for phase-2 features → capability-aligned files under `tests/unit/`, `tests/integration/`, and `tests/contract/`

### Integration Points

**Internal Communication:**
- Transport → tools → services → adapters
- New capability services communicate through shared domain models and exception taxonomy rather than direct tool-to-tool reuse

**External Integrations:**
- Sonos devices through `SoCo`
- MCP clients through `stdio` and `Streamable HTTP`
- Deployment/runtime config through env vars, Docker, and Helm values

**Data Flow:**
- Request enters transport
- Tool validates request shape
- Capability service enforces safety and Sonos eligibility rules
- Adapter performs Sonos interaction
- Service normalizes result into stable response schema
- Transport returns MCP-safe response

## Architecture Validation Refresh

### Coherence Validation ✅

**Decision Compatibility:**
The refreshed architecture remains internally coherent. Python, `uv`, the Python MCP SDK direction, and `SoCo` still fit the product scope and the revised PRD. The addition of Tier 1 and Tier 2 capability families does not conflict with the original transport, deployment, or stateless-runtime decisions.

**Pattern Consistency:**
The implementation patterns now better match the expanded capability surface. Naming, service ownership, adapter isolation, guard placement, and response normalization rules all support the new module families without introducing architectural drift.

**Structure Alignment:**
The refreshed project structure now explicitly supports the new feature areas. The addition of `audio`, `inputs`, `alarms`, `library`, and more explicit service modules keeps the original boundary model intact while preventing uncontrolled growth inside generic modules.

### Requirements Coverage Validation ✅

**Feature Coverage:**
All major PRD capability bands now have an architectural home:
- MVP control surface remains supported
- Tier 1 expansion areas map to explicit tool and service boundaries
- Tier 2 expansion areas map to explicit tool and service boundaries
- setup, diagnostics, deployment, and documentation remain first-class architecture concerns

**Functional Requirements Coverage:**
The architecture now supports the revised PRD requirement set, including the expanded advanced-control, alarm, playlist lifecycle, group-audio, and library requirements.

**Non-Functional Requirements Coverage:**
The revised NFR set is better reflected in the architecture through:
- transport-neutral response expectations
- stricter service and adapter boundaries
- expanded test coverage expectations
- explicit safety and guard placement
- deployment/runtime consistency across local and remote modes

### Implementation Readiness Validation ✅

**Decision Completeness:**
The architecture now includes the critical phase-2 decisions needed to prevent implementation ambiguity around service ownership, capability grouping, and Sonos-specific validation behavior.

**Structure Completeness:**
The refreshed structure is specific enough to support epic and story generation for the expanded PRD. The new modules are named, placed, and tied to requirements.

**Pattern Completeness:**
The main phase-2 conflict points are addressed: naming, service ownership, raw SoCo leakage, advanced capability guards, and capability-family test placement.

### Gap Analysis Results

**Critical Gaps:** None for phase-2 architecture definition.

**Important Gaps:**
- CI/test strategy may later need more explicit treatment for hardware-adjacent features such as alarms and music library flows
- If Tier 2 grows beyond Sonos-backed state cleanly, persistence decisions may need to be revisited explicitly
- Release/versioning guidance in architecture may still benefit from a more explicit ADR-style addendum later

**Nice-to-Have Gaps:**
- contributor guidance for adding new capability families
- a capability-to-module matrix optimized for epic planning
- explicit story-splitting guidance for tool, service, and adapter implementation slices

### Validation Issues Addressed

The original architecture was complete but stale relative to the updated PRD. The refresh resolves that by:
- aligning requirements coverage with the expanded PRD
- adding explicit capability-family module ownership
- preserving the original architectural foundation while avoiding a phase-2 reset

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Updated PRD analyzed
- [x] Expanded capability scope assessed
- [x] Technical constraints revalidated
- [x] Cross-cutting concerns refreshed

**✅ Architectural Decisions**
- [x] Core phase-2 decisions documented
- [x] Existing starter decision revalidated
- [x] Service-boundary expansion defined
- [x] Stateless assumptions reaffirmed

**✅ Implementation Patterns**
- [x] Capability-family naming conventions established
- [x] Guard-placement rules defined
- [x] Response normalization rules specified
- [x] Phase-2 testing patterns documented

**✅ Project Structure**
- [x] Expanded directory structure defined
- [x] New capability modules mapped
- [x] Requirements-to-structure mapping refreshed
- [x] Integration points updated

### Architecture Readiness Assessment

**Overall Status:** READY FOR EPIC AND STORY PLANNING

**Confidence Level:** High

**Key Strengths:**
- preserves a coherent architecture base
- explicitly accommodates phase-2 capability growth
- reduces ambiguity for AI-agent implementation
- keeps the architecture aligned with the revised PRD

**Areas for Future Enhancement:**
- persistence strategy for any post-phase-2 stateful needs
- more explicit release/versioning architecture notes
- optional contributor guidance for module expansion

### Implementation Handoff

**AI Agent Guidelines:**
- follow the refreshed capability-family boundaries exactly
- do not collapse new features back into generic modules without justification
- keep service-layer guards and adapter isolation intact
- treat the architecture refresh as authoritative for phase-2 feature placement

**First Implementation Priority:**
Use this refreshed architecture as the source of truth for epic and story decomposition of the Tier 1 and Tier 2 PRD expansion.

## Project Context Analysis — Phase 3 (Optional Auth)

### Requirements Overview

**Functional Requirements:**
The optional auth PRD adds a credential-gate for the HTTP transport only. 27 FRs span seven areas: authentication mode configuration, static Bearer token validation, OIDC JWT validation (RS256, JWKS, key-rotation retry), startup preflight checks, strict no-op backward compatibility for `AUTH_MODE=none` and stdio, secret masking for the static token, and documentation/deployment guidance for all three modes across pip, Docker, and Helm. The architecture must expand the configuration model, introduce a new auth module, and wire a `TokenVerifier` into the server factory — touching only six files in the existing source tree.

**Non-Functional Requirements:**
12 NFRs add architectural pressure in three areas: performance (< 5ms overhead for any auth path; zero overhead for `AUTH_MODE=none`; JWKS cached to eliminate per-request network calls), security (constant-time static token comparison; JWT validation fails closed; static token masked from all outputs; HTTPS-only JWKS; expiry validated on every request), and integration (provider-agnostic OIDC; FastMCP `TokenVerifier` as the sole integration point; `SSL_CERT_FILE` as the CA cert mechanism; `verify_token` returns `None`, never raises, for invalid tokens).

**Scale & Complexity:**
This is a bounded brownfield feature addition to a running production system. Complexity arises from the opt-in contract (zero impact on the common path), the FastMCP `TokenVerifier` protocol wiring, PyJWT JWKS caching, self-signed CA cert handling, and maintaining exact backward compatibility across all three distribution channels.

- Primary domain: developer tool / MCP integration service (unchanged)
- Complexity level: low-medium (well-researched, bounded scope)
- Estimated new architectural components: 2 (auth module, auth config fields)

### Technical Constraints & Dependencies

The architecture is constrained by:
- `mcp[cli]>=1.26.0` — `TokenVerifier` Protocol is the only supported integration point; no ASGI middleware bypass; no Uvicorn wrapping
- `PyJWT>=2.8` — sole new production dependency; `PyJWKClient` with `ssl_context` since 2.8.0; `cryptography>=46.0.7` already present
- FastMCP's auth wiring requires `AuthSettings` alongside `token_verifier` in the `FastMCP()` constructor; `AUTH_MODE=none` must leave the constructor call identical to current behaviour
- MCP spec (April 2026 draft): authorization is OPTIONAL for HTTP, NOT applicable for stdio
- Authelia client pre-registration required via Terraform (dynamic registration unsupported)
- Self-signed homelab CA must be supplied via `SSL_CERT_FILE` env var or explicit `oidc_ca_bundle` config path

### Cross-Cutting Concerns Identified

Auth is explicitly a **transport concern**, not a domain concern. It must not reach tools, services, or adapters. Cross-cutting implications:
- Config model expansion (`SoniqConfig`) — new fields with `@model_validator` for consistency checks
- Preflight validation extension — OIDC startup JWKS connectivity check, static token presence check
- Secret masking — `auth_token` must never appear in logs, Pydantic serialisation, or tracebacks
- Stdio/HTTP transport parity — auth verifier constructed only for HTTP; stdio path is completely unaffected
- Deployment documentation — all three distribution channels require documented auth setup paths

## Starter Template Evaluation — Phase 3 (Optional Auth)

### Primary Technology Domain

Python backend / MCP integration service — no change from Phase 2

### Starter Options Considered

1. Continue with existing `uv` + `mcp[cli]` + SoCo foundation, adding `PyJWT>=2.8`
2. Introduce a higher-level auth framework (e.g. `authlib`, `fastapi-users`)
3. Use the separate `fastmcp` package (jlowin/fastmcp) which includes a built-in `JWTVerifier`

### Selected Starter: Continue with existing foundation + PyJWT>=2.8

**Rationale for Selection:**
The auth feature is a bounded addition to the existing application — not a platform change. The `mcp[cli]` 1.26.0 SDK already provides the `TokenVerifier` Protocol. `PyJWT>=2.8` provides `PyJWKClient` with JWKS caching and `ssl_context` support, and `cryptography>=46.0.7` (already a production dependency) supplies the RSA backend. No new framework is needed.

The separate `fastmcp` package was ruled out: it is a different package from `mcp[cli]`, the project is already committed to the official SDK, and switching would be a larger breaking change than the feature warrants.

**Dependency Addition:**

```toml
# pyproject.toml — add one line
"PyJWT>=2.8",
```

**Architectural Decisions Provided by Starter:**
No change to language, runtime, build tooling, testing framework, code organisation, or development experience. The sole change is one new production dependency and one new source module (`src/soniq_mcp/auth/`).

**Note:** No project re-initialisation is required. Phase 3 is a pure feature-addition inside the existing repository structure.

## Core Architectural Decisions — Phase 3 (Optional Auth)

### Decision Priority Analysis

**Critical Decisions (Block Phase-3 Implementation):**
- `AUTH_MODE` as a three-value enum: `none` | `static` | `oidc` — default `none`
- FastMCP `TokenVerifier` Protocol as the sole integration point — no ASGI bypass
- `PyJWT>=2.8` (`PyJWKClient`) as the JWT/JWKS library
- Auth wired exclusively in `create_server()` in `server.py` — never in tools, services, or adapters
- `AUTH_MODE=none` must leave the `FastMCP()` constructor call equivalent to current behaviour
- Static token stored as Pydantic `SecretStr` in `SoniqConfig` to prevent serialisation leakage

**Important Decisions (Shape Architecture):**
- `AuthSettings` is always required alongside `token_verifier` (FastMCP enforces this at construction time); for `auth_mode=static`, `issuer_url` is derived from the server's own HTTP base URL (`http://{host}:{port}`) — no external issuer, no arbitrary placeholder constant
- CA cert delivery: dual-path — `SSL_CERT_FILE` env var (zero-code, standard Python) as primary; `SONIQ_MCP_OIDC_CA_BUNDLE` config field as explicit optional override for Docker Compose and direct paths
- JWKS cache: in-memory via `PyJWKClient` — no external cache; single-instance assumption holds
- Preflight checks belong in `config/validation.py` `run_preflight()` — not in verifier constructors
- OIDC startup preflight performs a live JWKS connectivity check, aborting with an actionable error before accepting connections; static mode preflight checks only that `auth_token` is set
- Stdio transport: `auth_mode != none` with `transport=stdio` emits a preflight warning (not error)

**Deferred Decisions (Post-Phase-3):**
- RBAC / role-based claims validation
- Token acquisition helper scripts for AI agent clients
- Auth status in a health/readiness endpoint

### Data Architecture

No change. Auth state is not persisted. Verifier instances are constructed once at startup and held in memory for the process lifetime.

### Authentication & Security

Three-mode opt-in model:

- `auth_mode=none` (default): zero code path entered after startup; `FastMCP()` constructor identical to current
- `auth_mode=static`: `StaticBearerVerifier` uses `secrets.compare_digest` for constant-time comparison; token sourced from `SoniqConfig.auth_token` (`SecretStr`); never logged or serialised; `AuthSettings.issuer_url` derived from the server's own base URL
- `auth_mode=oidc`: `OIDCVerifier` uses `PyJWKClient` for JWKS fetch and in-memory caching; `jwt.decode()` validates signature, `iss`, `aud`, and `exp` atomically; returns `None` (never raises) for invalid tokens; JWKS refreshed on unknown `kid` to handle key rotation; custom CA cert supported via `ssl_context` built from `SSL_CERT_FILE` or `oidc_ca_bundle`

Both verifiers implement: `async verify_token(token: str) -> AccessToken | None`.

**Secret Handling:**
`SONIQ_MCP_AUTH_TOKEN` maps to `SoniqConfig.auth_token: SecretStr | None`. Pydantic `SecretStr` masks the value in `repr()`, `str()`, and model serialisation. `get_secret_value()` is called only inside `StaticBearerVerifier.verify_token()`.

**Security Properties:**
- Timing: `secrets.compare_digest` prevents token enumeration
- Fail-closed: JWT exceptions → `None` → FastMCP returns `401`
- HTTPS enforcement: `PyJWKClient` does not support plaintext HTTP JWKS URIs
- Audience binding: `AuthSettings.resource_server_url` binds tokens to this specific server per RFC 8707

### API & Communication Patterns

No change to the MCP tool surface. Auth is invisible at the tool/service level. FastMCP's `RequireAuthMiddleware` handles `401` before tool handlers are invoked.

### Infrastructure & Deployment

Three deployment paths gain documented auth configuration:
- **pip/uvx**: env vars only; no install changes
- **Docker**: env vars in `docker-compose.yml`; CA cert via volume mount + `SSL_CERT_FILE`
- **Helm (k3s)**: auth env vars in chart values; CA cert via ConfigMap + `subPath` mount; `SSL_CERT_FILE` in pod spec

No new infrastructure components. Authelia OIDC is an external dependency for OIDC mode only.

### Decision Impact Analysis

**Implementation Sequence:**
1. Add auth fields to `SoniqConfig` — `auth_mode` enum, `auth_token` (`SecretStr`), `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, `oidc_resource_url` — with `@model_validator` consistency checks
2. Extend `config/loader.py` env-var mappings for all new `SONIQ_MCP_AUTH_*` vars
3. Extend `config/validation.py` `run_preflight()` with auth config and OIDC JWKS connectivity checks
4. Implement `src/soniq_mcp/auth/verifiers.py` — `StaticBearerVerifier` and `OIDCVerifier`
5. Wire `TokenVerifier` + `AuthSettings` into `create_server()` in `server.py` behind `auth_mode != none` guard
6. Unit tests for both verifiers — mock JWKS; valid/expired/tampered/missing token cases
7. Extend smoke tests — 401 without token, 200 with valid token (`auth_mode=static`), stdio no-op
8. Add `docs/setup/authentication.md`; update `.env.example`
9. Helm chart and Docker Compose updates for auth env vars and CA cert mount

**Cross-Component Dependencies:**
Config changes gate everything. Verifier module depends on config. Server wiring depends on both. CI tests use `auth_mode=static` only — no Authelia dependency in the automated test environment.

## Implementation Patterns — Phase 3 (Optional Auth)

### Pattern Categories Defined

**Critical Conflict Points Identified:**
6 areas where AI agents could make incompatible choices implementing the auth feature:
- auth module structure and file layout
- `AuthMode` enum placement
- `SecretStr` access discipline
- JWKS client ownership and lifecycle
- preflight integration point
- auth failure logging discipline

### Naming Patterns

**Auth Module Naming:**
- The auth module is `src/soniq_mcp/auth/` — two files: `__init__.py` (exports `build_token_verifier`) and `verifiers.py` (class implementations)
- Verifier classes are named `StaticBearerVerifier` and `OIDCVerifier` — not `StaticVerifier`, `BearerVerifier`, `JWTVerifier`, or similar
- The factory function is `build_token_verifier(config: SoniqConfig) -> TokenVerifier` — not `create_`, `make_`, or `get_`

**Config Field Naming:**
- Enum type: `AuthMode` (values: `none`, `static`, `oidc`) — placed in `config/models.py` alongside `SoniqConfig`, not in the auth module
- Config fields: `auth_mode`, `auth_token`, `oidc_issuer`, `oidc_audience`, `oidc_jwks_uri`, `oidc_ca_bundle`, `oidc_resource_url`
- Env vars: `SONIQ_MCP_AUTH_MODE`, `SONIQ_MCP_AUTH_TOKEN`, `SONIQ_MCP_OIDC_ISSUER`, `SONIQ_MCP_OIDC_AUDIENCE`, `SONIQ_MCP_OIDC_JWKS_URI`, `SONIQ_MCP_OIDC_CA_BUNDLE`, `SONIQ_MCP_OIDC_RESOURCE_URL`

**Server Wiring Naming:**
- Private helper in `server.py`: `_build_auth_settings(config: SoniqConfig) -> AuthSettings` — prefixed `_`, never exported

### Structure Patterns

**Module Placement:**
- `AuthMode` enum lives in `config/models.py` — it is a config concern, not an auth-module concern
- `StaticBearerVerifier` and `OIDCVerifier` live in `auth/verifiers.py` — never in `server.py` or `config/`
- `build_token_verifier()` factory exported from `auth/__init__.py` — the only public surface of the auth module
- No auth logic in `tools/`, `services/`, `adapters/`, or `transports/`

**Preflight Placement:**
- Auth preflight checks are added to `config/validation.py` `run_preflight()` — not as a method on verifier classes, not as a standalone function, not in `server.py`
- OIDC connectivity check constructs a temporary `PyJWKClient` in `run_preflight()` solely for the connectivity test; it does not share state with the runtime verifier instance

**Test Placement:**
- Verifier unit tests: `tests/unit/auth/test_verifiers.py`
- Config validator tests for auth fields: `tests/unit/config/test_validation.py` (existing file, new test class)
- Smoke test extensions: existing `tests/smoke/streamable_http/test_streamable_http_smoke.py` — new test functions, not a new file

### Format Patterns

**`verify_token` Return Contract:**
- Both verifiers MUST return `None` for any invalid token — never raise into the FastMCP layer
- `OIDCVerifier.verify_token` catches `PyJWTError` and all subclasses; any uncaught exception is caught by a bare `except Exception` fallback that returns `None` and logs at `ERROR` level
- `AccessToken` is constructed with: `token=token`, `client_id` from JWT `client_id` or `sub` claim, `scopes` parsed from `scp` or `scope` claim, `expires_at` from `exp` claim

**`AuthSettings` Construction:**
- For `auth_mode=static`: `issuer_url` = `f"http://{config.http_host}:{config.http_port}"`, `resource_server_url` = `config.oidc_resource_url`
- For `auth_mode=oidc`: `issuer_url` = `config.oidc_issuer`, `resource_server_url` = `config.oidc_resource_url`
- `required_scopes` is always `None` — scope enforcement is deferred

### Communication Patterns

**Secret Access Discipline:**
- `config.auth_token.get_secret_value()` is called in exactly one place: inside `StaticBearerVerifier.verify_token()` — nowhere else
- The raw token value must never be assigned to a local variable with a longer scope than the comparison expression
- Log statements including config context must use `config.auth_token` (the `SecretStr` object), never its unwrapped value

**Auth Failure Logging:**
- Auth failures: `WARNING` level, no token content
- Successful auth: `DEBUG` level with `client_id` only
- OIDC JWKS cache misses: `DEBUG` level
- Startup preflight auth checks: `INFO` on success, `ERROR` on failure

**JWKS Client Lifecycle:**
- `PyJWKClient` is an instance variable on `OIDCVerifier`, initialised in `__init__` — not a module-level singleton, not recreated per request
- `ssl_context` is also constructed once in `__init__` — not per-request

### Process Patterns

**`server.py` Wiring Pattern:**

```python
# CORRECT — clean conditional, no auth code in main flow
def create_server(config: SoniqConfig) -> FastMCP:
    kwargs: dict[str, Any] = {}
    if config.auth_mode != AuthMode.NONE:
        kwargs["auth"] = _build_auth_settings(config)
        kwargs["token_verifier"] = build_token_verifier(config)
    app = FastMCP("soniq-mcp", **kwargs)
    register_all(app, config)
    return app
```

**Testing Pattern:**
- Unit tests for `OIDCVerifier` use `cryptography` (already present) to generate an in-process RSA key pair and sign test JWTs — no network, no Authelia, no external JWKS
- Unit tests for `StaticBearerVerifier` need no special fixtures — plain string comparison cases
- Smoke tests use `auth_mode=static` only; `auth_mode=oidc` is not tested in CI

### Enforcement Guidelines

**All AI Agents MUST:**
- Keep `AuthMode` enum in `config/models.py`, not in the auth module
- Access `SecretStr.get_secret_value()` only inside `StaticBearerVerifier.verify_token()`
- Return `None` (never raise) from both `verify_token` implementations for any invalid token
- Add auth preflight checks to `run_preflight()` in `config/validation.py` — not elsewhere
- Use `auth_mode=static` for all CI smoke tests — never add an Authelia dependency to the test environment
- Never add auth logic below the `server.py` boundary

**Pattern Enforcement:**
- `make lint` (`ruff` + `mypy`) catches type errors in verifier signatures and `SecretStr` misuse
- Contract tests should assert that `verify_token` signature matches `TokenVerifier` Protocol
- Code review rejects any `get_secret_value()` call outside `StaticBearerVerifier.verify_token()`

### Pattern Examples

**Good Examples:**
- `auth/verifiers.py` implements both verifier classes; `auth/__init__.py` exports only `build_token_verifier`
- `server.py` calls `build_token_verifier(config)` and `_build_auth_settings(config)` — no JWT or PyJWT import in `server.py`
- Preflight adds an OIDC connectivity check to `run_preflight()` alongside existing Sonos checks
- Unit test generates an RSA key pair inline with `cryptography`, signs a JWT, patches `PyJWKClient`, asserts `verify_token` returns an `AccessToken`

**Anti-Patterns:**
- Putting `OIDCVerifier` in `server.py` or `transports/streamable_http.py`
- Calling `config.auth_token.get_secret_value()` in `server.py` or `config/validation.py`
- Raising `AuthenticationError` or any exception from `verify_token` instead of returning `None`
- Adding a `verify_jwks_connectivity()` standalone function outside `run_preflight()`
- Using `auth_mode=oidc` in smoke tests with a mocked Authelia server

## Architecture Validation — Phase 3 (Optional Auth)

### Coherence Validation ✅

**Decision Compatibility:**
All Phase 3 technology choices are compatible. `PyJWT>=2.8` uses `cryptography>=46.0.7` (already a production dependency) for RSA operations — no new transitive deps. `mcp[cli]` 1.26.0 `TokenVerifier` Protocol is verified by package inspection. `SecretStr` is Pydantic built-in. `secrets.compare_digest` is Python stdlib. The `AUTH_MODE=none` guard produces a FastMCP constructor call structurally identical to the current codebase, with no branches, no imports, and no performance impact.

**Pattern Consistency:**
All patterns align with the Phase 2 established model: config in `config/`, business logic in `services/`, transport concerns at `server.py`. Auth follows the same boundary discipline — a new capability module (`auth/`) that touches `server.py` and `config/` only, with no downward reach into tools or services.

**Structure Alignment:**
The six-file change surface is consistent with the existing module organisation. New `auth/` module mirrors the structure of other capability modules. New `tests/unit/auth/` mirrors the structure of other unit test directories.

### Requirements Coverage Validation ✅

**Functional Requirements Coverage:**
All 27 FRs are mapped to specific files. No FR category is orphaned. The strictest requirement — FR17 (`AUTH_MODE=none` is a strict no-op) — is enforced architecturally by the guard in `create_server()` that leaves the `FastMCP()` constructor call unchanged.

**Non-Functional Requirements Coverage:**
- NFR1 (< 5ms): string comparison (static) and cached JWKS + RSA verify (OIDC cache hit) — both well within budget
- NFR2 (JWKS caching): `PyJWKClient` in-memory cache; no per-request network calls
- NFR3 (zero overhead for `none`): confirmed by guard structure — no code path entered
- NFR4 (`secrets.compare_digest`): enforced in `StaticBearerVerifier`
- NFR5 (token not in logs): enforced by `SecretStr` + discipline rule
- NFR6 (fail-closed): enforced by `except Exception` fallback returning `None`
- NFR7 (HTTPS-only JWKS): `PyJWKClient` does not support `http://` JWKS URIs
- NFR8 (expiry on every request): `jwt.decode()` validates `exp` atomically
- NFR9–NFR12 (integration): `TokenVerifier` Protocol, `SSL_CERT_FILE`, `None` return — all specified

### Implementation Readiness Validation ✅

**Decision Completeness:**
All blocking decisions are documented with verified versions. The one open point — `oidc_resource_url` default — is flagged as a story-level acceptance criterion rather than an architecture blocker.

**Structure Completeness:**
Two new source files, two new test files, one new doc file, and nine modified files are all named with their specific change described. No placeholders.

**Pattern Completeness:**
All 6 conflict points resolved. The `server.py` wiring pattern is shown as concrete Python. The `verify_token` return contract, `SecretStr` access discipline, and JWKS client lifecycle are unambiguous.

### Gap Analysis Results

**Critical Gaps:** None.

**Important Gaps:**
- `oidc_resource_url` default behaviour when not set: `resource_server_url=None` in `AuthSettings` may affect RFC 8707 audience binding. Story AC for the OIDC story must verify whether Authelia's `aud` claim validation works with `resource_server_url=None` or whether this field should be required when `auth_mode=oidc`.

**Nice-to-Have Gaps:**
- Explicit `make test-auth` and `make smoke-auth` Makefile targets — recommended but not blocking
- Token acquisition example scripts for AI agent clients — deferred to Phase 3 post-MVP

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Phase 3 PRD analyzed (27 FRs, 12 NFRs, 4 user journeys)
- [x] Complexity assessed — bounded brownfield feature addition
- [x] Technical constraints identified — FastMCP API, PyJWT, CA cert delivery
- [x] Cross-cutting concerns mapped — config, preflight, secret masking, transport parity

**✅ Architectural Decisions**
- [x] Critical decisions documented — auth mode enum, integration point, JWT library, placement
- [x] AuthSettings constraint verified by source inspection — cannot skip, issuer_url required
- [x] CA cert dual-path decided — `SSL_CERT_FILE` + optional `oidc_ca_bundle`
- [x] Secret handling approach specified — Pydantic `SecretStr`

**✅ Implementation Patterns**
- [x] Module structure and file layout specified
- [x] Class and factory naming specified
- [x] `SecretStr` access discipline enforced
- [x] JWKS client lifecycle specified
- [x] Preflight integration point specified
- [x] Logging discipline specified

**✅ Project Structure**
- [x] New files enumerated — 2 source, 2 test, 1 doc
- [x] Modified files enumerated with specific change described
- [x] All FRs mapped to specific files
- [x] Auth data flow documented

### Architecture Readiness Assessment

**Overall Status:** READY FOR EPIC AND STORY PLANNING

**Confidence Level:** High — key technical facts verified by direct `mcp[cli]` 1.26.0 source inspection; one open point (`oidc_resource_url` default) flagged for story-level AC

**Key Strengths:**
- Smallest possible change surface for the feature delivered
- Strict backward compatibility enforced architecturally, not just by convention
- FastMCP integration uses the correct first-class API — no transport-layer hacks
- Security properties (fail-closed, constant-time, secret masking) specified at the code pattern level
- CI test strategy is independent of Authelia — no external dependency in automated tests

**Areas for Future Enhancement:**
- RBAC / role-based claims validation if MCP spec mandates it
- Token acquisition helpers for AI agent clients
- Auth status in a future health/readiness endpoint

### Implementation Handoff

**AI Agent Guidelines:**
- `AuthMode` enum belongs in `config/models.py` — do not move it to `auth/`
- `get_secret_value()` is called in exactly one place: `StaticBearerVerifier.verify_token()`
- Both verifiers return `None` for invalid tokens — never raise
- Auth preflight belongs in `run_preflight()` — not in verifier constructors or `server.py`
- Smoke tests use `auth_mode=static` only — do not add Authelia to CI

**First Implementation Priority:**
Story A — auth config fields: add `AuthMode` enum and auth fields to `SoniqConfig`, extend `config/loader.py` env-var mappings, extend `run_preflight()` with auth config validation. This is the foundation that gates all other Phase 3 implementation work.

## Project Structure & Boundaries — Phase 3 (Optional Auth)

### New and Modified Files

The Phase 3 change surface is minimal. The existing structure from Phase 2 is unchanged except for the additions below.

**New files:**

```text
src/soniq_mcp/
└── auth/
    ├── __init__.py          # exports: build_token_verifier(config) -> TokenVerifier
    └── verifiers.py         # StaticBearerVerifier, OIDCVerifier

tests/
└── unit/
    └── auth/
        ├── __init__.py
        └── test_verifiers.py

docs/setup/
└── authentication.md        # all three modes, Authelia walkthrough, CA cert pattern,
                             # Claude Desktop scope note
```

**Modified files:**

| File | Change |
|------|--------|
| `src/soniq_mcp/config/models.py` | Add `AuthMode` enum; add 7 new fields to `SoniqConfig`; add `@model_validator` consistency checks |
| `src/soniq_mcp/config/loader.py` | Add `SONIQ_MCP_AUTH_*` and `SONIQ_MCP_OIDC_*` env-var mappings |
| `src/soniq_mcp/config/validation.py` | Extend `run_preflight()` with auth config checks and OIDC JWKS connectivity check |
| `src/soniq_mcp/server.py` | Add `_build_auth_settings()` helper; wire `auth` + `token_verifier` into `create_server()` |
| `tests/unit/config/test_validation.py` | New test class for auth preflight validation cases |
| `tests/smoke/streamable_http/test_streamable_http_smoke.py` | New test functions: 401 without token, 200 with valid static token, stdio no-op |
| `pyproject.toml` | Add `PyJWT>=2.8` to production dependencies |
| `.env.example` | Add commented auth env var examples |
| `helm/soniq/values.yaml` | Add auth env var entries and CA cert ConfigMap volume mount scaffolding |

### Architectural Boundaries

**Auth Boundary:**
- Auth is enforced at the FastMCP middleware layer, above tool handlers
- `auth/` module is only imported by `server.py` — no other module imports from `auth/`
- `config/models.py` defines `AuthMode` and auth config fields — imported by `auth/verifiers.py` and `server.py`
- `config/validation.py` imports `PyJWKClient` directly for the preflight connectivity check only

**Component Boundaries (unchanged from Phase 2):**
- `tools/`, `services/`, `adapters/` have zero awareness of auth
- Transport runners (`transports/`) have zero auth logic; auth wiring happens in `server.py` above them

**Data Boundaries:**
- No new persistent state
- `SoniqConfig.auth_token` is `SecretStr | None` — Pydantic handles masking at the model boundary
- `OIDCVerifier._jwks_client` holds the in-memory JWKS cache — scoped to the verifier instance lifetime

### Requirements to Structure Mapping

| FR Category | Files |
|-------------|-------|
| Auth mode config (FR1–FR4) | `config/models.py`, `config/loader.py`, `config/validation.py` |
| Static mode (FR5–FR7) | `auth/verifiers.py` (`StaticBearerVerifier`), `server.py` |
| OIDC mode (FR8–FR13) | `auth/verifiers.py` (`OIDCVerifier`), `server.py` |
| Startup validation (FR14–FR16) | `config/validation.py` (`run_preflight()`) |
| No-op & backward compat (FR17–FR19) | `server.py` conditional guard; no change to other files |
| Secret handling (FR20) | `config/models.py` (`SecretStr`), `auth/verifiers.py` |
| Documentation (FR21–FR25) | `docs/setup/authentication.md`, `.env.example` |
| Deployment config (FR26–FR27) | `helm/soniq/values.yaml`, `docker-compose.yml` (docs only) |

### Integration Points

**Internal Communication:**
- `run_preflight(config)` → auth field validation → OIDC JWKS connectivity check (if `auth_mode=oidc`)
- `create_server(config)` → `build_token_verifier(config)` → `StaticBearerVerifier` or `OIDCVerifier`
- `create_server(config)` → `_build_auth_settings(config)` → `AuthSettings(issuer_url=..., resource_server_url=...)`
- FastMCP constructor receives `auth=` + `token_verifier=` → wires `BearerAuthBackend` + `RequireAuthMiddleware` automatically

**External Integrations:**
- `OIDCVerifier` → Authelia JWKS endpoint (startup fetch + cache; refresh on unknown `kid`)
- CA cert trust: `SSL_CERT_FILE` env var (Python stdlib picks it up automatically) or `ssl.create_default_context(cafile=config.oidc_ca_bundle)` in `OIDCVerifier.__init__`

**Data Flow (auth path):**
1. HTTP request arrives at FastMCP
2. `BearerAuthBackend` extracts `Authorization: Bearer <token>`
3. FastMCP calls `token_verifier.verify_token(token)`
4. Verifier returns `AccessToken` (valid) or `None` (invalid)
5. `None` → FastMCP returns `401 Unauthorized` with `WWW-Authenticate` header
6. `AccessToken` → `RequireAuthMiddleware` passes request to tool handler

### Development Workflow Integration

**New `make` targets (recommended):**
- `make test-auth` — runs `tests/unit/auth/` in isolation
- `make smoke-auth` — runs auth smoke tests with `SONIQ_MCP_AUTH_MODE=static`

**No CI changes required.** `make lint` (`ruff` + `mypy`) covers new code automatically. Auth unit and smoke tests run under existing `make test` and `make smoke` targets.
