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
- `docs/paper/submissions/<venue>-<round>/`

Workflow:
1. Run deterministic checks for length, references, figure files, anonymization, required statements, and result traceability.
2. Use `scientific-author` mode `submission-prose` for statement or prose fixes.
3. Require explicit user approval before any external submission, upload, or communication.
