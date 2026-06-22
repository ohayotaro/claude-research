---
name: ask-codex
description: Ask a one-off read-only Codex reviewer question without changing repository files outside the task directory.
when_to_use: For strict logic, statistics, code, or reproducibility checks that do not require a full workflow.
---

# /ask-codex

Use `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.

Rules:
- Reviewer mode is fresh-context and read-only.
- The brief must include exact artifacts and the question being reviewed.
- The answer is advisory until the Research Lead accepts or assigns follow-up work.
- Do not use this skill for code implementation; use `/run-experiment`, `/analyze-results`, or a dedicated Codex builder task.
