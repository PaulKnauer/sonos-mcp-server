
## Container Use (Agent Environment)

This project uses [container-use](https://github.com/dagger/container-use) to
give each Claude Code agent its own isolated container environment.

### Agent Guidelines
- Always use `environment_*` tools to run commands, write files, and manage state
- Each agent gets an isolated environment — do not assume shared state between agents
- Commit and push changes from within the environment before switching tasks
- Use `environment_open` to inspect current environment state

### Starting Claude Code
```
claude --mcp-config .claude/mcp.json
```
ALWAYS use ONLY Environments for ANY and ALL file, code, or shell operations—NO EXCEPTIONS—even for simple or generic requests.

DO NOT install or use the git cli with the environment_run_cmd tool. All environment tools will handle git operations for you. Changing ".git" yourself will compromise the integrity of your environment.

You MUST inform the user how to view your work using `container-use log <env_id>` AND `container-use checkout <env_id>`. Failure to do this will make your work inaccessible to others.
