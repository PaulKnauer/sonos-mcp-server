---
stepsCompleted: [1, 2, 3]
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
FR28: Users can trigger whole-home or multi-room grouping through explicit commands that target all discovered rooms or a specified room set.
FR29: Users can view a defined system-information set that supports control operations, including room names, coordinator state, group membership, and addressable speaker identity data.
FR30: Users can view and change shuffle mode for a selected room or its active coordinator.
FR31: Users can view and change repeat mode for a selected room or its active coordinator.
FR32: Users can view and change crossfade mode for a selected room or its active coordinator.
FR33: Users can seek to a specified position within the currently playing track for a selected room.
FR34: Users can set and inspect a sleep timer for a selected room.
FR35: Users can view and adjust bass settings for a selected room.
FR36: Users can view and adjust treble settings for a selected room.
FR37: Users can view and change loudness settings for a selected room.
FR38: Users can switch a selected room to supported line-in or TV input sources when the target device supports those inputs.
FR39: Users can run the server as a local MCP endpoint for same-machine AI client usage.
FR40: Users can run the server as a network-accessible MCP endpoint for trusted home-network usage.
FR41: MCP-compatible AI clients can invoke the server’s control capabilities through supported transports.
FR42: Agent-based systems can use the server as a Sonos control layer within broader workflows.
FR43: Users can use the same core Sonos capabilities through both direct AI-client usage and agent-mediated usage.
FR44: Users can understand which runtime mode to use for their scenario through product-provided guidance and examples.
FR45: Users can install the product through an official Python package distribution.
FR46: Users can run the product through an official container image.
FR47: Users can deploy the product through an official Helm chart.
FR48: Users can configure the product for a single-household home Sonos environment.
FR49: Users can use documented default configuration profiles for the common local `stdio` and home-network deployment paths.
FR50: Users can validate configuration before attempting normal runtime operation.
FR51: Users can identify configuration errors through actionable setup feedback.
FR52: Users can access guided setup and onboarding documentation for supported usage patterns.
FR53: Users can access MCP client configuration examples for supported client types.
FR54: Users can choose between local and home-network deployment patterns based on documented guidance.
FR55: Users can restrict which tools or capabilities are exposed to connected MCP clients where MCP permission models support it.
FR56: Users can control the default exposure posture of the server for local and home-network operation.
FR57: Users can operate the product within a home-use trust model without exposing it beyond the home network by default.
FR58: Users can avoid disruptive control outcomes through safe control behavior around sensitive actions such as volume changes and room targeting.
FR59: Users can avoid invalid or misleading advanced-control actions when a requested capability depends on device type, active coordinator state, or supported input source.
FR60: Users can access example usage patterns for local `stdio` operation.
FR61: Users can access example usage patterns for Docker-based operation.
FR62: Users can access example usage patterns for Helm-based deployment.
FR63: Users can access example usage patterns for cross-device and home-network scenarios.
FR64: Users can access example usage patterns for agentic and automation integrations such as Home Assistant and `n8n`.
FR65: Users can access troubleshooting guidance for installation, configuration, transport setup, and Sonos control issues.
FR66: Users can view, create, update, and delete Sonos alarms for supported households and rooms.
FR67: Users can view, create, update, and delete Sonos playlists exposed through the household.
FR68: Users can control group-level volume and mute state for an active Sonos group.
FR69: Users can browse and select content from the local Sonos music library with pagination or bounded-result behavior that remains usable for collections of at least 1,000 items.
FR70: Users can use the same named advanced-control capabilities through direct AI-client interactions and agent-mediated workflows, with no capability-category mismatch between the two access patterns.

### NonFunctional Requirements

NFR1: Core control actions such as play, pause, stop, room targeting, and volume changes shall return an initial MCP tool response in under 2 seconds for 95% of requests in a healthy single-household environment.
NFR2: Configuration validation and startup checks shall complete in under 10 seconds for 95% of runs on supported local and containerized setups.
NFR3: The product shall sustain at least 20 sequential control actions within a 60-second window in a single active session without process restart, request timeout, or control-state corruption.
NFR4: Local `stdio` operation shall have median end-to-end request latency no worse than 20% faster than equivalent home-network operation under the same household conditions.
NFR5: Repeating the same supported control action against the same target room under unchanged household conditions shall produce the same resulting Sonos state in at least 99% of test runs.
NFR6: When speakers are unreachable, configuration is invalid, or MCP transport setup is incorrect, the product shall return a typed failure response with corrective guidance and without unhandled process termination in 100% of tested failure cases.
NFR7: For every user-correctable runtime failure, the product shall return an error message that identifies the failed action, the affected target, and at least one corrective next step.
NFR8: Volume-changing actions shall respect configured safety limits in 100% of test cases, and room-targeted actions shall not affect an unintended room in any supported single-command success scenario.
NFR9: Official Python-package, Docker, and Helm installation paths shall succeed from documented instructions without undocumented manual intervention in clean test environments.
NFR10: Default configuration shall bind the product only to local process or trusted home-network use cases and shall not require public-internet exposure for any supported v1 workflow.
NFR11: No documented deployment pattern shall require broader network access than the minimum needed for the selected runtime mode and Sonos household reachability.
NFR12: Where the client ecosystem supports MCP permission or tool-restriction controls, the product shall expose enough metadata and configuration control to disable restricted tool categories before runtime.
NFR13: Configuration and deployment guidance shall document at least one safe-default exposure pattern and at least one explicitly advanced exposure pattern, with the risks of the latter stated in operator-facing language.
NFR14: Logs, examples, and default configuration flows shall exclude secrets, auth tokens, and household-specific identifiers except where the user explicitly enables diagnostic verbosity.
NFR15: The product shall preserve functional parity for all documented core tools across supported transports, except where transport limitations are explicitly documented.
NFR16: The product shall preserve the same room-targeting model, safety behavior, and advanced-capability naming across direct AI-client usage and agent-mediated usage.
NFR17: Official examples shall cover local `stdio`, Docker-based runtime, Helm deployment, and at least three representative MCP client or automation configurations.
NFR18: A new user following the official integration documentation shall be able to complete a supported client integration without consulting source code or undocumented configuration files.
NFR19: The codebase shall preserve separable module boundaries for Sonos control logic, MCP transport logic, configuration handling, and deployment assets so that changes in one area do not require cross-cutting edits in all others for routine feature additions.
NFR20: Automated tests shall cover configuration validation, core Sonos control behavior, and regression-prone service logic, and the CI path shall run those checks on every protected-branch change.
NFR21: Adding a new MCP client example, deployment pattern, or downstream agent integration shall not require redesign of the core Sonos control domain model.
NFR22: Documentation, examples, and operational assets shall be versioned and updated in the same release cycle as behavior changes that would otherwise make them inaccurate.
NFR23: The product shall support a single-household, self-hosted environment with at least 10 addressable Sonos rooms without functional degradation in supported control flows.
NFR24: The product shall tolerate concurrent interaction from at least 3 client sessions within the same household without requiring redesign of the core product model or causing inconsistent room state.
NFR25: The product shall not require optimization for multi-tenant or internet-scale deployment in v1, and architecture decisions shall favor single-household robustness over generalized scale efficiency.

### Additional Requirements

- Continue using the existing `uv` application scaffold, Python MCP SDK direction, and `SoCo` foundation; phase 2 is capability expansion, not a platform reset.
- Preserve the `tools -> services -> adapters` boundary model and keep `SoCoAdapter` as the only direct Sonos integration boundary.
- Keep phase 2 stateless by default; do not introduce an application database unless a later requirement clearly exceeds Sonos-backed state.
- Maintain `stdio` for local transport and `Streamable HTTP` for remote transport with transport-neutral tool semantics.
- Add or refine capability-specific modules for `playback`, `audio`, `inputs`, `alarms`, `playlists`, `library`, and `groups` rather than collapsing all new features into generic modules.
- Keep Sonos coordinator checks, device-support guards, and advanced capability validation in service-layer logic, not in tool handlers or transport code.
- Normalize Sonos and SoCo objects before returning MCP responses; raw SoCo objects must not escape through the tool boundary.
- Extend request, response, and error schema consistency across all new capability families.
- Extend unit, integration, contract, and smoke tests for the phase-2 capability surface while keeping default automated validation hardware-independent.
- Preserve Python-package, Docker, Helm, diagnostics, setup, and example-driven onboarding as first-class implementation areas alongside the new tool families.

### UX Design Requirements

No dedicated UX Design document exists. UX requirements are represented through setup guidance, diagnostics, troubleshooting, documentation, and example-driven onboarding behavior in the PRD and architecture.

### FR Coverage Map

FR23: Epic 3 - Existing playlist playback is extended into playlist lifecycle management
FR24: Epic 3 - Existing playlist playback remains part of the playlist management value area
FR25: Epic 2 - Group and topology context supports safer expanded group-audio operations
FR26: Epic 2 - Existing group membership controls remain part of the group-audio user outcome
FR27: Epic 2 - Existing group membership controls remain part of the group-audio user outcome
FR28: Epic 2 - Explicit multi-room grouping belongs with expanded group-audio behavior
FR29: Epic 2 - System topology and identity data support input and group-audio decisions
FR30: Epic 1 - Shuffle mode control is part of advanced playback behavior
FR31: Epic 1 - Repeat mode control is part of advanced playback behavior
FR32: Epic 1 - Crossfade control is part of advanced playback behavior
FR33: Epic 1 - Seek control is part of advanced playback behavior
FR34: Epic 1 - Sleep timer management is part of advanced playback behavior
FR35: Epic 1 - Bass control is part of advanced room-level audio tuning
FR36: Epic 1 - Treble control is part of advanced room-level audio tuning
FR37: Epic 1 - Loudness control is part of advanced room-level audio tuning
FR38: Epic 2 - Input switching is grouped with capability-aware room and group audio expansion
FR39: Epic 5 - Phase-2 rollout must preserve local MCP endpoint support
FR40: Epic 5 - Phase-2 rollout must preserve network-accessible MCP endpoint support
FR41: Epic 4 - Library access must remain invocable through supported transports
FR42: Epic 4 - Library access must remain usable in agent workflows
FR43: Epic 4 - Expanded library capabilities must preserve direct and agent-mediated parity
FR44: Epic 5 - Documentation must explain how to use the expanded runtime modes
FR49: Epic 5 - Default configuration profiles must support the expanded capability surface
FR50: Epic 5 - Validation must continue to support the expanded capability surface
FR51: Epic 5 - Actionable errors must continue to support the expanded capability surface
FR52: Epic 5 - Guided onboarding docs must cover the new capability families
FR53: Epic 5 - MCP client examples must cover the expanded surface where relevant
FR54: Epic 5 - Deployment guidance must still work for the expanded feature set
FR55: Epic 5 - Tool exposure controls must extend to the new phase-2 tool families
FR56: Epic 5 - Default exposure posture must remain controllable for the expanded surface
FR57: Epic 5 - Home-use trust boundaries must remain intact as the surface expands
FR58: Epic 2 - Safe behavior around room and audio changes is central to group and input expansion
FR59: Epic 1 - Advanced playback must enforce capability-aware safety guards
FR59: Epic 2 - Input and group-audio operations must enforce capability-aware safety guards
FR59: Epic 3 - Alarm and playlist lifecycle operations must reject invalid target states cleanly
FR59: Epic 4 - Library selection flows must reject invalid or unsupported requests cleanly
FR60: Epic 5 - Local stdio examples must cover or reference the expanded feature surface
FR61: Epic 5 - Docker examples must cover or reference the expanded feature surface
FR62: Epic 5 - Helm examples must cover or reference the expanded feature surface
FR63: Epic 5 - Cross-device examples must cover or reference the expanded feature surface
FR64: Epic 5 - Agent-integration examples must cover or reference the expanded feature surface
FR65: Epic 5 - Troubleshooting guidance must cover the new capability families
FR66: Epic 3 - Alarm lifecycle management is a standalone user-value area
FR67: Epic 3 - Playlist CRUD is a standalone user-value area
FR68: Epic 2 - Group-level volume and mute control belong with expanded group behavior
FR69: Epic 4 - Local library browsing and selection are the core user outcome of this epic
FR70: Epic 1 - Advanced playback must preserve parity across direct and agent-mediated workflows
FR70: Epic 2 - Input and group-audio expansion must preserve parity across direct and agent-mediated workflows
FR70: Epic 3 - Alarm and playlist lifecycle operations must preserve parity across direct and agent-mediated workflows
FR70: Epic 4 - Library access must preserve parity across direct and agent-mediated workflows

## Epic List

### Epic 1: Advanced Playback and Audio Control
Users can control richer playback behaviors in an active room, including play modes, seek, sleep timer, and room-level audio tuning, without losing the existing safety and coordinator semantics.
**FRs covered:** FR30, FR31, FR32, FR33, FR34, FR35, FR36, FR37, FR59, FR70

### Epic 2: Input and Group Audio Expansion
Users can switch supported room inputs and control group-level audio behavior in ways that remain safe, capability-aware, and consistent across direct and agent-mediated use.
**FRs covered:** FR38, FR68, FR25, FR26, FR27, FR28, FR29, FR58, FR59, FR70

### Epic 3: Alarm and Playlist Lifecycle Management
Users can manage repeatable listening workflows by creating, updating, and deleting Sonos alarms and playlists, while preserving predictable response structures and safe error handling.
**FRs covered:** FR23, FR24, FR66, FR67, FR59, FR70

### Epic 4: Local Music Library Access and Selection
Users can browse and select items from the local Sonos music library with bounded-result behavior that works for large collections and remains usable through both AI clients and agent workflows.
**FRs covered:** FR69, FR70, FR41, FR42, FR43, FR59

### Epic 5: Phase-2 Contract Hardening and Documentation
Users and integrators can adopt the expanded phase-2 tool surface with stable schemas, examples, diagnostics, safety controls, and deployment/runtime parity across supported transports.
**FRs covered:** FR39, FR40, FR44, FR49, FR50, FR51, FR52, FR53, FR54, FR55, FR56, FR57, FR60, FR61, FR62, FR63, FR64, FR65

## Epic 1: Advanced Playback and Audio Control

Users can control richer playback behaviors in an active room, including play modes, seek, sleep timer, and room-level audio tuning, without losing the existing safety and coordinator semantics.

### Story 1.1: Expose play mode controls for active rooms

As a Sonos user,
I want to view and change shuffle, repeat, and crossfade for a target room,
So that I can control playback behavior without leaving my AI workflow.

**Acceptance Criteria:**

**Given** a reachable target room with an active coordinator
**When** the client requests the current play mode state
**Then** the service returns the normalized shuffle, repeat, and crossfade values for that room
**And** the response uses stable `snake_case` fields.

**Given** a reachable target room with an active coordinator
**When** the client requests a shuffle, repeat, or crossfade change
**Then** the service applies the requested mode through the phase-2 playback boundary
**And** the response returns the target room and resulting mode state.

**Given** a room that cannot perform the requested mode change because of coordinator or availability constraints
**When** the client invokes the tool
**Then** the service returns a typed validation or capability error
**And** it does not return a raw SoCo error object.

### Story 1.2: Support seek and sleep timer operations

As a Sonos user,
I want to seek within the current track and manage a sleep timer for a room,
So that I can control active listening sessions more precisely.

**Acceptance Criteria:**

**Given** a room with an active track
**When** the client requests a seek to a valid track position
**Then** the service applies the seek operation for the target room
**And** returns the normalized resulting playback state.

**Given** a room that supports sleep-timer operations
**When** the client requests the current sleep timer status
**Then** the service returns the normalized timer state for that room.

**Given** a room that supports sleep-timer operations
**When** the client sets or clears a sleep timer
**Then** the service applies the requested change
**And** returns the resulting timer state in a structured response.

### Story 1.3: Add room-level audio EQ controls

As a Sonos user,
I want to view and change bass, treble, and loudness for a room,
So that I can tune the listening experience from the same AI control surface.

**Acceptance Criteria:**

**Given** a reachable target room
**When** the client requests current bass, treble, and loudness settings
**Then** the service returns the normalized audio-setting values for that room.

**Given** a reachable target room
**When** the client updates bass, treble, or loudness
**Then** the service validates the request against supported ranges and types
**And** applies the change through the dedicated audio-settings service boundary.

**Given** an invalid audio-setting request
**When** the client invokes the tool
**Then** the service returns a typed validation error
**And** the room state remains unchanged.

### Story 1.4: Harden advanced playback contracts and regression coverage

As a maintainer,
I want the new advanced playback and audio tools to use consistent schemas and tests,
So that the expanded capability surface remains stable across transports and future changes.

**Acceptance Criteria:**

**Given** the advanced playback and audio tools are implemented
**When** contract tests run
**Then** tool names, parameter shapes, and response fields remain stable across supported transports.

**Given** unit and integration tests run in default CI
**When** the advanced playback and audio stories are exercised
**Then** the tests pass without requiring real Sonos hardware.

**Given** the new tools are documented
**When** examples are reviewed
**Then** the documentation shows how the same capability family works in both direct AI-client and agent-mediated usage.

## Epic 2: Input and Group Audio Expansion

Users can switch supported room inputs and control group-level audio behavior in ways that remain safe, capability-aware, and consistent across direct and agent-mediated use.

### Story 2.1: Support capability-aware input switching

As a Sonos user,
I want to switch a supported room to line-in or TV input,
So that I can control external sources from the same AI workflow.

**Acceptance Criteria:**

**Given** a room that supports line-in or TV input
**When** the client requests an input switch
**Then** the service validates device capability support before invoking the adapter
**And** returns the resulting normalized input state.

**Given** a room that does not support the requested input
**When** the client invokes the input-switching tool
**Then** the service returns a typed unsupported-capability error
**And** no playback state is changed.

### Story 2.2: Add group-level volume and mute controls

As a Sonos user,
I want to control volume and mute for an active group,
So that I can manage multi-room listening without changing rooms one by one.

**Acceptance Criteria:**

**Given** an active Sonos group with a coordinator
**When** the client requests group-level volume or mute state
**Then** the service returns the normalized group audio state.

**Given** an active Sonos group with a coordinator
**When** the client updates group volume or mute
**Then** the service applies the change through the group-service boundary
**And** respects configured safety limits for volume-related actions.

**Given** a request that targets a non-grouped or invalid room state
**When** the group-audio tool is invoked
**Then** the service returns a typed validation error
**And** does not affect unrelated rooms.

### Story 2.3: Strengthen topology and grouping support for expanded audio flows

As a Sonos user,
I want topology and grouping tools to support whole-home and specified-room-set flows reliably,
So that group-audio and input-aware behavior can build on accurate room context.

**Acceptance Criteria:**

**Given** a reachable household with multiple rooms
**When** the client requests current topology
**Then** the service returns room names, coordinator state, group membership, and addressable room identity data.

**Given** a whole-home or specified-room-set grouping request
**When** the client invokes the grouping tool
**Then** the service applies the grouping request explicitly against the discovered room set
**And** returns the resulting topology in a normalized structure.

**Given** an invalid grouping target or ambiguous room set
**When** the client invokes the grouping tool
**Then** the service returns an actionable validation error
**And** the current grouping remains unchanged.

### Story 2.4: Document and test expanded group and input behavior

As a maintainer,
I want group-audio and input-switching features to have stable contracts and examples,
So that integrators can adopt them safely across transports.

**Acceptance Criteria:**

**Given** the group and input tools are implemented
**When** contract and integration tests run
**Then** the tests verify normalized responses, guard behavior, and safe error handling for these tools.

**Given** documentation and examples are updated
**When** a user reviews setup and integration guidance
**Then** they can identify when to use room-level, group-level, and input-specific controls.

## Epic 3: Alarm and Playlist Lifecycle Management

Users can manage repeatable listening workflows by creating, updating, and deleting Sonos alarms and playlists, while preserving predictable response structures and safe error handling.

### Story 3.1: Add alarm discovery and lifecycle operations

As a Sonos user,
I want to view, create, update, and delete Sonos alarms,
So that I can automate repeatable listening behavior through the MCP server.

**Acceptance Criteria:**

**Given** a reachable household with alarm support
**When** the client requests the alarm list
**Then** the service returns normalized alarm records for supported rooms.

**Given** a valid alarm payload
**When** the client creates or updates an alarm
**Then** the service validates the request through the alarm-service boundary
**And** returns the resulting normalized alarm record.

**Given** an existing alarm identifier
**When** the client deletes the alarm
**Then** the service removes it successfully
**And** returns a structured confirmation response.

### Story 3.2: Introduce Sonos playlist CRUD operations

As a Sonos user,
I want to view, create, update, and delete Sonos playlists,
So that I can manage reusable listening collections from the same control surface.

**Acceptance Criteria:**

**Given** a reachable household with playlist support
**When** the client requests playlist inventory
**Then** the service returns normalized playlist metadata for the household.

**Given** a valid playlist lifecycle request
**When** the client creates, updates, or deletes a playlist
**Then** the service performs the requested operation through the playlist-service boundary
**And** returns the resulting normalized playlist state or structured delete confirmation.

**Given** an invalid playlist identifier or an unsupported household playlist mutation
**When** the client invokes the playlist lifecycle tool
**Then** the service returns a typed validation or unsupported-operation error.

### Story 3.3: Preserve existing playlist playback alongside playlist lifecycle support

As a Sonos user,
I want playlist playback to remain stable while new playlist lifecycle features are added,
So that the expanded playlist surface does not break established usage.

**Acceptance Criteria:**

**Given** the playlist lifecycle tools are implemented
**When** the client invokes existing playlist playback behavior
**Then** playback still works through the same target-room workflow as before.

**Given** a playlist created or updated through the new lifecycle tools
**When** the client selects it for playback
**Then** the playlist is discoverable and playable through the playlist playback flow.

### Story 3.4: Add tests and docs for alarm and playlist lifecycle flows

As a maintainer,
I want alarm and playlist lifecycle features covered by stable tests and examples,
So that phase-2 automation workflows remain safe to evolve.

**Acceptance Criteria:**

**Given** the alarm and playlist lifecycle features are implemented
**When** unit, integration, and contract tests run
**Then** they validate normalized responses, error categories, and lifecycle behavior without requiring hardware in the default path.

**Given** the new lifecycle tools are documented
**When** integrators review examples
**Then** they can distinguish playlist playback from playlist management and understand the supported alarm workflows.

### Story 3.5: Investigate supported Sonos playlist rename capability

As a maintainer,
I want to verify whether a newer supported SoCo release or alternate Sonos integration path can provide playlist rename cleanly,
So that future playlist lifecycle expansion does not rely on unsupported workarounds.

**Acceptance Criteria:**

**Given** the current playlist lifecycle implementation excludes rename
**When** the maintainer evaluates newer supported `SoCo` releases and relevant Sonos API surfaces
**Then** the research identifies whether a supported rename path exists without violating the current architecture.

**Given** the rename investigation is complete
**When** the findings are documented
**Then** the outcome explicitly recommends `implement`, `defer`, or `reject`
**And** identifies the architecture and contract implications of that choice.

## Epic 4: Local Music Library Access and Selection

Users can browse and select items from the local Sonos music library with bounded-result behavior that works for large collections and remains usable through both AI clients and agent workflows.

### Story 4.1: Add bounded local music library browsing

As a Sonos user,
I want to browse the local Sonos music library through the MCP server,
So that I can discover playable content without leaving my AI workflow.

**Acceptance Criteria:**

**Given** a reachable household with a local music library
**When** the client requests a library browse operation
**Then** the service returns normalized library results with bounded-result or pagination behavior.

**Given** a library with at least 1,000 items
**When** the client browses a large result set
**Then** the service remains usable through pagination, bounded results, or continuation semantics
**And** does not return an unbounded raw payload.

### Story 4.2: Support selection and playback from library results

As a Sonos user,
I want to select a browsed library item and play it in a room,
So that library discovery leads directly to listening actions.

**Acceptance Criteria:**

**Given** a valid normalized library item
**When** the client selects it for playback in a target room
**Then** the service resolves the selection into a playable action
**And** returns the resulting normalized playback confirmation.

**Given** an invalid or unsupported library selection
**When** the client invokes the selection flow
**Then** the service returns a typed validation or unsupported-operation error
**And** no unintended playback begins.

### Story 4.3: Preserve parity for library access across direct and agent-mediated usage

As an integrator,
I want local music library capabilities to behave the same in direct AI and agent workflows,
So that I do not need different mental models for the same library actions.

**Acceptance Criteria:**

**Given** the library tools are exposed over supported transports
**When** a direct AI client or an agent workflow invokes the same library capability
**Then** the request and response semantics are equivalent aside from transport-specific envelope details.

**Given** documentation and examples are reviewed
**When** a user compares direct and agent-mediated library usage
**Then** the same named capability family and expected result structure are shown consistently.

## Epic 5: Phase-2 Contract Hardening and Documentation

Users and integrators can adopt the expanded phase-2 tool surface with stable schemas, examples, diagnostics, safety controls, and deployment/runtime parity across supported transports.

### Story 5.1: Extend schemas and error contracts for phase-2 capability families

As an integrator,
I want the phase-2 tool surface to use stable request, response, and error contracts,
So that I can adopt the new capabilities without reverse engineering behavior.

**Acceptance Criteria:**

**Given** the new phase-2 tool families are implemented
**When** request and response schemas are reviewed
**Then** they use consistent `snake_case` naming and normalized structures across the expanded surface.

**Given** a validation, capability, connectivity, or internal failure occurs
**When** a phase-2 tool returns an error
**Then** the error is mapped into the shared typed error model
**And** raw SoCo objects or unstructured trace strings are not returned.

### Story 5.2: Preserve transport parity and tool exposure controls

As an operator,
I want the expanded phase-2 tool surface to behave consistently across local and remote modes,
So that I can expose capabilities safely without transport-specific surprises.

**Acceptance Criteria:**

**Given** the expanded tool surface is available
**When** the same supported capability is invoked over local `stdio` and remote HTTP transport
**Then** the functional result and response semantics remain equivalent aside from transport envelope details.

**Given** tool exposure controls are configured
**When** an operator disables restricted tool categories
**Then** the phase-2 tool families respect the configured exposure posture before runtime.

### Story 5.3: Update setup, examples, and troubleshooting for phase 2

As a user,
I want the setup and integration documentation to reflect the expanded capability surface,
So that I can use the new features without guessing how they fit the existing product.

**Acceptance Criteria:**

**Given** the phase-2 capability families are implemented
**When** documentation is updated
**Then** the local `stdio`, Docker, Helm, cross-device, and agent-integration guides include or reference the new capabilities where relevant.

**Given** troubleshooting content is reviewed
**When** a user encounters a phase-2 configuration or runtime issue
**Then** the docs provide a corrective path without requiring source-code inspection.

### Story 5.4: Expand automated regression coverage for phase-2 rollout

As a maintainer,
I want the expanded capability surface covered by automated regression checks,
So that phase 2 can ship without weakening transport, safety, or documentation guarantees.

**Acceptance Criteria:**

**Given** the phase-2 epics are implemented
**When** unit, integration, contract, and smoke tests run in CI
**Then** the checks cover the new capability families, transport parity, and regression-prone validation behavior.

**Given** phase-2 documentation and examples change
**When** release validation is performed
**Then** the release includes current docs and example assets aligned with the implemented tool surface.
