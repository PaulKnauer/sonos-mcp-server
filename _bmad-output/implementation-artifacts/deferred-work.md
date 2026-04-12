# Deferred Work

## Deferred from: Epic 3 scope correction (2026-04-12)

- Story 3.5 `Investigate supported Sonos playlist rename capability` — deferred out of active Phase 2 scope after verifying the current supported `SoCo` stack does not expose a clean first-class playlist rename path; revisit only if a newer supported `SoCo` release or alternate Sonos integration path can preserve the current `tools -> services -> adapters` architecture without workaround state

## Deferred from: code review of 1-1-expose-play-mode-controls-for-active-rooms (2026-04-07)

- Untyped `object` parameters in `PlayModeService.__init__` — pre-existing pattern across all services; define Protocols when type strictness is prioritized
- `_resolve_coordinator` calls `list_rooms()` on every invocation — pre-existing pattern in `SonosService`; consider caching if performance becomes a concern
- `PlayModeResponse` duplicates `PlayModeState` field-for-field without `Literal` or `Enum` constraints — pre-existing pattern across all response schemas; address when schema generation for MCP clients is tightened
- Partial-write atomicity: `zone.play_mode` and `zone.cross_fade` writes are not atomic — no rollback mechanism available in SoCo; accept risk or add retry/re-read
- Contract tests access `app._tool_manager` private API — pre-existing pattern in all contract tests; address when FastMCP exposes a stable public introspection API
- Unexpected exception types in tool handlers not caught by a broad handler — pre-existing 3-exception pattern from `playback.py` template; add `except Exception` catch-all if defensive error handling becomes a project-wide requirement

## Deferred from: code review of 2-1-support-capability-aware-input-switching (2026-04-09)

- Full network discovery on every capability check (`room_service.py::get_speakers_for_room`) — pre-existing no-caching architecture; address when caching or topology snapshots are introduced
- Invisible speakers matched by `room_name` fallback in `get_speakers_for_room` — OR condition is likely intentional for bonded satellites/subs with `room_uid=None`; revisit if capability false-positives are observed in practice
- `Literal` type not enforced at runtime in `InputState.input_source` (`domain/models.py`) — pre-existing pattern across all domain dataclasses; Python does not enforce Literal at runtime
