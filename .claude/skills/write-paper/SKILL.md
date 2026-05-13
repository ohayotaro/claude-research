---
name: write-paper
description: Assemble the IMRaD draft from research notes. Markdown+BibTeX or LaTeX per the resolved paper's paper_format.
when_to_use: After /discuss-results, or to revise the draft after edits to the research notes.
inputs:
  - <paper_id> as optional positional argument (resolution per .claude/rules/multi-paper.md §4)
  - docs/research/{lit-review,methodology,analysis,discussion,hypotheses}.md
  - CLAUDE.md Zone B `papers:` registry + `output_language.paper`
outputs:
  - docs/paper/<paper_id>/draft.md (markdown_bibtex) or docs/paper/<paper_id>/main.tex (latex)
  - docs/paper/<paper_id>/changelog.md (appended)
delegated_agent: paper-writer
next_skill: /peer-review <paper_id>
---

# /write-paper

## Steps for the orchestrator

1. **Resolve paper_id** per `.claude/rules/multi-paper.md` §4.
   - Run the filesystem state check (§5.1) first. If state A (clean legacy) is detected, drive the lazy migration before proceeding.
   - If the user passed an unknown `paper_id`, run the `/add-paper` flow inline (or delegate) and append the registry entry before any draft is written.
   - If `paper_id` is omitted, confirm the selection with the user even when only one entry exists. Show the registry hint (Japanese): "登録 paper: <id> (<title or untitled>) — これに書きますか？".

2. **Pre-flight.** All five research notes (`lit-review.md`, `hypotheses.md`, `methodology.md`, `analysis.md`, `discussion.md`) exist and are non-trivial (have at least one `##` section beyond the header). Abort with the missing file name(s) and the skill that produces them otherwise.

3. **Look up the resolved paper's `paper_format`** from Zone B `papers[id == <paper_id>].paper_format`. Do NOT fall back to the root `paper_format`. If the per-paper field is missing, that is a registry integrity issue — abort and suggest editing Zone B.

4. **Launch** `paper-writer` with `paper_id` and resolved format in the delegation prompt. The agent assembles into:
   - `docs/paper/<paper_id>/draft.md` if `markdown_bibtex`
   - `docs/paper/<paper_id>/main.tex` if `latex`

5. **Citation sanity check.** The `citation-guard` hook runs on every Write/Edit; if it warns, the agent must fix before declaring done.

6. **Contribution-claim check.** Every contribution claim in the introduction maps to a results subsection. Ask `paper-writer` to flag any unmatched claim.

7. **Word count vs target.** Compare against the resolved paper's `venue` (Zone B `papers[id == <paper_id>].venue`), NOT the root `target_venue`. If over by > 10%, ask the writer to tighten.

8. **Update changelog.** Verify the writer appended to `docs/paper/<paper_id>/changelog.md`.

9. **Update Zone B status** for this paper: set `papers[id == <paper_id>].status: drafting` (or leave as-is if already past drafting).

10. **Update Zone C**: `current_phase: writing`, `last_paper_id: <paper_id>`, `next_action: "Run /peer-review <paper_id>"`.

## Hard rules

- The resolved `paper_id` MUST be confirmed with the user (or explicitly provided by them) before any file is written. Silent auto-selection is forbidden, even when the registry has one entry. See `.claude/rules/multi-paper.md` §4.1 and §10.
- Never read root-level `paper_format` or `target_venue` at runtime. Use the per-paper values from `papers[id == <paper_id>]`.
- Never touch files under `docs/paper/<other_paper_id>/` while operating on `<paper_id>`.
