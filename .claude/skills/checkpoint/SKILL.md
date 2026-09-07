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

Content rules:
- Zone C holds current state only: objectives, accepted decisions, unresolved issues, the
  next action, and paths to detailed records. It is loaded into every session, so anything
  stored here shapes future PM replies.
- Field values are schema-typed. `last_run_id` is a run ID, `last_skill_run` is a skill
  name, `recent_artifacts` is a list of paths. Do not put narrative into typed fields.
- `notes` is at most 4 lines. No retrospectives, self-evaluation, emphatic language, or
  bare chains of identifiers. Explain the subject before any ID.
- Correction histories and retrospectives go to a Research Lead-owned task record under
  `.claude/tasks/<task-id>/`; link it from `notes` or `recent_artifacts` instead of
  restating it. An existing paper changelog may be referenced but is written only by
  `scientific-author` through `/revise`; a checkpoint never writes it.
- Unresolved caveats and approval boundaries stay in `notes` until resolved. Keeping them
  takes precedence over the 4-line limit; if space is short, shorten other lines first.

Stale context:
- If an existing note references a retired skill, agent, or field, update only the
  obsolete name (or add one `stale:` line naming the item and its replacement). Keep every
  unresolved caveat and approval boundary the note carried.
- Never edit Zone B during a checkpoint. If Zone B mentions retired components, add a
  `stale:` line to `notes` and tell the user to update it via `/init-research`.

Example:

```yaml
current_phase: revision
active_agent: null
last_skill_run: revise
last_run_id: 2026-09-01T10-12-03_a1b2c3d4
recent_artifacts:
  - docs/paper/main/review-1.md
  - docs/paper/main/changelog.md
last_paper_id: main
active_codex_task: null
next_action: "Run /peer-review main to check the revised draft."
notes: |
  Review 1 major findings addressed; changelog has the details.
  Calibration failure for the sensitivity test is reported descriptively; keep it in main text.
  stale: Zone B lists agent `figure-reviewer`; replaced by static-figure-review in /analyze-results.
```
