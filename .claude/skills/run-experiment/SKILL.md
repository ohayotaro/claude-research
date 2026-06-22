---
name: run-experiment
description: Send an accepted methodology to Codex builder for implementation, execution, tests, and reproducibility artifacts.
when_to_use: After /design-experiment and required approvals.
---

# /run-experiment

Codex builder owns this work through `scripts/codex_research.py build`.

Inputs:
- Accepted `docs/research/methodology.md`
- Approved hypotheses and data paths
- Any required seeds, runtime limits, and acceptance criteria

Outputs:
- `src/experiments/**`
- `tests/**`
- `data/results/<run_id>/metadata.json`
- run logs and raw result artifacts under `data/results/<run_id>/`

Workflow:
1. Confirm no unresolved blocker/major methodology review findings remain.
2. Ask for explicit approval before replacing a run, using credentials, acquiring non-public data, or performing destructive operations.
3. Write `.claude/tasks/<task-id>/brief.md` with implementation scope and expected artifacts.
4. Run `python scripts/codex_research.py build <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
5. On failure, use `/codex-debug` style workflow by running `python scripts/codex_research.py debug <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
6. Update Zone C with `current_phase: experiment`, `last_run_id`, and next action `/analyze-results`.
