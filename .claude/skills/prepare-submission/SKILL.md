---
name: prepare-submission
description: Package the resolved paper's draft for submission to a target venue. Verifies length, format, anonymization, supplementary material, and produces a submission bundle under docs/paper/<paper_id>/submissions/<venue>-<round>/.
when_to_use: After the draft has passed at least one /peer-review round and the user is ready to submit (or transfer to a venue's submission system).
inputs:
  - <paper_id> as required positional argument (resolution per .claude/rules/multi-paper.md §4; ambiguity must be resolved interactively)
  - [--venue=<slug>] optional one-shot override (does NOT mutate Zone B)
  - docs/paper/<paper_id>/draft.md or docs/paper/<paper_id>/main.tex (required)
  - docs/references.bib (required)
  - data/results/<run_id>/figures/ (optional — for figure files referenced in the draft)
  - CLAUDE.md Zone B `papers[id == <paper_id>]` (venue, paper_format), `output_language.paper`
outputs:
  - docs/paper/<paper_id>/submissions/<venue>-<round>/  (self-contained bundle)
  - docs/paper/<paper_id>/submissions/<venue>-<round>/manifest.json (file inventory + checks)
  - docs/paper/<paper_id>/submissions/<venue>-<round>/checklist.md (venue requirements + status)
delegated_agent: paper-writer (with optional viz-reviewer pass on referenced figures)
next_skill: any (typically post-submission /respond-reviewers when reviews come back)
---

# /prepare-submission

Produces a clean, venue-compliant submission bundle from the resolved paper's draft. Performs mechanical checks (length, citation completeness, figure embedding) and produces a checklist of requirements that need a human eye (anonymization, conflicts of interest, ethics statement).

## Steps for the orchestrator

1. **Resolve paper_id** per `.claude/rules/multi-paper.md` §4. `paper_id` is required; do not auto-select silently. If `paper_id` is omitted, AskUserQuestion to pick.

2. **Determine venue.** Precedence:
   - `--venue=<slug>` argument if provided → one-shot override; Zone B is NOT mutated.
   - Else `papers[id == <paper_id>].venue` from Zone B.
   - Else ask the user. If the user wants the answer persisted, they must edit Zone B (or re-run `/add-paper` for a fresh entry).

3. **Pre-flight.**
   - Draft exists at `docs/paper/<paper_id>/{draft.md|main.tex}` per `papers[id == <paper_id>].paper_format`.
   - At least one `docs/paper/<paper_id>/review-<n>.md` exists with verdict `accept` / `minor revision` (warn loudly if all reviews are `major revision` / `reject`).
   - A venue has been resolved (step 2).

4. **Determine bundle target.** Slugify the venue: `neurips-2026` → `docs/paper/<paper_id>/submissions/neurips-2026-r1/`. Round increments: `r1`, `r2`, ... If a folder for the same venue + round already exists, ask before overwriting.

5. **Launch** `paper-writer` in **submission mode** with `paper_id` and resolved venue. The agent:
   - Re-reads the draft and venue requirements (from a known list of common venues, or the user-supplied URL).
   - Performs mechanical checks:
     - **Length**: word count vs venue limit; page count if LaTeX.
     - **Cite-key resolution**: every `[@key]` resolves in `references.bib`.
     - **Contribution-claim ↔ result match**: every claim in introduction has a result subsection.
     - **Figure embedding**: every referenced figure file exists; resolution ≥ 300 dpi for raster.
     - **References**: BibTeX validates; mark preprints; flag retracted papers (via Gemini if available).
     - **Anonymization**: scan for the user's name, affiliation, GitHub handle, "as we showed in [@selfcite]" patterns.
     - **Required statements**: ethics, data availability, code availability, funding, author contributions (per venue).

6. **Optional figure pass**: if any figure was modified since the last `/review-figures`, suggest a fresh `/review-figures` before the bundle is finalized.

7. **Assemble the bundle**:
   - Copy / convert the resolved paper's draft into `docs/paper/<paper_id>/submissions/<venue>-<round>/` under the venue's expected layout (Markdown stays as `.md` + `references.bib`; LaTeX gets `main.tex` + `.bib` + figure files).
   - Embed all referenced figures from `data/results/<run_id>/figures/`.
   - Generate `manifest.json` listing every file with size + sha256. Include `paper_id` and `venue` at the top level for downstream tooling.
   - Generate `checklist.md` with: venue requirements (left column), status (auto-checked / needs-human / not-applicable), and per-row pointer to the file.

8. **Surface to user** (Japanese, polite, no emojis):
   - Paper id and bundle path.
   - Auto-checks passed / failed counts.
   - Items needing human review (anonymization, conflicts, etc.).
   - Suggested next: human-in-the-loop review of the checklist before upload.

9. **Update Zone B status** for this paper: `papers[id == <paper_id>].status: submitted` (after the user confirms upload, not at bundle creation).

10. **Update Zone C**: `current_phase: submission`, `last_paper_id: <paper_id>`, `last_skill_run: prepare-submission`, `next_action: "Review checklist.md, then submit to <venue>"`.

## Hard rules

- **`--venue` is a one-shot override.** It does NOT mutate Zone B `papers[].venue`. To persistently change a paper's venue, the user must edit Zone B directly or re-run `/add-paper` for a new entry.
- **Never auto-submit.** This skill produces a bundle; the human uploads it. There is no `--upload` flag.
- **Never mutate the original draft.** The bundle is a copy / build artifact under `docs/paper/<paper_id>/submissions/`. The source of truth stays at `docs/paper/<paper_id>/draft.md` (or `main.tex`).
- **Anonymization is advisory, not authoritative.** The skill flags suspicious tokens; the human is responsible for true blind compliance.
- If a previous bundle exists for the same `<venue>-<round>` under the same `paper_id`, ask before overwriting (keep the old one for diff purposes).
- Use per-paper `paper_format` from `papers[id == <paper_id>]`. Never read root `paper_format` at runtime.
