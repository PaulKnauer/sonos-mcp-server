# Edge Case Hunter Review Prompt

Use the `bmad-review-edge-case-hunter` skill.

Review the diff below for unhandled branches, unsafe defaults, portability issues, startup lifecycle problems, network edge cases, and test gaps. You may read the repository for context. Output a markdown list. Each finding should include:
- a short title
- severity
- affected file/area
- the specific edge case or branch that is unhandled

Use this diff:

See `review-blind-hunter.md` in the same folder for the exact diff block. Review that diff against the current repository state.
