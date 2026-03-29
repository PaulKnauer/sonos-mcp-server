# SoniqMCP — Sonos MCP Server

Control your Sonos system from any MCP-compatible AI client. Run locally over stdio, or deploy as a Docker container or Helm release for whole-home access.

## What it does

SoniqMCP is an [MCP](https://modelcontextprotocol.io/) server that exposes your Sonos system as tools for AI agents. Connect Claude Desktop (or any MCP client) to control playback, volume, queues, favourites, playlists, and room grouping through natural conversation.

**Tools available:**

| Category | Tools |
|---|---|
| System | `list_rooms`, `get_system_topology` |
| Playback | `play`, `pause`, `stop`, `next_track`, `previous_track`, `get_playback_state`, `get_track_info` |
| Volume | `get_volume`, `set_volume`, `adjust_volume`, `mute`, `unmute`, `get_mute` |
| Queue | `get_queue`, `add_to_queue`, `remove_from_queue`, `clear_queue`, `play_from_queue` |
| Favourites | `list_favourites`, `play_favourite` |
| Groups | `get_group_topology`, `join_group`, `unjoin_room`, `party_mode` |
| Setup | `ping`, `server_info` |

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

See [docs/setup/stdio.md](docs/setup/stdio.md) for the full local setup guide including Claude Desktop wiring.

## Deployment models

| | Local stdio | Docker (HTTP) | Helm / k3s (HTTP) |
|---|---|---|---|
| Best for | Same-machine AI client | Linux home-lab server | Self-hosted k3s/Kubernetes |
| Client location | Same machine only | Any network client | Any network client |

See [docs/setup/README.md](docs/setup/README.md) for the full deployment comparison and setup guides.

## Configuration

All configuration is via a project-local `.env` file or environment variables.
When both are present, environment variables win:

| Variable | Default | Description |
|---|---|---|
| `SONIQ_MCP_TRANSPORT` | `stdio` | Transport mode (`stdio` or `http`) |
| `SONIQ_MCP_EXPOSURE` | `local` | Network exposure posture (`local` or `home-network`) |
| `SONIQ_MCP_LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `SONIQ_MCP_DEFAULT_ROOM` | _(none)_ | Optional default Sonos room |
| `SONIQ_MCP_MAX_VOLUME_PCT` | `80` | Volume safety cap (0–100) |
| `SONIQ_MCP_TOOLS_DISABLED` | _(none)_ | Comma-separated tools to disable |
| `SONIQ_MCP_HTTP_HOST` | `0.0.0.0` | Bind address (HTTP transport only) |
| `SONIQ_MCP_HTTP_PORT` | `8000` | Port (HTTP transport only) |

## Make targets

| Target | What it does |
|---|---|
| `make install` | Install dependencies (`uv sync`) |
| `make run` | Start the server over stdio |
| `make run-stdio` | Explicitly start in stdio mode |
| `make test` | Run the test suite |
| `make check` | Compile-check all Python source |
| `make lint` | Run ruff lint and format checks |
| `make format` | Auto-fix lint and format issues |
| `make type-check` | Run mypy static type checks |
| `make coverage` | Run tests with coverage report |
| `make audit` | Run dependency vulnerability scan |
| `make ci` | Run all quality gates (lint, type-check, coverage, audit, build-check) |
| `make docker-build` | Build the Docker image |
| `make docker-run` | Run the server as a Docker container |
| `make docker-compose-up` | Start via Docker Compose (detached) |
| `make docker-compose-down` | Stop Docker Compose |
| `make helm-lint` | Validate the Helm chart |
| `make helm-template` | Preview rendered Helm manifests |
| `make helm-install` | Deploy/upgrade via Helm |
| `make tree` | Print the project directory tree |

## Docs

- [Setup overview and deployment models](docs/setup/README.md)
- [Local stdio setup guide](docs/setup/stdio.md)
- [Docker deployment guide](docs/setup/docker.md)
- [Helm deployment guide](docs/setup/helm.md)
- [Troubleshooting](docs/setup/troubleshooting.md)
- [Claude Desktop integration](docs/integrations/claude-desktop.md)
- [Home Assistant integration](docs/integrations/home-assistant.md)
- [n8n integration](docs/integrations/n8n.md)
- [Example prompts](docs/prompts/example-uses.md)
