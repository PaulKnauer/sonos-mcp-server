---
title: 'Claude Code Implementation Brief — SoniqMCP Voice/Search/Events Primitives'
date: '2026-10-18'
author: 'Paul'
audience: 'claude-code'
repo: 'sonos-mcp-server'
related: '_bmad-output/planning-artifacts/brief-hermes-integration.md'
---

# Claude Code Implementation Brief

You are implementing new SoCo-backed capabilities in the `sonos-mcp-server` repo (package `soniq_mcp`, SoCo 0.30.14). Read `CLAUDE.md` and `AGENTS.md` first, then the existing code you are extending. Follow the repo's established layered pattern exactly. Do not rearchitect anything.

## Mission

Add the missing SoCo primitives so the MCP server can (1) snapshot and restore playback non-destructively, (2) play an arbitrary URI (the TTS/announcement path), (3) search music services, and (4) expose a bundle of small high-value controls. Event subscription is a separate, later effort — do NOT attempt it in this run.

## Non-Negotiables (follow exactly)

- **Layered pattern:** every capability is adapter → service → tool → register. SoCo is imported ONLY inside `src/soniq_mcp/adapters/`. Services and tools receive domain objects, never SoCo objects.
- **Tool modules** expose a `register(app: FastMCP, config: SoniqConfig, service) -> None` function; each tool is a closure decorated with `@app.tool(...)`, guarded by `if "<tool_name>" not in config.tools_disabled:` and `assert_tool_permitted("<tool_name>", config)`; uses `ToolAnnotations` (read-only vs control hints); catches domain exceptions and returns `ErrorResponse.from_*(...).model_dump()`; returns `*Response.from_domain(...).model_dump()` for data. Mirror `src/soniq_mcp/tools/playback.py`.
- **Wiring:** register new services/tools in `src/soniq_mcp/tools/__init__.py::register_all`, mirroring existing lines (construct service with `(room_service, adapter)` or `(sonos_service=...)`, then call its `register`).
- **Domain:** new models in `src/soniq_mcp/domain/models.py`; new exceptions in `src/soniq_mcp/domain/exceptions.py` inheriting `SoniqDomainError` with an `error_category`; new response schemas in `src/soniq_mcp/schemas/responses.py`; new error factories in `src/soniq_mcp/schemas/errors.py`.
- **Tests:** unit tests with fake adapters in `tests/unit/adapters/` and `tests/unit/services/`, matching existing test style. No real Sonos hardware is required.
- **Quality gate (all must pass):** `uv run ruff check src tests`, `uv run mypy src`, `uv run pytest --cov --cov-report=term-missing`.
- **Volume safety:** any path that changes volume must still respect `config.max_volume_pct` (reuse the existing `VolumeCapExceeded` / volume-service guard). Do not bypass it.
- Do not modify the PRD, epics, or existing brief; only code, tests, and the README tool table + a new integration doc.

## Work Items

### 1. Snapshot / Restore

- **SoCo API:** `soco.snapshot.Snapshot(device, snapshot_queue=False)` with `.snapshot()`, `.restore(fade=False)`, and context-manager support. `device` is a `soco.SoCo(ip)` instance (mirror `_make_zone` in `soco_adapter.py`).
- **Adapter:** new `src/soniq_mcp/adapters/snapshot_adapter.py` with `capture(ip, include_queue) -> dict` and `restore(ip, state: dict, fade: bool) -> None`. Serialize the captured state to a plain dict (transport, volume, play mode, and queue only when `include_queue`), and rebuild a Snapshot-style restore from it. Keep SoCo here.
- **Domain:** `SnapshotToken` (or `SnapshotState`) dataclass; `SnapshotError(SoniqDomainError)`.
- **Service:** `src/soniq_mcp/services/snapshot_service.py` holding an in-memory registry (dict) so a token can be restored in a later call. Token must be opaque and keyed by room. Document that tokens do not survive a server restart (acceptable for v1).
- **Tools:** `src/soniq_mcp/tools/snapshot.py` — `snapshot(room, include_queue=False) -> {snapshot_id, room}` and `restore_snapshot(room, snapshot_id, fade=False) -> {status}`. `include_queue` defaults false; only restore the queue if it was captured.
- **Semantics:** restore must not skip an already-stopped room into playing. Fade volume restore via `fade` to avoid a jump.

### 2. Generic URI Playback

- **SoCo API:** `zone.play_uri(uri, meta='', title='', start=True, force_radio=False)`.
- **Adapter:** add `play_uri(ip, uri, meta, title, force_radio)` to `SoCoAdapter` (`soco_adapter.py`).
- **Service + tool:** add `play_uri(room, uri, meta="", title="", force_radio=False)` to `PlaybackService` and `tools/playback.py` (or a small dedicated module). This is the exact primitive Hermes needs to play a served TTS audio URL. Docstring must note: single HTTP audio URLs are treated by Sonos as radio streams — for one-shot announcements, pair with `snapshot`/`restore_snapshot`; do not assume the stream ends on its own.

### 3. Music-Service Search

- **SoCo API:** `soco.music_services.MusicService` — `get_all_music_services_names()`, `get_data_for_name(name)`, `search(category, term, index=0, count=100)`, `get_media_uri(item_id)`, `get_media_metadata(item_id)`, `available_search_categories()`, `sonos_uri_from_id(item_id)`. Also `soco.music_services.accounts.Account.get_accounts(soco=...)` for linked accounts.
- **Adapter:** new `src/soniq_mcp/adapters/music_service_adapter.py`. Extract DIDL URIs via `.get_uri()` / `.resources[0].uri` — NEVER `.uri` (this has already caused a bug in this repo).
- **Domain:** `MusicServiceRecord`, `MusicServiceSearchResult`, `MusicServiceAccount` dataclasses; `MusicServiceError(SoniqDomainError)`.
- **Service:** `src/soniq_mcp/services/music_service_service.py`.
- **Tools:** `src/soniq_mcp/tools/music_services.py` — `list_music_services()`, `search_music_service(service_name, category, term, count=100)`, `play_music_service_item(room, service_name, item_id)`. `play_music_service_item` resolves `get_media_uri` (or `sonos_uri_from_id`) then queues/plays via the existing queue path.
- **Constraints:** no OAuth in scope — authentication is inherited from the household's linked accounts. A service with no linked account must return a clear "not configured" error, not a raw SOAP failure. `search` category names come from `available_search_categories()`.

### 4. Small High-Value Gaps (bundle)

All are thin adapter wraps. Add each to `SoCoAdapter` (or the appropriate adapter), a service method, a tool, and a unit test.

- `get_battery_info(room)` — `zone.get_battery_info()` (portable speakers only; return a typed "unsupported" result for non-portable rooms — mirror the input-capability-guard style, no crash).
- `list_radio_favourites(room)` / `play_radio_favourite(room, uri)` — `zone.get_favorite_radio_stations()` / `zone.get_favorite_radio_shows()` (TuneIn).
- `add_to_queue(room, uri, as_next=False)` — extend the existing adapter to pass `as_next` through to `zone.add_uri_to_queue(uri, as_next=...)`; also add `add_multiple_to_queue(room, uris)` via `zone.add_multiple_to_queue(...)`.
- `save_queue_as_playlist(room, title)` — `zone.create_sonos_playlist_from_queue(title)`.
- `remove_from_playlist` / `reorder_playlist` — `zone.remove_from_sonos_playlist(playlist, track, update_id=0)` / `zone.reorder_sonos_playlist(...)` / `zone.move_in_sonos_playlist(...)`. Playlist rename stays unsupported (SoCo has no rename).
- `set_status_light(room, enabled)` — `zone.status_light`.
- `ramp_volume(room, target, ramp_type="SLEEP_TIMER_RAMP_TYPE")` — `zone.ramp_to_volume(...)`.
- `create_stereo_pair(room, slave_room)` / `separate_stereo_pair(room)` — `zone.create_stereo_pair(...)` / `zone.separate_stereo_pair()`.

### 5. Event Subscription — DO NOT implement in this run

`soco.events` / `soco.events_asyncio` (`EventListener`, `Subscription.subscribe/renew/unsubscribe`) plus `zonegroupstate.ZoneGroupState.poll()` is a separate architectural effort requiring an inbound port for Sonos NOTIFY callbacks. Leave it. Do not stub it.

## Definition of Done

- Every new tool is unit-tested with a fake adapter (no hardware).
- `uv run ruff check src tests`, `uv run mypy src`, and `uv run pytest --cov` all pass.
- README tool table updated with the new tools.
- New `docs/integrations/hermes.md` documenting the snapshot → TTS → restore recipe (Hermes generates audio, serves over LAN HTTP with a correct audio `Content-Type` like `audio/mpeg`, calls `snapshot` → `play_uri(url)` → `restore_snapshot`).
- No changes outside code, tests, README, and docs.

## Pitfalls (do not repeat these)

- **DIDL objects expose `.get_uri()` / `.resources[0].uri`, never `.uri`.** Applies to favourites, playlists, and music-service results.
- **Snapshot requires a SoCo device, not an IP string** — construct with `soco.SoCo(ip)` inside the adapter.
- **`get_battery_info` is portable-only** — guard it; non-portable rooms must not raise.
- **`play_uri` on HTTP audio = radio stream** — snapshot/restore is mandatory for one-shot announcements.
- **Volume cap** — `MAX_VOLUME_PCT` must apply to any new volume path (ramp, announcements).
- **`host.docker.internal` is macOS-only** — on Linux/k3s use the LAN IP (existing project knowledge).
- **Keep SoCo imports inside `adapters/`** — services/tools must not import `soco`.

## How Paul will run you

```bash
cd /home/ubuntu/github/sonos-mcp-server
claude -p "Implement the brief at _bmad-output/planning-artifacts/brief-claude-implementation.md" \
  --allowedTools "Read,Edit,Write,Bash" --dangerously-skip-permissions --max-turns 50
```

Work in the order given: snapshot → play_uri → music services → small gaps. Commit logical units with clear messages as you go, and run the quality gate before reporting done.
