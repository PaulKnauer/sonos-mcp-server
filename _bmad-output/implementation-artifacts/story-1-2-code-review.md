# Story 1.2 Code Review

Review scope:
- Story 1.2 change set relative to commit `1abdae5`
- Spec context: `1-2-implement-typed-configuration-and-validation.md`
- Review method: Blind Hunter, Edge Case Hunter, Acceptance Auditor

## Patch

- High: Startup preflight is not wired into the actual launch path, so invalid configuration does not block runtime startup as required by AC 2.
  Location: [src/soniq_mcp/__main__.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/__main__.py#L3), [src/soniq_mcp/server.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/server.py#L8), [src/soniq_mcp/config/validation.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/validation.py#L27)
  Detail: `run_preflight()` exists and is tested in isolation, but the real startup path still only calls `create_application()` and prints scaffold metadata. That means a bad `SONIQ_MCP_*` value can bypass the promised “fail before runtime” behavior unless every caller manually invokes validation.

- High: Unknown override keys are silently ignored by `SoniqConfig`, which can mask typos and leave the app running with defaults while appearing configured.
  Location: [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py#L39)
  Detail: `BaseModel` defaults to ignoring extra keys. A call like `load_config(overrides={"loglevel": "DEBUG"})` will not fail fast, even though the override is ineffective. For a config boundary, that is weak validation.

- Medium: File-based configuration is exposed but not implemented.
  Location: [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py#L27), [src/soniq_mcp/config/models.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/models.py#L62), [.env.example](/Users/paul/github/sonos-mcp-server/.env.example#L16)
  Detail: The story task allows file-based config if it is part of the chosen design. This patch exposes `config_file` in the model and example config, but the loader never reads the referenced file, so the advertised config path is currently a no-op.

- Medium: Whitespace-only overrides for optional string fields are normalized inconsistently and can become empty strings instead of `None`.
  Location: [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py#L45), [src/soniq_mcp/config/loader.py](/Users/paul/github/sonos-mcp-server/src/soniq_mcp/config/loader.py#L51)
  Detail: Environment values are stripped before use, but programmatic overrides are merged verbatim. `{"default_room": "   "}` or `{"config_file": "   "}` ends up as an empty string after model stripping instead of an absent value, which weakens normalization guarantees.

- Low: Some config tests are not isolated from pre-existing `SONIQ_MCP_*` environment state.
  Location: [tests/unit/config/test_loader.py](/Users/paul/github/sonos-mcp-server/tests/unit/config/test_loader.py#L29), [tests/integration/config/test_preflight_startup.py](/Users/paul/github/sonos-mcp-server/tests/integration/config/test_preflight_startup.py#L32)
  Detail: Several tests set only one or two environment variables without clearing the rest first. They can therefore inherit unrelated `SONIQ_MCP_*` values from the shell or future tests, which risks flakiness and false positives.

## Summary

- 0 intent_gap
- 0 bad_spec
- 5 patch
- 0 defer
- 4 findings rejected as noise or out of scope

Rejected items:
- Treating whitespace-only env values as “unset” instead of invalid is acceptable given the safe-default design.
- The Makefile `uv` bootstrap behavior is real, but it is not a Story 1.2 config-boundary defect.
- The global `str_strip_whitespace` concern is speculative for the current field set.
- Duplicate variants of the startup-preflight and file-config findings were merged above.
