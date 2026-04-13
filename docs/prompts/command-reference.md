# Command Reference

Use this page as the canonical command surface for SoniqMCP. It covers the supported `Makefile` targets, direct CLI invocation patterns, and how those commands relate to local `stdio` versus remote `Streamable HTTP` usage.

For natural-language examples, start with [example-uses.md](example-uses.md). For deployment-specific setup, use [../setup/README.md](../setup/README.md) and the linked guides.

## Core developer and operator targets

Run these from the project root:

| Target | What it does | Typical use |
|---|---|---|
| `make install` | Install dependencies with `uv sync` | First-time setup or after dependency changes |
| `make run` | Start the server with the default transport from config | Day-to-day local runs |
| `make run-stdio` | Force local `stdio` transport for the current run | Claude Desktop and same-machine testing |
| `make test` | Run the full test suite | General verification |
| `make check` | Compile-check Python source and tests | Fast syntax sanity check |
| `make lint` | Run `ruff check` and `ruff format --check` | Lint and formatting verification |
| `make format` | Apply formatter changes and lint auto-fixes | Local cleanup before re-running checks |
| `make type-check` | Run `mypy` on `src` | Static type verification |
| `make coverage` | Run tests with coverage output | Coverage-oriented validation |
| `make audit` | Run dependency vulnerability scan | Dependency hygiene |
| `make ci` | Run lint, type-check, coverage, audit, and build-check | Full local quality gate before review |
| `make release-version` | Print the current package version from `pyproject.toml` | Release prep and version checks |
| `make release-bump-patch` | Increment the patch version in `pyproject.toml` | Backward-compatible bug-fix release prep |
| `make release-bump-minor` | Increment the minor version in `pyproject.toml` | Backward-compatible feature release prep |
| `make release-bump-major` | Increment the major version in `pyproject.toml` | Breaking-change release prep |
| `make release-tag` | Create annotated git tag `vX.Y.Z` from the current version | Release cut after the version bump is committed |
| `make release-gh` | Create a GitHub Release with generated notes via `gh` | Manual GitHub Release bootstrap or recovery |
| `make docker-build` | Build the Docker image | Prepare a remote HTTP deployment artifact |
| `make docker-run` | Run the HTTP server in Docker on port `8000` | Linux home-lab validation |
| `make docker-compose-up` | Build and start the Compose stack in detached mode | Compose-based remote setup |
| `make docker-compose-down` | Stop the Compose stack | Compose teardown |
| `make helm-lint` | Validate the Helm chart | Helm chart review |
| `make helm-template` | Render Helm manifests locally | Inspect the generated Kubernetes manifests |
| `make helm-install` | Install or upgrade the Helm release | Deploy to k3s / Kubernetes |
| `make tree` | Print the project directory tree | Orientation and documentation work |

## Choosing the right command path

### Local `stdio`

Use local `stdio` when the MCP client runs on the same machine as SoniqMCP.

```bash
make install
cp .env.example .env
make run-stdio
```

Use that manual start path for same-machine testing with MCP clients that expect you to launch the server yourself.

For Claude Desktop local integration, do not pre-start `make run-stdio`. Claude Desktop launches the server as its own subprocess using the config flow in [../integrations/claude-desktop.md](../integrations/claude-desktop.md) and the setup details in [../setup/stdio.md](../setup/stdio.md).

### Remote `Streamable HTTP`

Use a remote HTTP deployment when another machine, automation system, or remote MCP consumer needs to reach the server at `http://<host>:8000/mcp`.

- Docker: [../setup/docker.md](../setup/docker.md)
- Helm / k3s: [../setup/helm.md](../setup/helm.md)
- Integrations and agent-mediated usage: [../integrations/README.md](../integrations/README.md)

These remote paths remain subject to the documented caveats around Linux host networking, Sonos SSDP discovery, and Helm `hostNetwork` requirements.

## Direct CLI invocation

Use these when you want to bypass `make` and launch the server directly.

```bash
# Start with the configured transport
uv run python -m soniq_mcp

# Force stdio for the current session
SONIQ_MCP_TRANSPORT=stdio uv run python -m soniq_mcp

# Override log level for a session
SONIQ_MCP_LOG_LEVEL=DEBUG uv run python -m soniq_mcp

# Override volume cap for a session
SONIQ_MCP_MAX_VOLUME_PCT=50 uv run python -m soniq_mcp

# Disable a tool for a session
SONIQ_MCP_TOOLS_DISABLED=ping uv run python -m soniq_mcp

# Use the installed entry point after `make install`
.venv/bin/soniq-mcp
```

## Phase-2 capability families

These tool families are part of the supported MCP contract. They keep the same business semantics across local `stdio`, remote `Streamable HTTP`, direct AI clients, and agent-mediated workflows. Transport changes setup and envelope details, not what the tools mean.

If a tool from one of these families is missing, check `SONIQ_MCP_TOOLS_DISABLED` and the diagnostics guidance in [../setup/troubleshooting.md](../setup/troubleshooting.md) before assuming the docs or transport are wrong.

When you are adopting a new capability family, start with `ping`, `server_info`, and `list_rooms`, then move to the family-specific tools below. Use [example-uses.md](example-uses.md) for end-to-end prompt flows and [../setup/troubleshooting.md](../setup/troubleshooting.md) if discovery or setup does not match what you expect.

### Playback modes, seek, and sleep timer

| Tool | Typical use | Notes |
|---|---|---|
| `get_play_mode` | Inspect shuffle, repeat, and `cross_fade` state | Read-only state check before mutation |
| `set_play_mode` | Update shuffle, repeat, or `cross_fade` | Keeps playback semantics transport-neutral |
| `seek` | Jump within the current track | Uses `HH:MM:SS` position input |
| `get_sleep_timer` | Read active timer state | Useful before changing an existing timer |
| `set_sleep_timer` | Set or clear the sleep timer | Use `0` minutes to clear |

### Room EQ, inputs, and group audio

| Tool | Typical use | Notes |
|---|---|---|
| `get_eq_settings` | Inspect bass, treble, and loudness | Read room-level audio state before tuning |
| `set_bass` | Adjust bass for one room | Room-level control |
| `set_treble` | Adjust treble for one room | Room-level control |
| `set_loudness` | Toggle loudness for one room | Room-level control |
| `switch_to_line_in` | Move a supported room to line-in | Input-specific control, not playback transport |
| `switch_to_tv` | Move a supported room to TV input | Input-specific control, not playback transport |
| `get_group_volume` | Inspect synced-group volume and mute state | Group-level control |
| `set_group_volume` | Set synced-group volume | Safety cap still applies |
| `adjust_group_volume` | Change synced-group volume relatively | Safety cap still applies |
| `group_mute` | Mute a synced group | Group-level control |
| `group_unmute` | Unmute a synced group | Group-level control |

### Group topology

| Tool | Typical use | Notes |
|---|---|---|
| `get_group_topology` | Inspect the current coordinator/member layout | Read-only topology check before regrouping |
| `join_group` | Add one room to an existing coordinator | Incremental grouping |
| `unjoin_room` | Remove one room from its current group | Returns the room to standalone playback |
| `party_mode` | Join all rooms into one whole-home group | Whole-home shortcut |
| `group_rooms` | Build an explicit room set with an optional coordinator | Preferred when the caller knows the exact target set |

## Alarm and playlist lifecycle surface

These lifecycle tools are part of the supported MCP contract and are transport-neutral across local `stdio` and remote `Streamable HTTP`.

### Alarm tools

| Tool | Required parameters | Notes |
|---|---|---|
| `list_alarms` | none | Returns normalized alarm records with `alarm_id` values. |
| `create_alarm` | `room`, `start_time`, `recurrence` | Optional fields: `enabled`, `volume`, `include_linked_zones`. |
| `update_alarm` | `alarm_id`, `room`, `start_time`, `recurrence`, `enabled` | Optional fields: `volume`, `include_linked_zones`. |
| `delete_alarm` | `alarm_id` | Destructive operation; returns delete confirmation. |

Alarm lifecycle operations target alarms by `alarm_id`. Use `list_alarms` first when the caller needs to discover or confirm the current identifiers.

### Playlist tools

| Tool | Required parameters | Notes |
|---|---|---|
| `list_playlists` | none | Returns normalized playlist records with both playback `uri` and lifecycle `item_id`. |
| `play_playlist` | `room`, `uri` | Playback operation only; starts a saved playlist by `uri`. |
| `create_playlist` | `title` | Creates an empty saved playlist and returns its normalized record. |
| `update_playlist` | `playlist_id`, `room` | Replaces the saved playlist contents with the current queue from the named room. |
| `delete_playlist` | `playlist_id` | Destructive operation; returns delete confirmation. |

Playlist playback and playlist management intentionally use different identifiers:

- `play_playlist` uses the playlist `uri`
- `create_playlist`, `update_playlist`, and `delete_playlist` use the playlist `item_id` returned by `list_playlists`
- `rename_playlist` is not part of the supported MCP surface

For natural-language examples of these flows, use [example-uses.md](example-uses.md).

## Local music library surface

These library tools are part of the supported MCP contract and are transport-neutral across local `stdio`, remote `Streamable HTTP`, direct AI clients, and agent-mediated workflows.

### Library tools

| Tool | Required parameters | Notes |
|---|---|---|
| `browse_library` | `category` | Read-only browse tool. Optional fields: `start`, `limit`, `parent_id`. Returns a bounded result set with pagination metadata. |
| `play_library_item` | `room`, `title`, `uri`, `is_playable` | Control tool. Optional field: `item_id`. Plays a normalized playable selection returned by `browse_library`. |

Library browsing and playback intentionally use different interaction phases:

- `browse_library` returns normalized items with fields such as `title`, `item_type`, `item_id`, `uri`, `is_browsable`, and `is_playable`
- `play_library_item` should be called only with a normalized playable selection
- if a result is browse-only, browse deeper instead of guessing playback behavior
- transport differences should stay limited to setup and envelope details, not to business semantics

## Related guides

- [Example prompts and usage flows](example-uses.md)
- [Setup overview](../setup/README.md)
- [Troubleshooting](../setup/troubleshooting.md)
- [Claude Desktop integration](../integrations/claude-desktop.md)
