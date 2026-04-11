---
workflow: correct-course
date: 2026-04-11
project: sonos-mcp-server
change_trigger: "Story 3.2 still promises playlist rename, but verified current SoCo support does not provide a supported rename path."
scope_classification: moderate
status: approved
---

# Sprint Change Proposal: Story 3.2 Playlist Rename Course Correction

## 1. Issue Summary

### Triggering Issue

- Triggering story: `phase-2/3-2-introduce-sonos-playlist-crud-operations`
- Trigger type: technical limitation discovered during implementation
- Discovery context: code review and subsequent technical research during Story 3.2 execution

### Problem Statement

Story 3.2 currently promises playlist rename support, but the verified current `SoCo` integration layer used by this project does not expose a supported first-class playlist rename capability. The implementation was corrected to remove `rename_playlist` from the public MCP tool surface, but the story, acceptance criteria, and sprint tracker still describe the work as if rename were part of delivered scope.

### Evidence

- `SoCo` stable API docs expose playlist create, lookup, update-style mutation, and delete operations, but no documented rename method.
- Current upstream `SoCo` source also does not expose a supported rename helper.
- Sonos platform docs show rename exists in other API surfaces, so the limitation is real but specific to the chosen stack.
- Current implementation already removed `rename_playlist` from the exposed MCP surface to preserve contract honesty.

## 2. Impact Analysis

### Epic Impact

- Affected epic: `Epic 3 - Alarm and Playlist Lifecycle Management`
- Epic viability: still viable without fundamental redesign
- Required epic change: clarify that Story 3.2 covers supported playlist lifecycle operations on the current stack, not guaranteed rename support
- Future epic dependency: optional follow-up investigation story for supported rename feasibility

### Story Impact

- Directly affected story: `3.2 Introduce Sonos playlist CRUD operations`
- Current issue:
  - story text says `create, rename, update, and delete`
  - acceptance criteria say `creates, renames, updates, or deletes`
  - task list and test coverage still treat rename as expected delivery
- Tracker mismatch:
  - story implementation behavior no longer exposes rename
  - sprint tracker currently marks `3-2-introduce-sonos-playlist-crud-operations` as `done`
  - that `done` state is not trustworthy until the story language matches the actual supported scope

### PRD Impact

- No core PRD rewrite is required.
- `FR67` already says: `Users can view, create, update, and delete Sonos playlists exposed through the household.`
- The PRD therefore already aligns more closely with the implemented capability set than Story 3.2 does.
- No MVP or broader roadmap reduction is required.

### Architecture Impact

- No architectural reversal is required.
- The current architecture is reinforced by this change:
  - public MCP tools should map to adapter-backed capabilities
  - unsupported dependency operations should not remain exposed as normal user workflows
- Architecture wording that says `playlist CRUD` can remain, because the actual delivered contract remains create/read-update/delete oriented without inventing unsupported rename behavior.

### UX / Docs Impact

- No dedicated UX spec exists.
- User-facing examples and future docs should avoid mentioning playlist rename until a supported path exists.
- Story `3.4` should absorb documentation coverage for the deferred rename decision so examples stay honest.

### Secondary Artifact Impact

- Affected artifacts:
  - `_bmad-output/planning-artifacts/epics.md`
  - `_bmad-output/implementation-artifacts/phase-2/3-2-introduce-sonos-playlist-crud-operations.md`
  - `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Potential future artifact:
  - a new backlog story for rename feasibility investigation if product value justifies it

## 3. Recommended Approach

### Selected Path

Hybrid of:

- `Option 1: Direct Adjustment`
- plus a small `Option 3: scope clarification` at story level

### Recommendation

Keep the current implementation as the correct technical outcome, revise Story 3.2 to remove rename from committed scope, and add a separate backlog follow-up only if playlist rename remains strategically desirable.

### Rationale

- Lowest implementation churn: the code already reflects the safest contract.
- Lowest technical risk: avoids undocumented workaround behavior.
- Minimal planning impact: PRD and architecture remain mostly valid.
- Highest maintainability: keeps the public tool contract aligned with adapter capability.
- Best momentum preservation: avoids rollback and avoids reopening completed code solely to satisfy an unsupported story promise.

### Options Evaluated

#### Option 1: Direct Adjustment

- Viable: yes
- Effort: low
- Risk: low
- Notes: update story wording, acceptance criteria, tasks, tests expectations, and sprint status

#### Option 2: Potential Rollback

- Viable: no
- Effort: medium
- Risk: medium
- Notes: rolling back the current implementation would reintroduce a misleading public contract or force a broken rename promise

#### Option 3: PRD MVP Review

- Viable: partially, but unnecessary as primary path
- Effort: low
- Risk: low
- Notes: only a narrow scope clarification is needed because the PRD already does not require rename explicitly

## 4. Detailed Change Proposals

### A. Story 3.2 scope correction

Story: `3.2 Introduce Sonos playlist CRUD operations`  
Section: Story statement

OLD:

```md
As a Sonos user,
I want to create, rename, update, and delete Sonos playlists,
so that I can manage reusable listening collections from the same control surface.
```

NEW:

```md
As a Sonos user,
I want to view, create, update, and delete Sonos playlists,
so that I can manage reusable listening collections from the same control surface.
```

Rationale: matches `FR67`, current implementation, and verified supported capability on the current stack.

Story: `3.2 Introduce Sonos playlist CRUD operations`  
Section: Acceptance Criterion 2

OLD:

```md
Given a valid playlist lifecycle request, when the client creates, renames, updates, or deletes a playlist, then the service performs the requested operation through the playlist-service boundary and returns the resulting normalized playlist state.
```

NEW:

```md
Given a valid supported playlist lifecycle request, when the client creates, updates, or deletes a playlist, then the service performs the requested operation through the playlist-service boundary and returns the resulting normalized playlist state or structured delete confirmation.
```

Rationale: removes unsupported rename promise and aligns response wording with actual delete behavior.

Story: `3.2 Introduce Sonos playlist CRUD operations`  
Section: Acceptance Criterion 3

OLD:

```md
Given an invalid playlist identifier or unsupported mutation, when the client invokes the playlist lifecycle tool, then the service returns a typed validation or unsupported-operation error.
```

NEW:

```md
Given an invalid playlist identifier or an unsupported household playlist mutation, when the client invokes the playlist lifecycle tool, then the service returns a typed validation or unsupported-operation error.
```

Rationale: preserves the domain rule without advertising rename as a supported workflow.

### B. Story 3.2 task and test cleanup

Story: `3.2 Introduce Sonos playlist CRUD operations`  
Section: lifecycle scope, tasks, and tests

OLD:

```md
- playlist rename
- rename_playlist(...)
- rename flow
```

NEW:

```md
- remove rename from committed story scope for the current dependency set
- keep typed unsupported-operation handling inside the service/adapter boundary for future unsupported household mutations
- cover list/create/update/delete flows and preserve playback compatibility
- add a note that playlist rename is deferred pending supported dependency or alternate integration research
```

Rationale: keeps the story faithful to the delivered capability while preserving architectural handling for unsupported operations.

### C. Epic 3 wording adjustment

Artifact: `epics.md`  
Section: Story 3.2

OLD:

```md
I want to create, rename, update, and delete Sonos playlists
```

NEW:

```md
I want to view, create, update, and delete Sonos playlists
```

Rationale: matches `FR67` and removes the only known epic-level rename promise conflict.

### D. Add follow-up backlog story

Artifact: `epics.md`  
Proposed addition after Story 3.4 or as backlog note

NEW:

```md
Story 3.x: Investigate supported Sonos playlist rename capability

As a maintainer,
I want to verify whether a newer supported SoCo release or alternate Sonos integration path can provide playlist rename cleanly,
so that future playlist lifecycle expansion does not rely on unsupported workarounds.
```

Suggested acceptance criteria:

- research compares current and newer supported `SoCo` versions for rename support
- research identifies whether an alternate Sonos API path is viable without violating current architecture
- outcome explicitly recommends `implement`, `defer`, or `reject`

Rationale: isolates rename as a technical investigation instead of a silently broken delivery promise.

### E. Sprint tracker correction

Artifact: `sprint-status.yaml`

OLD:

```yaml
3-2-introduce-sonos-playlist-crud-operations: done
```

NEW:

```yaml
3-2-introduce-sonos-playlist-crud-operations: in-progress
```

Rationale: keep the story open until the approved planning correction is applied. After artifact updates are complete, it can move back to `done`.

## 5. MVP Impact and Action Plan

### MVP Impact

- MVP / phase direction is not fundamentally reduced.
- No epic removal is needed.
- No architecture rollback is needed.
- The change is a scope-clarity correction inside Epic 3.

### High-Level Action Plan

1. Approve this change proposal.
2. Update `epics.md` Story 3.2 wording.
3. Update the Story 3.2 implementation artifact to remove rename from committed scope and note deferral.
4. Update `sprint-status.yaml` to `in-progress` until those changes are applied.
5. Optionally add the rename investigation story to backlog.
6. After artifact alignment, return Story 3.2 to `done`.

### Dependencies

- Technical research is complete and sufficient.
- No code rollback is required.
- No PRD rewrite is required.

## 6. Implementation Handoff

### Scope Classification

- Moderate

### Handoff Recipients

- Scrum Master / planning workflow:
  - update story and sprint tracking artifacts
  - insert follow-up backlog item if approved
- Product Owner / PM:
  - confirm whether playlist rename still has strategic value worth a future investigation story
- Development team:
  - no immediate code changes required if planning artifacts are aligned with current implementation

### Success Criteria

- Story 3.2 no longer promises rename on the current stack.
- Epic and story wording match `FR67` and current implementation.
- Sprint tracker reflects the temporary correction state accurately.
- If rename remains desired, it exists only as an explicit follow-up investigation, not as a hidden broken promise.

## 7. Checklist Summary

- [x] 1.1 Triggering story identified
- [x] 1.2 Core problem defined
- [x] 1.3 Evidence gathered
- [x] 2.1 Current epic evaluated
- [x] 2.2 Epic-level changes identified
- [x] 2.3 Remaining epics reviewed for impact
- [x] 2.4 Need for new follow-up work assessed
- [x] 2.5 Epic order reviewed
- [x] 3.1 PRD checked for conflict
- [x] 3.2 Architecture checked for conflict
- [N/A] 3.3 Dedicated UX spec conflict review
- [x] 3.4 Secondary artifacts reviewed
- [x] 4.1 Direct adjustment evaluated
- [x] 4.2 Rollback evaluated
- [x] 4.3 MVP review evaluated
- [x] 4.4 Path forward selected
- [x] 5.1 Issue summary created
- [x] 5.2 Artifact adjustment needs documented
- [x] 5.3 Recommendation documented
- [x] 5.4 MVP impact and action plan defined
- [x] 5.5 Handoff plan established
