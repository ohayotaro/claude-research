---
name: prepare-submission
description: Prepare a local submission bundle with deterministic checks and author prose fixes; never submit externally.
when_to_use: Before venue submission or internal review packaging.
---

# /prepare-submission

Inputs:
- accepted manuscript
- venue instructions supplied by the user
- references, figures, result ledgers, ethics and data statements

Outputs:
- `docs/paper/<paper_id>/submissions/<venue-slug>-r<round>/`

Workflow:
1. Resolve `paper_id` per multi-paper.md §4. `paper_id` is required; `--venue` is an optional one-shot override.
2. Run deterministic checks for length, references, figure files, anonymization, required statements, and result traceability.
3. Use `scientific-author` mode `submission-prose` for statement or prose fixes.
4. Update Zone B `papers[id == <paper_id>].status` to `submitted`.
5. Update Zone C with `current_phase: submission` and next action.
6. Require explicit user approval before any external submission, upload, or communication.
