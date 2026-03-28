# Troubleshooting — Local Setup

Common problems and fixes for SoniqMCP local stdio setup.

---

## Configuration errors at startup

**Symptom:** The server prints an error and exits immediately, e.g.:

```
[soniq-mcp] configuration error: transport: Input should be 'stdio'
[soniq-mcp] fix the above errors and restart.
```

**What's happening:** SoniqMCP validates all configuration before starting. Invalid values cause a clean exit with a message naming the offending field.

**Fix:** Read the field name in the error message, check your project `.env` or exported environment variables, and correct the value. Valid values:

| Field | Valid values |
|---|---|
| `SONIQ_MCP_TRANSPORT` | `stdio` |
| `SONIQ_MCP_EXPOSURE` | `local` |
| `SONIQ_MCP_LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SONIQ_MCP_MAX_VOLUME_PCT` | Integer 0–100 |

---

## Server starts but Claude Desktop shows no tools

**Symptom:** Server starts with no errors, but Claude Desktop does not show Soniq tools.

**Possible causes and fixes:**

1. **Wrong path in `claude_desktop_config.json`**
   Check that `cwd` is the absolute path to your `sonos-mcp-server` directory.

   ```bash
   pwd   # run this inside the project directory to get the absolute path
   ```

   If Claude Desktop keeps overwriting its own file, keep your Soniq entry in
   `~/.config/soniq-mcp/claude-desktop-soniq.json` and merge it back into
   `~/Library/Application Support/Claude/claude_desktop_config.json` instead of
   editing Claude's file as your primary copy.

2. **`uv` not on PATH when Claude Desktop launches**
   Claude Desktop launches with a restricted PATH that typically does not include `~/.local/bin`
   (where `uv` is installed). The most reliable fix is to bypass `uv` entirely and use the
   absolute path to the pre-built venv entry point:

   ```json
   "command": "/absolute/path/to/sonos-mcp-server/.venv/bin/soniq-mcp"
   ```

   This script has a hardcoded shebang pointing to the venv Python, so it works regardless of PATH.
   No `cwd` or `args` are needed.

   If you prefer to keep the `uv run` invocation, use the full path to `uv` and add `--directory`:

   ```json
   "command": "/Users/you/.local/bin/uv",
   "args": ["run", "--directory", "/absolute/path/to/sonos-mcp-server", "python", "-m", "soniq_mcp"]
   ```

   Find your uv path with: `which uv`

3. **Claude Desktop was not restarted after editing the config**
   Always fully quit and relaunch Claude Desktop after editing `claude_desktop_config.json`.

4. **JSON syntax error in config file**
   Validate the file: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool`

5. **Claude Desktop rewrote your config**
   Claude only reads its own runtime file. Use a separate source-of-truth file such as:

   ```text
   ~/.config/soniq-mcp/claude-desktop-soniq.json
   ```

   Then merge that snippet into Claude's runtime file after changes. See
   [stdio setup](stdio.md) for the exact merge command.

6. **Wrong Claude Desktop config shape**
   Claude Desktop expects server entries nested under a top-level `mcpServers` key:

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

---

## `make install` or `uv sync` fails

**Symptom:** `uv sync` exits with a dependency or build error.

**Fix:**
1. Confirm Python 3.12+: `python3 --version`
2. Try creating a fresh venv: `uv venv --clear && uv sync`
3. If behind a corporate proxy, set `HTTPS_PROXY` before running uv.

---

## Volume requests rejected by the AI agent

**Symptom:** The AI agent reports that volume cannot be set above a certain level.

**What's happening:** The `max_volume_pct` safety cap is enforced. The default is 80.

**Fix:** Raise the cap in your `.env`:

```dotenv
SONIQ_MCP_MAX_VOLUME_PCT=95
```

Restart the server. The new cap will be shown in `server_info`.

---

## A tool is missing from the tool panel

**Symptom:** A tool like `ping` or `server_info` does not appear.

**What's happening:** The tool may be in `SONIQ_MCP_TOOLS_DISABLED`.

**Fix:** Check your `.env` for:

```dotenv
SONIQ_MCP_TOOLS_DISABLED=ping,server_info
```

Remove the tool name from the list and restart.

---

## Server prints startup logs but then hangs

**What's happening:** This is normal. The stdio transport waits for a client connection on stdin. When Claude Desktop launches the server, it connects immediately. The "hang" only happens when you run the server directly in a terminal without a client.

There is no useful raw terminal interaction before an MCP client completes the stdio initialization handshake. For a same-machine check:

```bash
cp .env.example .env
make run
```

If you see the startup logs and no configuration error, the server is waiting correctly for Claude Desktop or another MCP client to connect.

---

## Enabling debug logging

Add to your `.env`:

```dotenv
SONIQ_MCP_LOG_LEVEL=DEBUG
```

All log output goes to stderr. In Claude Desktop, MCP server stderr is visible in the developer console.

---

## Still stuck?

Check the GitHub issues page or open a new issue with:
- Your OS and Python version
- The full error output (stderr)
- Your `.env` contents (redact any private values)
