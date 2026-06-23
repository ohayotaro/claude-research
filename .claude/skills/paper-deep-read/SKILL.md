---
name: paper-deep-read
description: Produce a structured deep-read note for one paper, URL, DOI, or local PDF.
when_to_use: When one source needs careful extraction before synthesis or rebuttal.
context: fork
agent: scientific-author
---

# /paper-deep-read

Use `scientific-author` mode `paper-deep-read`.

Inputs:
- One DOI, URL, citation, or local PDF path.
- The research question and any extraction rubric from the Research Lead.

Output:
- `docs/research/papers/<slug>.md`
- Optional new or corrected entry in `docs/references.bib`

Workflow:
1. Verify source identity, venue, year, authors, and cite key.
2. Extract claims, methods, data, measures, results, limitations, and relevance.
3. Mark unverified or inaccessible details explicitly.
4. Do not invent quotations, page numbers, identifiers, or numerical results.
