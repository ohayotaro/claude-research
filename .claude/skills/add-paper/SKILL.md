---
name: add-paper
description: Register a new paper variant in a research repo that already produces a paper. Validates the slug, asks for title/venue/format/derived_from, appends to Zone B `papers:`, and scaffolds docs/paper/<paper_id>/.
when_to_use: When the user wants to split off a workshop/short paper, journal extension, or any second paper from the same research substrate. Required before any other paper-skill will operate on the new paper_id.
inputs:
  - <paper_id> as positional argument (required)
  - CLAUDE.md Zone B `papers:` registry (read + appended)
  - CLAUDE.md Zone B root `paper_format` / `target_venue` (read as defaults)
outputs:
  - CLAUDE.md Zone B (papers: appended)
  - docs/paper/<paper_id>/draft.md or docs/paper/<paper_id>/main.tex (placeholder)
  - docs/paper/<paper_id>/changelog.md (header line)
delegated_agent: orchestrator (no subagent)
next_skill: /write-paper <paper_id>
---

# /add-paper

Adds a new paper to the registry. The first paper in any repo is created by `/init-research`; subsequent papers are created here.

## Steps for the orchestrator

1. **Pre-flight.**
   - Zone B `status` must be `initialized`. If not, abort and suggest `/init-research`.
   - The positional `<paper_id>` argument is required. If omitted, AskUserQuestion for it.

2. **Validate the slug** per `.claude/rules/multi-paper.md` §1:
   - Regex `^[a-z0-9][a-z0-9-]{0,31}$`.
   - Not in the reserved denylist (`submissions`, `figures`, `_template`, `template`, `assets`, `release`, `releases`, `latest`, `current`, `.`, `..`, Windows device names, `-r<digits>` suffix).
   - Not already present in Zone B `papers:` (uniqueness).
   On any failure, surface a precise reason in Japanese and abort. Do NOT normalize-and-continue; reject typos loudly.

3. **Filesystem state check** per `.claude/rules/multi-paper.md` §5.1. If state D (ambiguous) or E (orphan registry entry) is detected, abort and surface the issue.

4. **Run the questionnaire** via `AskUserQuestion` (Japanese):
   - 論文タイトル（title） — free text; null if undecided.
   - 想定投稿先（venue） — free text; default = root `target_venue` from Zone B.
   - フォーマット（paper_format） — `markdown_bibtex` (default = root paper_format) / `latex`.
   - 派生元の paper_id（derived_from） — optional. If provided, must reference another id already in `papers:`. This is a weak lineage hint only — no files are copied or inherited.

5. **Append to Zone B** `papers:`:
   ```yaml
   - id: <paper_id>
     title: <title or null>
     venue: <venue or null>
     paper_format: <paper_format>
     status: drafting
     derived_from: <derived_from or null>
   ```
   Rewrite Zone B between the `<!-- ZONE_B_BEGIN -->` / `<!-- ZONE_B_END -->` markers. Preserve all other Zone B fields. Do not touch Zone A or Zone C.

6. **Scaffold the paper directory**:
   - `docs/paper/<paper_id>/` (mkdir).
   - If `paper_format == markdown_bibtex`: `docs/paper/<paper_id>/draft.md` with the front matter from `paper-writer` agent's contract (include `paper_id: <paper_id>`).
   - If `paper_format == latex`: `docs/paper/<paper_id>/main.tex` with a minimal preamble + `\bibliography{../../references}`.
   - `docs/paper/<paper_id>/changelog.md` with a single header line: `# Changelog — <paper_id>`.
   Do NOT scaffold `submissions/`, `review-*.md`, or `rebuttal.md`; they are created on demand by `/prepare-submission`, `/peer-review`, `/revise`.

7. **Update Zone C** `last_paper_id: <paper_id>` (hint only).

8. **Report** to the user (Japanese):
   - The new entry's id / title / venue / format / derived_from.
   - The scaffolded path.
   - Suggested next: `/write-paper <paper_id>`.

## Idempotence

- Re-running with an existing `paper_id` is rejected (uniqueness violation). To edit an existing entry's title/venue/format, the user edits Zone B directly or re-runs the questionnaire after first removing the entry (manual step).

## Hard rules

- **Never silently mutate an existing entry.** This skill only appends.
- **Never bypass slug validation.** Typos in `paper_id` are filesystem mistakes that compound; reject early.
- **Never copy content from `derived_from`.** It is a metadata pointer only. Users who want to seed an introduction from another paper should `cp` it manually.
- **Do not auto-invoke `/write-paper`.** This skill ends with a recommendation; the user runs the next skill.

## Examples

| User says (Japanese) | Args |
|---|---|
| "ワークショップ版を別 paper として追加して" | `/add-paper workshop-neurips26` |
| "派生で short paper 作りたい、main を派生元に" | `/add-paper short-aaai26` then questionnaire sets `derived_from: main` |
