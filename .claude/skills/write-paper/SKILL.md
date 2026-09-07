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
1. Resolve `paper_id` per multi-paper.md §4 (confirm even with a single registry entry). If an unknown `paper_id` is passed, enter the `/add-paper` flow to register it before writing.
2. Produce the editorial brief defined in `scientific-author` (audience, central message, contributions separated from quality-control procedures and limitations, outline, and main/supplement/record destination for each result family) before drafting.
3. Reorganize the accepted evidence around the research question. Do not transcribe research notes or follow development chronology; apply the placement rules in `writing-style.md`.
4. Preserve claim-evidence alignment and result-ID citations.
5. Do not add unsupported novelty, priority, causal, or numerical claims.
6. Run prose traceability checks before handoff.
7. Update Zone C with `current_phase: writing`, `last_paper_id`, and next action.
