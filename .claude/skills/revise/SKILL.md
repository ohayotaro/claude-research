---
name: revise
description: Revise manuscript prose and rebuttal text against review findings while preserving evidence traceability.
when_to_use: After /peer-review or external reviewer comments.
context: fork
agent: scientific-author
---

# /revise

Use `scientific-author` mode `revision-and-rebuttal`.

Inputs:
- current manuscript
- `docs/paper/<paper_id>/review-*.md` or external comments
- `docs/references.bib`
- relevant result ledgers

Outputs:
- revised manuscript
- `docs/paper/<paper_id>/rebuttal.md`
- `docs/paper/<paper_id>/changelog.md`

Workflow:
1. Resolve `paper_id` per multi-paper.md §4 (confirm even with a single registry entry).
2. Address blocker/major findings first.
3. Record substantive changes in the changelog.
4. Do not weaken limitations or reframe exploratory findings as confirmatory.
5. Re-run citation and result-ID traceability checks.
6. Update Zone C with `current_phase: revision` and next action.
