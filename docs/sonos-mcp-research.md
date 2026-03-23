# PRD: Python Sonos MCP Server

**Project:** `sonos-mcp-python`
**Status:** Discovery / Pre-build
**Owner:** Paul
**Last Updated:** 2026-03-23
**Reference:** BMAD PRD v1

---

## 1. Problem Statement

No production-ready, Python-native, remotely-deployable MCP server exists for controlling Sonos audio systems. The current landscape consists of three niche community projects (all under 10 GitHub stars), none of which supports containerized or Kubernetes deployment, streamable HTTP transport, or PyPI distribution. The Python/SoCo niche specifically has a single abandoned MVP with 9 commits and no active maintenance.

This project fills that gap: a well-engineered, deployable Python MCP server that exposes the full richness of the SoCo library as MCP tools — suitable for use with Claude, n8n agents, and other MCP-compatible AI clients.

---

## 2. Goals

- Build a Python-native Sonos MCP server using **SoCo** and **Anthropic's official MCP Python SDK (FastMCP)**
- Support both `stdio` (local/dev) and **SSE/Streamable HTTP** (remote/production) transports
- Deploy cleanly to **k3s / Kubernetes** via Docker + Helm
- Expose a comprehensive, well-documented set of MCP tools covering all major Sonos capabilities
- Publish to **PyPI** as a proper installable package
- Be the reference Python implementation where none currently exists

### Non-Goals (v1)

- Full music service OAuth integration (Spotify, Apple Music, Tidal) — Phase 2
- GUI or web dashboard
- Multi-household Sonos support (single household v1)

---

## 3. Background & Research Summary

### 3.1 Existing Sonos MCP Servers

Three dedicated Sonos MCP servers exist publicly as of March 2026:

| Project | Language | Library | Stars | Commits | Native SSE | PyPI | Docker |
|---|---|---|---|---|---|---|---|
| `Tommertom/sonos-ts-mcp` | TypeScript | Custom UPnP/SOAP | 8 | 63 | ✅ | npm | ❌ |
| `WinstonFassett/sonos-mcp-server` | Python | SoCo | 5 | 9 | ❌ (supergateway) | ❌ | ❌ |
| `sebsto/MusicAgentKit` | Swift 6 | node-sonos-http-api | 6 | 61 | ❌ | ❌ | ❌ |

**Key findings:**
- No server uses **SoCo-CLI** in any form
- No server is published on **PyPI**
- No server ships a **Docker image or Helm chart**
- No server implements **streamable HTTP** (newer MCP spec)
- No server appears in any official MCP registry or `awesome-mcp-servers` list
- The only Python server (`WinstonFassett`) is effectively abandoned — last meaningful activity ~7+ months ago

### 3.2 Why Build vs. Adopt

The TypeScript `sonos-ts-mcp` is the technical leader (50+ tools, event subscriptions, native SSE) but requires a Node.js runtime and is not remotely deployable. For a Python/k3s/AI-agent use case, **no viable alternative exists**. Building from scratch is the only path to:

- Python-native integration with the broader n8n / Bedrock / Weaviate stack
- Proper containerized deployment
- Streamable HTTP transport for remote MCP clients
- A maintainable, extensible codebase with full SoCo coverage

### 3.3 Sonos Library Selection

| Library | Language | Verdict |
|---|---|---|
| **SoCo** | Python | ✅ Primary — mature, comprehensive, 2k+ stars |
| **SoCo-CLI** | Python (CLI wrapper) | ✅ Secondary — consider wrapping its HTTP API as a sidecar for advanced CLI features |
| `node-sonos-ts` | TypeScript | ❌ Wrong language |
| `node-sonos` | JavaScript | ❌ Wrong language |
| `ByteDev.Sonos` | .NET | ❌ Wrong language |

---

## 4. Technical Architecture

```
AI Tool / Claude / n8n Agent
          │
          ▼ (MCP via SSE or Streamable HTTP)
┌─────────────────────────────┐
│   sonos-mcp-python server   │
│   FastMCP + Python 3.12     │
│   Deployed in k3s pod       │
└─────────────────────────────┘
          │
          ▼ (LAN / hostNetwork or speaker VLAN bridge)
┌─────────────────────────────┐
│   SoCo Library              │
│   UPnP/SSDP discovery       │
│   SOAP control              │
└─────────────────────────────┘
          │
          ▼
  Sonos Speakers (local network)
```

### 4.1 Key Technology Decisions

| Concern | Decision | Rationale |
|---|---|---|
| MCP framework | `FastMCP` (official Anthropic Python SDK) | Minimal boilerplate, decorator-based tools, official support |
| Sonos control | `SoCo` library | Most mature Python option, broad protocol coverage |
| Transport (dev) | `stdio` | Fast local iteration, zero config |
| Transport (prod) | SSE / Streamable HTTP | Required for k3s remote deployment |
| Speaker discovery | Static IP config (v1) | SSDP multicast doesn't cross k8s network boundaries reliably |
| Container runtime | Docker → k3s | Matches existing Rancher Desktop / Helm pipeline |
| Auth | Traefik middleware / network policy (v1) | Layer security at the ingress, not in the app |

### 4.2 Network Topology Note

SoCo uses **SSDP (UDP multicast)** for auto-discovery, which doesn't traverse Kubernetes network boundaries. Two options:

- **Option A (v1 — recommended):** Configure speaker IPs via environment variables, skip SSDP
- **Option B (v2):** Run the pod with `hostNetwork: true` to allow multicast on the LAN

---

## 5. MCP Tool Inventory (Target)

### Core Playback
- `play(room)` — Resume playback
- `pause(room)` — Pause playback
- `stop(room)` — Stop playback
- `next_track(room)` — Skip forward
- `previous_track(room)` — Skip back
- `get_current_track(room)` — Now playing info (title, artist, album, art)
- `get_playback_state(room)` — Playing / paused / stopped / transitioning

### Volume & Audio
- `get_volume(room)` — Get current volume
- `set_volume(room, level)` — Set volume (0–100)
- `adjust_volume(room, delta)` — Relative volume change
- `mute(room)` / `unmute(room)` / `get_mute(room)`
- `set_bass(room, level)` / `set_treble(room, level)`

### Queue Management
- `get_queue(room)` — List queue items
- `clear_queue(room)`
- `add_uri_to_queue(room, uri)` — Add a URI (stream, file, TuneIn)
- `play_from_queue(room, position)`
- `remove_from_queue(room, position)`

### Room & Group Management
- `list_rooms()` — All available rooms/zones
- `list_groups()` — Current group topology
- `join_group(room, coordinator)` — Add room to group
- `unjoin(room)` — Remove room from group
- `party_mode()` — Join all rooms
- `set_play_mode(room, mode)` — Normal / repeat / shuffle etc.

### Favourites & Radio
- `get_favourites()` — List Sonos favourites
- `play_favourite(room, name)` — Play a saved favourite
- `get_sonos_playlists()` — List Sonos playlists
- `play_playlist(room, name)`

### System
- `get_system_info()` — All speakers, firmware, IP addresses
- `get_sleep_timer(room)` / `set_sleep_timer(room, minutes)`
- `get_alarms()` / `create_alarm(...)` / `delete_alarm(id)`
- `reboot_speaker(room)`

### Advanced (v1.5+)
- `subscribe_to_events(room)` — UPnP GENA event subscription
- `play_tts(room, text, language)` — Text-to-speech notification
- `play_local_file(room, path)` — Play audio file from filesystem
- `snapshot(room)` / `restore_snapshot(room)` — Save/restore playback state

---

## 6. Deployment Plan

### Phase 1 — Local Development
```bash
# Install
pip install sonos-mcp-python  # (target PyPI name)

# Run via stdio (Claude Desktop / Cursor)
sonos-mcp --transport stdio --speakers "Kitchen=192.168.1.101,Lounge=192.168.1.102"
```

### Phase 2 — k3s Deployment
```yaml
# values.yaml (Helm)
sonosMcp:
  transport: sse
  port: 3000
  speakers:
    Kitchen: "192.168.1.101"
    Lounge: "192.168.1.102"
  hostNetwork: false  # set true if SSDP discovery needed
```

```
Traefik Ingress → Service → Deployment (sonos-mcp-python pod)
                                    │
                              hostNetwork or speaker VLAN route
```

### Phase 3 — Streamable HTTP + Auth
- Migrate to streamable HTTP transport (newer MCP spec)
- Add Traefik middleware for API key or OAuth token validation
- Consider mTLS for internal cluster communication

---

## 7. Project Structure (Target)

```
sonos-mcp-python/
├── src/
│   └── sonos_mcp/
│       ├── __init__.py
│       ├── server.py          # FastMCP app + tool registration
│       ├── tools/
│       │   ├── playback.py
│       │   ├── volume.py
│       │   ├── queue.py
│       │   ├── groups.py
│       │   ├── favourites.py
│       │   └── system.py
│       ├── sonos_client.py    # SoCo wrapper / connection manager
│       └── config.py          # Env var config (speaker IPs, transport)
├── tests/
├── helm/
│   └── sonos-mcp/             # Helm chart for k3s
├── Dockerfile
├── pyproject.toml
└── README.md
```

---

## 8. Competitive Differentiation

| Capability | sonos-ts-mcp | sonos-mcp-server (Python) | **This project** |
|---|---|---|---|
| Language | TypeScript | Python | **Python** |
| Tool depth | 50+ | ~15 | **50+ (target)** |
| PyPI package | npm only | ❌ | **✅** |
| Docker image | ❌ | ❌ | **✅** |
| Helm chart | ❌ | ❌ | **✅** |
| Native SSE | ✅ | ❌ | **✅** |
| Streamable HTTP | ❌ | ❌ | **✅ (v2)** |
| Static IP config | ❌ | ❌ | **✅** |
| TTS support | ❌ | ❌ | **✅ (v1.5)** |
| SoCo-CLI integration | ❌ | ❌ | **✅ (v2)** |
| Maintained | Active | Abandoned | **Active** |

---

## 9. Success Criteria

**v1.0 (MVP)**
- [ ] All core playback, volume, queue, and room tools working
- [ ] Runs via `stdio` and `SSE` transports
- [ ] Deployable to k3s via Docker + Helm chart
- [ ] Static IP speaker configuration via env vars
- [ ] Published on PyPI
- [ ] README with Claude Desktop and k3s setup guides

**v1.5**
- [ ] Favourites and playlists tools
- [ ] TTS notification support
- [ ] Snapshot/restore
- [ ] Alarm management

**v2.0**
- [ ] Streamable HTTP transport
- [ ] SoCo-CLI HTTP API sidecar integration
- [ ] SSDP discovery option (`hostNetwork` mode)
- [ ] Auth middleware (API key / OAuth)
- [ ] Music service search (Spotify etc.) — where SoCo supports it

---

## 10. References

- [SoCo GitHub](https://github.com/SoCo/SoCo) — Primary Sonos Python library
- [SoCo-CLI GitHub](https://github.com/avantrec/soco-cli) — CLI wrapper for SoCo
- [MCP Python SDK (FastMCP)](https://pypi.org/project/mcp/) — Anthropic's official MCP SDK
- [sonos-ts-mcp](https://github.com/Tommertom/sonos-ts-mcp) — TypeScript reference implementation (feature benchmark)
- [WinstonFassett/sonos-mcp-server](https://github.com/WinstonFassett/sonos-mcp-server) — Existing Python/SoCo MVP
- [MCP Specification](https://modelcontextprotocol.io) — Protocol reference
- [node-sonos-ts](https://github.com/svrooij/node-sonos-ts) — TypeScript Sonos library (reference)
