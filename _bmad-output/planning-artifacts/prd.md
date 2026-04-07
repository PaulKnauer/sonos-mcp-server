---
date: '2026-03-23'
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: []
workflowType: 'prd'
workflow: 'edit'
briefCount: 0
researchCount: 0
brainstormingCount: 0
projectDocsCount: 0
classification:
  projectType: 'developer_tool'
  domain: 'general'
  complexity: 'medium'
  projectContext: 'greenfield'
lastEdited: '2026-04-02'
editHistory:
  - date: '2026-04-02'
    changes: 'Added Tier 1 and Tier 2 SoCo capability expansion scope, roadmap updates, and functional requirements from the capability gap analysis.'
  - date: '2026-04-02'
    changes: 'Applied validation-driven refinements: measurable NFRs, developer-tool completeness, journey traceability updates, and scope/FR wording fixes.'
---

# Product Requirements Document - Soniq

**Author:** Paul
**Date:** 2026-03-23
**Technical Name:** SoniqMCP
**Descriptor:** A production-grade Sonos MCP server for AI clients and agents

## Executive Summary

`Soniq` is a production-grade Python MCP server for Sonos home audio control, built on `SoCo` and designed for MCP-compatible AI clients and agents. It gives Sonos owners a practical way to control playback, volume, queues, grouping, favourites, and system functions through AI while remaining deployable in real home environments.

The product targets home tinkerers first, but the direction is broader: it should become approachable for less technical Sonos owners over time. The problem is not the absence of Sonos control APIs, but the absence of a Sonos MCP offering that is feature-rich, maintained, and convenient to deploy or configure. `Soniq` closes that gap with a polished, self-hostable server that supports both local experimentation and operational home deployment through Docker and Helm, including private registry-based image delivery.

### What Makes This Special

The differentiator is the combination of capability depth and setup quality. On capability, the product is built on `SoCo`, which is believed to be the most full-featured Sonos control library available, creating a foundation for broader and more reliable Sonos support than existing MCP servers. On usability, the project is explicitly designed to reduce adoption friction through a strong installation and configuration experience, including guided setup, configuration validation, Docker-first onboarding, Helm-based deployment guidance, and potentially an installer or setup script.

The core insight is that the missing product in the market is not merely a Sonos MCP server, but a Sonos MCP server that is both feature-complete and easy to operationalize. Users should choose this product because it gives them a world-class Sonos control layer for AI with a setup experience that respects real-world home infrastructure rather than assuming advanced manual integration work.

## Project Classification

This is a `developer_tool` in the `general` domain, with a smart-home and home-automation subdomain. It is a `medium` complexity greenfield project. The complexity comes from integrating MCP transports, Sonos network control, containerized deployment, and a low-friction configuration experience, without the burden of heavy regulatory or compliance constraints.

## Success Criteria

### User Success

- Within the first-run experience, a user shall be able to install the server, complete configuration validation, connect a supported MCP-capable AI client, and successfully execute `play`, `pause`, `volume`, and room-targeting actions in under 20 minutes by following only the official setup documentation.
- In usability testing against the documented local `stdio` path, at least 90% of representative users shall complete five common Sonos tasks without needing to understand Sonos protocols, MCP internals, or container orchestration details.
- For supported conversational control flows, at least 95% of successful commands shall affect the intended room or group without requiring a corrective follow-up action.
- The v1 tool surface shall cover room discovery, playback, volume, grouping, queue inspection, favourites or playlist playback, and configuration validation, with Tier 1 expansion areas scheduled in the follow-on roadmap rather than left undefined.

### Business Success

- Within the first 3 months, the product shall run continuously in the primary home environment for at least 14 consecutive days without requiring an unplanned rebuild or manual recovery, and it shall support verified local `stdio`, Docker, and Helm-based deployment paths.
- Within the first public-release cycle, the project shall publish a Python package, a container image, and operator documentation that allows an external evaluator to complete installation and first control actions using only the published materials.
- Within 12 months, the project shall maintain public distribution through `PyPI` and container publishing and provide enough documented capability depth and deployment maturity that a user comparing Python-native Sonos MCP options can evaluate it as a credible top-tier choice.
- Community interest may be tracked through installs, GitHub stars, issues, or outside usage reports, but those signals are secondary to proving that the product is operationally credible and adoptable by users beyond the original builder.

### Technical Success

- The product shall support both local `stdio` usage and deployed HTTP-based MCP access in the same release, with documented and testable separation between transport, configuration, Sonos control logic, and deployment assets.
- Default setup profiles shall allow a clean local installation and a clean containerized installation to pass configuration validation without manual file editing beyond documented required values.
- Automated tests shall cover configuration validation, core service behavior, and regression-prone control paths, and the protected-branch CI workflow shall execute those checks on every change.
- Docker and Helm deployment paths shall start successfully from the documented instructions in clean test environments without undocumented patching, and upgrade/troubleshooting documentation shall remain accurate for the released version.

### Measurable Outcomes

- A successful initial release shall allow a new user to install and configure the product, connect an MCP-capable AI client, and execute at least five common Sonos actions locally via `stdio` during first-run setup.
- A successful deployed configuration shall allow the same release artifact to run from a containerized environment using the documented HTTP-based transport path and complete the same core control actions from a second device on the home network.
- The released product shall publish successfully to `PyPI`, publish a container image suitable for practical self-hosted use, and provide a Helm packaging path that passes documented installation and startup verification.
- The roadmap shall define competitive expansion beyond basic playback and grouping through Tier 1 and Tier 2 Sonos capabilities, with the next planned areas explicitly named in the PRD rather than implied.

## Product Scope

### MVP - Minimum Viable Product

The MVP should be a credible release, not a thin proof of concept. It should include a competitive core Sonos tool surface covering playback, volume, mute, queue access, current state, room discovery or configured room targeting, group management, and practical playlist or favourites support where needed to make the product genuinely useful. It should support local `stdio` operation, HTTP-based deployed usage, Docker packaging, Helm deployment, PyPI distribution, and a polished configuration path with opinionated defaults, validation, and strong documentation.

The MVP should be release-worthy for real home use and strong enough that a user comparing available options would see it as a serious alternative rather than an incomplete starting point.

### Growth Features (Post-MVP)

Post-MVP work should deepen the competitive advantage through play modes, seek, sleep timer management, audio EQ controls, input switching, alarm management, playlist CRUD support, group volume and mute controls, local music library access, installer or setup-script support, better diagnostics, richer system introspection, snapshot or restore flows, and stronger support for less technical users. Growth work should also improve the operational experience with better discovery helpers, better error messaging, and further reduction in setup friction.

These features are not required to prove the product is useful, but they materially strengthen the claim that the product is the easiest serious Sonos MCP server to adopt and operate.

### Vision (Future)

The long-term vision is to become the reference Python Sonos MCP server for both direct AI-client use and agent-driven automation. In that future, the server enables richer conversational control experiences such as AI-assisted music recommendations, playlist selection, ambient playback during ongoing conversation, event-driven behavior, and broader ecosystem integration.

Future work can include more advanced transport evolution, event subscriptions, TTS, snapshot orchestration, optional discovery modes, and other capabilities that make the product not only feature-rich but foundational for agentic home audio experiences.

## User Journeys

### Journey 1: Primary User, Local AI Client Success Path

Paul is a home tinkerer with a Sonos system across several rooms and an interest in making AI tools useful beyond chat. He uses an MCP-capable AI client on his computer and wants a direct, low-friction way to control Sonos without standing up infrastructure before he knows the product is worthwhile.

The opening scene is local and simple. He installs the server on the same machine as his AI client, uses a guided setup flow, accepts documented default settings for the standard local profile, validates the configuration, and connects over `stdio`. He asks the AI to suggest music for a mood, start playback in a specific room, adjust the volume, change shuffle or repeat mode, seek within the current track, and later regroup rooms. The product delivers value when these actions work naturally and reliably without requiring him to understand Sonos protocols or MCP transport details.

The climax is when he realizes he can get meaningful, conversational Sonos control from a local AI client with very little setup burden. The resolution is that local `stdio` becomes the easiest day-0 experience and the fastest path to value.

**Reference use case:** running the MCP server locally on the same machine as Claude Desktop, ChatGPT-compatible MCP tooling, or another desktop MCP client.

This journey reveals requirements for local-first onboarding, `stdio` support, documented default profiles, guided configuration, room targeting, playlist or favourites support, play mode control, seek support, and strong validation before runtime.

### Journey 2: Primary User, Setup Failure and Recovery Path

The same user starts setup, but the experience breaks down because the configuration is wrong or the MCP client is not wired correctly. He may not understand how to configure an MCP server, how the client launches it, or how Sonos addressing should be expressed. He is capable of following guidance, but not of diagnosing low-level integration issues from raw logs.

The opening scene is frustration: the client cannot see the server, the server cannot find the expected speaker, or requests reach the wrong place. The product needs to guide recovery rather than merely report failure. It validates configuration early, explains errors in plain language, identifies likely root causes, and suggests corrective action. Ideally, the setup flow can be supported by AI-assisted guidance, a helper skill, or troubleshooting output that is usable by someone who is not deeply technical.

The climax is the recovery moment where the user understands what is wrong and gets back to a working configuration. The resolution is trust: even when setup fails, the product feels supportive rather than brittle.

**Reference use case:** a user attempting first-time setup for Claude, ChatGPT, or another MCP client and needing help correcting a bad config or MCP launch definition.

This journey reveals requirements for config validation, preflight checks, client-specific setup guidance, actionable error messages, guided troubleshooting, and opinionated day-0 defaults.

### Journey 3: Home-Lab Deployment and Networked Use

The same person, now acting as a home-lab operator, wants the product running independently of any one desktop machine. After validating the concept locally, he wants to deploy it on a machine inside the home network so it can serve broader usage patterns and survive beyond an ad hoc local process. He may use Docker directly, publish to a private registry, or deploy through Helm to existing home infrastructure.

The opening scene is a move from experimentation to durable service operation. He deploys the MCP server on a home machine, mini PC, NAS, or Kubernetes environment and exposes it over HTTP/S within the home network. He expects the product to provide a clear, documented path for container configuration, registry usage, network assumptions, upgrades, and validation.

The climax is when the server becomes a dependable service on the home network rather than a local-only experiment. The resolution is operational confidence: the product can be reached by supported AI clients and workflows across devices in the home and fits naturally into a self-hosted environment.

**Reference use case:** running the MCP server on a home-lab machine over HTTP/S and using it from another device on the same network.

This journey reveals requirements for Docker packaging, Helm chart quality, private-registry support, documented HTTP/S deployment, environment-based configuration, upgrade guidance, and reliable network behavior in home environments.

### Journey 4: Mobile and Cross-Device AI Access

A user wants to interact with the Sonos system from a networked mobile device rather than from the machine that hosts the MCP server. The AI experience may live on a phone, tablet, or another device in the home, while the Sonos MCP server runs elsewhere on the local network. The user expects the system to feel seamless even though the architecture is distributed.

The opening scene is convenience: the user is moving around the house and wants to ask Claude, ChatGPT, Gemini, or another AI assistant to start music, change rooms, or shift the vibe without being tied to the host machine. The product succeeds when the deployment model for this scenario is clearly documented, the networking assumptions are understandable, and the remote experience feels as dependable as the local one.

The climax is the first moment of successful remote control from a secondary device. The resolution is that the product becomes a shared home capability rather than a single-machine hack.

**Reference use case:** a user hosting the MCP server inside the home network and interacting with it from a mobile or secondary device running an AI client or agent-capable interface.

This journey reveals requirements for clear remote deployment guidance, home-network-friendly defaults, transport clarity, and documentation for supported client connection patterns.

### Journey 5: Integration User Building Agentic Experiences

An advanced user wants to connect the server into Home Assistant, `n8n`, or a custom agent workflow. Their goal is not just direct control, but richer AI-driven experiences where recommendations, routines, or conversational reasoning lead to Sonos actions. The MCP server is the action layer, not the agent brain, so its job is to expose clean, expressive, dependable tools.

The opening scene is ambition: the user wants an assistant that can reason about mood, time, preferences, and context, then use the MCP server to perform the right audio actions. The product succeeds when its tool interface is broad enough to support real orchestration and stable enough that integrations do not feel like brittle glue code. That includes higher-value Sonos controls such as sleep behavior, audio EQ, input switching, alarm scheduling, richer playlist operations, and music-library-driven playback selection.

The climax is when the integration becomes composable and reusable, supporting direct AI-client usage and agent-driven orchestration with the same underlying control model. The resolution is that the MCP server becomes a platform capability for home audio automation rather than a one-off integration.

**Reference use case:** wiring the MCP server into Home Assistant, `n8n`, or a custom agent workflow to support higher-level conversational or automated audio experiences.

This journey reveals requirements for a clear and comprehensive MCP tool surface, predictable semantics, compatibility across direct and agent-mediated use, and strong integration documentation.

### Journey Requirements Summary

These journeys show that the product must support multiple deployment and usage modes from the start: local `stdio`, home-network HTTP/S deployment, mobile or cross-device access, and agent-driven integrations. The product must make the simplest path extremely easy while still supporting more advanced self-hosted patterns.

They also show that onboarding and recovery are product-defining capabilities. Users need guided setup, sensible defaults, plain-language validation, and clear troubleshooting for different AI-client connection models. Finally, the journeys confirm that the tool interface must be expressive enough to support not just direct playback commands, but broader conversational and orchestration-driven Sonos experiences, including play mode changes, seek, sleep behavior, audio tuning, input switching, alarm flows, richer playlist handling, and library-driven playback selection.

## Domain-Specific Requirements

### Compliance & Regulatory

This product does not operate in a heavily regulated industry and does not require formal compliance frameworks such as HIPAA, PCI-DSS, or similar sector-specific controls. However, it still operates in a trust-sensitive home environment where AI-triggered actions affect physical devices. As a result, the product should respect user control boundaries, support the permission and tool-restriction mechanisms available through MCP, and make it easy for users to limit what connected AI clients or agents are allowed to do.

The product should be positioned clearly as a complementary AI control layer for Sonos, not as a replacement for the official Sonos app. Configuration, documentation, and tool design should reflect this narrower and more focused product role.

### Technical Constraints

The default operating assumption is a single home and a single Sonos household. The product should optimize for home use rather than general multi-tenant or multi-household environments. Default deployment posture should assume local or home-network-only exposure, with any broader exposure treated as an explicit user choice rather than a default product path.

The system must be robust, predictable, and socially appropriate in how it affects the listening environment. In practice, that means avoiding surprising or disruptive behavior, especially around volume control and playback targeting. The user experience should feel civil and classy: commands should behave consistently, configuration should be forgiving, and failures should be explained calmly and clearly rather than exposing technical noise without guidance.

### Integration Requirements

The product must support the full practical extent of MCP-based control boundaries, including permission-aware tool exposure and restrictions where MCP clients support them. It must work in both direct AI-client usage and broader agent-driven orchestration patterns without changing the core mental model of the product.

The product must support two primary runtime patterns: local `stdio` use on the same machine as the AI client, and home-network deployment over HTTP/S for use from other trusted devices or automation systems. It should also document how these patterns differ, when users should choose each one, and what network assumptions apply in a home Sonos environment.

### Risk Mitigations

Unexpectedly loud playback is a key product risk because it breaks trust immediately in a home environment. The product should mitigate this through safe defaults, predictable volume behavior, and design choices that reduce the chance of disruptive commands having outsized impact.

Unreliable setup and inconsistent behavior are also primary risks. The product should mitigate these through guided setup, strong validation, sensible defaults, clear diagnostics, and architecture that emphasizes determinism and repeatability. The system should feel dependable across installation, configuration, transport setup, and Sonos control operations.

## Innovation & Novel Patterns

### Detected Innovation Areas

The core innovation is not the existence of Sonos MCP control by itself, but the decision to treat end-user experience, setup quality, and operational polish as first-class product requirements in a category that currently appears to underinvest in them. `Soniq` aims to deliver a world-class Sonos MCP server that combines deeper feature coverage with a noticeably better user experience than existing alternatives.

A second innovation pattern is the application of high-end software engineering standards to a home-automation MCP product. The differentiator is that `SoniqMCP` is being approached with production-grade architecture, packaging, validation, deployment discipline, and user-centered onboarding rather than as a thin hobby integration. That combination of feature richness and polished usability is the strongest novel pattern in the product.

A third innovation area is the product’s support for multiple modes of use within one coherent system: local `stdio`, home-network HTTP/S deployment, direct AI-client use, and agent-driven orchestration. The product is designed not as a single narrow integration, but as a reusable control layer for AI-driven home audio.

A further innovation pattern is that the server is intentionally designed to support downstream agentic products without absorbing them into scope. For example, a future `DJ Agent` or similar party-oriented agent could use `Soniq` as its Sonos action layer. That keeps the core offering focused while still making it foundational for richer AI audio experiences.

### Market Context & Competitive Landscape

The competitive gap is not simply missing Sonos MCP options. It is the lack of a clearly compelling Sonos MCP product that feels complete, dependable, and considerate toward the end user. Existing solutions may prove the category is viable, but they do not appear to set a strong bar for user experience, setup smoothness, or production-grade polish.

`Soniq` challenges the market by assuming that end-user quality matters even in a technically niche integration space. It also assumes that a Python-native Sonos MCP server can be feature-rich, operationally credible, and pleasant to adopt, rather than trading away usability for raw functionality.

### Validation Approach

The innovation should be validated through user experience outcomes as much as through technical capability. The first proof point is whether users can install, configure, and successfully use `Soniq` with less friction than they would experience with alternatives. The second proof point is whether the server offers a broader and more useful Sonos tool surface in practice, not just in theory.

A practical validation path is:
- prove the local `stdio` path is exceptionally smooth
- prove the Docker and Helm deployment path is dependable and well documented
- demonstrate broader or better Sonos feature support than competing servers
- confirm that users can use the product directly from AI clients and also build richer automations and downstream agents on top of it

The future `DJ Agent` direction should be validated separately as an external consumer of `Soniq`, not as part of the core MCP server scope.

### Risk Mitigation

The primary innovation risk is overreaching by trying to deliver both a world-class server and higher-level AI audio products too early. That should be mitigated by keeping `Soniq` focused on its core role: `a production-grade Sonos MCP server for AI clients and agents`. Richer downstream experiences, including a `DJ Agent`, should be treated as separate products or consumers built on top of the server.

Another risk is claiming superior user experience without delivering materially lower setup friction. That risk should be mitigated by making installer quality, defaults, validation, and troubleshooting measurable product outcomes rather than aspirational language. If the broader innovation thesis does not fully land at first, the fallback success case is still strong: `SoniqMCP` becomes the most feature-rich and operationally credible Sonos MCP server in its category.

## Developer Tool Specific Requirements

### Project-Type Overview

`Soniq` is a Python-native developer tool packaged as `SoniqMCP`, designed to provide production-grade Sonos control through the Model Context Protocol. The implementation and primary packaging target are Python, but the product is intended to work with any MCP-compatible client regardless of that client’s implementation language, as long as it supports the relevant transport and tool-calling model.

The product must balance two expectations that are often in tension in developer tools: deep technical capability and a smooth end-user experience. In this case, usability is part of the technical offering. Installation, integration, examples, and troubleshooting are not secondary documentation tasks; they are part of the core product surface.

### Technical Architecture Considerations

The product should be structured as a cleanly packaged Python project with a stable CLI entry point, well-defined internal modules, and separation between transport handling, Sonos control logic, configuration, and deployment concerns. It must support local `stdio` execution for same-machine MCP use as well as HTTP-based operation for deployed home-network scenarios.

Distribution should support the main ways users are likely to adopt the tool:
- installation from `PyPI`
- containerized execution via Docker image
- self-hosted deployment via Helm chart
- optional setup script or installer to reduce setup friction

The architecture should make it easy to support MCP-compatible AI clients and automation systems without coupling the implementation to any single client vendor. Client-specific integrations belong in examples and configuration guidance, not in product lock-in.

### Language and Installation Methods

The implementation language is Python, and Python packaging is a first-class part of the product strategy. The product should be installable and runnable through standard Python workflows while also supporting users who prefer container-first operation and never want to manage Python environments directly.

Official installation methods for the PRD are:
- `pip` / `PyPI`
- Docker image
- Helm chart
- optional setup script or installer

This mix is important because it supports different user maturity levels. Some users will want the fastest path through `pip` and local `stdio`; others will want a containerized service with repeatable infrastructure; less technical users may benefit most from an installer or guided setup flow.

### Language Support Matrix

The product must define language support in terms of server implementation, package distribution, and client interoperability. The server implementation is Python-only for v1. Official package distribution is Python-first through `PyPI`, with container delivery for language-agnostic runtime use. Client interoperability should be documented for any MCP-compatible client regardless of implementation language, with explicit examples for Python-hosted workflows, desktop AI clients, and networked clients that consume MCP over supported transports.

The PRD should treat Python as the only implementation language commitment for v1. It should not imply official SDKs or native packages for JavaScript, Go, Rust, or other languages unless those become explicit roadmap items.

### API Surface Summary

The product must define a clear consumer-facing tool surface organized by capability area rather than by internal module boundaries. At minimum, the documented surface should group tools into playback control, queue and favourites management, room topology and grouping, advanced playback controls, setup and diagnostics, and deployment/runtime guidance.

The product should also document the expected interaction model for the tool surface: room-targeted control, coordinator-aware actions where Sonos semantics require them, supported advanced-control guards for device-specific features, and parity expectations between direct AI-client use and agent-mediated workflows.

### Client Integration Examples

The PRD should treat the following as first-class example integrations:
- Claude Desktop
- ChatGPT-compatible MCP clients
- Gemini-capable clients where MCP support exists
- Home Assistant
- `n8n`

These integrations should be presented as reference patterns rather than hardcoded dependencies. The product should demonstrate how `Soniq` can be consumed directly by AI clients and indirectly by broader automation or agent systems.

### Documentation and Example Requirements

The documentation set for v1 should include:
- local `stdio` setup
- Docker run setup
- Helm deployment
- MCP client configuration examples
- troubleshooting guide
- example prompts and use cases

These examples should be practical and scenario-based, including local same-machine use, home-network deployment, cross-device access, and integration with external automation or agent systems. The documentation must help users choose the right runtime model for their situation instead of assuming one universal deployment pattern.

### Migration and Upgrade Guidance

The product must define an explicit upgrade and migration posture for users adopting new releases. Documentation should state how users upgrade Python-package installs, containerized deployments, and Helm-based deployments, and should note when configuration changes, tool-surface changes, or breaking behavior changes require manual action.

For v1, the minimum migration commitment is release-note quality guidance covering version-to-version upgrade steps, configuration changes, deprecated options, and any tool-surface changes that could affect MCP clients or automations.

### Implementation Considerations

Because this is a developer tool competing partly on experience quality, implementation decisions should favor clarity, predictability, and maintainability over cleverness. The CLI, config model, error messages, and example assets should all feel deliberate and polished. The product should also be designed so that new MCP clients, new deployment patterns, and downstream agentic consumers can be supported without architectural rework.

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** experience-led platform MVP

The MVP for `Soniq` is not a thin prototype. It is a credibility-first release intended to prove that a Sonos MCP server can be both feature-rich and materially better to adopt than current alternatives. The goal is to make early users say not only “this works,” but “this is the first version I’d actually want to use.”

This means the MVP must deliver both core Sonos utility and a polished operational experience. The product is competing on capability depth, setup smoothness, packaging quality, and deployment maturity at the same time. That increases the initial scope, but it is aligned with the product thesis and competitive position already established in the PRD.

**Resource Requirements:** one primary builder with strong engineering breadth across Python packaging, MCP integration, Sonos control logic, testing, containerization, and documentation. Because this is effectively a one-person build, scoping discipline matters: the MVP should be complete enough to be compelling, but follow-on features should still be staged deliberately.

### MVP Feature Set (Phase 1)

**Core User Journeys Supported:**
- direct local use from an MCP-capable AI client over `stdio`
- setup and recovery for users who struggle with MCP wiring or Sonos configuration
- home-lab deployment over HTTP/S for networked use
- integration into agentic and automation workflows such as Home Assistant or `n8n`

**Must-Have Capabilities:**
- playback controls
- volume and mute controls
- current track and playback state
- room listing and room targeting
- group management
- queue inspection and control
- favourites and playlists
- local `stdio` support
- HTTP/S remote mode
- Docker image
- Helm chart
- PyPI package
- guided setup and configuration validation
- MCP client configuration examples

**Explicitly Out of Scope for MVP:**
- event subscriptions and push-style state propagation
- third-party music-service-specific integrations beyond what existing Sonos abstractions already expose cleanly
- soundbar-specialized tuning features that require device-family-specific behavior
- multi-tenant or internet-exposed deployment models
- non-Python implementation targets or client SDKs

This MVP should be sufficient to make the product feel complete for its intended use cases. It should support the core direct-control and integration journeys without forcing users to wait for basic credibility features in later phases.

### Post-MVP Features

**Phase 2 (Tier 1 Expansion):**
- play mode controls including shuffle, repeat, and crossfade
- seek within the current track
- sleep timer support
- audio EQ controls including bass, treble, and loudness
- input switching for supported line-in and TV scenarios
- setup installer or helper script
- advanced diagnostics
- richer guidance for remote, mobile, and cross-device usage

This phase is the immediate capability expansion recommended by the SoCo gap analysis. It adds high-value Sonos controls that require minimal architectural change and materially improve the usefulness of AI-assisted listening workflows.

**Phase 3 (Tier 2 Expansion):**
- alarm management
- playlist CRUD support
- group volume and mute controls
- local music library browsing and playback support
- snapshot and restore flows
- TTS capabilities

Phase 3 should deepen the product’s control-surface advantage with medium-effort SoCo-backed capabilities that improve daily utility and automation potential without pushing into specialist or architectural-expansion territory.

**Phase 4 (Expansion):**
- event subscriptions
- broader discovery options beyond static configuration
- richer support for downstream agentic consumers
- expanded transport evolution and ecosystem integrations

Phase 4 is where `Soniq` can become not just a strong Sonos MCP server, but a foundational control layer for more advanced AI-powered home audio experiences.

### Risk Mitigation Strategy

**Technical Risks:** the biggest technical risk is trying to deliver too many high-quality concerns at once: Sonos feature depth, transport support, packaging, deployment, setup quality, and documentation. Mitigation requires strong architectural separation, deliberate release discipline, and prioritizing the core tool surface plus the most important setup paths first.

**Market Risks:** the biggest market risk is that the product may claim better usability than existing alternatives without delivering a clearly better day-0 experience. Mitigation requires validating setup smoothness, documentation quality, and practical deployment success with real user flows rather than assuming that feature depth alone will differentiate the product.

**Resource Risks:** the biggest resource risk is solo-builder scope pressure. Mitigation requires keeping the MVP focused on the agreed must-haves, explicitly staging secondary capabilities into later phases, and resisting the temptation to absorb downstream agent products such as a `DJ Agent` into the core server roadmap too early.

## Functional Requirements

### Core Sonos Control

- FR1: Users can list available Sonos rooms that the server can control.
- FR2: Users can target a specific Sonos room when invoking playback and control actions.
- FR3: Users can start playback in a selected room.
- FR4: Users can pause playback in a selected room.
- FR5: Users can stop playback in a selected room.
- FR6: Users can skip to the next track in a selected room.
- FR7: Users can return to the previous track in a selected room.
- FR8: Users can view the current playback state for a selected room.
- FR9: Users can view current track information for a selected room.
- FR10: Users can get the current volume for a selected room.
- FR11: Users can set the volume for a selected room.
- FR12: Users can adjust the volume of a selected room relative to its current level.
- FR13: Users can mute a selected room.
- FR14: Users can unmute a selected room.
- FR15: Users can view the mute state of a selected room.

### Queue, Playlist, and Favourites Management

- FR16: Users can view the queue for a selected room.
- FR17: Users can add playable items to the queue for a selected room.
- FR18: Users can remove queue items from a selected room.
- FR19: Users can clear the queue for a selected room.
- FR20: Users can start playback from a selected queue position.
- FR21: Users can view available Sonos favourites.
- FR22: Users can start playback of a selected favourite in a target room.
- FR23: Users can view available Sonos playlists.
- FR24: Users can start playback of a selected Sonos playlist in a target room.

### Room Grouping and Household Topology

- FR25: Users can view the current Sonos grouping topology.
- FR26: Users can add a room to an existing group.
- FR27: Users can remove a room from its current group.
- FR28: Users can trigger whole-home or multi-room grouping through explicit commands that target all discovered rooms or a specified room set.
- FR29: Users can view a defined system-information set that supports control operations, including room names, coordinator state, group membership, and addressable speaker identity data.
- FR30: Users can view and change shuffle mode for a selected room or its active coordinator.
- FR31: Users can view and change repeat mode for a selected room or its active coordinator.
- FR32: Users can view and change crossfade mode for a selected room or its active coordinator.
- FR33: Users can seek to a specified position within the currently playing track for a selected room.
- FR34: Users can set and inspect a sleep timer for a selected room.
- FR35: Users can view and adjust bass settings for a selected room.
- FR36: Users can view and adjust treble settings for a selected room.
- FR37: Users can view and change loudness settings for a selected room.
- FR38: Users can switch a selected room to supported line-in or TV input sources when the target device supports those inputs.

### MCP Client and Agent Integration

- FR39: Users can run the server as a local MCP endpoint for same-machine AI client usage.
- FR40: Users can run the server as a network-accessible MCP endpoint for trusted home-network usage.
- FR41: MCP-compatible AI clients can invoke the server’s control capabilities through supported transports.
- FR42: Agent-based systems can use the server as a Sonos control layer within broader workflows.
- FR43: Users can use the same core Sonos capabilities through both direct AI-client usage and agent-mediated usage.
- FR44: Users can understand which runtime mode to use for their scenario through product-provided guidance and examples.

### Setup, Configuration, and Onboarding

- FR45: Users can install the product through an official Python package distribution.
- FR46: Users can run the product through an official container image.
- FR47: Users can deploy the product through an official Helm chart.
- FR48: Users can configure the product for a single-household home Sonos environment.
- FR49: Users can use documented default configuration profiles for the common local `stdio` and home-network deployment paths.
- FR50: Users can validate configuration before attempting normal runtime operation.
- FR51: Users can identify configuration errors through actionable setup feedback.
- FR52: Users can access guided setup and onboarding documentation for supported usage patterns.
- FR53: Users can access MCP client configuration examples for supported client types.
- FR54: Users can choose between local and home-network deployment patterns based on documented guidance.

### Permission, Safety, and Control Boundaries

- FR55: Users can restrict which tools or capabilities are exposed to connected MCP clients where MCP permission models support it.
- FR56: Users can control the default exposure posture of the server for local and home-network operation.
- FR57: Users can operate the product within a home-use trust model without exposing it beyond the home network by default.
- FR58: Users can avoid disruptive control outcomes through safe control behavior around sensitive actions such as volume changes and room targeting.
- FR59: Users can avoid invalid or misleading advanced-control actions when a requested capability depends on device type, active coordinator state, or supported input source.

### Documentation, Examples, and Troubleshooting

- FR60: Users can access example usage patterns for local `stdio` operation.
- FR61: Users can access example usage patterns for Docker-based operation.
- FR62: Users can access example usage patterns for Helm-based deployment.
- FR63: Users can access example usage patterns for cross-device and home-network scenarios.
- FR64: Users can access example usage patterns for agentic and automation integrations such as Home Assistant and `n8n`.
- FR65: Users can access troubleshooting guidance for installation, configuration, transport setup, and Sonos control issues.

### Advanced Sonos Automation and Library Control

- FR66: Users can view, create, update, and delete Sonos alarms for supported households and rooms.
- FR67: Users can view, create, update, and delete Sonos playlists exposed through the household.
- FR68: Users can control group-level volume and mute state for an active Sonos group.
- FR69: Users can browse and select content from the local Sonos music library with pagination or bounded-result behavior that remains usable for collections of at least 1,000 items.
- FR70: Users can use the same named advanced-control capabilities through direct AI-client interactions and agent-mediated workflows, with no capability-category mismatch between the two access patterns.

## Non-Functional Requirements

### Performance

- NFR1: Core control actions such as play, pause, stop, room targeting, and volume changes shall return an initial MCP tool response in under 2 seconds for 95% of requests in a healthy single-household environment.
- NFR2: Configuration validation and startup checks shall complete in under 10 seconds for 95% of runs on supported local and containerized setups.
- NFR3: The product shall sustain at least 20 sequential control actions within a 60-second window in a single active session without process restart, request timeout, or control-state corruption.
- NFR4: Local `stdio` operation shall have median end-to-end request latency no worse than 20% faster than equivalent home-network operation under the same household conditions.

### Reliability

- NFR5: Repeating the same supported control action against the same target room under unchanged household conditions shall produce the same resulting Sonos state in at least 99% of test runs.
- NFR6: When speakers are unreachable, configuration is invalid, or MCP transport setup is incorrect, the product shall return a typed failure response with corrective guidance and without unhandled process termination in 100% of tested failure cases.
- NFR7: For every user-correctable runtime failure, the product shall return an error message that identifies the failed action, the affected target, and at least one corrective next step.
- NFR8: Volume-changing actions shall respect configured safety limits in 100% of test cases, and room-targeted actions shall not affect an unintended room in any supported single-command success scenario.
- NFR9: Official Python-package, Docker, and Helm installation paths shall succeed from documented instructions without undocumented manual intervention in clean test environments.

### Security

- NFR10: Default configuration shall bind the product only to local process or trusted home-network use cases and shall not require public-internet exposure for any supported v1 workflow.
- NFR11: No documented deployment pattern shall require broader network access than the minimum needed for the selected runtime mode and Sonos household reachability.
- NFR12: Where the client ecosystem supports MCP permission or tool-restriction controls, the product shall expose enough metadata and configuration control to disable restricted tool categories before runtime.
- NFR13: Configuration and deployment guidance shall document at least one safe-default exposure pattern and at least one explicitly advanced exposure pattern, with the risks of the latter stated in operator-facing language.
- NFR14: Logs, examples, and default configuration flows shall exclude secrets, auth tokens, and household-specific identifiers except where the user explicitly enables diagnostic verbosity.

### Integration

- NFR15: The product shall preserve functional parity for all documented core tools across supported transports, except where transport limitations are explicitly documented.
- NFR16: The product shall preserve the same room-targeting model, safety behavior, and advanced-capability naming across direct AI-client usage and agent-mediated usage.
- NFR17: Official examples shall cover local `stdio`, Docker-based runtime, Helm deployment, and at least three representative MCP client or automation configurations.
- NFR18: A new user following the official integration documentation shall be able to complete a supported client integration without consulting source code or undocumented configuration files.

### Maintainability and Quality

- NFR19: The codebase shall preserve separable module boundaries for Sonos control logic, MCP transport logic, configuration handling, and deployment assets so that changes in one area do not require cross-cutting edits in all others for routine feature additions.
- NFR20: Automated tests shall cover configuration validation, core Sonos control behavior, and regression-prone service logic, and the CI path shall run those checks on every protected-branch change.
- NFR21: Adding a new MCP client example, deployment pattern, or downstream agent integration shall not require redesign of the core Sonos control domain model.
- NFR22: Documentation, examples, and operational assets shall be versioned and updated in the same release cycle as behavior changes that would otherwise make them inaccurate.

### Scalability

- NFR23: The product shall support a single-household, self-hosted environment with at least 10 addressable Sonos rooms without functional degradation in supported control flows.
- NFR24: The product shall tolerate concurrent interaction from at least 3 client sessions within the same household without requiring redesign of the core product model or causing inconsistent room state.
- NFR25: The product shall not require optimization for multi-tenant or internet-scale deployment in v1, and architecture decisions shall favor single-household robustness over generalized scale efficiency.
