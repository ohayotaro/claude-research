---
name: init-research
description: Bootstrap or update project configuration, directories, placeholders, and starter utilities.
when_to_use: First skill in a fresh project; also re-runnable to update Zone B.
---

# /init-research

The Research Lead performs this deterministic workflow directly.

Ask the user in Japanese for:
- domain, theme, research question, optional sub-questions, and optional seed hypotheses
- paper language, paper format, target venue, and initial paper title when known
- runtime language and Python version
- data sensitivity, IRB/ethics needs, and default figure style
- whether to include the visualization helper (`viz.py`) — explain it provides colorblind-safe palettes, multi-format save, and publication/presentation style profiles for matplotlib; skip if the project does not use matplotlib

Write Zone B with:
- `status: initialized`
- a `papers:` registry containing at least `id: main`
- `external_cli.codex` only; ignore and remove obsolete external CLI fields when rewriting Zone B

Scaffold only missing files:
- `docs/research/{lit-review,gaps,hypotheses,methodology,analysis,discussion}.md`
- `docs/references.bib`
- `docs/paper/main/draft.md` or `docs/paper/main/main.tex`
- `src/{experiments,analysis,utils}/__init__.py`
- `repro.py` from `.claude/templates/<language>/`, falling back to Python templates
- `viz.py` from `.claude/templates/<language>/` only if the user opted in
- `data/{raw,processed,results}/.gitkeep`
- `notebooks/.gitkeep`
- `tests/test_smoke.py`
- `.claude/paper-template-config.json`

Idempotence:
- Re-running rewrites Zone B and `.claude/paper-template-config.json` only.
- Do not overwrite existing research notes, paper drafts, source files, data, tests, or notebooks.
- Do not change Zone A.

After initialization, update Zone C to `current_phase: literature` and next action `/literature-review`.
