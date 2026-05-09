---
name: prepare-submission
description: Package the paper draft for submission to a target venue. Verifies length, format, anonymization, supplementary material, and produces a submission bundle under docs/paper/submissions/<venue>-<round>/.
when_to_use: After the draft has passed at least one /peer-review round and the user is ready to submit (or transfer to a venue's submission system).
inputs:
  - docs/paper/draft.md or docs/paper/main.tex (required)
  - docs/references.bib (required)
  - data/results/<run_id>/figures/ (optional — for figure files referenced in the draft)
  - CLAUDE.md Zone B (target_venue, paper_format, output_language.paper)
outputs:
  - docs/paper/submissions/<venue>-<round>/  (self-contained bundle)
  - docs/paper/submissions/<venue>-<round>/manifest.json (file inventory + checks)
  - docs/paper/submissions/<venue>-<round>/checklist.md (venue requirements + status)
delegated_agent: paper-writer (with optional viz-reviewer pass on referenced figures)
next_skill: any (typically post-submission /respond-reviewers when reviews come back)
---

# /prepare-submission

Produces a clean, venue-compliant submission bundle from the current draft. Performs mechanical checks (length, citation completeness, figure embedding) and produces a checklist of requirements that need a human eye (anonymization, conflicts of interest, ethics statement).

## Steps for the orchestrator

1. **Pre-flight.**
   - Draft exists (`docs/paper/draft.md` or `docs/paper/main.tex`).
   - At least one `docs/paper/review-<n>.md` exists with verdict `accept` / `minor revision` (warn loudly if all reviews are `major revision` / `reject`).
   - `CLAUDE.md` Zone B has `target_venue` set; if not, ask the user.
2. **Determine bundle target.** Slugify the venue: `neurips-2026` → `docs/paper/submissions/neurips-2026-r1/`. Round increments: `r1`, `r2`, ... If a folder for the same venue + round already exists, ask before overwriting.
3. **Launch** `paper-writer` in **submission mode**. The agent:
   - Re-reads the draft and venue requirements (from a known list of common venues, or the user-supplied URL).
   - Performs mechanical checks:
     - **Length**: word count vs venue limit; page count if LaTeX.
     - **Cite-key resolution**: every `[@key]` resolves in `references.bib`.
     - **Contribution-claim ↔ result match**: every claim in introduction has a result subsection.
     - **Figure embedding**: every referenced figure file exists; resolution ≥ 300 dpi for raster.
     - **References**: BibTeX validates; mark preprints; flag retracted papers (via Gemini if available).
     - **Anonymization**: scan for the user's name, affiliation, GitHub handle, "as we showed in [@selfcite]" patterns.
     - **Required statements**: ethics, data availability, code availability, funding, author contributions (per venue).
4. **Optional figure pass**: if any figure was modified since the last `/review-figures`, suggest a fresh `/review-figures` before the bundle is finalized.
5. **Assemble the bundle**:
   - Copy / convert the draft into the bundle directory under the venue's expected layout (Markdown stays as `.md` + `references.bib`; LaTeX gets `main.tex` + `.bib` + figure files).
   - Embed all referenced figures from `data/results/<run_id>/figures/`.
   - Generate `manifest.json` listing every file with size + sha256.
   - Generate `checklist.md` with: venue requirements (left column), status (auto-checked / needs-human / not-applicable), and per-row pointer to the file.
6. **Surface to user** (Japanese, polite, no emojis):
   - Bundle path.
   - Auto-checks passed / failed counts.
   - Items needing human review (anonymization, conflicts, etc.).
   - Suggested next: human-in-the-loop review of the checklist before upload.
7. **Update Zone C**: `current_phase: submission`, `last_skill_run: prepare-submission`, `next_action: "Review checklist.md, then submit to <venue>"`.

## Hard rules

- **Never auto-submit.** This skill produces a bundle; the human uploads it. There is no `--upload` flag.
- **Never mutate the original draft.** The bundle is a copy / build artifact under `submissions/`. The source of truth stays at `docs/paper/draft.md` (or `main.tex`).
- **Anonymization is advisory, not authoritative.** The skill flags suspicious tokens; the human is responsible for true blind compliance.
- If a previous bundle exists for the same `<venue>-<round>`, ask before overwriting (keep the old one for diff purposes).
