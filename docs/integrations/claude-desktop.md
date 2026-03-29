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

```json
{
  "mcpServers": {
    "soniq-mcp": {
      "url": "http://soniq-host:8000/mcp"
    }
  }
}
```

Replace `soniq-host` with the IP address or hostname of the machine running the container or pod (e.g., `192.168.1.42` or `my-server.local`).

The default port is `8000`. If you changed `SONIQ_MCP_HTTP_PORT`, update the port in the URL to match.

For Docker setup, see [docker.md](../setup/docker.md). For Helm setup, see [helm.md](../setup/helm.md).

---

## Differences between `command` and `url`

| | Local stdio (`command`) | Remote HTTP (`url`) |
|---|---|---|
| Config field | `command` (path to executable) | `url` (HTTP endpoint) |
| Server launched by | Claude Desktop (subprocess) | Already running independently |
| Transport | stdin/stdout | Streamable HTTP |
| Same-machine required | Yes | No — any network-reachable host |
| Port opened on host | None | 8000 (configurable) |
| `env` field supported | Yes | No — env vars set at server startup |

---

## Restart requirement

Claude Desktop must be **fully quit and relaunched** after editing `claude_desktop_config.json`. Closing the window is not enough — use Quit from the application menu, then relaunch.

After relaunch, the SoniqMCP tools will appear in the tools panel. Ask Claude: "Can you ping the SoniqMCP server?" to confirm the connection. Claude will call the `ping` tool and return `pong`.
