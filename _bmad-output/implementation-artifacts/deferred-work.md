# Deferred Work

## Deferred from: code review of 1-1-expose-play-mode-controls-for-active-rooms (2026-04-07)

- Untyped `object` parameters in `PlayModeService.__init__` — pre-existing pattern across all services; define Protocols when type strictness is prioritized
- `_resolve_coordinator` calls `list_rooms()` on every invocation — pre-existing pattern in `SonosService`; consider caching if performance becomes a concern
- `PlayModeResponse` duplicates `PlayModeState` field-for-field without `Literal` or `Enum` constraints — pre-existing pattern across all response schemas; address when schema generation for MCP clients is tightened
- Partial-write atomicity: `zone.play_mode` and `zone.cross_fade` writes are not atomic — no rollback mechanism available in SoCo; accept risk or add retry/re-read
- Contract tests access `app._tool_manager` private API — pre-existing pattern in all contract tests; address when FastMCP exposes a stable public introspection API
- Unexpected exception types in tool handlers not caught by a broad handler — pre-existing 3-exception pattern from `playback.py` template; add `except Exception` catch-all if defensive error handling becomes a project-wide requirement
