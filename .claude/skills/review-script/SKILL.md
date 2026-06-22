---
name: review-script
description: Run a fresh read-only Codex review of experiment or analysis code before execution or publication.
when_to_use: Before running changed scripts or when a technical artifact needs independent review.
---

# /review-script

Use Codex reviewer through `scripts/codex_research.py review`.

Review rubric:
- statistical correctness, leakage, confounding, assumptions, missing data, multiplicity
- reproducibility metadata and deterministic seeds
- test coverage and fixture realism
- ownership boundaries and result-ledger compatibility

Workflow:
1. Create `.claude/tasks/<task-id>/brief.md` with file paths, intended run, methodology, and rubric.
2. Run `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
3. Treat reviewer output as read-only findings; builder or Research Lead applies fixes separately.
