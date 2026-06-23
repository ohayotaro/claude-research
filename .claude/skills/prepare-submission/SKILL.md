---
name: prepare-submission
description: Prepare a local submission bundle with deterministic checks and author prose fixes; never submit externally.
when_to_use: Before venue submission or internal review packaging.
---

# /prepare-submission

This is a PM-orchestrated multi-phase skill. Codex builder owns local bundle packaging and
validation. `scientific-author` owns only prose fixes. The PM never submits externally from
this skill.

Inputs:
- accepted manuscript
- venue instructions supplied by the user
- references, figures, result ledgers, ethics and data statements

Outputs:
- `docs/paper/<paper_id>/submissions/<venue-slug>-r<round>/`

Workflow:
1. Resolve `paper_id` per multi-paper.md §4. `paper_id` is required; `--venue` is an optional one-shot override.
2. PM validates that the manuscript is accepted for local packaging, venue instructions are
   available, required result ledgers exist, and ethics/data statements are present.
3. PM creates `.claude/tasks/<task-id>/brief.md` for Codex builder with the resolved
   `paper_id`, venue slug/round, output directory, venue instructions, required files, and
   deterministic checks for length, references, figure files, anonymization, required
   statements, package manifest, and result traceability.
4. PM runs `python scripts/codex_research.py build <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
5. PM invokes `scientific-author` with mode `submission-prose` for statement or prose fixes
   only. The invocation must name the exact manuscript/prose paths to edit, the submission
   package path to read, and acceptance criteria for venue compliance, citation grounding,
   result-ID traceability, and no invented external-submission metadata.
6. PM reruns deterministic checks and `python scripts/research_evidence.py trace-prose`
   when prose or result-referenced files changed.
7. Do not update Zone B status during bundle preparation. Only after the user confirms
   the submission was actually made, update status to `submitted`.
8. PM updates Zone C with `current_phase: submission`, `last_skill_run: prepare-submission`,
   and next action.
9. Require explicit user approval before any external submission, upload, communication, or
   credential use. Only after the user confirms the external submission actually occurred may
   PM update Zone B `papers[id == <paper_id>].status` to `submitted`.
