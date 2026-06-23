---
name: generate-hypothesis
description: Draft testable hypotheses, then send them to fresh Codex review for falsifiability and operationalization.
when_to_use: After /identify-gaps.
---

# /generate-hypothesis

This is a PM-orchestrated multi-phase skill. The Research Lead validates inputs, invokes
`scientific-author` only for hypothesis prose, then invokes a fresh Codex reviewer through
the centralized runner.

Inputs:
- `docs/research/gaps.md`
- `docs/research/lit-review.md`
- Zone B constraints and ethics tier

Output:
- `docs/research/hypotheses.md`
- `.claude/tasks/<task-id>/review.md`

Workflow:
1. PM validates `docs/research/gaps.md`, `docs/research/lit-review.md`, Zone B constraints,
   and ethics tier. Stop for explicit user approval if hypothesis generation would involve
   participants, regulated or sensitive data, or a confirmatory-analysis commitment that the
   user has not approved.
2. PM spawns `scientific-author` with mode `hypothesis-writing`, inputs above, output path
   `docs/research/hypotheses.md`, and acceptance criteria requiring 3-6 falsifiable
   hypotheses with variables, expected direction, scope, measurable outcomes, and clear
   links to the accepted gaps.
3. PM creates `.claude/tasks/<task-id>/brief.md` for reviewer. Include the draft path,
   source inputs, ethics constraints, and a rubric covering falsifiability, operationalization,
   measurement feasibility, confounding, scope creep, and unsupported claims.
4. PM runs `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
5. PM resolves blocker and major findings with `scientific-author` in mode
   `hypothesis-writing`, then reruns review when needed. Design work must not start until
   blocker and major findings are resolved or explicitly waived by the Research Lead with
   rationale.
6. PM updates Zone C to `current_phase: hypothesis`, `last_skill_run: generate-hypothesis`,
   and `next_action: /design-experiment`.
