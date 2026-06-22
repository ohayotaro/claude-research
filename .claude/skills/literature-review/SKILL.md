---
name: literature-review
description: Rewrite docs/research/lit-review.md from primary-source evidence for the current research question.
when_to_use: After /init-research or when the literature review needs a full refresh.
context: fork
agent: scientific-author
---

# /literature-review

Use `scientific-author` mode `literature-synthesis`.

Inputs:
- `CLAUDE.md` Zone B research question, sub-questions, domain, and target venue.
- Seed papers, PDFs, DOI/URL lists, or constraints supplied by the user.
- Existing `docs/references.bib` if present.

Workflow:
1. Confirm the project is initialized and define search scope with the Research Lead.
2. Ask the author to locate and verify primary sources using local files, WebSearch, and WebFetch.
3. Write `docs/research/lit-review.md` and update `docs/references.bib`.
4. Require precise cite keys for external factual claims. Do not rely on page summaries for publishable claims.
5. Update Zone C to `current_phase: literature`, `last_skill_run: literature-review`, and next action `/identify-gaps`.

This skill rewrites the literature review. For append-only coverage of a subtopic, use `/extend-literature`.
