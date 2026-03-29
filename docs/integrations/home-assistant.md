# Home Assistant Integration

Home Assistant can use SoniqMCP as an MCP-compatible Sonos control layer when you want a separate assistant, workflow, or automation to call the same tool surface that direct AI clients use.

SoniqMCP does not ship a Home Assistant integration component or custom Home Assistant dependency. The supported pattern is to run SoniqMCP as a separate MCP server and connect to it from whatever Home Assistant MCP-compatible workflow or bridge you manage.

---

## Recommended runtime pattern

For Home Assistant and other long-running home automations, use **Streamable HTTP** rather than local `stdio`.

| Setting | Recommended value |
|---|---|
| `SONIQ_MCP_TRANSPORT` | `http` |
| `SONIQ_MCP_EXPOSURE` | `home-network` |
| Endpoint | `http://<host>:8000/mcp` |

This keeps SoniqMCP running independently as a service while Home Assistant or a companion automation layer connects over the network.

---

## When to use this pattern

Use the Home Assistant pattern when:

- Home Assistant runs on a different machine than the MCP client or agent
- you want long-running automations to call Sonos tools without launching a subprocess
- you want the same tool semantics available to both conversational assistants and automations

If everything runs on one workstation and the client can launch subprocesses directly, local `stdio` is usually simpler.

---

## Deployment options

Choose one of the documented remote deployment paths:

1. Docker on Linux, where host networking can reach Sonos discovery traffic reliably
2. Helm on k3s or Kubernetes only if you are willing to apply the documented `hostNetwork: true` manual workaround

For deployment details, see [Docker setup](../setup/docker.md) and [Helm setup](../setup/helm.md).

Docker on Linux is the cleaner remote option today. The current Helm chart still requires a `hostNetwork: true` manual workaround for reliable Sonos discovery, so treat Helm as an advanced self-hosted path rather than a turnkey default.

The MCP endpoint for both remote patterns is:

```text
http://<host>:8000/mcp
```

Replace `<host>` with the hostname or IP address of the machine running SoniqMCP.

---

## Safety and exposure guidance

- Keep SoniqMCP on a trusted local or home network.
- Do not treat public internet exposure as a default or recommended setup.
- Keep explicit room targeting in your automations whenever possible.
- Respect `SONIQ_MCP_MAX_VOLUME_PCT` so downstream automations cannot exceed the configured volume cap.

SoniqMCP is designed for home-use trust boundaries, not as a publicly exposed Sonos control API.

---

## What stays stable across integrations

Home Assistant should consume the same tool model used by direct AI clients:

- the same tool names
- the same request parameters
- the same safety boundaries
- the same room, queue, grouping, favourites, and playback semantics

No Home Assistant-specific implementation path is required inside SoniqMCP.

---

## Representative use cases

- A Home Assistant assistant decides which room should play a saved favourite and calls `play_favourite`.
- A home routine checks `get_group_topology` before calling `join_group` for evening whole-home playback.
- A voice or automation flow checks `list_rooms` and `server_info` before issuing playback commands to verify the server is reachable and the environment is correct.

---

## Troubleshooting checklist

1. Confirm SoniqMCP is reachable at `http://<host>:8000/mcp`.
2. Confirm the machine or pod running SoniqMCP can discover Sonos speakers on the local network.
3. Confirm the automation uses supported MCP request shapes rather than vendor-specific assumptions about Sonos internals.
4. If a control action fails, use the setup and diagnostics tools first:
   `ping`, `server_info`, and `list_rooms`.

For general transport and discovery problems, see [troubleshooting](../setup/troubleshooting.md). The same guide also explains the shared `configuration`, `connectivity`, `validation`, and `operation` error categories returned by SoniqMCP tools.
