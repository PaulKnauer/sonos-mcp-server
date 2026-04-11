# Edge Case Hunter Prompt

Use the `bmad-review-edge-case-hunter` skill.

Review the diff for unhandled branching paths, boundary conditions, validation gaps, invariants, and missing negative-path coverage. You may inspect the repository read-only for context.

Diff file: `/Users/paul/github/sonos-mcp-server/_bmad-output/implementation-artifacts/review-prompts/story-3-1-alarm-review.diff`
Repository root: `/Users/paul/github/sonos-mcp-server`

Output findings as a Markdown list. Each finding should include:
- concise title
- severity
- edge case or branch condition
- evidence from the diff and any supporting repository context
