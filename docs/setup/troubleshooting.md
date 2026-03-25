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

**Fix:** Read the field name in the error message, check your `.env` or environment variables, and correct the value. Valid values:

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

2. **`uv` not on PATH when Claude Desktop launches**
   Claude Desktop may not inherit your shell PATH. Use the full path to `uv`:

   ```json
   "command": "/Users/you/.local/bin/uv"
   ```

   Find your uv path with: `which uv`

3. **Claude Desktop was not restarted after editing the config**
   Always fully quit and relaunch Claude Desktop after editing `claude_desktop_config.json`.

4. **JSON syntax error in config file**
   Validate the file: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool`

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

To test the server in isolation, use:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | uv run python -m soniq_mcp
```

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
