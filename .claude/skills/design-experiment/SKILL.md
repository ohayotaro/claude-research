---
name: design-experiment
description: Write the scientific protocol, then require fresh Codex review of estimands, power, leakage, ethics, and reproducibility.
when_to_use: After hypotheses are accepted.
context: fork
agent: scientific-author
---

# /design-experiment

Use `scientific-author` mode `methodology-writing`, followed by a fresh Codex reviewer.

Inputs:
- `docs/research/hypotheses.md`
- relevant source/data constraints
- Zone B ethics and data-sensitivity fields

Output:
- `docs/research/methodology.md`
- `.claude/tasks/<task-id>/review.md`

Workflow:
1. Draft confirmatory and exploratory analyses separately.
2. Specify estimands, outcomes, inclusion/exclusion criteria, stopping rules, missing-data handling, multiplicity, power, and reproducibility requirements before data inspection.
3. Stop for explicit user approval if ethics, regulated data, primary outcomes, or sensitive data are involved.
4. Run a fresh Codex review with `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
5. Resolve blocker/major findings before the Research Lead accepts the protocol.
6. Update Zone C with `current_phase: design` and next action.
