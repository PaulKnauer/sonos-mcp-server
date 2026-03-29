# Story 5.2: Deliver Consistent Diagnostics and Troubleshooting Support

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want actionable diagnostics when setup or runtime behavior fails,
so that I can recover without trial-and-error guesswork.

## Acceptance Criteria

1. Given a configuration, connectivity, or runtime problem occurs, when the server reports the issue, then the error is categorized consistently using the shared error model.
2. Given a configuration, connectivity, or runtime problem occurs, when the server reports the issue, then the user-facing guidance distinguishes correctable setup problems from operational failures.
3. Given a configuration, connectivity, or runtime problem occurs, when the server reports the issue, then diagnostics avoid exposing unnecessary sensitive information.
4. Given a configuration, connectivity, or runtime problem occurs, when the user follows the troubleshooting guidance, then the guidance matches the actual failure modes supported by the implementation.

## Tasks / Subtasks

- [x] Tighten the shared error model and its mappings across tool surfaces (AC: 1, 2, 3)
  - [x] Audit the current domain exception taxonomy in `src/soniq_mcp/domain/exceptions.py` and the user-facing schema factories in `src/soniq_mcp/schemas/errors.py`.
  - [x] Fill any gap where setup/configuration failures, Sonos discovery failures, and operational playback/queue/group failures are not clearly represented and mapped with consistent fields and suggestions.
  - [x] Keep the error contract transport-agnostic so `stdio` and `Streamable HTTP` surface the same categories and user guidance.

- [x] Improve startup and runtime diagnostics without leaking sensitive data (AC: 2, 3)
  - [x] Extend startup diagnostics in `src/soniq_mcp/__main__.py`, `src/soniq_mcp/server.py`, and `src/soniq_mcp/logging_config.py` only as needed to make failures clearer while preserving the current redaction posture.
  - [x] Ensure setup-support responses and startup messages continue to expose only safe metadata such as transport, exposure, log level, and volume cap, not filesystem secrets or private network details.
  - [x] Preserve the distinction between user-facing remediation text and developer-oriented logs.

- [x] Align troubleshooting documentation with implemented failure modes (AC: 2, 4)
  - [x] Update `docs/setup/troubleshooting.md` so each documented class of issue maps to real validation/runtime behavior already implemented in the codebase.
  - [x] Cross-check setup docs and integration guides so troubleshooting advice for local stdio, Docker, remote HTTP, Claude Desktop, Home Assistant, and `n8n` does not overstate unsupported recovery paths.
  - [x] Add or refine links from the main setup and integration entry points only where they improve discoverability of the real troubleshooting flow.

- [x] Add regression coverage for diagnostics behavior and documentation promises (AC: 1, 2, 3, 4)
  - [x] Extend contract tests around `src/soniq_mcp/schemas/errors.py` to lock in category/field/suggestion consistency and non-leakage expectations.
  - [x] Add or extend unit/integration coverage around startup failure messaging and safe `server_info` output.
  - [x] Add or extend documentation regression tests so troubleshooting guidance stays aligned with current runtime behavior and supported deployment patterns.

- [x] Verify the story using the canonical quality gates (AC: 1, 2, 3, 4)
  - [x] Run targeted pytest selections for error-schema, startup, transport, and docs regression coverage while iterating.
  - [x] Run the relevant repo gates from the Makefile or the equivalent `uv run` commands for linting, typing, and tests before review.

## Dev Notes

### Story Intent

This story is about making diagnostics feel productized rather than incidental:

- Users should see consistent, structured failure categories instead of a mix of raw exception text and ad hoc guidance.
- Setup and runtime failures should help the user recover, not just confirm that something broke.
- The docs must only promise recovery steps that match what the code and tests actually support today.

The likely center of gravity is shared error mapping plus troubleshooting documentation, not a large new feature surface. Prefer strengthening existing exceptions, schemas, tests, and docs over inventing a parallel diagnostics subsystem.

### What Already Exists

**Current runtime and schema surface**

- `src/soniq_mcp/domain/exceptions.py` already defines a shared domain-error family for volume, discovery, playback, favourites, queue, grouping, and tool-permission failures.
- `src/soniq_mcp/schemas/errors.py` already provides structured `ErrorResponse` factories with `error`, `field`, and `suggestion`.
- `src/soniq_mcp/__main__.py` already converts config validation failures into clean stderr diagnostics and exits with `sys.exit(1)` instead of a traceback.
- `src/soniq_mcp/tools/setup_support.py` already exposes `ping` and `server_info`, and `server_info` intentionally returns only non-sensitive metadata.
- `src/soniq_mcp/logging_config.py` already documents the rule that raw config values must not be logged.

**Existing test and docs coverage**

- `tests/contract/error_mapping/test_error_schemas.py` already locks in some error-schema behavior but is still narrow.
- `tests/unit/test_main.py` and `tests/smoke/stdio/test_entrypoint_smoke.py` already assert human-readable startup diagnostics for invalid config.
- `tests/integration/transports/test_server_bootstrap.py` already checks that startup diagnostics and `server_info` stay non-sensitive.
- `docs/setup/troubleshooting.md` already covers local, Docker, Helm, and remote-client problems, but this story should tighten alignment between that guidance and real implementation behavior.
- `tests/unit/test_integration_docs.py` already exists from Story 5.1 and is the right place to extend docs regression expectations if troubleshooting guidance or integration caveats become product-critical.

### Previous Story Intelligence

Story 5.1 established a strong pattern that this story should reuse:

- Treat docs and validation as product work, not optional follow-up.
- Keep transport and integration semantics shared across `stdio` and HTTP rather than creating transport-specific behavior.
- Prefer contract and integration tests that inspect metadata and supported behavior without depending on live Sonos hardware.
- Be precise about what is and is not productized. The previous story explicitly corrected docs that overstated Docker and Helm support; diagnostics and troubleshooting content must keep that same discipline.

### Architecture Guardrails

- Keep the transport boundary in `src/soniq_mcp/transports/` and shared app assembly in `src/soniq_mcp/server.py`. Do not create transport-specific error models.
- Keep tool handlers thin and continue to use shared domain exceptions plus structured schemas for user-facing failures.
- Preserve the architecture rule that user-facing guidance and internal diagnostic logs are distinct concerns.
- Continue to avoid exposing unnecessary sensitive information in logs, examples, setup output, or troubleshooting docs.
- Treat setup, diagnostics, and troubleshooting as product-critical assets that deserve regression tests.

### Project Structure Notes

- The architecture document mentions a future `services/diagnostics_service.py`, but the current codebase does not have that module. For this story, align with the implemented structure instead of creating an architectural placeholder just to satisfy the document.
- Existing diagnostics responsibility is currently distributed across `src/soniq_mcp/__main__.py`, `src/soniq_mcp/logging_config.py`, `src/soniq_mcp/domain/exceptions.py`, `src/soniq_mcp/schemas/errors.py`, `src/soniq_mcp/tools/setup_support.py`, and the setup/integration docs.
- If a helper abstraction becomes necessary, keep it small and justified by duplicated logic. Do not introduce a broad new service layer unless the implementation truly needs it.

### Expected File Touches

Likely to modify:

- `src/soniq_mcp/domain/exceptions.py`
- `src/soniq_mcp/schemas/errors.py`
- `src/soniq_mcp/__main__.py`
- `src/soniq_mcp/server.py`
- `src/soniq_mcp/logging_config.py`
- `src/soniq_mcp/tools/setup_support.py`
- `tests/contract/error_mapping/test_error_schemas.py`
- `tests/unit/test_main.py`
- `tests/integration/transports/test_server_bootstrap.py`
- `tests/unit/test_integration_docs.py`
- `docs/setup/troubleshooting.md`
- `docs/setup/README.md`
- `docs/integrations/home-assistant.md`
- `docs/integrations/n8n.md`
- `README.md`

Potentially inspect but avoid changing unless required:

- `src/soniq_mcp/transports/bootstrap.py`
- `src/soniq_mcp/transports/stdio.py`
- `src/soniq_mcp/transports/streamable_http.py`
- `tests/smoke/stdio/test_entrypoint_smoke.py`
- `docs/setup/docker.md`
- `docs/setup/helm.md`

### Implementation Guidance

**Error categorization**

- Keep using the existing shared exception family and `ErrorResponse` factories as the single source of truth for user-facing failure categories.
- Differentiate at least these buckets consistently where the code can support them: configuration/setup error, Sonos connectivity/discovery error, input/validation error, and operational playback/queue/group failure.
- If you add schema helpers, make them additive and consistent with current field naming. Do not replace structured errors with free-form strings.

**User-facing remediation**

- Suggestions should tell the user what to do next, not just restate the error.
- Setup problems should point toward configuration correction or client wiring fixes.
- Operational failures should point toward room reachability, queue state, grouping prerequisites, or Sonos availability as appropriate.
- Keep messages concise and plain-language. This story is about recoverability, not verbose internal diagnostics.

**Sensitive-information handling**

- Do not leak `config_file` paths, raw environment values, tokens, secrets, or unnecessary private network details in startup diagnostics, tool responses, or docs examples.
- Preserve the current `server_info` contract as non-sensitive metadata only.
- When updating troubleshooting docs, keep example output sanitized and representative rather than copied from raw stack traces.

**Documentation alignment**

- The troubleshooting guide should mirror real failure modes already covered by config validation, startup behavior, transport wiring, and tool/service error mapping.
- If the implementation does not yet provide a certain automated diagnostic or recovery path, document the manual recovery path honestly instead of implying more automation than exists.
- Reuse and cross-link existing setup/integration docs rather than duplicating guidance.

**Testing**

- Reuse the existing testing pattern: unit tests for schema/logging/startup behavior, contract tests for response shape, integration tests for server/bootstrap behavior, and docs regression tests for user-facing promises.
- Keep automated coverage hardware-independent. Use mocked failures and metadata inspection instead of requiring real Sonos devices.
- Prefer targeted assertions that prove categories, safe fields, remediation suggestions, and non-leakage guarantees.

### Git Intelligence Summary

Recent commits show the team is actively finishing Epic 5 with a docs-plus-validation pattern:

- `6a68e1d` marked Story 5.1 done after follow-up validation.
- `6e34f76` addressed Story 5.1 review findings and tightened wording around deployment claims.
- `9370bea` implemented Story 5.1 using docs, tests, and parity validation instead of adding new runtime integrations.

Use the same bar here: strengthen implementation truthfulness, tighten regression coverage, and avoid speculative platform claims.

### Library / Framework Requirements

- Stay within the current project baseline in `pyproject.toml`: Python `>=3.12`, `mcp[cli]>=1.26.0`, `python-dotenv>=1.2.2`, and `soco>=0.30.14`.
- Use the existing test and quality stack already configured in the repo: `pytest`, `ruff`, and `mypy`.
- Do not add a new logging, telemetry, or diagnostics dependency for this story unless an actual gap cannot be solved with the standard library and existing project structure.

### Verification Notes

Use the Makefile as the canonical command surface when practical. Prefer the smallest commands that prove the story while iterating:

- `uv run pytest tests/contract/error_mapping/test_error_schemas.py tests/unit/test_main.py tests/integration/transports/test_server_bootstrap.py tests/unit/test_integration_docs.py`
- `uv run pytest tests/smoke/stdio/test_entrypoint_smoke.py`
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src`

Run broader `make test`, `make lint`, or `make type-check` if the final diff reaches beyond the targeted diagnostics surface.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-5-Integration-Diagnostics-and-Productized-Adoption]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-52-Deliver-Consistent-Diagnostics-and-Troubleshooting-Support]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey-2-Primary-User-Setup-Failure-and-Recovery-Path]
- [Source: _bmad-output/planning-artifacts/prd.md#Journey-5-Integration-User-Building-Agentic-Experiences]
- [Source: _bmad-output/planning-artifacts/prd.md#Documentation-Examples-and-Troubleshooting]
- [Source: _bmad-output/planning-artifacts/prd.md#Reliability]
- [Source: _bmad-output/planning-artifacts/prd.md#Integration]
- [Source: _bmad-output/planning-artifacts/prd.md#Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#File-Organization-Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements-to-Structure-Mapping]
- [Source: src/soniq_mcp/__main__.py]
- [Source: src/soniq_mcp/server.py]
- [Source: src/soniq_mcp/logging_config.py]
- [Source: src/soniq_mcp/domain/exceptions.py]
- [Source: src/soniq_mcp/schemas/errors.py]
- [Source: src/soniq_mcp/tools/setup_support.py]
- [Source: tests/contract/error_mapping/test_error_schemas.py]
- [Source: tests/unit/test_main.py]
- [Source: tests/integration/transports/test_server_bootstrap.py]
- [Source: tests/smoke/stdio/test_entrypoint_smoke.py]
- [Source: tests/unit/test_integration_docs.py]
- [Source: docs/setup/troubleshooting.md]
- [Source: docs/setup/README.md]
- [Source: docs/integrations/home-assistant.md]
- [Source: docs/integrations/n8n.md]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex

### Debug Log References

- `./.venv/bin/pytest tests/contract/error_mapping/test_error_schemas.py tests/unit/test_main.py tests/integration/transports/test_server_bootstrap.py tests/unit/test_integration_docs.py tests/smoke/stdio/test_entrypoint_smoke.py`
- `./.venv/bin/pytest tests/unit/test_main.py tests/unit/test_integration_docs.py tests/contract/error_mapping/test_error_schemas.py tests/integration/transports/test_server_bootstrap.py tests/smoke/stdio/test_entrypoint_smoke.py`
- `./.venv/bin/ruff check src tests`
- `./.venv/bin/ruff format --check src tests`
- `./.venv/bin/mypy src`

### Completion Notes List

- Added stable `configuration`, `connectivity`, `validation`, and `operation` categories to the shared domain/schema error contract so tool responses stay transport-agnostic.
- Added user-facing redaction in `ErrorResponse` so URLs, private hosts, and filesystem paths do not leak through diagnostic payloads.
- Split startup diagnostics into setup-validation versus runtime-initialization guidance while keeping user-facing stderr messages safe and actionable.
- Updated troubleshooting and integration docs so the documented recovery flow matches the implemented diagnostics surface (`ping`, `server_info`, `list_rooms`) and current deployment caveats.
- Added regression coverage for category mapping, redaction, startup messaging, safe `server_info` output, and docs alignment.
- Fixed the troubleshooting valid-values table so `SONIQ_MCP_EXPOSURE` reflects both supported postures and clarifies when `home-network` is valid.
- Pointed post-validation startup failures to a transport-neutral runtime initialization section instead of the remote-only troubleshooting anchor.

### File List

- src/soniq_mcp/__main__.py
- src/soniq_mcp/domain/exceptions.py
- src/soniq_mcp/schemas/errors.py
- docs/setup/troubleshooting.md
- docs/integrations/home-assistant.md
- docs/integrations/n8n.md
- tests/contract/error_mapping/test_error_schemas.py
- tests/unit/test_main.py
- tests/integration/transports/test_server_bootstrap.py
- tests/unit/test_integration_docs.py

### Change Log

- 2026-03-29: Implemented Story 5.2 diagnostics hardening, troubleshooting doc alignment, and regression coverage; moved story to review.
- 2026-03-29: Addressed review findings by correcting troubleshooting exposure guidance and routing runtime startup failures to a transport-neutral troubleshooting section.
