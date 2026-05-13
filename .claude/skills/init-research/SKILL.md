---
name: init-research
description: Bootstrap a new research project. Interactively collects domain, theme, RQ, paper format, runtime; writes CLAUDE.md Zone B; scaffolds docs/, src/, data/, notebooks/, tests/. Run this first.
when_to_use: First skill in a fresh project. Also re-runnable to update Zone B.
inputs: User answers via AskUserQuestion (Japanese)
outputs:
  - CLAUDE.md (Zone B updated, including seed papers: [{id: main, ...}])
  - docs/research/{lit-review,gaps,hypotheses,methodology,analysis,discussion}.md (placeholders)
  - docs/paper/main/draft.md or docs/paper/main/main.tex (placeholder for the seed paper)
  - docs/references.bib (empty)
  - src/{experiments,analysis,utils}/__init__.py
  - data/{raw,processed,results}/.gitkeep
  - tests/test_smoke.py
  - notebooks/.gitkeep
  - .claude/paper-template-config.json
delegated_agent: orchestrator (no subagent)
next_skill: /literature-review
---

# /init-research

Initializes a research project from the orchestrator template. The orchestrator runs this directly — no subagent.

## Steps

1. **Read** `CLAUDE.md` and `.claude/logs/setup-status.json` (if present).
2. **Ask the user** (Japanese) for the project parameters via `AskUserQuestion`. Suggested questions and defaults:
   - 研究分野（domain）— free text. Examples: computer-science, biology, social-science.
   - 研究テーマ（theme）— free text, one line.
   - リサーチクエスチョン（RQ）— free text, one sentence. Translate to English internally.
   - サブクエスチョン（sub_questions）— optional, free text list.
   - 既存の仮説があれば（hypotheses）— optional, free text list.
   - 論文出力言語（output_language.paper）— en (default) / ja / other.
   - 論文フォーマット（paper_format）— `markdown_bibtex` (default) / `latex`.
   - 実行環境のPythonバージョン（runtime.python_version）— default 3.12.
   - 想定投稿先（target_venue）— optional.
   - データ機微度（ethics.data_sensitivity）— none / low / medium / high.
   - IRB必要か（ethics.irb_required）— bool.
   - 図表スタイルのデフォルト（viz_preferences.default_profile）— `default` / `publication` / `presentation`. After init, the user can add custom profiles by editing `src/utils/viz.py` `STYLE_PROFILES` and switch by editing this Zone B field. The viz-reviewer agent critiques rendered figures regardless of which profile is chosen.
3. **Build a Zone B YAML** from the answers. Preserve the user's free-text RQ verbatim (Japanese OK in Zone B). Keep `status: initialized`. Always emit a `papers:` registry with one seed entry:
   ```yaml
   papers:
     - id: main
       title: null
       venue: <root target_venue from the answers, or null>
       paper_format: <root paper_format from the answers>
       status: drafting
       derived_from: null
   ```
   The root-level `paper_format` and `target_venue` are kept as init-time defaults (per `.claude/rules/multi-paper.md` §3.2). Runtime resolution always reads `papers[id == <paper_id>]`, never the root.
4. **Write Zone B** by replacing the content between `<!-- ZONE_B_BEGIN -->` and `<!-- ZONE_B_END -->` in `CLAUDE.md`. Do not touch Zone A or Zone C.
5. **Scaffold directories** (idempotent):
   ```
   docs/research/
   docs/paper/
   src/experiments/  src/analysis/  src/utils/
   data/raw/  data/processed/  data/results/
   notebooks/
   tests/
   ```
6. **Create placeholder files** (only if they do not exist):
   - `docs/research/lit-review.md` — header only.
   - `docs/research/gaps.md`, `hypotheses.md`, `methodology.md`, `analysis.md`, `discussion.md` — header only.
   - `docs/references.bib` — empty.
   - If `paper_format == markdown_bibtex`: `docs/paper/main/draft.md` with the front matter from `paper-writer` agent's contract (include `paper_id: main`).
   - If `paper_format == latex`: `docs/paper/main/main.tex` with a minimal article preamble + `\bibliography{../../references}`.
   - `src/experiments/__init__.py`, `src/analysis/__init__.py`, `src/utils/__init__.py` (empty).
   - **Language-scoped starter scripts**: read Zone B `runtime.language` (default `python`) and copy from `.claude/templates/<language>/` to `src/utils/`:
     - For `python`: `repro.py` (reproducibility metadata helper) and `viz.py` (publication-quality matplotlib styling, Okabe-Ito palette, `save_figure`).
     - If `.claude/templates/<language>/` does not exist, fall back to `python/` and warn the user that the orchestrator does not ship native recipes for `<language>` yet (R / Julia / Stata are placeholders for future expansion).
   - `tests/test_smoke.py` — imports each src module to check the package is wired.
   - `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/results/.gitkeep`, `notebooks/.gitkeep`.
7. **Write `.claude/paper-template-config.json`** with `{"default_paper_format": "...", "default_target_venue": "..."}`. This is an init-time default record; runtime path resolution uses Zone B `papers:` instead (see `.claude/rules/multi-paper.md`).
8. **Append** to `.claude/logs/init-research.log` an ISO-stamped record of the run.
9. **Update Zone C** of `CLAUDE.md` to set `current_phase: literature` and `next_action: "Run /literature-review"`.
10. **Report** to the user (Japanese) a summary: paths created, next suggested skill.

## Idempotence rules

- Re-running `/init-research` is allowed and **only** rewrites Zone B and `paper-template-config.json`. It does **not** overwrite any existing `docs/research/*.md` content (only creates them if absent).
- It does **not** touch existing files under `src/`, `data/`, `tests/`.
- It does **not** modify an existing `papers:` registry with more than one entry — only seeds it when absent. To add additional papers, use `/add-paper`.

## Hard rules

- Do not delete user content. If a placeholder already has more than the header, leave it alone.
- Do not change Zone A.
- The `git_clean` check in any later experiment requires this repo to be a git repo. After scaffold, suggest `git init && git add -A && git commit -m "init research scaffold"` — but do not run it without user confirmation.

## Source of starter scripts

Starter scripts live under `.claude/templates/<language>/` and are copied
verbatim. The template repo tracks them as real source files so they can be
linted and tested without inline copies in this SKILL.md. See
`.claude/templates/README.md` for the full structure and the contract for
adding a new language.

For `runtime.language: python`:

| Copy from | Copy to |
|---|---|
| `.claude/templates/python/repro.py` | `src/utils/repro.py` |
| `.claude/templates/python/viz.py`   | `src/utils/viz.py` |

For other languages, look for `.claude/templates/<language>/`. If it does
not exist, fall back to the python recipe and warn the user.
