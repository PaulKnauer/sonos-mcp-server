# Example Prompts and Usage

Natural-language examples for direct clients and agent-mediated workflows. For the canonical command surface, use [command-reference.md](command-reference.md).

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

If the server does not respond as expected, continue with [../setup/troubleshooting.md](../setup/troubleshooting.md) before issuing playback commands.

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

### Control play mode

> "Turn shuffle on in the Kitchen."
> "Set repeat to all in the Living Room and leave the other play mode settings alone."
> "Show me the current shuffle, repeat, and crossfade settings in the Bedroom."

Claude calls `set_play_mode` or `get_play_mode` and returns the normalized shuffle, repeat, and `cross_fade` state for the target room.

### Seek within the current track

> "Seek the Living Room to 0:01:30."
> "Jump the Kitchen ahead to 0:45:00 in the current track."

Claude calls `seek` with the target room and `HH:MM:SS` position, then returns the resulting playback state.

### Manage the sleep timer

> "What is the sleep timer status in the Bedroom?"
> "Set a 30 minute sleep timer in the Living Room."
> "Clear the Kitchen sleep timer."

Claude calls `get_sleep_timer` or `set_sleep_timer`. Use `0` minutes to clear an active timer.

### Tune room EQ

> "What are the bass, treble, and loudness settings in the Office?"
> "Set the Kitchen bass to 4."
> "Turn loudness off in the Living Room."

Claude calls `get_eq_settings`, `set_bass`, `set_treble`, or `set_loudness` and returns the normalized EQ state for the room.

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

## Agent and automation workflows

These examples assume SoniqMCP is running as a long-lived remote service over **Streamable HTTP** so an external automation or agent can call `http://<host>:8000/mcp`. For the setup steps behind that endpoint, use [../setup/docker.md](../setup/docker.md), [../setup/helm.md](../setup/helm.md), and the integration guides in [../integrations/README.md](../integrations/README.md).

The key rule is that the automation uses the same tool surface as a direct AI client. No separate "agent mode" exists inside SoniqMCP.

### Home Assistant style flow

> "Check that SoniqMCP is reachable, list the rooms, and start my Kitchen Morning Mix favourite."

Expected tool flow:

1. `ping`
2. `list_rooms`
3. `list_favourites`
4. `play_favourite`

This keeps room targeting explicit and verifies connectivity before playback.

### `n8n` workflow example

> "If the Living Room is not already grouped, join the Kitchen to it and start party mode for the evening routine."

Expected tool flow:

1. `get_group_topology`
2. `join_group` or `party_mode`

The automation system decides the branch. SoniqMCP remains the execution layer only.

### Safe volume automation

> "Set the Office to volume 35, but never exceed the configured safety cap."

Claude or the automation calls `set_volume`. Requests above `SONIQ_MCP_MAX_VOLUME_PCT` are rejected, so downstream agents inherit the same safety behavior as direct usage.

### Advanced playback automation

> "If the Living Room is playing, enable shuffle, seek to 0:20:00, and set a 45 minute sleep timer."

Expected tool flow:

1. `get_playback_state`
2. `set_play_mode`
3. `seek`
4. `set_sleep_timer`

This keeps the advanced playback flow transport-neutral while using the same tools available to a direct AI client.

### Audio tuning automation

> "Check the Bedroom EQ settings and, if loudness is on, turn it off and reduce treble by 2."

Expected tool flow:

1. `get_eq_settings`
2. `set_loudness`
3. `set_treble`

The automation still uses the same room-level audio tools and normalized responses as a direct conversational client.

### Queue-aware automation

> "Show the current Living Room queue and start from track 2 if the queue is already loaded."

Expected tool flow:

1. `get_queue`
2. `play_from_queue`

### Recovery-oriented automation

> "Check the server, confirm the Bedroom is available, and only then retry playback."

Expected tool flow:

1. `server_info`
2. `list_rooms`
3. `play`

This pattern avoids brittle retries that assume the same network or room state still exists.

For the supported command surface, use [command-reference.md](command-reference.md). For Claude Desktop configuration details, use [../integrations/claude-desktop.md](../integrations/claude-desktop.md). For local onboarding, use [../setup/stdio.md](../setup/stdio.md).
