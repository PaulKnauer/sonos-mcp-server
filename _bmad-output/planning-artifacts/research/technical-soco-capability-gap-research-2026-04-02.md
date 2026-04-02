---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - '_bmad-output/planning-artifacts/epics.md'
  - '_bmad-output/planning-artifacts/prd.md'
  - 'src/soniq_mcp/tools/'
  - 'https://docs.python-soco.com/en/latest/api/soco.core.html'
workflowType: 'research'
lastStep: 5
research_type: 'technical'
research_topic: 'SoCo Python library capability gap analysis for sonos-mcp-server'
research_goals: 'Identify SoCo capabilities not yet exposed as MCP tools'
user_name: 'Paul'
date: '2026-04-02'
web_research_enabled: true
source_verification: true
---

# Research Report: SoCo Python Library — Capability Gap Analysis for sonos-mcp-server

**Date:** 2026-04-02
**Author:** Paul
**Research Type:** Technical — Library Capability Gap Analysis
**SoCo Version:** 0.31.0-dev

---

## Technical Research Scope Confirmation

**Research Topic:** SoCo Python library capability gap analysis for sonos-mcp-server
**Research Goals:** Identify SoCo capabilities not yet exposed as MCP tools; examples included shuffle/repeat, sleep timer, alarms, line-in/TV input, audio EQ, crossfade, seek, TuneIn/radio.

**Research Methodology:**
- Codebase inspection of all 30 implemented MCP tools and their SoCo API calls
- Web research against official SoCo documentation (docs.python-soco.com) and GitHub
- Cross-reference to produce an authoritative gap table with implementation guidance

**Scope Confirmed:** 2026-04-02

---

## Technology Stack Analysis

### SoCo Library Overview

SoCo (Sonos Controller) is the authoritative open-source Python library for Sonos control.

| Attribute | Value |
|---|---|
| Current version | 0.31.0-dev |
| Python support | 3.6+ |
| Documentation | http://docs.python-soco.com |
| GitHub | https://github.com/SoCo/SoCo |
| PyPI | https://pypi.org/project/soco/ |
| Protocol | UPnP over local network (no Sonos cloud required) |

**SoCo API Surface Summary:**
- ~55 read/write or read-only properties on the core `SoCo` class
- ~40 instance methods + static methods
- 15 music library methods on `MusicLibrary`
- 10 music service methods on `MusicService`
- 8 alarm functions/methods
- 9 discovery functions
- 14 low-level UPnP service classes
- 3 event subscription backends (threaded, Twisted, asyncio)

### Current Implementation

The sonos-mcp-server project wraps SoCo behind a clean layered architecture:

| Layer | Location | Role |
|---|---|---|
| Tools | `src/soniq_mcp/tools/` | Thin MCP handlers |
| Services | `src/soniq_mcp/services/` | Business logic orchestration |
| Adapters | `src/soniq_mcp/adapters/` | SoCo API boundary (only touch SoCo here) |
| Domain | `src/soniq_mcp/domain/` | Domain models and exceptions |

**Total implemented MCP tools: 30** across 8 modules.

_Sources: SoCo official documentation (docs.python-soco.com), codebase inspection of `src/soniq_mcp/`_

---

## Current Implementation Inventory

The following SoCo capabilities are **already exposed** as MCP tools:

| Tool Name | SoCo API Used |
|---|---|
| `list_rooms` | `soco.discover()`, `zone.player_name`, `.uid`, `.ip_address`, `.is_coordinator`, `.group` |
| `get_system_topology` | `zone.all_zones`, `zone.get_speaker_info()`, `zone.is_visible` |
| `play` | `zone.play()` |
| `pause` | `zone.pause()` |
| `stop` | `zone.stop()` |
| `next_track` | `zone.next()` |
| `previous_track` | `zone.previous()` |
| `get_playback_state` | `zone.get_current_transport_info()` |
| `get_track_info` | `zone.get_current_track_info()` |
| `get_volume` | `zone.volume` (read), `zone.mute` (read) |
| `set_volume` | `zone.volume` (write) |
| `adjust_volume` | `zone.volume` (read + write) |
| `mute` | `zone.mute = True` |
| `unmute` | `zone.mute = False` |
| `get_mute` | `zone.mute` (read) |
| `get_queue` | `zone.get_queue(max_items=200)` |
| `add_to_queue` | `zone.add_uri_to_queue(uri)` |
| `remove_from_queue` | `zone.get_queue()`, `zone.remove_from_queue(item)` |
| `clear_queue` | `zone.clear_queue()` |
| `play_from_queue` | `zone.play_from_queue(position)` |
| `list_favourites` | `zone.music_library.get_sonos_favorites()` |
| `play_favourite` | `zone.play_uri(uri, meta)` |
| `list_playlists` | `zone.music_library.get_music_library_information("sonos_playlists")` |
| `play_playlist` | `zone.clear_queue()`, `zone.add_uri_to_queue()`, `zone.play_from_queue(0)` |
| `get_group_topology` | `zone.is_coordinator`, `zone.group`, `zone.group.coordinator` |
| `join_group` | `zone.join(coordinator_zone)` |
| `unjoin_room` | `zone.unjoin()` |
| `party_mode` | `zone.partymode()` |
| `ping` | (none) |
| `server_info` | (none) |

---

## Capability Gap Analysis

### Gap Category 1: Play Modes (Shuffle / Repeat / Crossfade)

**Priority: HIGH | Complexity: LOW | AI Value: HIGH**

These are among the most commonly requested features for music control and map directly to simple property reads/writes.

| SoCo API | Type | Description |
|---|---|---|
| `zone.play_mode` | r/w property | Combined mode string: `NORMAL`, `REPEAT_ALL`, `REPEAT_ONE`, `SHUFFLE`, `SHUFFLE_NOREPEAT`, `SHUFFLE_REPEAT_ONE` |
| `zone.shuffle` | r/w property | Boolean shorthand for shuffle state |
| `zone.repeat` | r/w property | `False` / `True` / `'ONE'` shorthand for repeat state |
| `zone.cross_fade` | r/w property | Boolean crossfade between tracks |

**Suggested MCP Tools:**
- `get_play_mode(room)` → returns `{play_mode, shuffle, repeat, cross_fade}`
- `set_play_mode(room, mode)` → accepts `NORMAL | REPEAT_ALL | REPEAT_ONE | SHUFFLE | SHUFFLE_NOREPEAT | SHUFFLE_REPEAT_ONE`
- `set_shuffle(room, enabled)` → convenience boolean wrapper
- `set_repeat(room, mode)` → convenience wrapper (`off | all | one`)
- `set_crossfade(room, enabled)` → boolean toggle

**Implementation notes:** These are pure property reads/writes on the coordinator. No additional service needed beyond extending `SoCoAdapter` and creating a new `playmode.py` tools module.

---

### Gap Category 2: Seek

**Priority: HIGH | Complexity: LOW | AI Value: HIGH**

Enables seeking to a position in the current track — essential for podcast/audiobook use.

| SoCo API | Type | Description |
|---|---|---|
| `zone.seek(position, track=None)` | method | Seek to `"HH:MM:SS"` position in current or specified track |

**Suggested MCP Tools:**
- `seek(room, position)` → `position` as `"HH:MM:SS"` string

**Implementation notes:** Single adapter method, minimal service logic. Validate position format.

---

### Gap Category 3: Sleep Timer

**Priority: HIGH | Complexity: LOW | AI Value: HIGH**

The sleep timer is one of the most used Sonos features — telling the system to stop playing after a set time. Very natural to ask an AI assistant.

| SoCo API | Type | Description |
|---|---|---|
| `zone.set_sleep_timer(sleep_time_seconds)` | method | Schedule stop after N seconds (pass `None` to cancel) |
| `zone.get_sleep_timer()` | method | Returns remaining seconds or `None` |

**Suggested MCP Tools:**
- `set_sleep_timer(room, minutes)` → converts to seconds internally; `0` or `None` cancels
- `get_sleep_timer(room)` → returns `{remaining_seconds, remaining_minutes}` or `{active: false}`

**Implementation notes:** Accepts minutes (more natural for AI users) and converts to seconds. The adapter wraps the coordinator's sleep timer.

---

### Gap Category 4: Audio EQ (Bass, Treble, Loudness, Balance)

**Priority: MEDIUM | Complexity: LOW | AI Value: MEDIUM**

These settings let users tune the audio character of a room.

| SoCo API | Type | Description |
|---|---|---|
| `zone.bass` | r/w property | EQ integer -10 to +10 |
| `zone.treble` | r/w property | EQ integer -10 to +10 |
| `zone.loudness` | r/w property | Boolean loudness compensation |
| `zone.balance` | r/w property | 2-tuple `(left, right)` 0–100 each (stereo pairs only) |
| `zone.trueplay` | r/w property | Boolean Trueplay calibration on/off |

**Suggested MCP Tools:**
- `get_eq_settings(room)` → returns `{bass, treble, loudness, balance}`
- `set_bass(room, level)` → integer -10 to +10
- `set_treble(room, level)` → integer -10 to +10
- `set_loudness(room, enabled)` → boolean
- `set_balance(room, left, right)` → stereo pairs only (guard with device capability check)

**Implementation notes:** `balance` only applies to stereo pairs; guard this with an appropriate error. `trueplay` is read-only on most devices (can be toggled only on supported hardware). Suggest a single `get_eq_settings` read tool plus individual setters.

---

### Gap Category 5: Input Switching (Line-In / TV)

**Priority: MEDIUM | Complexity: LOW | AI Value: HIGH**

Enables controlling Sonos speakers used with TVs or connected audio sources.

| SoCo API | Type | Description |
|---|---|---|
| `zone.switch_to_line_in(source=None)` | method | Switch to RCA line-in input |
| `zone.switch_to_tv()` | method | Switch soundbar to TV/HDMI ARC |
| `zone.is_playing_radio` | r/o property | Boolean |
| `zone.is_playing_tv` | r/o property | Boolean |
| `zone.is_playing_line_in` | r/o property | Boolean |
| `zone.music_source` | r/o property | String describing current source |

**Suggested MCP Tools:**
- `get_music_source(room)` → returns `{source, is_playing_tv, is_playing_line_in, is_playing_radio}`
- `switch_to_line_in(room)` → switches to line-in (guards: device must support it)
- `switch_to_tv(room)` → switches to TV input (guards: soundbar only)

**Implementation notes:** Both `switch_to_line_in` and `switch_to_tv` raise `SoCoException` on non-supported hardware. Guard these in the adapter with a helpful error message.

---

### Gap Category 6: Alarm Management

**Priority: MEDIUM | Complexity: MEDIUM | AI Value: HIGH**

Alarms are a core Sonos feature — waking up to music is a prime AI-assistant use case.

| SoCo API | Type | Description |
|---|---|---|
| `alarms.get_alarms(zone=None)` | function | Retrieve all system alarms as `Alarm` objects |
| `Alarm(zone, start_time, duration, recurrence, enabled, program_uri, play_mode, volume, include_linked_zones)` | class | Construct alarm |
| `alarm.save()` | method | Persist new/modified alarm |
| `alarm.remove()` | method | Delete alarm |
| `alarm.update(**kwargs)` | method | Modify alarm attributes |
| `alarm.get_next_alarm_datetime(from_datetime)` | method | When will alarm next fire |
| Recurrence patterns | — | `DAILY`, `ONCE`, `WEEKDAYS`, `WEEKENDS`, `ON_DDDDDD` |
| Play modes | — | `NORMAL`, `SHUFFLE`, `REPEAT_ALL`, etc. |

**Suggested MCP Tools:**
- `list_alarms()` → all alarms with ID, time, recurrence, enabled state, room
- `create_alarm(room, time, recurrence, volume, play_mode, enabled)` → create new alarm
- `update_alarm(alarm_id, **fields)` → modify existing alarm
- `delete_alarm(alarm_id)` → remove alarm
- `enable_alarm(alarm_id, enabled)` → toggle without full update

**Implementation notes:** `Alarm` objects require a SoCo zone instance. Alarms are household-wide (any device can be used to read). Medium complexity because of the rich Alarm data model and recurrence string parsing. Consider providing recurrence as an enum in the tool schema.

---

### Gap Category 7: Playlist Management (Create / Edit / Delete)

**Priority: MEDIUM | Complexity: MEDIUM | AI Value: MEDIUM**

Currently only `list_playlists` and `play_playlist` exist. Full CRUD for Sonos playlists is available.

| SoCo API | Type | Description |
|---|---|---|
| `zone.create_sonos_playlist(title)` | method | Create empty playlist |
| `zone.create_sonos_playlist_from_queue(title)` | method | Save queue as new playlist |
| `zone.remove_sonos_playlist(sonos_playlist)` | method | Delete a playlist |
| `zone.add_item_to_sonos_playlist(item, playlist)` | method | Add item to playlist |
| `zone.remove_from_sonos_playlist(playlist, tracks)` | method | Remove tracks from playlist |
| `zone.reorder_sonos_playlist(playlist, tracks, new_pos)` | method | Reorder tracks |
| `zone.get_sonos_playlist_by_attr(attr_name, match)` | method | Look up playlist by attribute |

**Suggested MCP Tools:**
- `create_playlist(title)` → creates empty Sonos playlist
- `save_queue_as_playlist(room, title)` → saves current queue as playlist
- `delete_playlist(uri)` → removes playlist
- `add_to_playlist(playlist_uri, track_uri)` → adds track
- `remove_from_playlist(playlist_uri, position)` → removes by position

**Implementation notes:** These operate on `DidlPlaylistContainer` objects. The existing `list_playlists` tool returns URIs which can be used as identifiers. Medium complexity due to DIDL object handling.

---

### Gap Category 8: Local Music Library Browsing

**Priority: MEDIUM | Complexity: MEDIUM | AI Value: MEDIUM**

For households with a NAS or local music library connected to Sonos, these provide search and browse capabilities.

| SoCo API | Type | Description |
|---|---|---|
| `soco.music_library.get_artists(**kwargs)` | method | List all artists |
| `soco.music_library.get_albums(**kwargs)` | method | List all albums |
| `soco.music_library.get_tracks(**kwargs)` | method | List all tracks |
| `soco.music_library.get_genres(**kwargs)` | method | List all genres |
| `soco.music_library.search_track(artist, album, track)` | method | Search by artist/album/title |
| `soco.music_library.get_albums_for_artist(artist)` | method | Albums by a specific artist |
| `soco.music_library.get_tracks_for_album(artist, album)` | method | Tracks on an album |
| `soco.music_library.browse(ml_item, start, ...)` | method | Navigate library hierarchy |
| `soco.music_library.library_updating` | property | Boolean: library scan in progress |
| `soco.music_library.start_library_update()` | method | Trigger library refresh |

**Suggested MCP Tools:**
- `search_music_library(query, type)` → type: `artists | albums | tracks | genres` — free-text search
- `get_library_artists()` / `get_library_albums()` / `get_library_tracks()` → list resources
- `get_albums_for_artist(artist)` → scoped album listing
- `get_tracks_for_album(artist, album)` → scoped track listing

**Implementation notes:** Only relevant for households with local music shares. Consider gating behind a config flag. May return large result sets — pagination support important. The existing `FavouritesService` / `SoCoAdapter` can be extended.

---

### Gap Category 9: Group Volume and Mute

**Priority: LOW-MEDIUM | Complexity: LOW | AI Value: MEDIUM**

Control volume/mute for an entire group at once rather than room by room.

| SoCo API | Type | Description |
|---|---|---|
| `soco.group.volume` | r/w property | Integer 0–100; group-level volume |
| `soco.group.mute` | r/w property | Boolean; group-level mute |
| `soco.group.set_relative_volume(rel)` | method | Adjust group volume by ±N |

**Suggested MCP Tools:**
- `get_group_volume(room)` → volume of room's group
- `set_group_volume(room, volume)` → set group volume
- `adjust_group_volume(room, delta)` → relative group adjustment
- `group_mute(room)` / `group_unmute(room)` → group mute toggles

**Implementation notes:** Operates on `zone.group` (the group object of any member). Simple property reads/writes.

---

### Gap Category 10: Speaker / Device Properties

**Priority: LOW | Complexity: LOW | AI Value: LOW-MEDIUM**

Expose additional system properties not yet surfaced in `get_system_topology`.

| SoCo API | Type | Description |
|---|---|---|
| `zone.status_light` | r/w property | Toggle the white LED ring |
| `zone.buttons_enabled` | r/w property | Enable/disable physical buttons |
| `zone.get_battery_info()` | method | Battery state (Sonos Move/Roam only) |
| `zone.is_soundbar` | r/o property | Device type identification |
| `zone.is_subwoofer` | r/o property | Device type identification |
| `zone.has_subwoofer` | r/o property | Has bonded sub |
| `zone.has_satellites` | r/o property | Has satellite speakers |
| `zone.household_id` | r/o property | Household identifier |
| `zone.available_actions` | r/o property | Currently available transport actions |

**Suggested MCP Tools:**
- `set_status_light(room, enabled)` → LED ring toggle
- `set_buttons_enabled(room, enabled)` → physical buttons toggle
- `get_battery_info(room)` → battery level/health for Move/Roam

**Implementation notes:** `get_battery_info` only works on portable speakers — wrap with a try/except. Status light and buttons are novelty controls; low priority but trivial to add.

---

### Gap Category 11: Soundbar / Home Theatre Settings

**Priority: LOW | Complexity: LOW | AI Value: LOW**

Relevant only for households with Sonos soundbars (Arc, Beam, Ray) and bonded subs/surrounds.

| SoCo API | Type | Description |
|---|---|---|
| `zone.night_mode` | r/w property | Reduce loud transients (soundbars) |
| `zone.dialog_mode` | r/w property | Enhance speech clarity (soundbars) |
| `zone.surround_enabled` | r/w property | Enable/disable surround speakers |
| `zone.sub_enabled` | r/w property | Enable/disable subwoofer |
| `zone.sub_gain` | r/w property | Subwoofer gain level |
| `zone.surround_volume_tv` | r/w property | Surround level in TV mode (-15 to +15) |
| `zone.surround_volume_music` | r/w property | Surround level in music mode |
| `zone.soundbar_audio_input_format` | r/o property | Audio format string (e.g. "Dolby 5.1") |

**Suggested MCP Tools:**
- `get_soundbar_settings(room)` → night mode, dialog, surround, sub state
- `set_night_mode(room, enabled)` → toggle
- `set_dialog_mode(room, enabled)` → toggle
- `set_surround_enabled(room, enabled)` → toggle
- `set_sub_enabled(room, enabled)` → toggle

**Implementation notes:** All guard on `zone.is_soundbar` or `zone.has_subwoofer`. Low priority unless user has home theatre setup.

---

### Gap Category 12: Third-Party Music Service Integration

**Priority: LOW | Complexity: HIGH | AI Value: HIGH (if addressed)**

SoCo provides `MusicService` to interact with streaming services (Spotify, TuneIn, Apple Music, etc.), but this is complex — authentication flows, service-specific search categories, and URI construction all vary per service.

| SoCo API | Type | Description |
|---|---|---|
| `MusicService.get_all_music_services_names()` | static method | List all configured services |
| `MusicService(name).search(category, term)` | method | Search in service |
| `MusicService(name).get_media_uri(item_id)` | method | Get streamable URI |
| `service.sonos_uri_from_id(item_id)` | method | Convert to play_uri-compatible URI |

**Suggested MCP Tools:**
- `list_music_services()` → list configured services
- `search_music_service(service_name, query, category)` → search results
- `play_service_item(room, service_name, item_id)` → play by service item ID

**Implementation notes:** Authentication is handled at the Sonos app level; SoCo inherits credentials from the Sonos system. However, search categories and result schemas differ per service. Recommend implementing TuneIn (radio) first as it is the simplest — no authentication needed and URIs are well-understood. Full multi-service support is a significant feature scope.

---

### Gap Category 13: Event Subscriptions (Real-Time Updates)

**Priority: LOW (architectural) | Complexity: HIGH | AI Value: HIGH (if applicable)**

SoCo's event system provides real-time UPnP push notifications for playback state changes, volume changes, and topology changes. This would enable the MCP server to push updates rather than poll.

| SoCo API | Type | Description |
|---|---|---|
| `service.subscribe(...)` | method | Subscribe to UPnP service events |
| `subscription.renew()` | method | Extend subscription |
| `subscription.unsubscribe()` | method | Cancel subscription |
| `soco.events_asyncio` | module | asyncio-compatible event backend |
| Subscribable services | — | `AVTransport`, `RenderingControl`, `ZoneGroupTopology`, `AlarmClock`, `Queue` |

**Implementation notes:** This is an architectural addition — the MCP server would need an event loop to manage subscriptions and a mechanism to push state to connected clients. The existing asyncio transport (`streamable-http`) could support this pattern. Not recommended as a near-term addition; would require significant architectural work.

---

## Integration Patterns

### How New Tools Should Be Added

The project's adapter pattern makes it straightforward to add new capabilities:

1. **Add method to `SoCoAdapter`** (`src/soniq_mcp/adapters/soco_adapter.py`) — only place that imports SoCo
2. **Add service method** (`src/soniq_mcp/services/`) — validation and orchestration
3. **Create or extend tool module** (`src/soniq_mcp/tools/`) — thin MCP handler
4. **Register tool** in `src/soniq_mcp/tools/__init__.py`
5. **Add custom exception** in `src/soniq_mcp/domain/exceptions.py` if a new error domain

For simple property-based features (play mode, bass, sleep timer), steps 1–4 are all minimal boilerplate.

### Example: Adding Shuffle

```python
# soco_adapter.py
@property
def shuffle(self) -> bool:
    return self._zone.shuffle

@shuffle.setter
def shuffle(self, enabled: bool) -> None:
    self._zone.shuffle = enabled

# services/playmode_service.py
def set_shuffle(self, room: str, enabled: bool) -> None:
    zone = self._get_coordinator(room)
    zone.shuffle = enabled

# tools/playmode.py
@mcp.tool()
def set_shuffle(room: str, enabled: bool) -> dict:
    """Enable or disable shuffle mode for a room."""
    service.set_shuffle(room, enabled)
    return {"status": "ok", "room": room, "shuffle": enabled}
```

---

## Prioritized Recommendations

### Tier 1 — High Value, Low Effort (recommended for next epic)

These 5 feature areas can be implemented with minimal architectural change and deliver immediate AI-assistant value:

| # | Feature Area | Tools Count | SoCo Complexity |
|---|---|---|---|
| 1 | **Play Modes** (shuffle, repeat, crossfade) | 5 | Property r/w — trivial |
| 2 | **Seek** | 1 | Single method call — trivial |
| 3 | **Sleep Timer** | 2 | Two method calls — trivial |
| 4 | **Audio EQ** (bass, treble, loudness) | 4 | Property r/w — trivial |
| 5 | **Input Switching** (line-in, TV) | 3 | Method calls + guards — easy |

**Total: ~15 new tools | Estimated 1 sprint**

---

### Tier 2 — Medium Value, Medium Effort

| # | Feature Area | Tools Count | SoCo Complexity |
|---|---|---|---|
| 6 | **Alarm Management** | 5 | Alarm object model — medium |
| 7 | **Playlist CRUD** | 5 | DIDL object handling — medium |
| 8 | **Group Volume/Mute** | 4 | Group property access — easy |
| 9 | **Local Music Library** | 4–5 | Large result sets, pagination — medium |

**Total: ~19 new tools | Estimated 1–2 sprints**

---

### Tier 3 — Specialist / Complex

| # | Feature Area | Tools Count | SoCo Complexity |
|---|---|---|---|
| 10 | **Speaker Properties** (LED, buttons, battery) | 3 | Trivial but niche |
| 11 | **Soundbar Settings** (night, dialog, surround, sub) | 5 | Device-type guards |
| 12 | **Third-Party Services** (TuneIn radio first) | 3 | High — service-specific auth + schema |
| 13 | **Event Subscriptions** | Architectural | High — new server capability |

---

## Summary

The sonos-mcp-server currently implements **30 MCP tools** covering the essential Sonos control surface. The SoCo library exposes a significantly broader API with approximately **55 properties and 40+ methods** on the core class alone.

**Immediate opportunity (Tier 1):** ~15 tools covering play modes, seek, sleep timer, audio EQ, and input switching — all achievable with simple property/method wrappers, no new architectural patterns needed, and high AI-assistant utility.

**Concrete next step:** Use `bmad-edit-prd` to add Tier 1 features as new functional requirements, then `bmad-create-epics-and-stories` to scope them as Epic 6.

---

## Sources

- [SoCo core module API — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.core.html)
- [SoCo source view — docs.python-soco.com](https://docs.python-soco.com/en/latest/_modules/soco/core.html)
- [SoCo groups module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.groups.html)
- [SoCo discovery module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.discovery.html)
- [SoCo alarms module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.alarms.html)
- [SoCo music_library module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.music_library.html)
- [SoCo music_services module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.music_services.music_service.html)
- [SoCo events module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.events.html)
- [SoCo data_structures module — docs.python-soco.com](https://docs.python-soco.com/en/latest/api/soco.data_structures.html)
- [SoCo GitHub — github.com/SoCo/SoCo](https://github.com/SoCo/SoCo)
- [SoCo PyPI — pypi.org/project/soco](https://pypi.org/project/soco/)
- [TuneIn example — github.com/SoCo/SoCo](https://github.com/SoCo/SoCo/blob/master/examples/commandline/tunein.py)
- sonos-mcp-server codebase — `src/soniq_mcp/` (inspected 2026-04-02)
