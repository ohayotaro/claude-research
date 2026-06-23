# `.claude/templates/`

Starter scripts that `/init-research` copies into the user's project on
initialization. Organized by **runtime language** so the orchestrator can
support more than just Python.

## Structure

```
.claude/templates/
  README.md           This file.
  python/             Recipes for Python projects (uv-managed, default).
    repro.py          → src/utils/repro.py   (reproducibility metadata helper — always copied)
    viz.py            → src/utils/viz.py     (matplotlib publication / presentation styling — optional, copied only if user opts in)
  r/                  (not yet shipped — placeholder)
    repro.R           → R/utils/repro.R
    viz.R             → R/utils/viz.R
  julia/              (not yet shipped — placeholder)
    repro.jl
    viz.jl
```

## How `/init-research` selects a recipe

1. Read `CLAUDE.md` Zone B → `runtime.language` (default: `python`).
2. Look for `.claude/templates/<language>/`.
3. Copy each file in that directory to its target path under the user's project (the mapping is documented per-recipe inside the file's docstring).
4. If `.claude/templates/<language>/` does not exist, fall back to `python/` and warn the user that no native recipes for `<language>` are shipped yet.

## Design principles for templates

- **Adapt to user preference, do not impose taste.** Where the template ships defaults, structure them so the user can express preferences declaratively (named profiles in `STYLE_PROFILES`, a Zone B field in `CLAUDE.md`) rather than having to monkey-patch generated code.
- **Three-layer structure**: (1) infrastructure that the rendered figure cannot reveal — e.g. `pdf.fonttype = 42` so vector text remains editable; (2) named profiles as starting points; (3) per-call kwarg overrides. Each layer is overridable from the layer above.
- **Reviewer-aware enforcement.** The orchestrator critiques rendered figures via review agents (`scientific-author` for visual review, Codex reviewer for data-mapping review). Things the reviewer can catch on the rendered output (font choice, colors, spine policy, composition) are treated as preference, not enforcement. Things the reviewer cannot catch (PDF text editability, multi-format save, untitled figures) are enforced.
- **Frameworks-of-the-language, not third-party stacks.** Python recipes use stdlib + matplotlib + numpy because those are in `pyproject.toml`. Avoid pulling in opinionated third-party stacks (Plotly, Polars, etc.) that the user may not want.
- **Generic fallback chains.** Don't pin OS-specific resources. Example: font families use `["DejaVu Serif", "Liberation Serif", ..., "serif"]` rather than hardcoding `Times New Roman` first.
- **Discipline checks, not aesthetic prescriptions.** Where the template raises an error, it should be a research-rigor concern (e.g. "figure has no title and no caption argument" → raise) rather than a style opinion.
- **Editable after copy.** Once copied, the file under `src/utils/` (or `R/utils/` etc.) belongs to the user's project. Project-specific edits — including new profiles — live there. The template file under `.claude/templates/` stays generic.

## Adding a new language

1. Create `.claude/templates/<language>/`.
2. Provide at minimum:
   - A reproducibility helper that captures: seeds, env / package versions, git rev, started_at / finished_at, runtime version. Output `metadata.json` with the same schema as `python/repro.py` so the `reproducibility-check` hook can validate it.
   - A visualization helper that ships at least the Okabe-Ito 8-color palette and a `save_figure`-equivalent that writes both a vector format (PDF / SVG) and a raster preview.
3. Update `init-research` SKILL.md to mention the new language as a supported `runtime.language` value.
4. Open a PR with example output from a smoke run.

## Open question (intentional)

This directory does **not** ship templates for visualization stacks beyond matplotlib (no Plotly / Bokeh / Altair / etc.) and does not ship LaTeX paper templates. Those are deliberately left to project-level customization because they are venue / preference dependent. If a strong default emerges (e.g. a NeurIPS LaTeX template), it can be added under a separate `.claude/templates/latex/` tree.
