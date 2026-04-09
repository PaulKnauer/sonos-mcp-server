# BMAD Phase Conventions

## Purpose

This project has BMAD artifacts from multiple delivery phases stored under the same `_bmad-output` tree. BMAD reused story numbering (`1-1`, `1-2`, etc.) in later phases, so the bare story key is **not globally unique**.

This file defines the canonical convention for resolving that ambiguity.

## Canonical Reference Format

Always refer to a story as:

`phase-<n>/<story-key>`

Examples:

- `phase-1/2-1-discover-addressable-rooms-and-system-topology`
- `phase-2/1-4-harden-advanced-playback-contracts-and-regression-coverage`

Do not use `1-1`, `2-1`, or similar by themselves unless the phase is already explicit in the surrounding context.

## Current Active Phase

- Active phase: `phase-2`
- Label: `Phase 2 (Tier 1 Expansion)`
- Active sprint tracker: [_bmad-output/implementation-artifacts/sprint-status.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/sprint-status.yaml)
- Phase index: [_bmad-output/phase-index.yaml](/Users/paul/github/sonos-mcp-server/_bmad-output/phase-index.yaml)

## Status Tracking Rule

- `sprint-status.yaml` tracks **Phase 2 only**
- Legacy Phase 1 story files remain in `implementation-artifacts/` for historical reference
- When a legacy Phase 1 file shares the same numeric key as a Phase 2 file, Phase 2 is the authoritative interpretation for `sprint-status.yaml`

## Collision Rule

If a story key exists in multiple phases:

1. Resolve the phase from context first.
2. If context is unclear, consult `phase-index.yaml`.
3. If the task concerns current work planning or sprint state, prefer `phase-2`.
4. If the task concerns historical implementation, use the canonical `phase-<n>/<story-key>` form.

## Practical Guidance

- For BMAD planning, sprinting, and “next story” workflows, treat the active namespace as `phase-2`.
- For old MVP artifacts, keep the existing files in place and reference them via `phase-1/...`.
- New notes, reviews, and manual status updates should include the phase in prose whenever a duplicate story key exists.
