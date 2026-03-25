# Example Prompts and Usage

Example prompts and command references for SoniqMCP local stdio usage.

> **Note:** Sonos control tools (playback, volume, grouping) arrive in Epic 2.
> The examples below use the setup-support tools available from Epic 1.

---

## Verifying the connection

Use these prompts to confirm SoniqMCP is connected and healthy.

### Ping the server

> "Ping the SoniqMCP server."
> "Are you connected to Sonos?"
> "Check if the SoniqMCP server is running."

Expected response: Claude calls `ping` and confirms `pong`.

### Get server details

> "What is the current SoniqMCP configuration?"
> "Show me the SoniqMCP server info."
> "What transport and exposure mode is the server using?"

Expected response: Claude calls `server_info` and returns:
```
Transport: stdio
Exposure: local
Log level: INFO
Max volume: 80%
```

---

## Checking your setup before adding Sonos tools

### Confirm the volume safety cap

> "What is the maximum volume the server will allow?"

Claude reads `server_info.max_volume_pct`.

### Confirm tool availability

> "What Sonos tools do you have available right now?"

Claude lists all registered MCP tools. If a tool is missing, check `SONIQ_MCP_TOOLS_DISABLED` in your `.env`.

---

## Makefile reference

Run these from the project root:

```bash
make install       # Install / update dependencies
make run           # Start the server (stdio)
make run-stdio     # Explicitly start in stdio mode
make test          # Run all tests
make check         # Compile-check all source files
make tree          # Print project directory structure
```

---

## Direct CLI invocation

```bash
# Standard start
uv run python -m soniq_mcp

# Override log level for a session
SONIQ_MCP_LOG_LEVEL=DEBUG uv run python -m soniq_mcp

# Override volume cap for a session
SONIQ_MCP_MAX_VOLUME_PCT=50 uv run python -m soniq_mcp

# Disable a tool for a session
SONIQ_MCP_TOOLS_DISABLED=ping uv run python -m soniq_mcp

# Using the installed script (after pip/uv install -e .)
soniq-mcp
```

---

## Claude Desktop config snippet

```json
{
  "mcpServers": {
    "soniq-mcp": {
      "command": "uv",
      "args": ["run", "python", "-m", "soniq_mcp"],
      "cwd": "/absolute/path/to/sonos-mcp-server",
      "env": {
        "SONIQ_MCP_LOG_LEVEL": "INFO",
        "SONIQ_MCP_MAX_VOLUME_PCT": "80"
      }
    }
  }
}
```

See [docs/setup/stdio.md](stdio.md) for a full walkthrough.
