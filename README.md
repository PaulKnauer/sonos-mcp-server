# SoniqMCP — Sonos MCP Server

Control your Sonos system from any MCP-compatible AI client running on the same machine.

## What it does

SoniqMCP is an [MCP](https://modelcontextprotocol.io/) server that exposes your local Sonos system as tools for AI agents. Run it locally and connect Claude Desktop (or any MCP client) to control playback, volume, and more through natural conversation.

## Quick start

**Prerequisites:** Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
# 1. Clone and install
git clone <repo-url> sonos-mcp-server
cd sonos-mcp-server
make install        # runs: uv sync

# 2. Configure (copy and edit)
cp .env.example .env

# 3. Run
make run            # starts the server over stdio
```

See [docs/setup/stdio.md](docs/setup/stdio.md) for the full local setup guide.

## Configuration

All configuration is via a project-local `.env` file or environment variables.
When both are present, environment variables win:

| Variable | Default | Description |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `stdio` | Transport mode |
| `SONIQ_MCP_EXPOSURE` | `local` | Network exposure posture |
| `SONIQ_MCP_LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `SONIQ_MCP_DEFAULT_ROOM` | _(none)_ | Optional default Sonos room |
| `SONIQ_MCP_MAX_VOLUME_PCT` | `80` | Volume safety cap (0–100) |
| `SONIQ_MCP_TOOLS_DISABLED` | _(none)_ | Comma-separated tools to disable |

## Make targets

| Target | What it does |
|---|---|
| `make install` | Install dependencies (`uv sync`) |
| `make run` | Start the server over stdio |
| `make run-stdio` | Same as `run`, explicitly sets `stdio` transport |
| `make test` | Run the test suite |
| `make check` | Compile-check all Python source |
| `make tree` | Print the project directory tree |

## Docs

- [Local setup guide](docs/setup/stdio.md)
- [Troubleshooting](docs/setup/troubleshooting.md)
- [Example prompts](docs/prompts/example-uses.md)

## Development status

Epic 1 (local foundation) is complete. Sonos playback control, grouping, and remote deployment arrive in later epics.
