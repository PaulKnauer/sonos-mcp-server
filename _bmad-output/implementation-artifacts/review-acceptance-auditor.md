# Acceptance Auditor Review Prompt

Review this Story 4.1 diff against the spec and current repository context. Check for:
- violations of acceptance criteria
- deviations from spec intent
- missing implementation of specified behavior
- contradictions between spec constraints and actual code

Output findings as a markdown list. Each finding must include:
- one-line title
- which AC or constraint it violates
- evidence from the diff and code

## Spec

File: `_bmad-output/implementation-artifacts/4-1-run-soniqmcp-over-streamable-http.md`

Acceptance criteria:
1. Given a valid deployment configuration, when the user starts the server with `SONIQ_MCP_TRANSPORT=http`, then the server exposes the MCP tool surface over `Streamable HTTP`.
2. Given the server is running in HTTP mode, when a client invokes tools, the remote mode uses the same underlying tool and service boundaries as `stdio` — no tool logic changes are required.
3. Given the server is started in HTTP mode, then the transport-specific bootstrap remains isolated from domain logic (tools and services are unaware of transport).
4. Given the server is configured with `SONIQ_MCP_EXPOSURE=home-network`, then the remote startup path supports the documented home-network trust model and emits appropriate posture guidance.

Key constraints:
- `transports/streamable_http.py` must not import from `tools/`, `services/`, or `adapters/`.
- `server.py` is the only place that creates `FastMCP`.
- Tools, services, and adapters should remain transport-agnostic.

## Diff

See `review-blind-hunter.md` in the same folder for the exact diff block. Audit that diff against the current repository state and the Story 4.1 spec.
