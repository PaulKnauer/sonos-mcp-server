# Claude Desktop Integration

Claude Desktop supports two ways to connect to SoniqMCP: **local stdio** (same machine) and **remote HTTP** (container or cluster on the network). The configuration differs between the two.

---

## Config file location

| Platform | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

---

## Local stdio configuration

Use this when SoniqMCP is installed on the same machine as Claude Desktop. Claude Desktop launches the server as a subprocess; no port is opened.

For full installation and local setup instructions, see [stdio.md](../setup/stdio.md).

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

Replace `/absolute/path/to/sonos-mcp-server` with the real path on your machine (e.g., `/Users/you/github/sonos-mcp-server`).

The `command` field points to the pre-built venv entry point. This bypasses PATH lookup entirely, which is required because Claude Desktop launches MCP servers with a restricted PATH that typically does not include `~/.local/bin`.

---

## Remote HTTP configuration

Use this when SoniqMCP is running as a Docker container or Helm release on another machine (or on the same machine but as a long-running service). Claude Desktop connects over HTTP instead of launching a subprocess.

Remote MCP servers in Claude Desktop are currently added through **Settings > Connectors**, not through `claude_desktop_config.json`.

In the Connectors UI:

1. Open **Settings > Connectors**
2. Choose to add a custom connector
3. Enter the server URL: `http://soniq-host:8000/mcp`
4. Save the connector and wait for Claude Desktop to finish connecting

Replace `soniq-host` with the IP address or hostname of the machine running the container or pod (for example, `192.168.1.42` or `my-server.local`).

The default port is `8000`. If you changed `SONIQ_MCP_HTTP_PORT`, use the matching port in the connector URL.

> `claude_desktop_config.json` is still used for **local stdio** servers. Claude Desktop does not use that file for remote MCP server URLs.

For Docker setup, see [docker.md](../setup/docker.md). For Helm setup, see [helm.md](../setup/helm.md).

---

## Differences between local and remote setup

| | Local stdio | Remote HTTP |
|---|---|---|
| Setup method | `claude_desktop_config.json` with `command` | Claude Desktop Connectors UI with server URL |
| Server launched by | Claude Desktop (subprocess) | Already running independently |
| Transport | stdin/stdout | Streamable HTTP |
| Same-machine required | Yes | No — any network-reachable host |
| Port opened on host | None | 8000 (configurable) |
| Runtime env vars | Set in Claude Desktop config | Set where the server is deployed |

---

## Restart requirement

After editing `claude_desktop_config.json` for local stdio, Claude Desktop must be **fully quit and relaunched**. Closing the window is not enough — use Quit from the application menu, then relaunch.

For remote connectors added through **Settings > Connectors**, follow the UI prompts. If Claude Desktop does not show the new connector immediately, quit and relaunch before troubleshooting further.

After the connection is active, ask Claude: "Can you ping the SoniqMCP server?" to confirm the connection. Claude will call the `ping` tool and return `pong`.
