# Local Setup Guide — stdio transport

This guide walks you through installing SoniqMCP, configuring it, and connecting a same-machine AI client over stdio.

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.12 or later | `python3 --version` to check |
| [uv](https://docs.astral.sh/uv/) | Fast Python package manager — `pip install uv` |
| A Sonos system on your local network | Needed for Sonos tools (Epic 2+); not required to start the server |
| Claude Desktop or another MCP client | For connecting an AI agent |

---

## 1. Install

```bash
git clone <repo-url> sonos-mcp-server
cd sonos-mcp-server
make install
```

`make install` runs `uv sync`, which creates a virtual environment and installs all dependencies.

To verify the install:

```bash
uv run python -c "import soniq_mcp; print('SoniqMCP import OK')"
```

---

## 2. Configure

Copy the example config and edit as needed:

```bash
cp .env.example .env
```

SoniqMCP automatically loads `.env` from the project root when you start it from this directory.
Open `.env` in your editor. The key fields:

```dotenv
# Transport — keep as stdio for local use
SONIQ_MCP_TRANSPORT=stdio

# Exposure — local means trusted home network only
SONIQ_MCP_EXPOSURE=local

# Log verbosity — DEBUG is useful during first setup
SONIQ_MCP_LOG_LEVEL=INFO

# Optional: set your main listening room
SONIQ_MCP_DEFAULT_ROOM=Living Room

# Safety cap: AI agents cannot set volume above this level
SONIQ_MCP_MAX_VOLUME_PCT=80
```

SoniqMCP validates your configuration at startup. If a field is wrong, it will print which field to fix and exit — no server starts with bad config.

---

## 3. Run locally

```bash
make run
# or explicitly:
make run-stdio
# or directly:
uv run python -m soniq_mcp
```

You should see startup log lines on stderr, ending with the server waiting for a client connection:

```
2026-01-01T12:00:00 soniq_mcp.__main__ INFO SoniqMCP starting — transport=stdio exposure=local max_volume=80%
2026-01-01T12:00:00 soniq_mcp.server INFO SoniqMCP server created — transport=stdio exposure=local max_volume=80%
2026-01-01T12:00:00 soniq_mcp.transports.stdio INFO Starting SoniqMCP over stdio transport
```

The process then waits for an MCP client on stdin/stdout. This is normal; it is not hung.

---

## 4. Connect Claude Desktop

Edit Claude Desktop's config file directly:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add a `soniq-mcp` entry inside the `mcpServers` object. Use the **absolute path to the venv entry point** — this is the most reliable approach because it bypasses PATH lookup entirely:

```json
{
  "mcpServers": {
    "soniq-mcp": {
      "command": "/absolute/path/to/sonos-mcp-server/.venv/bin/soniq-mcp",
      "args": [],
      "env": {
        "SONIQ_MCP_LOG_LEVEL": "INFO",
        "SONIQ_MCP_MAX_VOLUME_PCT": "80"
      }
    }
  }
}
```

Replace `/absolute/path/to/sonos-mcp-server` with the real path on your machine (e.g. `/Users/you/github/sonos-mcp-server`).

> **Why use the venv script instead of `uv run`?**
> Claude Desktop launches MCP servers with a restricted PATH that typically does not include `~/.local/bin` (where `uv` is installed). Using the absolute path to the pre-built venv entry point avoids the PATH lookup entirely and has no dependency on `uv` being discoverable at runtime.

Fully quit and relaunch Claude Desktop after editing the file (closing the window is not enough). The Soniq tools will appear in the tools panel.

---

## 5. Verify the connection

In Claude Desktop, ask:

> "Can you ping the SoniqMCP server?"

Claude will call the `ping` tool and return `pong`. If it does, the full stdio path is working.

Ask for server details:

> "What is the SoniqMCP server configuration?"

Claude calls `server_info` and returns the active transport, exposure posture, log level, and volume cap.

Before you start playback or lifecycle changes, run one more discovery check:

> "List the available Sonos rooms before we change anything."

Claude calls `list_rooms`. That diagnostics-first sequence keeps local troubleshooting simple and matches the same product workflow used by remote deployments and automation guides.

After the connection works, use [../prompts/example-uses.md](../prompts/example-uses.md) for phase-2 scenarios such as play modes, seek and sleep timer, room EQ, inputs, group audio, alarms, playlists, and local library flows. Use [../prompts/command-reference.md](../prompts/command-reference.md) for the canonical named tool surface. The same tool semantics apply over local `stdio` and remote Streamable HTTP; only setup and transport envelopes differ.

---

## Differences from remote deployment

This guide covers same-machine stdio only. Remote deployment (Docker, Helm, Streamable HTTP) is covered in Epic 4 docs. Key differences:

| | Local stdio | Remote HTTP |
|---|---|---|
| Transport | stdin/stdout | Streamable HTTP |
| Network | No port opened | Port 8000 (configurable) |
| Client location | Same machine | Any network client |
| Config | `.env` file or env vars | Same env vars, `SONIQ_MCP_TRANSPORT=http` |
