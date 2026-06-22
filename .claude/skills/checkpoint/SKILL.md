---
name: checkpoint
description: Persist current progress, recent artifacts, active Codex task, and next action into CLAUDE.md Zone C.
when_to_use: At natural pauses, before /exit, or when handing off to a future session.
---

# /checkpoint

The Research Lead performs this deterministic update directly.

Workflow:
1. Summarize this session in 2-4 bullets: skills run, artifacts produced, decisions made, and blockers.
2. Determine the current phase from populated artifacts and unresolved review state.
3. Record any active `.claude/tasks/<task-id>/` path in `active_codex_task`.
4. Replace only the content between `<!-- ZONE_C_BEGIN -->` and `<!-- ZONE_C_END -->`.

Zone C format:

```yaml
current_phase: <phase>
active_agent: <scientific-author or null>
last_skill_run: <name>
last_run_id: <run_id or null>
recent_artifacts:
  - <path1>
  - <path2>
last_paper_id: <paper_id last operated on, or null>
active_codex_task: <task_id or null>
next_action: "<one-line user-facing instruction>"
notes: |
  <2-4 lines: decisions, blockers, parallel tracks>
```

`last_paper_id` is only a hint. Skills must still resolve paper IDs explicitly.
