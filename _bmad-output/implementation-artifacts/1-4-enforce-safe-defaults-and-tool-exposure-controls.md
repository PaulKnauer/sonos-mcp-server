# Story 1.4: Enforce Safe Defaults and Tool Exposure Controls

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want safe default behavior and controllable tool exposure,
so that AI clients cannot cause unnecessary disruption in my home environment.

## Acceptance Criteria

1. Given the server is configured for home use, when a user reviews or applies runtime settings, then the default exposure posture assumes local or trusted-home-network usage.
2. Given a client ecosystem that supports MCP permission-aware tool restriction, when the server is configured, then tool restriction settings are supported.
3. Given risky actions such as volume changes are available, when they are invoked, then they are subject to explicit validation and safety rules.
4. Given the configured trust model, when the server starts, then it does not expose functionality beyond that model by default.

## Tasks / Subtasks

- [ ] Extend config and domain models for safety controls (AC: 1, 2, 3, 4)
  - [ ] Add explicit safe-default exposure settings
  - [ ] Add tool restriction configuration surfaces compatible with MCP client permission models
  - [ ] Add safety-oriented settings for risky actions such as volume changes
- [ ] Implement safety rule evaluation (AC: 1, 3, 4)
  - [ ] Add domain safety helpers in `domain/safety.py`
  - [ ] Ensure volume and trust-boundary checks can be reused by later control stories
  - [ ] Keep the rule evaluation transport-agnostic
- [ ] Wire tool exposure controls into startup and registration flow (AC: 2, 4)
  - [ ] Ensure disabled or restricted capabilities are not exposed by default when configuration says so
  - [ ] Keep the implementation compatible with local-first operation
- [ ] Add diagnostics and validation feedback for safety config (AC: 1, 2, 3, 4)
  - [ ] Explain invalid or conflicting safety settings clearly
  - [ ] Avoid vague failure modes that force users to reverse engineer behavior
- [ ] Test safety and permission behavior (AC: 1, 2, 3, 4)
  - [ ] Add unit tests for safety rules and config combinations
  - [ ] Add integration coverage for tool exposure behavior
  - [ ] Cover malformed, risky, and out-of-range input cases

## Dev Notes

- Depends on Stories 1.1 to 1.3, especially the config model and local bootstrap.
- The PRD makes safe defaults, permission-aware tool restrictions, and non-disruptive home behavior first-class product requirements, not optional hardening.
- MVP has no built-in end-user auth system. Safety in this story is about exposure posture, permission-aware tool restriction compatibility, and domain-level safeguards.
- The system must default to local or trusted home-network use. Public exposure is always an explicit user choice outside this story’s default path.
- This story should prepare reusable safety boundaries for later Sonos features, especially volume-related actions.
- Keep user-facing messaging civil, clear, and corrective. Robustness matters more than configurability here.

### Project Structure Notes

- Primary implementation paths:
  - `src/soniq_mcp/config/models.py`
  - `src/soniq_mcp/config/validation.py`
  - `src/soniq_mcp/domain/safety.py`
  - `src/soniq_mcp/domain/exceptions.py`
  - `src/soniq_mcp/schemas/errors.py`
  - `src/soniq_mcp/server.py`
  - `tests/unit/domain/`
  - `tests/unit/config/`
  - `tests/contract/error_mapping/`
- Do not implement safety rules as ad hoc checks scattered across tool handlers.
- Keep restriction and safety decisions in shared config/domain layers so later stories inherit them.

### References

- Story source and acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#story-14-enforce-safe-defaults-and-tool-exposure-controls]
- Authentication, security, and safe-default architecture decisions: [Source: _bmad-output/planning-artifacts/architecture.md#authentication--security]
- Error handling and safety process patterns: [Source: _bmad-output/planning-artifacts/architecture.md#process-patterns]
- Safety and permission structure mapping: [Source: _bmad-output/planning-artifacts/architecture.md#requirements-to-structure-mapping]
- FR46-F49 and security/reliability NFRs: [Source: _bmad-output/planning-artifacts/prd.md#permission-safety-and-control-boundaries] [Source: _bmad-output/planning-artifacts/prd.md#security] [Source: _bmad-output/planning-artifacts/prd.md#reliability]
- Domain-specific trust and risk constraints: [Source: _bmad-output/planning-artifacts/prd.md#domain-specific-requirements]

## Dev Agent Record

### Agent Model Used

gpt-5-codex

### Debug Log References

### Completion Notes List

### File List
