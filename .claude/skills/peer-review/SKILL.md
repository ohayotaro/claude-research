---
name: peer-review
description: Run a fresh read-only Codex review of manuscript logic, reporting completeness, and evidence alignment.
when_to_use: After a manuscript draft is ready for independent critique.
---

# /peer-review

Use Codex reviewer through `scripts/codex_research.py review`.

Inputs:
- manuscript path
- `docs/references.bib`
- relevant `docs/research/**`
- relevant `data/results/**/analysis.json`

Output:
- `docs/paper/<paper_id>/review-<n>.md`

Workflow:
1. Create a task brief with the manuscript path and review rubric.
2. Run `python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
3. Save the reviewer final message as `docs/paper/<paper_id>/review-<n>.md`.
4. Do not let the reviewer modify files.
