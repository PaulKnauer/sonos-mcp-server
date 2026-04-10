# n8n Integration

`n8n` can use SoniqMCP as an MCP-compatible Sonos action layer inside larger automations, routing, and AI-driven workflows.

SoniqMCP does not include `n8n`-specific runtime code or dependencies. The supported pattern is to run SoniqMCP separately and let your `n8n` workflow connect to the MCP endpoint with whatever MCP-compatible node or bridge you manage.

---

## Recommended runtime pattern

For `n8n`, use **Streamable HTTP** so workflows can call a long-running MCP server.

| Setting | Recommended value |
|---|---|
| `SONIQ_MCP_TRANSPORT` | `http` |
| `SONIQ_MCP_EXPOSURE` | `home-network` |
| Endpoint | `http://<host>:8000/mcp` |

This is the cleanest fit for workflow engines, scheduled jobs, and multi-step agent automations.

Today, that usually means Docker on Linux. Helm is still a documented advanced path rather than a turnkey default because the current chart requires a `hostNetwork: true` manual workaround for reliable Sonos discovery.

---

## What SoniqMCP is responsible for

SoniqMCP provides:

- stable Sonos tool names
- predictable request parameters
- safety controls such as tool exposure rules and volume caps
- transport-agnostic semantics across direct clients and automation systems

Your `n8n` workflow remains responsible for:

- orchestration logic
- conditional routing
- memory, scheduling, and retries
- any LLM reasoning you place around the Sonos tool calls

---

## Recommended workflow shape

1. Start with setup verification using `ping` or `server_info`.
2. Resolve or confirm the target room with `list_rooms`.
3. Perform a specific Sonos action such as `play`, `set_volume`, `play_favourite`, `get_queue`, or `party_mode`.
4. Handle failures as normal workflow branches instead of assuming every command succeeds.

This keeps the workflow explicit and avoids brittle glue code.

---

## Representative `n8n` scenarios

- A workflow receives a natural-language intent from an LLM step, maps it to a target room, then calls `play_favourite`.
- A scheduled routine checks whether rooms are already grouped before choosing `join_group` or `party_mode`.
- A recovery branch uses `server_info` and `list_rooms` before retrying a failed playback action.

### Representative Epic 2 workflow

For input and expanded group-audio flows, keep the sequence explicit:

1. Call `ping`.
2. Call `server_info`.
3. Call `list_rooms`.
4. Call `group_rooms` when the workflow needs an exact room set rather than incremental joins.
5. Call `get_group_volume`, `set_group_volume`, `adjust_group_volume`, `group_mute`, or `group_unmute` for group-level audio changes.

If the workflow is switching an active source instead of changing playback or volume, call `switch_to_tv` or `switch_to_line_in`.

`n8n` owns the orchestration and branching. SoniqMCP remains the execution layer only.

---

## Safety and deployment guidance

- Keep SoniqMCP on a trusted home network.
- Prefer Docker on Linux for a long-running remote deployment.
- Use Helm only if the documented `hostNetwork: true` manual workaround fits your environment.
- Avoid documenting or relying on public internet exposure as a normal pattern.
- Keep room targeting explicit in workflow steps so automations remain predictable.
- Respect the configured `SONIQ_MCP_MAX_VOLUME_PCT` limit for every workflow that changes volume.

---

## Troubleshooting checklist

1. Confirm the `n8n` host can reach `http://<host>:8000/mcp`.
2. Confirm SoniqMCP itself can discover Sonos speakers on the same local network.
3. Confirm the workflow is sending MCP tool calls that match the documented tool names and parameters.
4. If the endpoint is reachable but actions fail, verify the target room exists by calling `ping`, `server_info`, and `list_rooms` before mutation.

For general runtime and network setup issues, see [troubleshooting](../setup/troubleshooting.md). It documents the same `configuration`, `connectivity`, `validation`, and `operation` categories your workflow can branch on after a failed tool call.
