# Command Reference

Use this page as the canonical command surface for SoniqMCP. It covers the supported `Makefile` targets, direct CLI invocation patterns, and how those commands relate to local `stdio` versus remote `Streamable HTTP` usage.

For natural-language examples, start with [example-uses.md](example-uses.md). For deployment-specific setup, use [../setup/README.md](../setup/README.md) and the linked guides.

## Core developer and operator targets

Run these from the project root:

| Target | What it does | Typical use |
|---|---|---|
| `make install` | Install dependencies with `uv sync` | First-time setup or after dependency changes |
| `make run` | Start the server with the default transport from config | Day-to-day local runs |
| `make run-stdio` | Force local `stdio` transport for the current run | Claude Desktop and same-machine testing |
| `make test` | Run the full test suite | General verification |
| `make check` | Compile-check Python source and tests | Fast syntax sanity check |
| `make lint` | Run `ruff check` and `ruff format --check` | Lint and formatting verification |
| `make format` | Apply formatter changes and lint auto-fixes | Local cleanup before re-running checks |
| `make type-check` | Run `mypy` on `src` | Static type verification |
| `make coverage` | Run tests with coverage output | Coverage-oriented validation |
| `make audit` | Run dependency vulnerability scan | Dependency hygiene |
| `make ci` | Run lint, type-check, coverage, audit, and build-check | Full local quality gate before review |
| `make release-version` | Print the current package version from `pyproject.toml` | Release prep and version checks |
| `make release-bump-patch` | Increment the patch version in `pyproject.toml` | Backward-compatible bug-fix release prep |
| `make release-bump-minor` | Increment the minor version in `pyproject.toml` | Backward-compatible feature release prep |
| `make release-bump-major` | Increment the major version in `pyproject.toml` | Breaking-change release prep |
| `make release-tag` | Create annotated git tag `vX.Y.Z` from the current version | Release cut after the version bump is committed |
| `make release-gh` | Create a GitHub Release with generated notes via `gh` | Manual GitHub Release bootstrap or recovery |
| `make docker-build` | Build the Docker image | Prepare a remote HTTP deployment artifact |
| `make docker-run` | Run the HTTP server in Docker on port `8000` | Linux home-lab validation |
| `make docker-compose-up` | Build and start the Compose stack in detached mode | Compose-based remote setup |
| `make docker-compose-down` | Stop the Compose stack | Compose teardown |
| `make helm-lint` | Validate the Helm chart | Helm chart review |
| `make helm-template` | Render Helm manifests locally | Inspect the generated Kubernetes manifests |
| `make helm-install` | Install or upgrade the Helm release | Deploy to k3s / Kubernetes |
| `make tree` | Print the project directory tree | Orientation and documentation work |

## Choosing the right command path

### Local `stdio`

Use local `stdio` when the MCP client runs on the same machine as SoniqMCP.

```bash
make install
cp .env.example .env
make run-stdio
```

Use that manual start path for same-machine testing with MCP clients that expect you to launch the server yourself.

For Claude Desktop local integration, do not pre-start `make run-stdio`. Claude Desktop launches the server as its own subprocess using the config flow in [../integrations/claude-desktop.md](../integrations/claude-desktop.md) and the setup details in [../setup/stdio.md](../setup/stdio.md).

### Remote `Streamable HTTP`

Use a remote HTTP deployment when another machine, automation system, or remote MCP consumer needs to reach the server at `http://<host>:8000/mcp`.

- Docker: [../setup/docker.md](../setup/docker.md)
- Helm / k3s: [../setup/helm.md](../setup/helm.md)
- Integrations and agent-mediated usage: [../integrations/README.md](../integrations/README.md)

These remote paths remain subject to the documented caveats around Linux host networking, Sonos SSDP discovery, and Helm `hostNetwork` requirements.

## Direct CLI invocation

Use these when you want to bypass `make` and launch the server directly.

```bash
# Start with the configured transport
uv run python -m soniq_mcp

# Force stdio for the current session
SONIQ_MCP_TRANSPORT=stdio uv run python -m soniq_mcp

# Override log level for a session
SONIQ_MCP_LOG_LEVEL=DEBUG uv run python -m soniq_mcp

# Override volume cap for a session
SONIQ_MCP_MAX_VOLUME_PCT=50 uv run python -m soniq_mcp

# Disable a tool for a session
SONIQ_MCP_TOOLS_DISABLED=ping uv run python -m soniq_mcp

# Use the installed entry point after `make install`
.venv/bin/soniq-mcp
```

## Related guides

- [Example prompts and usage flows](example-uses.md)
- [Setup overview](../setup/README.md)
- [Troubleshooting](../setup/troubleshooting.md)
- [Claude Desktop integration](../integrations/claude-desktop.md)
