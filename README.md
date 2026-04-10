# SoniqMCP — Sonos MCP Server

Control your Sonos system from any MCP-compatible AI client. Run locally over stdio, deploy with Docker on Linux for whole-home access, or follow the documented Helm / k3s guidance when its networking caveats fit your environment.

## What it does

SoniqMCP is an [MCP](https://modelcontextprotocol.io/) server that exposes your Sonos system as tools for AI agents. Connect Claude Desktop (or any MCP client) to control playback, volume, queues, favourites, playlists, and room grouping through natural conversation.

**Tools available:**

| Category | Tools |
|---|---|
| System | `list_rooms`, `get_system_topology` |
| Playback | `play`, `pause`, `stop`, `next_track`, `previous_track`, `get_playback_state`, `get_track_info` |
| Playback Modes | `get_play_mode`, `set_play_mode`, `seek`, `get_sleep_timer`, `set_sleep_timer` |
| Volume | `get_volume`, `set_volume`, `adjust_volume`, `mute`, `unmute`, `get_mute` |
| Room Audio | `get_eq_settings`, `set_bass`, `set_treble`, `set_loudness` |
| Queue | `get_queue`, `add_to_queue`, `remove_from_queue`, `clear_queue`, `play_from_queue` |
| Favourites and Playlists | `list_favourites`, `play_favourite`, `list_playlists`, `play_playlist` |
| Groups | `get_group_topology`, `join_group`, `unjoin_room`, `party_mode`, `group_rooms` |
| Group Audio | `get_group_volume`, `set_group_volume`, `adjust_group_volume`, `group_mute`, `group_unmute` |
| Inputs | `switch_to_line_in`, `switch_to_tv` |
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

See [docs/setup/stdio.md](docs/setup/stdio.md) for the full local setup guide including Claude Desktop wiring. After the server is running, use [docs/prompts/example-uses.md](docs/prompts/example-uses.md) for direct and agent-mediated prompt examples, and use [docs/prompts/command-reference.md](docs/prompts/command-reference.md) as the canonical command surface.

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

## Command surface

The supported command surface lives in [docs/prompts/command-reference.md](docs/prompts/command-reference.md). That page is the canonical reference for:

- `make` targets for development, quality gates, Docker, Compose, and Helm
- direct CLI invocation examples
- the relationship between local `stdio` workflows and remote `Streamable HTTP` deployment paths

## Docs

- [Setup overview and deployment models](docs/setup/README.md)
- [Local stdio setup guide](docs/setup/stdio.md)
- [Docker deployment guide](docs/setup/docker.md)
- [Helm deployment guide](docs/setup/helm.md)
- [Troubleshooting](docs/setup/troubleshooting.md)
- [Operations and release guidance](docs/setup/operations.md)
- [Prompts and command reference index](docs/prompts/README.md)
- [Example prompts and usage flows](docs/prompts/example-uses.md)
- [Command reference](docs/prompts/command-reference.md)
- [Claude Desktop integration](docs/integrations/claude-desktop.md)
- [Home Assistant integration](docs/integrations/home-assistant.md)
- [n8n integration](docs/integrations/n8n.md)
- [Security policy](SECURITY.md)
- [Threat model](docs/security/threat-model.md)
