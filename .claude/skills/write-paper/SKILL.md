---
name: write-paper
description: Assemble the IMRaD draft from research notes. Markdown+BibTeX or LaTeX per Zone B paper_format.
when_to_use: After /discuss-results, or to revise the draft after edits to the research notes.
inputs:
  - docs/research/{lit-review,methodology,analysis,discussion,hypotheses}.md
  - CLAUDE.md Zone B (paper_format, target_venue, output_language.paper)
outputs:
  - docs/paper/draft.md (Markdown variant) or docs/paper/main.tex (LaTeX variant)
  - docs/paper/changelog.md (appended)
delegated_agent: paper-writer
next_skill: /peer-review
---

# /write-paper

## Steps for the orchestrator

1. **Pre-flight.** All five research notes (`lit-review.md`, `hypotheses.md`, `methodology.md`, `analysis.md`, `discussion.md`) exist and are non-trivial (have at least one `##` section beyond the header). Abort with the missing file name(s) and the skill that produces them otherwise.
2. **Launch** `paper-writer`. The agent reads Zone B for `paper_format` and assembles accordingly.
3. **Citation sanity check.** The `citation-guard` hook runs on every Write/Edit; if it warns, the agent must fix before declaring done.
4. **Contribution-claim check.** Every contribution claim in the introduction maps to a results subsection. Ask `paper-writer` to flag any unmatched claim.
5. **Word count vs target.** If the venue has a length limit, compare against `target_venue`. If over by > 10%, ask the writer to tighten.
6. **Update changelog.** Verify the writer appended to `docs/paper/changelog.md`.
7. **Update Zone C**: `current_phase: writing`, `next_action: "Run /peer-review"`.
