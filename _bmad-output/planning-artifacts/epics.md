---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd.md'
  - '/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/architecture.md'
---

# sonos-mcp-server - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for sonos-mcp-server, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Users can list available Sonos rooms that the server can control.
FR2: Users can target a specific Sonos room when invoking playback and control actions.
FR3: Users can start playback in a selected room.
FR4: Users can pause playback in a selected room.
FR5: Users can stop playback in a selected room.
FR6: Users can skip to the next track in a selected room.
FR7: Users can return to the previous track in a selected room.
FR8: Users can view the current playback state for a selected room.
FR9: Users can view current track information for a selected room.
FR10: Users can get the current volume for a selected room.
FR11: Users can set the volume for a selected room.
FR12: Users can adjust the volume of a selected room relative to its current level.
FR13: Users can mute a selected room.
FR14: Users can unmute a selected room.
FR15: Users can view the mute state of a selected room.
FR16: Users can view the queue for a selected room.
FR17: Users can add playable items to the queue for a selected room.
FR18: Users can remove queue items from a selected room.
FR19: Users can clear the queue for a selected room.
FR20: Users can start playback from a selected queue position.
FR21: Users can view available Sonos favourites.
FR22: Users can start playback of a selected favourite in a target room.
FR23: Users can view available Sonos playlists.
FR24: Users can start playback of a selected Sonos playlist in a target room.
FR25: Users can view the current Sonos grouping topology.
FR26: Users can add a room to an existing group.
FR27: Users can remove a room from its current group.
FR28: Users can trigger whole-home or multi-room grouping when appropriate.
FR29: Users can view system-level room and speaker information relevant to control operations.
FR30: Users can run the server as a local MCP endpoint for same-machine AI client usage.
FR31: Users can run the server as a network-accessible MCP endpoint for trusted home-network usage.
FR32: MCP-compatible AI clients can invoke the server’s control capabilities through supported transports.
FR33: Agent-based systems can use the server as a Sonos control layer within broader workflows.
FR34: Users can use the same core Sonos capabilities through both direct AI-client usage and agent-mediated usage.
FR35: Users can understand which runtime mode to use for their scenario through product-provided guidance and examples.
FR36: Users can install the product through an official Python package distribution.
FR37: Users can run the product through an official container image.
FR38: Users can deploy the product through an official Helm chart.
FR39: Users can configure the product for a single-household home Sonos environment.
FR40: Users can use sensible default settings for common setup paths.
FR41: Users can validate configuration before attempting normal runtime operation.
FR42: Users can identify configuration errors through actionable setup feedback.
FR43: Users can access guided setup and onboarding documentation for supported usage patterns.
FR44: Users can access MCP client configuration examples for supported client types.
FR45: Users can choose between local and home-network deployment patterns based on documented guidance.
FR46: Users can restrict which tools or capabilities are exposed to connected MCP clients where MCP permission models support it.
FR47: Users can control the default exposure posture of the server for local and home-network operation.
FR48: Users can operate the product within a home-use trust model without exposing it beyond the home network by default.
FR49: Users can avoid disruptive control outcomes through safe control behavior around sensitive actions such as volume changes and room targeting.
FR50: Users can access example usage patterns for local `stdio` operation.
FR51: Users can access example usage patterns for Docker-based operation.
FR52: Users can access example usage patterns for Helm-based deployment.
FR53: Users can access example usage patterns for cross-device and home-network scenarios.
FR54: Users can access example usage patterns for agentic and automation integrations such as Home Assistant and `n8n`.
FR55: Users can access troubleshooting guidance for installation, configuration, transport setup, and Sonos control issues.

### NonFunctional Requirements

NFR1: Core control actions such as play, pause, stop, room targeting, and volume changes should return an initial tool response quickly enough to feel responsive in conversational use.
NFR2: Configuration validation and startup checks should complete quickly enough to support an iterative setup experience rather than a long trial-and-error cycle.
NFR3: The product should remain responsive when handling typical single-household usage patterns, including multiple control actions during an active session.
NFR4: Local `stdio` operation should feel at least as responsive as remote home-network operation for equivalent actions.
NFR5: The product should behave predictably and consistently across repeated control actions against the same Sonos environment.
NFR6: The product should fail gracefully when speakers are unreachable, configuration is invalid, or MCP transport setup is incorrect.
NFR7: The product should provide actionable diagnostic feedback when control actions fail or cannot be completed as requested.
NFR8: The product should preserve user trust by minimizing surprising outcomes, especially for room targeting and volume-related operations.
NFR9: Official install and deployment paths should be repeatable without requiring undocumented manual intervention.
NFR10: The default security posture should assume local or trusted home-network usage rather than public internet exposure.
NFR11: The product should not require broader network exposure than necessary for supported usage patterns.
NFR12: The product should support MCP-compatible permission and tool-restriction models where the client ecosystem supports them.
NFR13: Configuration and deployment guidance should clearly distinguish safe default exposure from advanced or user-managed exposure choices.
NFR14: The product should avoid storing or exposing unnecessary sensitive information in logs, examples, or default configuration flows.
NFR15: The product should provide stable, well-documented MCP capability semantics across supported transports.
NFR16: The product should support the same core control model across direct AI-client usage and agent-mediated usage.
NFR17: Official examples should cover local `stdio`, Docker-based runtime, Helm deployment, and representative MCP client configurations.
NFR18: The product should provide enough configuration and troubleshooting clarity that supported clients and automation systems can be integrated without reverse engineering product behavior.
NFR19: The codebase should be organized so that Sonos control logic, MCP transport logic, configuration handling, and deployment assets can evolve independently.
NFR20: The product should include automated testing coverage for business logic, configuration validation, and other meaningful risk areas rather than coverage for its own sake.
NFR21: The architecture should support adding new MCP clients, deployment patterns, and downstream agent consumers without major restructuring.
NFR22: Documentation, examples, and operational assets should be maintained as product-critical artifacts rather than optional supporting material.
NFR23: The product should support the expected load profile of a single-household, self-hosted Sonos environment without degradation in normal use.
NFR24: The product should be able to support multiple client interactions within the same home environment without requiring redesign of the core product model.
NFR25: The product does not need to optimize for multi-tenant or internet-scale deployment in v1, and quality decisions should favor home-use robustness over generalized scale.

### Additional Requirements

- Initialize the project with `uv init --app soniq`, then add the official MCP Python SDK via `uv add "mcp[cli]" soco`.
- Keep the service stateless in MVP; do not introduce an application database.
- Use `stdio` for local transport and `Streamable HTTP` for remote transport.
- Separate transport, tools, services, adapters, config, domain, and deployment boundaries exactly as defined in the architecture.
- Treat setup, diagnostics, documentation, and examples as first-class implementation work, not optional follow-up tasks.
- Add a root `Makefile` as the canonical command reference for lint, test, smoke, Docker, Helm, and validation workflows.
- Implement typed configuration models, startup preflight validation, and deterministic error translation.
- Most automated tests must run without real Sonos hardware; isolate hardware-dependent checks from core automated validation.
- Ensure Docker packaging, Helm chart structure, and private-registry-friendly deployment support are part of the implementation plan.
- Preserve `snake_case` naming conventions across Python code, config fields, and MCP tool parameters.

### UX Design Requirements

No dedicated UX Design document exists. UX requirements are implied through the PRD and architecture and are represented via setup, validation, troubleshooting, documentation, and example-driven onboarding work.

### FR Coverage Map

FR1: Epic 2 - Room discovery and targeting
FR2: Epic 2 - Room-targeted control
FR3: Epic 2 - Playback start
FR4: Epic 2 - Pause
FR5: Epic 2 - Stop
FR6: Epic 2 - Next track
FR7: Epic 2 - Previous track
FR8: Epic 2 - Playback state
FR9: Epic 2 - Current track info
FR10: Epic 2 - Get volume
FR11: Epic 2 - Set volume
FR12: Epic 2 - Adjust volume
FR13: Epic 2 - Mute
FR14: Epic 2 - Unmute
FR15: Epic 2 - Get mute state
FR16: Epic 3 - View queue
FR17: Epic 3 - Add to queue
FR18: Epic 3 - Remove from queue
FR19: Epic 3 - Clear queue
FR20: Epic 3 - Play from queue
FR21: Epic 3 - View favourites
FR22: Epic 3 - Play favourite
FR23: Epic 3 - View playlists
FR24: Epic 3 - Play playlist
FR25: Epic 3 - View grouping topology
FR26: Epic 3 - Join group
FR27: Epic 3 - Unjoin room
FR28: Epic 3 - Whole-home grouping
FR29: Epic 2 - System-level room and speaker info
FR30: Epic 1 - Local MCP endpoint
FR31: Epic 4 - Network-accessible MCP endpoint
FR32: Epic 4 - Supported transport invocation
FR33: Epic 5 - Agent workflow integration
FR34: Epic 5 - Consistent direct and agent-mediated usage
FR35: Epic 1 - Runtime mode guidance
FR36: Epic 1 - Python package install path
FR37: Epic 4 - Container runtime
FR38: Epic 4 - Helm deployment
FR39: Epic 1 - Single-household configuration
FR40: Epic 1 - Sensible defaults
FR41: Epic 1 - Configuration validation
FR42: Epic 1 - Actionable setup feedback
FR43: Epic 1 - Guided onboarding docs
FR44: Epic 4 - MCP client configuration examples
FR45: Epic 4 - Deployment path guidance
FR46: Epic 1 - Tool restriction support
FR47: Epic 1 - Exposure posture control
FR48: Epic 1 - Home-use trust model defaults
FR49: Epic 1 - Safe control behavior
FR50: Epic 1 - Local `stdio` examples
FR51: Epic 4 - Docker examples
FR52: Epic 4 - Helm examples
FR53: Epic 4 - Cross-device and home-network examples
FR54: Epic 5 - Agent and automation examples
FR55: Epic 5 - Troubleshooting guidance

## Epic List

### Epic 1: Project Foundation and Safe Local Operation
Establish the `SoniqMCP` application foundation, validated configuration model, local `stdio` runtime, and the minimum safe operational path needed for users to run the server on the same machine as an MCP-capable AI client.
**FRs covered:** FR30, FR35, FR36, FR39, FR40, FR41, FR42, FR43, FR46, FR47, FR48, FR49, FR50, FR55

### Epic 2: Core Sonos Playback and Room Control
Enable users to discover rooms, target a room, and perform the primary playback and volume operations that make the product immediately useful for conversational Sonos control.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15, FR29

### Epic 3: Queue, Favourites, Playlists, and Group Control
Expand the control surface so users can manage queue-based playback, access favourites and playlists, and control room grouping for real multi-room household use.
**FRs covered:** FR16, FR17, FR18, FR19, FR20, FR21, FR22, FR23, FR24, FR25, FR26, FR27, FR28

### Epic 4: Remote Runtime and Deployment Paths
Make the product operationally credible beyond local development by adding `Streamable HTTP`, container packaging, Helm-based deployment, and the documentation required for home-network and cross-device operation.
**FRs covered:** FR31, FR32, FR37, FR38, FR44, FR45, FR51, FR52, FR53

### Epic 5: Integration, Diagnostics, and Productized Adoption
Complete the MVP by supporting agent-mediated integrations, consistent troubleshooting, and the polished docs/examples needed for users to adopt `Soniq` confidently across AI clients and automation workflows.
**FRs covered:** FR33, FR34, FR54, FR55

## Epic 1: Project Foundation and Safe Local Operation

Establish the `SoniqMCP` application foundation, validated configuration model, local `stdio` runtime, and the minimum safe operational path needed for users to run the server on the same machine as an MCP-capable AI client.

### Story 1.1: Initialize the SoniqMCP Application Scaffold

As a developer,
I want the project initialized with the agreed Python and MCP foundation,
So that all future work starts from a consistent, production-ready baseline.

**Acceptance Criteria:**

**Given** a new repository state for the implementation
**When** the project scaffold is created
**Then** the application is initialized using `uv` with the agreed Python application structure
**And** the official MCP Python SDK and `SoCo` are added as dependencies
**And** the root structure includes `pyproject.toml`, `Makefile`, `src/soniq_mcp/`, `tests/`, `helm/`, and `docs/`
**And** the scaffold matches the agreed architecture boundaries

### Story 1.2: Implement Typed Configuration and Validation

As a user,
I want the server configuration validated before runtime,
So that setup mistakes are caught early and explained clearly.

**Acceptance Criteria:**

**Given** the server is started with configuration inputs
**When** configuration is loaded
**Then** typed configuration models validate required fields, formats, and defaults
**And** invalid configuration fails before normal runtime begins
**And** validation errors identify the specific field or setting that must be corrected
**And** configuration supports a single-household Sonos environment

### Story 1.3: Run SoniqMCP Locally over stdio

As a user,
I want to run the server locally with `stdio`,
So that I can use it directly from an MCP-capable AI client on the same machine.

**Acceptance Criteria:**

**Given** a valid local configuration
**When** the user starts the server in `stdio` mode
**Then** the MCP server boots successfully and exposes the agreed tool surface
**And** the runtime uses the same internal tool and service boundaries defined by the architecture
**And** the server can be connected to a same-machine MCP-compatible AI client
**And** the startup path emits useful diagnostic output without exposing sensitive configuration

### Story 1.4: Enforce Safe Defaults and Tool Exposure Controls

As a user,
I want safe default behavior and controllable tool exposure,
So that AI clients cannot cause unnecessary disruption in my home environment.

**Acceptance Criteria:**

**Given** the server is configured for home use
**When** a user reviews or applies runtime settings
**Then** the default exposure posture assumes local or trusted-home-network usage
**And** permission-aware tool restriction settings are supported where MCP clients can use them
**And** risky actions such as volume changes are subject to explicit validation and safety rules
**And** the system does not expose functionality beyond the configured trust model by default

### Story 1.5: Deliver Local Setup and Troubleshooting Guidance

As a user,
I want clear local setup instructions and troubleshooting guidance,
So that I can get the product working without understanding MCP internals.

**Acceptance Criteria:**

**Given** a new user wants to run the server locally
**When** they follow the documented local setup path
**Then** they have step-by-step guidance for installation, configuration, and AI client connection
**And** the documentation includes example `stdio` usage
**And** troubleshooting guidance addresses common configuration and MCP wiring failures
**And** the local guidance matches the implemented command surface and runtime behavior

## Epic 2: Core Sonos Playback and Room Control

Enable users to discover rooms, target a room, and perform the primary playback and volume operations that make the product immediately useful for conversational Sonos control.

### Story 2.1: Discover Addressable Rooms and System Topology

As a user,
I want to list available Sonos rooms and basic system information,
So that I can target the correct room for playback operations.

**Acceptance Criteria:**

**Given** the server has a valid Sonos configuration
**When** the user invokes room and system discovery tools
**Then** the server returns the available rooms it can control
**And** the response includes the identifiers needed for later room-targeted actions
**And** system-level room and speaker information is returned in a structured format
**And** unreachable or misconfigured rooms are reported clearly

### Story 2.2: Control Core Playback in a Target Room

As a user,
I want to play, pause, stop, skip, and inspect playback state in a room,
So that I can use AI for basic day-to-day Sonos control.

**Acceptance Criteria:**

**Given** a valid target room
**When** the user invokes playback controls
**Then** the server supports play, pause, stop, next, and previous actions
**And** the server can return current playback state
**And** current track information is available in a structured response
**And** invalid room targeting returns a consistent, user-correctable error

### Story 2.3: Control Volume and Mute Safely

As a user,
I want to inspect and change volume in a room,
So that I can adjust playback without disruptive surprises.

**Acceptance Criteria:**

**Given** a valid target room
**When** the user invokes volume or mute controls
**Then** the server supports get volume, set volume, adjust volume, mute, unmute, and get mute state
**And** volume operations are validated against allowed ranges
**And** safety logic prevents malformed or unsafe volume requests from being applied
**And** errors are returned using the shared error model

### Story 2.4: Apply Reliable Sonos Service and Adapter Boundaries

As a developer,
I want the core playback and volume features implemented through stable service and adapter layers,
So that tool logic remains thin and transport-agnostic.

**Acceptance Criteria:**

**Given** the playback and volume capabilities are implemented
**When** the code is reviewed against the architecture
**Then** MCP tool handlers do not call `SoCo` directly
**And** Sonos operations are mediated through the agreed service and adapter boundaries
**And** domain exceptions are translated consistently into MCP-safe responses
**And** the code organization follows the agreed structure and naming conventions

## Epic 3: Queue, Favourites, Playlists, and Group Control

Expand the control surface so users can manage queue-based playback, access favourites and playlists, and control room grouping for real multi-room household use.

### Story 3.1: Manage the Sonos Queue

As a user,
I want to inspect and manage the queue for a room,
So that I can use AI to control what plays next.

**Acceptance Criteria:**

**Given** a valid room with queue-capable playback
**When** the user invokes queue tools
**Then** the server supports viewing the queue
**And** the server supports adding playable items to the queue
**And** the server supports removing items and clearing the queue
**And** the server supports starting playback from a selected queue position

### Story 3.2: Access and Play Favourites and Playlists

As a user,
I want to browse Sonos favourites and playlists and start them in a room,
So that I can use my saved Sonos content naturally through AI.

**Acceptance Criteria:**

**Given** the connected Sonos system has saved favourites or playlists
**When** the user invokes favourites or playlist tools
**Then** the server supports viewing available favourites
**And** the server supports playing a selected favourite in a target room
**And** the server supports viewing available Sonos playlists
**And** the server supports playing a selected Sonos playlist in a target room

### Story 3.3: Control Room Grouping and Multi-Room Playback

As a user,
I want to inspect and change room grouping,
So that I can control playback across multiple Sonos rooms.

**Acceptance Criteria:**

**Given** a Sonos household with multiple rooms
**When** the user invokes grouping tools
**Then** the server supports viewing current grouping topology
**And** the server supports joining a room to a coordinator group
**And** the server supports removing a room from a group
**And** the server supports whole-home or multi-room grouping where appropriate

## Epic 4: Remote Runtime and Deployment Paths

Make the product operationally credible beyond local development by adding `Streamable HTTP`, container packaging, Helm-based deployment, and the documentation required for home-network and cross-device operation.

### Story 4.1: Run SoniqMCP over Streamable HTTP

As a user,
I want to run the server remotely over `Streamable HTTP`,
So that I can use it from trusted devices and deployed MCP clients on my home network.

**Acceptance Criteria:**

**Given** a valid deployment configuration
**When** the user starts the server in remote mode
**Then** the server exposes the MCP tool surface over `Streamable HTTP`
**And** the remote mode uses the same underlying tool and service boundaries as `stdio`
**And** the transport-specific bootstrap remains isolated from domain logic
**And** the remote startup path supports the documented home-network trust model

### Story 4.2: Package the Server as a Docker Image

As a home-lab user,
I want a supported Docker image,
So that I can run the server consistently in containerized environments.

**Acceptance Criteria:**

**Given** the application is runnable locally
**When** the Docker build is executed
**Then** a container image is produced for the service
**And** runtime configuration can be injected without modifying application code
**And** container startup behavior matches the documented deployment paths
**And** the image is suitable for private-registry and public-registry publishing workflows

### Story 4.3: Provide a Helm Chart for Self-Hosted Deployment

As a home-lab operator,
I want a Helm chart for the service,
So that I can deploy it repeatably in k3s or similar environments.

**Acceptance Criteria:**

**Given** the Docker image is available
**When** the Helm chart is used for deployment
**Then** the chart provides configurable values for transport, networking, and speaker configuration
**And** chart templates include the resources needed for deployment and service exposure
**And** the chart structure matches the agreed architecture
**And** the deployment path remains compatible with the single-household home-use model

### Story 4.4: Document Remote, Docker, Helm, and Cross-Device Usage

As a user,
I want deployment guides for remote and self-hosted use,
So that I can choose the right runtime model for my environment.

**Acceptance Criteria:**

**Given** the remote and deployment features exist
**When** a user reads the documentation
**Then** they can follow separate guides for Docker, Helm, and cross-device/home-network usage
**And** MCP client configuration examples are provided for the supported remote patterns
**And** the docs explain the difference between local `stdio` and remote `Streamable HTTP`
**And** the docs include representative networking and troubleshooting guidance

## Epic 5: Integration, Diagnostics, and Productized Adoption

Complete the MVP by supporting agent-mediated integrations, consistent troubleshooting, and the polished docs/examples needed for users to adopt `Soniq` confidently across AI clients and automation workflows.

### Story 5.1: Support Agent-Mediated Integration Patterns

As an advanced user,
I want the server to work cleanly in agent and automation workflows,
So that I can use it through Home Assistant, `n8n`, and similar systems.

**Acceptance Criteria:**

**Given** the server is running in a supported transport mode
**When** an external agent system invokes the MCP tools
**Then** the same core control model is available as in direct AI-client use
**And** tool semantics remain stable and predictable for automation consumers
**And** integration usage does not require a different internal implementation path
**And** the product supports representative examples for agent-mediated usage

### Story 5.2: Deliver Consistent Diagnostics and Troubleshooting Support

As a user,
I want actionable diagnostics when setup or runtime behavior fails,
So that I can recover without trial-and-error guesswork.

**Acceptance Criteria:**

**Given** a configuration, connectivity, or runtime problem occurs
**When** the server reports the issue
**Then** the error is categorized consistently using the shared error model
**And** the user-facing guidance distinguishes correctable setup problems from operational failures
**And** diagnostics avoid exposing unnecessary sensitive information
**And** troubleshooting guidance matches the actual failure modes supported by the implementation

### Story 5.3: Deliver Productized Examples, Prompts, and Command Surface

As a user,
I want examples and common commands collected in one place,
So that I can adopt the product quickly and use it confidently.

**Acceptance Criteria:**

**Given** the MVP features are implemented
**When** the user reviews the product documentation and command surface
**Then** the project provides example prompts and example use cases for direct and agent-mediated usage
**And** the `Makefile` exposes the agreed developer and operator commands
**And** documentation treats examples, diagnostics, and onboarding as first-class product assets
**And** the docs remain aligned with the actual implementation and deployment paths
