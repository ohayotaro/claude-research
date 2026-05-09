---
name: release-artifacts
description: Prepare code and data for archival release (Zenodo / OSF / Dryad / institutional repo). Validates licenses, generates a data card, packages a citable archive, and emits the metadata needed for DOI registration.
when_to_use: After a paper is accepted (or alongside preprint posting). Reproducibility stops at local metadata.json without this skill — public release closes the loop.
inputs:
  - The repo as committed (state to be archived)
  - CLAUDE.md Zone B (target_venue, ethics.data_sensitivity)
  - data/raw/<file>.README.md sidecars (provenance per dataset)
outputs:
  - docs/release/<release-tag>/  (manifest, datacard, license, citation)
  - docs/release/<release-tag>/CITATION.cff
  - docs/release/<release-tag>/datacard.md
  - docs/release/<release-tag>/manifest.json
  - docs/release/<release-tag>/zenodo.json (Zenodo deposition payload)
delegated_agent: orchestrator + paper-writer (for citation text); literature-reviewer (for related-work pointers in datacard)
next_skill: any (typically external upload to Zenodo/OSF after this)
---

# /release-artifacts

Closes the reproducibility loop by producing a release-ready bundle and the metadata that Zenodo / OSF / Dryad / a institutional archive expects. Does **not** upload — the human runs the upload from the generated bundle so the DOI lands in their account.

## Steps for the orchestrator

1. **Pre-flight.**
   - At least one `data/results/<run_id>/` exists with a complete `metadata.json` (otherwise nothing to archive).
   - `docs/paper/draft.md` (or `main.tex`) exists — release should be paired with a paper.
   - `CLAUDE.md` Zone B `ethics.data_sensitivity`: if `medium` / `high`, abort with a clear message — sensitive data needs an IRB-approved release plan, not this generic skill.
2. **Determine release tag.** Format: `v<major>.<minor>` if user provides a paper version, else `release-<ISO-date>`. Check git tags for collisions; suggest a bump.
3. **License check.**
   - Repo root must have a LICENSE file. If missing, ask the user which license to add (default: MIT for code; CC-BY-4.0 for data; CC0 for raw data without privacy concerns).
   - Each `data/raw/<file>.README.md` sidecar must declare a license / source license. Flag any missing.
4. **Datacard generation** (`datacard.md`). Sections:
   - Purpose / overview.
   - Composition (datasets, sizes, formats).
   - Provenance per dataset (from raw README sidecars).
   - Collection methodology.
   - Preprocessing applied (link to `src/` scripts).
   - Recommended uses / known biases / limitations.
   - License.
   - Citation (cff format snippet).
5. **Code-release packaging.**
   - Generate `manifest.json` with sha256 of every file under `src/`, `tests/`, `data/processed/`, `data/results/<run_id>/`.
   - Exclude `data/raw/` if `data_sensitivity != none` (privacy-preserving release); include otherwise.
   - Run `/lint` once to confirm green; record the result in the manifest.
6. **CITATION.cff.**
   - Author block from a `CITATION.cff` template the user fills, OR auto-extract from git log + Zone B if Zone B has author info.
   - Title from the paper draft.
   - Version = release tag.
   - DOI placeholder (filled after Zenodo registration).
7. **Zenodo deposition payload** (`zenodo.json`).
   - Pre-filled with title, description (paper abstract), creators, keywords (from Zone B), license, related identifiers (paper DOI when known).
   - User uploads the bundle to Zenodo and pastes the resulting DOI back into `CITATION.cff`.
8. **Surface to user** (Japanese, polite, no emojis):
   - Bundle path: `docs/release/<release-tag>/`.
   - License decisions made.
   - Items needing human review (DOI placeholder, sensitive data exclusions).
   - Step-by-step Zenodo / OSF upload instructions inline (the skill does not auto-upload).
9. **Update Zone C**: `current_phase: release`, `last_skill_run: release-artifacts`, `next_action: "Upload bundle to Zenodo, then update CITATION.cff with the resulting DOI"`.

## Hard rules

- **Never include `data/raw/` in a release if `ethics.data_sensitivity` ≠ `none`.** Privacy-preserving release excludes raw data and references the original source instead.
- **Never auto-upload.** Bundle is local; the user runs the upload step so the deposit lands in their identity.
- **License must be declared.** Cannot proceed without a LICENSE file at repo root and license fields in each `data/raw/<file>.README.md`.
- **Citation must be machine-readable.** `CITATION.cff` is mandatory; plain-text citation alone is insufficient for archival systems.
