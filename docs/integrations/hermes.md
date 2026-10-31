# Hermes — voice announcements

Hermes is a voice assistant that speaks through Sonos. It generates speech audio itself, serves the file over HTTP on the LAN, and uses SoniqMCP to play it and then put the music back.

SoniqMCP never receives or stores the audio. It only tells a speaker which URL to fetch.

---

## The recipe: snapshot → play_uri → restore_snapshot

1. **`snapshot`** the target room. Save the returned `snapshot_id`.
2. **`play_uri`** with the URL of the generated audio file.
3. Wait for the audio to finish (see [Knowing when the announcement is over](#knowing-when-the-announcement-is-over)).
4. **`restore_snapshot`** with the same room and `snapshot_id`.

```text
snapshot(room="Kitchen")
  -> {"snapshot_id": "Q2x0...", "room": "Kitchen", "include_queue": false}

play_uri(room="Kitchen", uri="http://192.168.1.50:8123/tts/9f2c.mp3", title="Hermes")
  -> {"status": "ok", "room": "Kitchen"}

# ...wait for the clip's duration plus about a second...

restore_snapshot(room="Kitchen", snapshot_id="Q2x0...", fade=true)
  -> {"status": "restored", "room": "Kitchen", "queue_restored": false,
      "volume_restored": true, "snapshot_id": "Q2x0...", "note": null}
```

Do not skip the snapshot. Sonos treats a single HTTP audio URL as a **radio stream**, so `play_uri` replaces whatever was playing, and the stream does not reliably stop or hand back control by itself. `restore_snapshot` is what returns the room to its previous source, track, position, and play mode.

### What restore does

- A room that was **playing** resumes playing.
- A room that was **paused or stopped stays paused or stopped.** An announcement never starts music that was not already playing.
- `fade=true` ramps the volume up from zero to the saved level instead of jumping straight to it. The ramp is linear at about 1.25 steps per second, so returning to volume 30 takes roughly 24 seconds.
- Volume, mute, bass, treble, and loudness are restored. If the captured volume is above `max_volume_pct`, the volume is left as it is and the response has `volume_restored: false` with a note. SoniqMCP never raises a room above the cap.
- The snapshot is used up on success. If restore fails, the snapshot is kept so you can retry.

### Queue capture

`snapshot` takes `include_queue` (default `false`). Leave it off for announcements: `play_uri` does not touch the queue, so a normal restore puts the room back on the queue at the same track and position. Set it to `true` only if your workflow replaces the queue. Restoring a captured queue re-adds it one track at a time, which is slow for long queues.

### Grouped rooms

When the room is part of a group, `play_uri` plays on the group coordinator, so the whole group hears the announcement. `snapshot` and `restore_snapshot` also act on the coordinator, so the group goes back to what it was playing. Address the room by any member's name; use the same name for all three calls.

### Back-to-back announcements

Only one snapshot can be pending per room, or per group for grouped rooms. A second `snapshot` before `restore_snapshot` is rejected with a `validation` error on the `snapshot` field.

This is deliberate. A snapshot taken while an announcement is playing would save the announcement stream as the "previous" state, and restoring it would replay the announcement indefinitely.

To play several announcements in a row, snapshot once, call `play_uri` for each clip in turn (waiting for each to finish), then call `restore_snapshot` once at the end. If Hermes can produce announcements faster than it plays them, queue them on the Hermes side.

A pending snapshot stops blocking new snapshots after 10 minutes, so a client that crashes before restoring cannot lock a room until the server restarts. The old snapshot can still be restored after that.

### Snapshot lifetime

Snapshots are held in server memory. They are lost if SoniqMCP restarts, and the server keeps only the 64 most recent. Restore as soon as the announcement finishes. A missing snapshot returns a `validation` error on the `snapshot` field.

---

## Serving the audio

The Sonos speaker downloads the file itself, so the URL must be reachable **from the speaker**, not just from Hermes or SoniqMCP.

- **Use the LAN IP of the host serving the file**, for example `http://192.168.1.50:8123/tts/9f2c.mp3`. Do not use `localhost` or `127.0.0.1`: to the speaker, that is the speaker itself.
- `host.docker.internal` works only with Docker Desktop on macOS and Windows. On Linux hosts and k3s, use the host's LAN IP or a `hostNetwork` service address.
- **Send a correct audio `Content-Type`**, for example `audio/mpeg` for MP3 or `audio/wav` for WAV, and a `Content-Length` if you can. Speakers may refuse or stall on `application/octet-stream` or a missing type.
- Prefer plain HTTP on the LAN. Speakers do not trust self-signed HTTPS certificates.
- Use a fresh file name for each announcement, such as a hash of the text. Speakers can cache by URL.
- MP3 at 44.1 kHz or 48 kHz is the most widely supported format.

---

## Knowing when the announcement is over

Do not wait for the stream to end by itself. Hermes generated the audio, so it knows how long the clip is:

1. Read the duration from the TTS engine, or from the file.
2. After `play_uri` returns, sleep for that duration plus about one second of buffer.
3. Call `restore_snapshot`.

`get_playback_state` can confirm that the room is `PLAYING` after `play_uri`, but it is not a reliable end-of-clip signal for radio-style streams.

---

## Volume

The volume cap (`max_volume_pct`, default 80) applies to every volume change, including the announcement path:

- To make an announcement louder or quieter than current playback, call `set_volume` or `ramp_volume` between `snapshot` and `play_uri`. `restore_snapshot` puts the previous level back.
- `ramp_volume` with `ramp_type="AUTOPLAY_RAMP_TYPE"` fades up from zero quickly, which avoids a sudden blast at the start of the clip.
- Requests above the cap are rejected with a `validation` error. They are never silently clamped.

---

## Security notes

- `play_uri` makes a speaker fetch whatever URL it is given. Expose SoniqMCP only to trusted clients (see [../security/threat-model.md](../security/threat-model.md)). If you do not use announcements, disable it with `SONIQ_MCP_TOOLS_DISABLED=play_uri`.
- Keep the TTS file server on the LAN. Announcement audio can contain personal information, such as calendar or reminder text.
- Error messages returned by SoniqMCP redact URLs, IP addresses, and paths.

---

## Related

- [Command reference](../prompts/command-reference.md): the full tool surface and its parameters
- [Home Assistant](home-assistant.md) and [n8n](n8n.md): the other agent integrations
- [Troubleshooting](../setup/troubleshooting.md)
