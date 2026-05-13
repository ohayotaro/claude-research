---
name: release-artifacts
description: Prepare code and data for archival release (Zenodo / OSF / Dryad / institutional repo). Validates licenses, generates a data card, packages a citable archive, and emits the metadata needed for DOI registration. Repo-level release — one deposit may cover one or more papers in the same repo.
when_to_use: After a paper is accepted (or alongside preprint posting). Reproducibility stops at local metadata.json without this skill — public release closes the loop.
inputs:
  - [--papers=<id1>,<id2>,...] optional comma-separated list of paper_ids to include (default: ask the user)
  - [--tag=<release-tag>] optional release tag (default: v<major>.<minor> or release-<ISO-date>)
  - The repo as committed (state to be archived)
  - CLAUDE.md Zone B `papers:`, `ethics.data_sensitivity`
  - data/raw/<file>.README.md sidecars (provenance per dataset)
outputs:
  - docs/release/<release-tag>/  (manifest, datacard, license, citation — FLAT, not paper-nested)
  - docs/release/<release-tag>/CITATION.cff
  - docs/release/<release-tag>/datacard.md
  - docs/release/<release-tag>/manifest.json (includes "papers": [<id>, ...])
  - docs/release/<release-tag>/zenodo.json (Zenodo deposition payload)
delegated_agent: orchestrator + paper-writer (for citation text); literature-reviewer (for related-work pointers in datacard)
next_skill: any (typically external upload to Zenodo/OSF after this)
---

# /release-artifacts

Closes the reproducibility loop by producing a release-ready bundle and the metadata that Zenodo / OSF / Dryad / a institutional archive expects. Does **not** upload — the human runs the upload from the generated bundle so the DOI lands in their account.

A release is **repo-level**: a single deposit may cite one or more papers from this repository, since archives typically issue one DOI per archive even when multiple artefacts are covered.

## Steps for the orchestrator

1. **Resolve which papers to include.**
   - If `--papers=<id1>,<id2>` is provided, validate each id against Zone B `papers:` (each must exist).
   - Else AskUserQuestion presenting the full registry with id / title / status; user picks ≥ 1.
   - If exactly one paper exists in the registry and `--papers` is omitted, still confirm with the user (no silent default).

2. **Pre-flight.**
   - At least one `data/results/<run_id>/` exists with a complete `metadata.json` (otherwise nothing to archive).
   - For each selected `paper_id`: `docs/paper/<paper_id>/draft.md` (or `main.tex` per `papers[id == <paper_id>].paper_format`) exists — releases must be paired with at least one paper.
   - `CLAUDE.md` Zone B `ethics.data_sensitivity`: if `medium` / `high`, abort with a clear message — sensitive data needs an IRB-approved release plan, not this generic skill.

3. **Determine release tag.** Use `--tag` if provided; else default to `v<major>.<minor>` if the user supplies a version, else `release-<ISO-date>`. Check git tags for collisions; suggest a bump. Releases live FLAT under `docs/release/<tag>/` — they are not nested by `paper_id`.

4. **License check.**
   - Repo root must have a LICENSE file. If missing, ask the user which license to add (default: MIT for code; CC-BY-4.0 for data; CC0 for raw data without privacy concerns).
   - Each `data/raw/<file>.README.md` sidecar must declare a license / source license. Flag any missing.

5. **Datacard generation** (`datacard.md`). Sections:
   - Purpose / overview.
   - Composition (datasets, sizes, formats).
   - Provenance per dataset (from raw README sidecars).
   - Collection methodology.
   - Preprocessing applied (link to `src/` scripts).
   - Papers covered by this release (list of `paper_id`, title, venue, status from Zone B).
   - Recommended uses / known biases / limitations.
   - License.
   - Citation (cff format snippet).

6. **Code-release packaging.**
   - Generate `manifest.json` with sha256 of every file under `src/`, `tests/`, `data/processed/`, `data/results/<run_id>/`, and `docs/paper/<paper_id>/` for each selected `paper_id`.
   - Top level of `manifest.json` includes `"papers": ["<id1>", "<id2>", ...]` so downstream tooling can resolve which papers a deposit covers.
   - Exclude `data/raw/` if `data_sensitivity != none` (privacy-preserving release); include otherwise.
   - Run `/lint` once to confirm green; record the result in the manifest.

7. **CITATION.cff.**
   - Author block from a `CITATION.cff` template the user fills, OR auto-extract from git log + Zone B if Zone B has author info.
   - Title: if one paper is selected, use its title; if multiple, use the repo theme from Zone B and list paper titles under `references`.
   - Version = release tag.
   - DOI placeholder (filled after Zenodo registration).
   - `references:` block lists each selected paper's title / venue / status.

8. **Zenodo deposition payload** (`zenodo.json`).
   - Pre-filled with title, description (paper abstract — concatenated if multiple papers, with a divider), creators, keywords (from Zone B), license, related identifiers (paper DOIs when known, one per selected paper).
   - User uploads the bundle to Zenodo and pastes the resulting DOI back into `CITATION.cff`.

9. **Surface to user** (Japanese, polite, no emojis):
   - Bundle path: `docs/release/<release-tag>/`.
   - Selected papers (id / title).
   - License decisions made.
   - Items needing human review (DOI placeholder, sensitive data exclusions).
   - Step-by-step Zenodo / OSF upload instructions inline (the skill does not auto-upload).

10. **Update Zone C**: `current_phase: release`, `last_skill_run: release-artifacts`, `next_action: "Upload bundle to Zenodo, then update CITATION.cff with the resulting DOI"`. Set `last_paper_id` to the first selected paper id (or null if multiple).

## Hard rules

- **Releases are repo-level, flat-layout.** Path is `docs/release/<tag>/`, NOT `docs/release/<paper_id>/<tag>/`. This supports combined deposits covering multiple papers — the deposit cites all of them.
- **Each `paper_id` in the deposit MUST exist in Zone B `papers:` AND have a draft.** Releasing for an unregistered or empty paper is rejected.
- **Never include `data/raw/` in a release if `ethics.data_sensitivity` ≠ `none`.** Privacy-preserving release excludes raw data and references the original source instead.
- **Never auto-upload.** Bundle is local; the user runs the upload step so the deposit lands in their identity.
- **License must be declared.** Cannot proceed without a LICENSE file at repo root and license fields in each `data/raw/<file>.README.md`.
- **Citation must be machine-readable.** `CITATION.cff` is mandatory; plain-text citation alone is insufficient for archival systems.
- **Per-paper format precedence.** When manifesting paper files, use each `papers[id == <id>].paper_format` independently. Never assume one format applies to all selected papers.
