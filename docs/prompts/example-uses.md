# Example Prompts and Usage

Natural language prompts and command references for SoniqMCP.

---

## Verifying the connection

Use these prompts to confirm SoniqMCP is connected and healthy before issuing Sonos commands.

### Ping the server

> "Ping the SoniqMCP server."
> "Are you connected to Sonos?"
> "Check if the SoniqMCP server is running."

Expected response: Claude calls `ping` and confirms `pong`.

### Get server details

> "What is the current SoniqMCP configuration?"
> "Show me the SoniqMCP server info."
> "What transport and exposure mode is the server using?"

Expected response: Claude calls `server_info` and returns the active transport, exposure posture, log level, and volume cap.

---

## Room discovery

### List available rooms

> "What Sonos rooms do you have access to?"
> "List all the rooms in my Sonos system."
> "Which Sonos speakers can you see?"

Claude calls `list_rooms` and returns the room names available for targeting.

### Get full system topology

> "Show me the full Sonos system topology."
> "What speakers are in each room?"

Claude calls `get_system_topology` for a detailed view of rooms, speakers, and grouping.

---

## Playback control

All playback commands require a room name. If you have set `SONIQ_MCP_DEFAULT_ROOM` in your config, Claude will use it when no room is specified.

### Start, pause, and stop

> "Play music in the Kitchen."
> "Pause the Living Room."
> "Stop playback in the Bedroom."

Claude calls `play`, `pause`, or `stop` with the named room.

### Skip tracks

> "Skip to the next track in the Office."
> "Go back to the previous song in the Living Room."

Claude calls `next_track` or `previous_track`.

### Check what's playing

> "What's playing in the Kitchen?"
> "What song is on in the Living Room?"
> "Is anything playing in the Bedroom?"

Claude calls `get_playback_state` and `get_track_info` to return the current track, artist, album, and transport state.

---

## Volume control

### Get current volume

> "What's the volume in the Kitchen?"
> "How loud is the Living Room?"

Claude calls `get_volume` and returns the current level and mute state.

### Set volume

> "Set the Kitchen to volume 40."
> "Turn the Living Room up to 60."

Claude calls `set_volume`. Volume is capped at `SONIQ_MCP_MAX_VOLUME_PCT` (default 80) — requests above the cap are rejected with a clear message.

### Adjust volume relatively

> "Turn up the Kitchen a bit."
> "Lower the Bedroom by 10."

Claude calls `adjust_volume` with a positive or negative delta.

### Mute and unmute

> "Mute the Kitchen."
> "Unmute the Living Room."
> "Is the Office muted?"

Claude calls `mute`, `unmute`, or `get_mute`.

---

## Queue management

### View the queue

> "What's in the queue in the Living Room?"
> "Show me the current playlist in the Kitchen."

Claude calls `get_queue` and returns the track list with positions.

### Start from a queue position

> "Play track 3 in the Living Room."
> "Start from position 5 in the Kitchen queue."

Claude calls `play_from_queue` with the 1-based position.

### Remove a track

> "Remove track 2 from the Kitchen queue."

Claude calls `remove_from_queue` with the position.

### Clear the queue

> "Clear the queue in the Living Room."
> "Empty the Kitchen queue."

Claude calls `clear_queue`.

---

## Favourites and playlists

### Browse favourites

> "What Sonos favourites do I have?"
> "List my saved stations."

Claude calls `list_favourites` and returns all saved favourites with their URIs.

### Play a favourite

> "Play my Jazz Radio favourite in the Kitchen."
> "Put on the Morning Mix favourite in the Living Room."

Claude calls `list_favourites` to find the matching URI, then `play_favourite` to start it in the target room.

---

## Room grouping

### See current groups

> "How are my Sonos rooms grouped right now?"
> "Show me the room grouping."

Claude calls `get_group_topology` and returns the current coordinator/member structure.

### Join a room to a group

> "Add the Bedroom to the Living Room group."
> "Sync the Kitchen with the Living Room."

Claude calls `join_group` with the room to add and the coordinator room.

### Remove a room from its group

> "Ungroup the Bedroom."
> "Make the Kitchen play on its own."

Claude calls `unjoin_room`.

### Whole-home playback

> "Play music in every room."
> "Group all rooms together."
> "Party mode."

Claude calls `party_mode` to join all rooms into a single whole-home group.

---

## Makefile reference

Run these from the project root:

```bash
make install       # Install / update dependencies
make run           # Start the server (stdio)
make run-stdio     # Explicitly start in stdio mode
make test          # Run the test suite
make coverage      # Run tests with coverage report
make lint          # Check code style
make format        # Auto-fix code style
make type-check    # Run static type checks
make ci            # Run all quality gates
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

# Using the installed entry point (after uv sync)
.venv/bin/soniq-mcp
```

---

## Claude Desktop config snippet (local stdio)

Add this entry to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

Use the absolute path to the venv entry point — Claude Desktop launches MCP servers with a restricted PATH that typically does not include `~/.local/bin` (where `uv` lives).

For remote HTTP connections (Docker or Helm deployment), see [docs/integrations/claude-desktop.md](../integrations/claude-desktop.md).

See [docs/setup/stdio.md](../setup/stdio.md) for the full local setup walkthrough.
