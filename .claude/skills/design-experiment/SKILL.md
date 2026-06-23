---
name: design-experiment
description: Write the scientific protocol, then require fresh Codex review of estimands, power, leakage, ethics, and reproducibility.
when_to_use: After hypotheses are accepted.
---

# /design-experiment

This is a PM-orchestrated multi-phase skill. The Research Lead validates preconditions,
invokes `scientific-author` only for methodology prose, handles ethics gates, then invokes
a fresh Codex reviewer through the centralized runner.

Inputs:
- `docs/research/hypotheses.md`
- relevant source/data constraints
- Zone B ethics and data-sensitivity fields

Output:
- `docs/research/methodology.md`
- `.claude/tasks/<task-id>/review.md`

Workflow:
1. PM validates that `docs/research/hypotheses.md` exists and that hypotheses have been
   accepted after review. Stop if the hypothesis stage has unresolved blocker or major
   findings.
2. PM spawns `scientific-author` with mode `methodology-writing`, inputs above, output path
   `docs/research/methodology.md`, and acceptance criteria requiring separate confirmatory
   and exploratory plans.
3. PM ensures the methodology specifies estimands, outcomes, inclusion/exclusion criteria,
   stopping rules, missing-data handling, multiplicity, power, leakage controls, and
   reproducibility requirements before data inspection.
4. PM runs an ethics and safety check against Zone B. Stop for explicit user approval if
   participants, regulated or sensitive data, primary outcomes, confirmatory-analysis changes,
   external data acquisition with uncertain license, or other approval-gated work is involved.
5. PM creates `.claude/tasks/<task-id>/brief.md` for reviewer. Include the draft path,
   hypotheses, constraints, ethics/data-sensitivity fields, and a rubric covering estimands,
   power, leakage, missing data, multiplicity, reproducibility, and user approval gates.
6. PM runs `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
7. PM resolves blocker and major findings with `scientific-author` in mode
   `methodology-writing`, then reruns review when needed. The Research Lead accepts the
   protocol only after blocker and major findings are resolved or explicitly waived with
   rationale.
8. PM updates Zone C with `current_phase: design`, `last_skill_run: design-experiment`,
   and the next action.
