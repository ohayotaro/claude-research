---
name: identify-gaps
description: Convert the literature review into concrete research gaps and open questions.
when_to_use: After /literature-review or /extend-literature.
context: fork
agent: scientific-author
---

# /identify-gaps

Use `scientific-author` mode `gap-analysis`.

Inputs:
- `docs/research/lit-review.md`
- `docs/references.bib`
- Zone B research question and constraints

Output:
- `docs/research/gaps.md`

Workflow:
1. Identify gaps grounded in cited literature, not novelty assertions alone.
2. Distinguish empirical, methodological, theoretical, dataset, and reporting gaps.
3. State what evidence would close each gap.
4. Update Zone C to `current_phase: gap` and next action `/generate-hypothesis`.
