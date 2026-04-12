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

Use room-level controls when you want to change only one room's speaker output. Use group-level controls when you want a synchronized Sonos group to move together. Use input-specific controls when you want to switch the active source instead of changing playback or loudness.

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

## Input switching

Use input-specific controls when the task is "change the active source for this room." These tools are separate from room-level playback commands and group-level audio controls.

### Switch to line-in

> "Switch the Port in the Rack to line-in."
> "Move the Family Room input to line-in."

Claude calls `switch_to_line_in`. If the room does not support line-in, the tool returns a structured validation-style error instead of guessing.

### Switch to TV

> "Switch the Living Room Arc to TV audio."
> "Put the Den soundbar on TV input."

Claude calls `switch_to_tv` and returns the normalized input state for the addressed room.

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

### Browse saved playlists

> "What Sonos playlists do I have?"
> "List the saved playlists and show their IDs."

Claude calls `list_playlists` and returns each playlist's `title`, playback `uri`, and lifecycle `item_id`.

### Play a saved playlist

> "Play the playlist with URI `x-rincon-playlist://pl1` in the Kitchen."
> "Start the saved playlist URI from `list_playlists` in the Living Room."

Claude calls `play_playlist` with a room name and playlist `uri`.

Use `play_playlist` only for playback. It targets playlists by `uri`, not by lifecycle ID.

### Create a new empty playlist

> "Create a new Sonos playlist called Road Trip."
> "Make an empty playlist named Weekend Cleanup."

Claude calls `create_playlist` and returns the normalized playlist record, including the new `item_id` for future lifecycle operations.

### Replace a playlist's contents from a room queue

> "Replace playlist `SQ:1` with the current Living Room queue."
> "Update playlist `SQ:42` from whatever is queued in the Kitchen."

Claude calls `update_playlist` with the target playlist `item_id` and the room whose active queue should become the saved playlist contents.

Use `update_playlist` when you want to overwrite the saved playlist contents from a room queue. Use `play_playlist` when you want to start playback of an already-saved playlist by `uri`.

### Delete a saved playlist

> "Delete playlist `SQ:1`."
> "Remove the saved playlist with item ID `SQ:42`."

Claude calls `delete_playlist` with the playlist `item_id` and returns a delete confirmation.

### Playlist lifecycle rules

- `list_playlists` returns both `uri` and `item_id`.
- `play_playlist` uses `uri`.
- `create_playlist`, `update_playlist`, and `delete_playlist` use `item_id`.
- Playlist rename is not currently supported by the MCP server and should not be requested.

---

## Local music library

Use the library capability family when you want bounded discovery first and playback second. The same tool names and business semantics should apply in direct clients and agent-mediated workflows.

### Browse the library

> "Browse the albums in my local Sonos library."
> "Show me the first 25 artists from the local music library."

Claude calls `browse_library` with a supported category and returns a bounded result set with normalized fields such as `title`, `item_type`, `item_id`, `uri`, `is_browsable`, and `is_playable`.

### Drill into a browsable library container

> "Browse deeper into the artist with item ID `A:ARTIST/1`."
> "Use the album artist result I just got and show me the next level."

Claude calls `browse_library` again with the normalized `parent_id` from the earlier result.

### Play a normalized playable selection

> "Play the library track with URI `x-file-cifs://nas/Music/Track.mp3` in the Living Room."
> "Use the playable library result we just browsed and start it in the Kitchen."

Claude calls `play_library_item` with the room plus the normalized playable selection fields.

### Library selection rules

- Call `browse_library` first to discover or drill into library items.
- Call `play_library_item` only for a normalized playable selection.
- If a result is browse-only, browse deeper instead of guessing playback behavior.
- Direct AI clients and agent workflows should keep the same mental model and the same named tools.

---

## Alarm lifecycle

### List alarms

> "What Sonos alarms are configured?"
> "List all alarms and show their IDs."

Claude calls `list_alarms` and returns the normalized alarm records, including each `alarm_id`.

### Create an alarm

> "Create a weekday alarm for the Bedroom at 07:00:00."
> "Set a daily Living Room alarm for 06:30:00 at volume 20."

Claude calls `create_alarm` with `room`, `start_time`, `recurrence`, and any optional `enabled`, `volume`, or `include_linked_zones` values.

### Update an alarm

> "Disable alarm `101`."
> "Move alarm `101` to the Kitchen at 08:00:00 on weekdays."

Claude first uses `list_alarms` if it needs to confirm the current alarm state, then calls `update_alarm` with `alarm_id`, `room`, `start_time`, `recurrence`, `enabled`, and any optional lifecycle fields that need to change.

### Delete an alarm

> "Delete alarm `101`."
> "Remove the Sonos alarm with ID `205`."

Claude calls `delete_alarm` with the `alarm_id` and returns a delete confirmation.

### Alarm lifecycle rules

- `list_alarms` is the inventory/discovery step.
- `create_alarm` returns the normalized alarm record for the newly-created alarm.
- `update_alarm` and `delete_alarm` target alarms by `alarm_id`.
- Alarm lifecycle responses use typed validation, room, and connectivity errors rather than free-form failures.

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

### Group an explicit room set

> "Group the Living Room, Kitchen, and Patio together."
> "Create a group with Office and Bedroom, with Office as the coordinator."

Claude calls `group_rooms` when you want an exact room set, optionally with an explicit coordinator, instead of incrementally calling `join_group`.

---

## Group audio control

Use these tools when you want a synced group to behave as one audio target. For a single room only, stay with the room-level volume tools above.

### Read the current group audio state

> "What is the group volume for the Living Room group?"
> "Is the Kitchen group muted?"

Claude calls `get_group_volume` and returns the normalized coordinator, member list, volume, and mute state for the active group.

### Set or adjust group volume

> "Set the Living Room group volume to 35."
> "Turn the Kitchen group up by 5."

Claude calls `set_group_volume` or `adjust_group_volume`. The same configured safety cap still applies, but the target is the active synced group instead of one room.

### Mute or unmute a group

> "Mute the whole Office group."
> "Unmute the group that includes Patio."

Claude calls `group_mute` or `group_unmute`.

---

## Agent and automation workflows

These examples assume SoniqMCP is running as a long-lived remote service over **Streamable HTTP** so an external automation or agent can call `http://<host>:8000/mcp`. For the setup steps behind that endpoint, use [../setup/docker.md](../setup/docker.md), [../setup/helm.md](../setup/helm.md), and the integration guides in [../integrations/README.md](../integrations/README.md).

The key rule is that the automation uses the same tool surface as a direct AI client. No separate "agent mode" exists inside SoniqMCP.

### Home Assistant style flow

> "Check that SoniqMCP is reachable, inspect the rooms, group the Living Room and Kitchen, switch the Living Room to TV, and then set that group volume to 30."

Expected tool flow:

1. `ping`
2. `server_info`
3. `list_rooms`
4. `group_rooms`
5. `switch_to_tv`
6. `set_group_volume`

This verifies connectivity and room targeting before any mutation. The automation decides sequencing. SoniqMCP remains the execution layer only.

### `n8n` workflow example

> "Verify the server, list rooms, group Kitchen and Dining together, then mute that group for a call."

Expected tool flow:

1. `ping`
2. `server_info`
3. `list_rooms`
4. `group_rooms`
5. `group_mute`

The automation system decides any extra branching around `get_group_topology`, `group_rooms`, or `group_mute`. SoniqMCP remains the execution layer only.

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

### Library parity examples

- A Home Assistant assistant checks `ping`, `server_info`, and `list_rooms`, then calls `browse_library` to inspect a bounded category before deciding whether to browse deeper or play a normalized playable selection.
- An `n8n` workflow branches on `is_browsable` versus `is_playable` from a `browse_library` result, then calls `play_library_item` only when the selection is explicitly playable.
- The direct-client and agent-mediated flows should use the same fields and the same named capability family; only the transport envelope changes.

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
