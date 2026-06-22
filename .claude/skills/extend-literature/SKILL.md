---
name: extend-literature
description: Append a focused subtopic survey to the existing literature review without rewriting prior sections.
when_to_use: When a new subtopic, venue thread, or source cluster should be added to the review.
context: fork
agent: scientific-author
---

# /extend-literature

Use `scientific-author` mode `literature-synthesis`.

Inputs:
- Existing `docs/research/lit-review.md`.
- Existing `docs/references.bib`.
- The explicit subtopic and inclusion/exclusion boundaries from the Research Lead.

Workflow:
1. Confirm the subtopic and output heading.
2. Add only a new section or appendix section; do not rewrite existing literature-review prose.
3. Ground every external factual claim in primary-source evidence and valid cite keys.
4. Return unresolved source gaps separately from the appended prose.
