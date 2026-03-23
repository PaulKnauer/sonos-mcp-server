## Container Use (Agent Environment)

This project uses [container-use](https://github.com/dagger/container-use) to
give each coding agent its own isolated container environment.

### Agent Guidelines

- Always prefer `mcp__container-use__environment_*` tools for shell commands, file writes, file reads, and environment state management when those tools are available in the session.
- Each agent gets an isolated environment. Do not assume shared filesystem state between agents.
- Use `mcp__container-use__environment_open` first to inspect the current environment state when working inside a container-use session.
- Do not modify `.git` directly from inside the environment. Let the environment tooling manage repository state.
- Do not assume local workspace edits are visible inside a container-use environment unless they have been synchronized through the environment workflow.

### Working Rules

- Treat the container environment as the authoritative execution context for implementation work when container-use is enabled.
- Keep changes scoped and explicit so they can be reviewed and merged cleanly.
- If the task uses multiple agents, assign disjoint file ownership whenever possible.
- Always tell the user how to inspect the environment output:
  - `container-use log <env_id>`
  - `container-use checkout <env_id>`

### Codex Notes

- Codex should be configured with the `container-use stdio` MCP server in `~/.codex/config.toml`.
- After updating Codex MCP configuration, restart Codex so the `mcp__container-use__environment_*` tools are available in new sessions.
- If those MCP tools are not available in the current session, fall back to normal Codex tools and tell the user that container-use is configured but not active in the live session.
