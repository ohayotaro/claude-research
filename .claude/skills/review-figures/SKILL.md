---
name: review-figures
description: Multimodal review of rendered figures via Gemini. Critiques chart choice, color, typography, composition, accessibility, data honesty, and journal-readiness. Recommended after /analyze-results and before /write-paper.
when_to_use: After /analyze-results has produced figures under data/results/<run_id>/figures/. Re-runnable after fixes.
inputs:
  - run_id (required) — defaults to the most recent run if omitted
  - Optional: a specific figure path to review just one figure
outputs:
  - data/results/<run_id>/figures/review.md
  - .claude/logs/cli/<ISO>-gemini-vizreview-*.md (per figure)
delegated_agent: viz-reviewer
next_skill: /write-paper (if all verdicts are publication-ready), or fix and re-run
---

# /review-figures

The figure-level analogue of `/peer-review`. Catches chart-type misuse, palette problems, axis dishonesty, and unreadable typography **before** figures land in the paper draft.

## Steps for the orchestrator

1. **Resolve the target.**
   - If the user names a `run_id`, use that.
   - If the user gives a single figure path, scope to that one figure.
   - Otherwise, default to the most recent `run_id` under `data/results/` that contains a non-empty `figures/` subdirectory.
2. **Pre-flight.**
   - Gemini availability via `.claude/logs/setup-status.json`. If absent, abort and inform the user — Claude cannot reliably critique rendered figures alone. Suggest installing Gemini CLI or skipping this skill.
   - Verify `data/results/<run_id>/figures/` exists and has at least one figure.
3. **Launch** `viz-reviewer` with the run_id (or single path).
4. **Receive** the structured review. Surface to the user (in Japanese, polite, no emojis):
   - Per-figure verdicts (publication-ready / needs-minor-polish / needs-rework / not-suitable-for-this-claim).
   - Aggregate counts: blockers / majors / minors.
   - Top 3 cross-figure issues.
   - Path to `figures/review.md`.
5. **Recommend next step**:
   - All `publication-ready` → safe to invoke `/write-paper` (or proceed with paper assembly).
   - Any `needs-rework` or `not-suitable-for-this-claim` → return to `data-analyst` to redraw, then re-run `/review-figures`.
   - Only `needs-minor-polish` → user judgment; minor fixes can land alongside the paper draft.
6. **Update Zone C** lightly: `last_skill_run: review-figures`. Do not change `current_phase`.

## Common variants

- **Single-figure focused review**: user pastes a figure path or asks "review fig3 only" — pass that single path.
- **Re-review after redraw**: subsequent invocations overwrite `figures/review.md` with the new findings; the old one is retrievable from git history.
- **Pre-submission check**: invoke once more right before `/peer-review` runs, to catch any figure tweaks the analyst made after the initial review.

## Hard rules

- **Do not edit figure files or `src/analysis/`.** Reviews are advisory.
- **Do not skip Gemini.** A "review" without seeing the actual rendered figure is not a review — abort if Gemini is unavailable.
- The skill writes to `data/results/<run_id>/figures/review.md`. This is an analysis output and is appropriate to commit to git for the historical record. (`data/raw/` and `data/processed/` are gitignored; `data/results/<run_id>/` is generally tracked.)
