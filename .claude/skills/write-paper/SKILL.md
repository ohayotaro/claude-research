---
name: write-paper
description: Assemble or revise a manuscript from accepted research notes, citations, and reviewed result ledgers.
when_to_use: After discussion is accepted or when a paper needs a major drafting pass.
context: fork
agent: scientific-author
---

# /write-paper

Use `scientific-author` mode `manuscript-drafting`.

Inputs:
- `docs/research/{lit-review,gaps,hypotheses,methodology,analysis,discussion}.md`
- `docs/references.bib`
- relevant `data/results/<run_id>/analysis.json`
- Zone B `papers:` registry and target venue constraints

Output:
- `docs/paper/<paper_id>/draft.md` or `docs/paper/<paper_id>/main.tex`

Workflow:
1. Resolve `paper_id` explicitly; never assume from `last_paper_id` without confirmation.
2. Preserve claim-evidence alignment and result-ID citations.
3. Do not add unsupported novelty, priority, causal, or numerical claims.
4. Run prose traceability checks before handoff.
