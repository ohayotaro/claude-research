---
name: checkpoint
description: Persist current progress, recent artifacts, and next action into CLAUDE.md Zone C. Run before ending a session.
when_to_use: At natural pauses, before /exit, or when handing off to a future session.
inputs:
  - Current session state (skills run, artifacts produced)
outputs:
  - CLAUDE.md Zone C updated
delegated_agent: orchestrator (no subagent)
next_skill: any
---

# /checkpoint

## Steps for the orchestrator

1. **Summarize this session** in 2–4 bullets:
   - Skills executed.
   - Artifacts produced (file paths).
   - Decisions made (especially methodology lock-ins or scope changes).
2. **Determine current phase** by looking at which research notes are populated.
3. **Determine next action** by consulting the **research pipeline** order (this skill, `/checkpoint`, is the session-handoff layer and is not part of the research progression itself):
   - lit-review → identify-gaps → generate-hypothesis → design-experiment → run-experiment → analyze-results → review-figures → discuss-results → write-paper → peer-review → revise.
4. **Write Zone C** by replacing content between `<!-- ZONE_C_BEGIN -->` and `<!-- ZONE_C_END -->`. Format:

```yaml
current_phase: <phase>
active_agent: <last delegate or null>
last_skill_run: <name>
last_run_id: <run_id or null>
recent_artifacts:
  - <path1>
  - <path2>
last_paper_id: <paper_id last operated on, or null>
next_action: "<one-line user-facing instruction>"
notes: |
  <2–4 line free-text — decisions, blockers, parallel tracks>
```

`last_paper_id` is a **hint only**. Skills MUST NOT use it as a silent default — confirm with the user per `.claude/rules/multi-paper.md` §4. It may be surfaced in prompts (e.g. "前回は <id> を編集していました — 続けますか？") to reduce friction.

5. **Report** to user (Japanese): summary of what was saved, including which paper was last touched if applicable.
