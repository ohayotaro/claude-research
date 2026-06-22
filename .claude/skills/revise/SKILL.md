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
1. Address blocker/major findings first.
2. Record substantive changes in the changelog.
3. Do not weaken limitations or reframe exploratory findings as confirmatory.
4. Re-run citation and result-ID traceability checks.
