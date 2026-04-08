# Story 1.2: Support seek and sleep timer operations

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Sonos user,
I want to seek within the current track and manage a sleep timer for a room,
so that I can control active listening sessions more precisely.

## Acceptance Criteria

1. **Seek within current track:** Given a room with an active track, when the client requests a seek to a valid track position, then the service applies the seek operation for the target room and returns the normalized resulting playback state.

2. **Get sleep timer:** Given a room that supports sleep-timer operations, when the client requests the current sleep timer status, then the service returns the normalized timer state for that room.

3. **Set or clear sleep timer:** Given a room that supports sleep-timer operations, when the client sets or clears a sleep timer, then the service applies the requested change and returns the resulting timer state in a structured response.

## Tasks / Subtasks

- [x] Add sleep-timer domain and response models (AC: 2, 3)
  - [x] Add `SleepTimerState` frozen dataclass to `src/soniq_mcp/domain/models.py` with fields `room_name: str`, `active: bool`, `remaining_seconds: int | None`, and `remaining_minutes: int | None`
  - [x] Add `SleepTimerResponse` Pydantic model to `src/soniq_mcp/schemas/responses.py` with `from_domain(state: SleepTimerState)` factory

- [x] Extend `SoCoAdapter` for seek and sleep timer operations (AC: 1, 2, 3)
  - [x] Add `seek(ip_address: str, position: str) -> None` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Add `get_sleep_timer(ip_address: str, room_name: str) -> SleepTimerState` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Add `set_sleep_timer(ip_address: str, room_name: str, minutes: int) -> SleepTimerState` to `src/soniq_mcp/adapters/soco_adapter.py`
  - [x] Convert minutes to seconds in the adapter for `set_sleep_timer`; `minutes=0` must clear the timer by passing `None` to SoCo
  - [x] Normalize `zone.get_sleep_timer()` return values into stable domain state and wrap SoCo failures as `PlaybackError`

- [x] Extend shared playback orchestration instead of creating a new capability module (AC: 1, 2, 3)
  - [x] Add `seek`, `get_sleep_timer`, and `set_sleep_timer` to `src/soniq_mcp/services/sonos_service.py`
  - [x] Add pass-through methods with the same names to `src/soniq_mcp/services/playback_service.py`
  - [x] Reuse coordinator-routing semantics for session-level operations so grouped rooms target the active coordinator when required
  - [x] Validate seek position and sleep-timer minutes in the service layer before calling the adapter

- [x] Extend the playback tool surface in the existing module (AC: 1, 2, 3)
  - [x] Add `seek`, `get_sleep_timer`, and `set_sleep_timer` tool handlers to `src/soniq_mcp/tools/playback.py`
  - [x] Reuse `_CONTROL_TOOL_HINTS` for `seek` and `set_sleep_timer`
  - [x] Reuse `_READ_ONLY_TOOL_HINTS` for `get_sleep_timer`
  - [x] Return `PlaybackStateResponse` from `seek`
  - [x] Return `SleepTimerResponse` from `get_sleep_timer` and `set_sleep_timer`
  - [x] Keep error handling aligned with existing playback tools: `RoomNotFoundError`, `PlaybackError`, `SonosDiscoveryError` only

- [x] Register new tool names and preserve transport parity (AC: 1, 2, 3)
  - [x] Add `seek`, `get_sleep_timer`, and `set_sleep_timer` to `KNOWN_TOOL_NAMES` in `src/soniq_mcp/config/models.py`
  - [x] Ensure `src/soniq_mcp/tools/__init__.py` needs no new service-registration branch beyond the existing playback registration path
  - [x] Update `tests/integration/transports/test_http_bootstrap.py` expected tool names/count to include the three new tools

- [x] Add regression coverage across adapter, service, tools, schemas, and transport parity (AC: 1, 2, 3)
  - [x] Add adapter tests in `tests/unit/adapters/test_soco_adapter_seek_sleep_timer.py`
  - [x] Add service tests in `tests/unit/services/test_playback_service_seek_sleep_timer.py` or extend an existing playback-service test module if one is introduced
  - [x] Add tool tests in `tests/unit/tools/test_playback.py` or a capability-aligned sibling if that produces clearer ownership
  - [x] Add contract tests in `tests/contract/tool_schemas/test_playback_tool_schemas.py`
  - [x] Add schema tests in `tests/unit/schemas/test_responses.py` for `SleepTimerResponse`

## Dev Notes

### Story intent and boundary

- Story 1.2 stays inside the existing playback boundary. Unlike Story 1.1, do not introduce a new `sleep_timer_service.py`, `seek_service.py`, or separate playback-adjacent tools module.
- The architecture maps Tier 1 seek and sleep timer to `tools/playback.py`, `services/playback_service.py`, and `adapters/soco_adapter.py`. This story should reinforce that boundary rather than fragment it further.

### Required tool surface

- Add these MCP tools:
  - `seek(room, position)`
  - `get_sleep_timer(room)`
  - `set_sleep_timer(room, minutes)`
- Keep names stable and `snake_case`.
- `seek.position` should use the `"HH:MM:SS"` format.
- `set_sleep_timer.minutes` should be an integer number of minutes; `0` is the clear/cancel path.

### Response shape requirements

- `seek` should return `PlaybackStateResponse`, not a bespoke response and not raw track info.
- `get_sleep_timer` and `set_sleep_timer` should return `SleepTimerResponse` with:
  - `room_name`
  - `active`
  - `remaining_seconds`
  - `remaining_minutes`
- For an inactive timer, return `active=False` and `remaining_seconds=None`, `remaining_minutes=None`.

### Validation rules

- Validate seek position in the service layer before calling the adapter.
- Accept only the explicit `HH:MM:SS` shape; reject malformed strings with `PlaybackError`.
- Validate `minutes >= 0` in the service layer.
- Treat `minutes=0` as clear timer.
- Do not let raw `ValueError`, SoCo exceptions, or free-form messages escape tool handlers.

### Coordinator and routing rules

- Seek and sleep timer are active-session controls. For grouped rooms, route through the coordinator in the same spirit as `get_track_info` and Story 1.1 play-mode routing.
- Reuse or generalize existing coordinator-resolution logic from [src/soniq_mcp/services/sonos_service.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/services/sonos_service.py) rather than duplicating ad hoc room-resolution code in multiple places.
- Tool handlers must continue to accept the room the user targeted, even if the underlying Sonos command is routed to the coordinator IP.

### Adapter implementation requirements

- `SoCoAdapter` remains the only direct `soco` boundary.
- `seek` should call `zone.seek(position)`.
- `set_sleep_timer` should call `zone.set_sleep_timer(...)` with seconds or `None` for clear.
- `get_sleep_timer` should call `zone.get_sleep_timer()`.
- Wrap all failures as `PlaybackError`.
- Normalize timer state in the adapter so the service and tool layers never deal with raw SoCo timer values.

### Service-layer implementation guidance

- Extend `SonosService` with the new operations, then expose them from `PlaybackService`.
- After a successful seek, return normalized playback state for the requested room. The simplest compliant path is:
  - resolve the correct room/coordinator for the command
  - perform `adapter.seek(...)`
  - return `get_playback_state(room_name)`
- For sleep timer operations, return `SleepTimerState` built by adapter normalization.
- Prefer a shared private helper for coordinator/session routing if it can replace the narrower `_resolve_track_info_room` helper cleanly without unrelated churn.

### File structure requirements

- Modify existing files first; do not add new capability modules unless truly required by a missing shared type.
- Expected primary touch points:
  - `src/soniq_mcp/domain/models.py`
  - `src/soniq_mcp/schemas/responses.py`
  - `src/soniq_mcp/adapters/soco_adapter.py`
  - `src/soniq_mcp/services/sonos_service.py`
  - `src/soniq_mcp/services/playback_service.py`
  - `src/soniq_mcp/tools/playback.py`
  - `src/soniq_mcp/config/models.py`
  - `tests/unit/adapters/...`
  - `tests/unit/tools/...`
  - `tests/unit/schemas/...`
  - `tests/contract/tool_schemas/test_playback_tool_schemas.py`
  - `tests/integration/transports/test_http_bootstrap.py`

### Testing requirements

- Adapter tests must cover:
  - successful seek delegation
  - seek SoCo failure wrapping
  - active sleep timer normalization
  - inactive sleep timer normalization
  - `minutes=0` clearing behavior
  - positive-minute conversion to seconds
- Service tests must cover:
  - valid seek position
  - invalid seek position
  - valid and invalid timer minute values
  - grouped-room coordinator routing for both seek and sleep timer
  - returned playback-state behavior after seek
- Tool tests must cover:
  - registration and `tools_disabled`
  - annotation correctness
  - success and all three mapped error classes
  - stable response fields
- Contract tests must cover:
  - tool names
  - required/optional parameters
  - response field stability
  - read-only vs control annotations
- Integration parity test must include the three new tools in both HTTP and stdio surfaces.

### Previous story intelligence

- Story 1.1 established the pattern of:
  - frozen dataclass domain models
  - matching response models with `from_domain(...)`
  - adapter-only SoCo access
  - typed error mapping through existing error factories
  - contract tests that protect the MCP tool surface
- Reuse those patterns directly.
- Story 1.1 also added new tool names to `KNOWN_TOOL_NAMES` and updated HTTP parity coverage. Story 1.2 must do the same or config validation and transport-parity tests will drift.

### Git intelligence

- Recent commits show Story 1.1 was completed and then hardened via review fixes:
  - `1f38347 Story 1.1 quality gate fixes`
  - `51b98fc Story 1.1 dev, review and fixes`
- That means the play-mode implementation is the freshest example of how this repository wants new Sonos capability work to be structured and tested.
- Use it as a pattern reference for response-model creation, tool annotations, adapter error wrapping, and parity-test maintenance.

### Reinvention and regression guardrails

- Do not add direct `soco` imports anywhere outside `src/soniq_mcp/adapters/soco_adapter.py`.
- Do not create a second registration path in `tools/__init__.py` for seek/sleep timer.
- Do not return raw integers from sleep-timer tools; always return the structured timer response.
- Do not expose alternative seek formats such as seconds-only integers or free-form durations in this story.
- Do not skip updates to `KNOWN_TOOL_NAMES`; that breaks validated config behavior.
- Do not forget HTTP parity coverage; tool-surface drift is a regression.

### References

- Story definition and acceptance criteria: [epics.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/epics.md)
- Phase-2 feature intent: [prd.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/prd.md)
- Architecture refresh and capability-family mapping: [architecture.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/architecture.md)
- SoCo capability notes for seek and sleep timer: [technical-soco-capability-gap-research-2026-04-02.md](/Users/paul/github/sonos-mcp-server/_bmad-output/planning-artifacts/research/technical-soco-capability-gap-research-2026-04-02.md)
- Prior story implementation pattern: [1-1-expose-play-mode-controls-for-active-rooms.md](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/1-1-expose-play-mode-controls-for-active-rooms.md)
- Existing playback tools: [playback.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/tools/playback.py)
- Existing playback facade: [playback_service.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/services/playback_service.py)
- Existing Sonos orchestration helper: [sonos_service.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/services/sonos_service.py)
- Existing adapter boundary: [soco_adapter.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/adapters/soco_adapter.py)
- Existing response-model patterns: [responses.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/schemas/responses.py)
- Existing config tool-name validation: [models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py)
- Existing playback tool contract tests: [test_playback_tool_schemas.py](/Users/paul/github/sonos-mcp-server/tests/contract/tool_schemas/test_playback_tool_schemas.py)
- Existing HTTP parity test: [test_http_bootstrap.py](/Users/paul/github/sonos-mcp-server/tests/integration/transports/test_http_bootstrap.py)

## Dev Agent Record

### Agent Model Used

gpt-5

### Debug Log References

- No `project-context.md` file was present in this repository.
- `_resolve_track_info_room` in `sonos_service.py` was renamed to `_resolve_coordinator` to serve as the shared helper for all three new session-level operations (seek, get_sleep_timer, set_sleep_timer), per story guidance.
- SoCo `get_sleep_timer()` returns an integer (remaining seconds) or `None` when inactive; `0` is treated as inactive to match falsy semantics.
- `tools/__init__.py` required no changes — seek and sleep timer register through the existing `playback_service` / `register_playback` path.
- Tightened seek validation beyond regex-only matching so invalid values like `00:99:00` and `00:00:99` are rejected before reaching SoCo.
- `set_sleep_timer()` now rereads the timer from Sonos after writes so the response reflects authoritative device state rather than a synthesized echo of the requested value.

### Completion Notes List

- Added `SleepTimerState` frozen dataclass to `domain/models.py` and `SleepTimerResponse` Pydantic model to `schemas/responses.py`, following Story 1.1 frozen-dataclass + `from_domain()` pattern.
- Extended `SoCoAdapter` with `seek`, `get_sleep_timer`, `set_sleep_timer` — the only SoCo boundary. All failures wrapped as `PlaybackError`.
- Extended `SonosService` with the three new operations using the generalized `_resolve_coordinator` helper (replaces narrower `_resolve_track_info_room`). Position format validated by regex in service layer; negative minutes rejected before adapter call.
- Added pass-through methods to `PlaybackService` facade.
- Added three tool handlers to `tools/playback.py` reusing existing hint constants and error handling patterns.
- Added `seek`, `get_sleep_timer`, `set_sleep_timer` to `KNOWN_TOOL_NAMES`; updated HTTP parity test from 31 to 34 tools.
- Strengthened seek validation to reject out-of-range minute and second components instead of accepting any two-digit values.
- Changed sleep timer writes to return the authoritative post-write timer state from Sonos, preventing stale or synthesized responses after device-side rounding/normalization.
- Full test suite: 823 passed, 3 skipped, 0 failures.

### Change Log

- 2026-04-08: Addressed Story 1.2 review-quality issues by tightening seek validation, returning authoritative post-write sleep timer state, extending targeted regression coverage, and rerunning the full suite.
- 2026-04-08: Story status updated from `review` to `done`.

### File List

- `_bmad-output/implementation-artifacts/1-2-support-seek-and-sleep-timer-operations.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `src/soniq_mcp/domain/models.py`
- `src/soniq_mcp/schemas/responses.py`
- `src/soniq_mcp/adapters/soco_adapter.py`
- `src/soniq_mcp/services/sonos_service.py`
- `src/soniq_mcp/services/playback_service.py`
- `src/soniq_mcp/tools/playback.py`
- `src/soniq_mcp/config/models.py`
- `tests/unit/schemas/test_responses.py`
- `tests/unit/adapters/test_soco_adapter_seek_sleep_timer.py`
- `tests/unit/services/test_playback_service_seek_sleep_timer.py`
- `tests/unit/tools/test_playback.py`
- `tests/contract/tool_schemas/test_playback_tool_schemas.py`
- `tests/integration/transports/test_http_bootstrap.py`
