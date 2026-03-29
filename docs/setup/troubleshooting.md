# Troubleshooting — Local Setup

Common problems and fixes for SoniqMCP local stdio setup.

---

## Diagnostic categories you will see

SoniqMCP now keeps user-facing failures in four stable categories across tool responses and startup guidance:

| Category | Typical fields | What it means | What to do next |
|---|---|---|---|
| `configuration` | `tools_disabled` | A local setup choice prevents the requested action | Fix `.env`, environment variables, or tool exposure settings, then restart |
| `connectivity` | `sonos_network` | SoniqMCP cannot discover or reach the Sonos household | Check host networking, Docker/Helm discovery posture, then retry |
| `validation` | `room`, `volume` | The request target or value is invalid for the current system state | Correct the room name, queue position, or volume input |
| `operation` | `playback`, `queue`, `group`, `favourites`, `sonos_volume` | Sonos accepted the request path but the action could not complete | Check room reachability, playback state, queue state, or grouping prerequisites |

Tool responses keep the same `error`, `field`, `category`, and `suggestion` keys across `stdio` and Streamable HTTP. User-facing errors do not intentionally expose config file paths, raw secret values, or private host details.

---

## Configuration errors at startup

**Symptom:** The server prints an error and exits immediately, e.g.:

```
[soniq-mcp] setup error: configuration validation blocked startup.
[soniq-mcp] configuration error: transport: Input should be 'stdio'
[soniq-mcp] next step: fix the above configuration values and restart. See docs/setup/troubleshooting.md#configuration-errors-at-startup
```

**What's happening:** This is a `configuration` failure. SoniqMCP validates all configuration before starting. Invalid values cause a clean exit with a message naming the offending field.

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

**What's happening:** This is a `validation` failure. The `max_volume_pct` safety cap is enforced. The default is 80.

**Fix:** Raise the cap in your `.env`:

```dotenv
SONIQ_MCP_MAX_VOLUME_PCT=95
```

Restart the server. The new cap will be shown in `server_info`.

---

## A tool is missing from the tool panel

**Symptom:** A tool like `ping` or `server_info` does not appear.

**What's happening:** This is usually a `configuration` failure. The tool may be in `SONIQ_MCP_TOOLS_DISABLED`.

**Fix:** Check your `.env` for:

```dotenv
SONIQ_MCP_TOOLS_DISABLED=ping,server_info
```

Remove the tool name from the list and restart.

---

## Server prints startup logs but then hangs

**What's happening:** This is normal, not an error category. The stdio transport waits for a client connection on stdin. When Claude Desktop launches the server, it connects immediately. The "hang" only happens when you run the server directly in a terminal without a client.

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
- The user-facing `category`, `field`, and `suggestion` values if the failure came from a tool response

---

## Remote deployment troubleshooting

The sections below cover Docker, Helm, and remote MCP client issues. For remote setup guides, see [docker.md](docker.md) and [helm.md](helm.md).

---

### Docker: container can't discover Sonos rooms

**Symptom:** SoniqMCP starts inside the container but reports no Sonos rooms found. Sonos device discovery times out.

**What's happening:** This is a `connectivity` failure. Docker's default bridge network does not forward UDP multicast traffic. SoCo uses SSDP (UDP multicast on `239.255.255.250:1900`) to discover Sonos devices; the container never receives these packets.

**Fix (Linux):** Restart the container with `--network=host` to use the host network stack directly:

```bash
docker run --rm --network=host \
  -e SONIQ_MCP_TRANSPORT=http \
  -e SONIQ_MCP_HTTP_HOST=0.0.0.0 \
  -e SONIQ_MCP_HTTP_PORT=8000 \
  -e SONIQ_MCP_EXPOSURE=home-network \
  soniq-mcp:local
```

**macOS / Windows Docker Desktop:** `--network=host` routes to the Docker Desktop Linux VM, not the physical host. SSDP still does not reach the home network. There is no simple workaround. For these platforms, the local stdio setup is more reliable.

---

### Docker: port not reachable from remote client

**Symptom:** MCP client reports connection refused or timeout connecting to `http://<host>:8000/mcp`.

**What's happening:** This is also usually a `connectivity` failure.

**Checks:**

1. Confirm the container is running: `docker ps`
2. Confirm the port is mapped (not using `--network=host`): the `PORTS` column should show `0.0.0.0:8000->8000/tcp`
3. Check the host firewall: inbound TCP on port 8000 must be allowed on the Docker host
4. Confirm `SONIQ_MCP_HTTP_HOST=0.0.0.0` — binding to `127.0.0.1` restricts connections to the container's own loopback

---

### Helm: pod fails to start or CrashLoopBackOff

**Symptom:** `kubectl get pods` shows `CrashLoopBackOff` or the pod restarts immediately.

**Diagnosis:**

```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
```

Common causes:

- **Configuration error:** This is a `configuration` failure. SoniqMCP exits cleanly on invalid config with a message naming the offending field (e.g., `configuration error: transport: Input should be 'http'`). Check the log output.
- **Image pull failure:** The pod status may show `ImagePullBackOff`. Ensure `image.repository` and `image.tag` point to an image your cluster can pull. For k3s, you can load a local image with: `docker save soniq-mcp:local | sudo k3s ctr images import -`
- **Port conflict on node:** If using `hostNetwork: true`, confirm port 8000 is free on the node.

---

### Remote: MCP client can't connect to server URL

**Symptom:** Claude Desktop or another MCP client fails to connect to `http://<host>:8000/mcp`. The client may show a connection error or the server does not appear in the tools panel.

**What's happening:** Treat this as a `connectivity` failure until you prove otherwise. If the endpoint is reachable but a Sonos action still fails, use the user-facing `field` and `category` from the tool response to decide whether the next step is network repair, input correction, or Sonos playback recovery.

**Checks:**

1. Confirm the server is running and listening: from the server host, run `curl http://localhost:8000/mcp` — a response (even an error body) confirms the server is up.
2. Confirm the URL uses the correct host and port. The default port is `8000`; if `SONIQ_MCP_HTTP_PORT` was changed, update the URL.
3. For Docker: confirm the port is mapped and the host firewall allows the connection (see [Docker: port not reachable](#docker-port-not-reachable-from-remote-client)).
4. For Helm without ingress: use `kubectl port-forward svc/soniq 8000:8000` and connect to `http://localhost:8000/mcp` from your local machine to test without going through the network.
5. For Claude Desktop, confirm the remote server was added through **Settings > Connectors** with the correct URL. `claude_desktop_config.json` is for local stdio servers, not remote MCP URLs.

---

## Fast recovery flow

Use this order when you need the quickest supported diagnosis path:

1. Confirm the process started cleanly. If startup failed before tools loaded, treat it as a `configuration` or runtime startup problem and use the startup stderr guidance above.
2. Call `server_info` to confirm the active transport, exposure posture, log level, and volume cap without exposing sensitive config.
3. Call `ping` to verify the MCP server is responsive.
4. Call `list_rooms` to confirm Sonos discovery works from the machine or container where SoniqMCP is running.
5. Retry the user action and follow the returned `category`, `field`, and `suggestion`.
