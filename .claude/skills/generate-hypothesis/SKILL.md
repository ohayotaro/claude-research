---
name: generate-hypothesis
description: Draft testable hypotheses, then send them to fresh Codex review for falsifiability and operationalization.
when_to_use: After /identify-gaps.
context: fork
agent: scientific-author
---

# /generate-hypothesis

Use `scientific-author` mode `hypothesis-writing`, followed by a fresh Codex reviewer.

Inputs:
- `docs/research/gaps.md`
- `docs/research/lit-review.md`
- Zone B constraints and ethics tier

Output:
- `docs/research/hypotheses.md`
- `.claude/tasks/<task-id>/review.md`

Workflow:
1. Have the author draft 3-6 falsifiable hypotheses with variables, expected direction, scope, and measurable outcomes.
2. Create `.claude/tasks/<task-id>/brief.md` with the draft path and review rubric.
3. Run `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
4. Resolve reviewer findings with the author and Research Lead before design work starts.
5. Update Zone C to `current_phase: hypothesis` and next action `/design-experiment`.
