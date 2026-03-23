# Story 1.5: Deliver Local Setup and Troubleshooting Guidance

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want clear local setup instructions and troubleshooting guidance,
so that I can get the product working without understanding MCP internals.

## Acceptance Criteria

1. Given a new user wants to run the server locally, when they follow the documented local setup path, then they have step-by-step guidance for installation, configuration, and AI client connection.
2. Given the local setup docs, when the user reads them, then the documentation includes example `stdio` usage.
3. Given common setup problems occur, when the user consults troubleshooting guidance, then common configuration and MCP wiring failures are addressed.
4. Given the local guidance exists, when it is compared to the implementation, then the docs match the implemented command surface and runtime behavior.

## Tasks / Subtasks

- [ ] Create the local setup guide (AC: 1, 2, 4)
  - [ ] Document installation prerequisites and local run flow
  - [ ] Document config creation and validation steps
  - [ ] Document starting the server in `stdio` mode
- [ ] Add MCP client connection guidance (AC: 1, 4)
  - [ ] Provide at least one concrete same-machine AI client setup example
  - [ ] Keep examples aligned with the implemented command surface
  - [ ] Note where local and remote setup paths differ
- [ ] Create troubleshooting guidance for common local failures (AC: 3, 4)
  - [ ] Cover bad configuration
  - [ ] Cover invalid MCP client launch definitions or connection setup
  - [ ] Cover common startup and validation failures
- [ ] Add example prompts and operator-facing command references (AC: 2, 4)
  - [ ] Include basic local `stdio` usage examples
  - [ ] Reference the `Makefile` targets and expected outputs
- [ ] Verify docs against the implementation (AC: 1, 2, 3, 4)
  - [ ] Cross-check every command and path against the running local workflow
  - [ ] Update docs when command names or config fields drift

## Dev Notes

- Depends on Stories 1.1 to 1.4. The docs should follow the implemented local path, not invent one.
- Documentation is a product artifact in this project, not a cleanup step. The PRD explicitly treats guided setup, examples, and troubleshooting as part of the product surface.
- Local-first onboarding is the day-0 path. Keep the primary narrative centered on same-machine `stdio`, not remote deployment.
- Troubleshooting should be plain-language and actionable. Users should not need to know MCP internals to recover from common failures.
- Use examples that match the actual developer/operator command surface, especially `make` targets and local run commands.
- Keep references ready for later docs expansion into Docker, Helm, and cross-device guides, but do not dilute this story with remote deployment detail.

### Project Structure Notes

- Primary implementation paths:
  - `docs/setup/stdio.md`
  - `docs/setup/troubleshooting.md`
  - `docs/prompts/example-uses.md`
  - `README.md`
  - `Makefile`
- Optional integration example references may later expand under `docs/integrations/`, but this story is focused on the local same-machine path.
- Avoid burying setup guidance inside planning artifacts; the user-facing docs belong in `docs/` and `README.md`.

### References

- Story source and acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#story-15-deliver-local-setup-and-troubleshooting-guidance]
- User journey for local AI client success and recovery: [Source: _bmad-output/planning-artifacts/prd.md#journey-1-primary-user-local-ai-client-success-path] [Source: _bmad-output/planning-artifacts/prd.md#journey-2-primary-user-setup-failure-and-recovery-path]
- Documentation and onboarding requirements FR43, FR50, FR55: [Source: _bmad-output/planning-artifacts/prd.md#setup-configuration-and-onboarding] [Source: _bmad-output/planning-artifacts/prd.md#documentation-examples-and-troubleshooting]
- Docs as product surface and command-surface guidance: [Source: _bmad-output/planning-artifacts/architecture.md#development-workflow-integration] [Source: _bmad-output/planning-artifacts/architecture.md#project-structure--boundaries]
- Technical success expectation around setup quality: [Source: _bmad-output/planning-artifacts/prd.md#technical-success]

## Dev Agent Record

### Agent Model Used

gpt-5-codex

### Debug Log References

### Completion Notes List

### File List
