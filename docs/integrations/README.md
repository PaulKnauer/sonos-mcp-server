# Integrations

SoniqMCP implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) and works with any MCP-compatible client.

---

## Available integration guides

- [Claude Desktop](claude-desktop.md) — Connect Claude Desktop using local stdio or remote HTTP transport
- [Home Assistant](home-assistant.md) — Use SoniqMCP as a remote MCP action layer for home automations and assistants
- [n8n](n8n.md) — Use SoniqMCP from automation workflows that need stable Sonos control tools

---

## Integration principles

All supported integrations use the same MCP tool surface:

- local same-machine clients should prefer `stdio`
- remote agents and automation systems should usually consume the `Streamable HTTP` endpoint at `http://<host>:8000/mcp`
- vendor-specific setup belongs in client configuration and workflow examples, not in SoniqMCP runtime code
- capability families such as `browse_library` and `play_library_item` should keep the same request and response semantics across direct and agent-mediated use

SoniqMCP is the Sonos control layer. It does not embed Home Assistant logic, `n8n` workflow semantics, or agent reasoning. That separation is intentional and keeps the tool semantics stable across direct and agent-mediated use.

Start with `ping`, `server_info`, and `list_rooms` before mutation in any integration. For the canonical named tool surface, use [../prompts/command-reference.md](../prompts/command-reference.md). For scenario-driven flows covering play modes, seek and sleep timer, room EQ, inputs, group audio, alarms, playlists, and library browsing, use [../prompts/example-uses.md](../prompts/example-uses.md). For setup recovery, use [../setup/troubleshooting.md](../setup/troubleshooting.md).
