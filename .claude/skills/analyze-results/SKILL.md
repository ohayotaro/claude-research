---
name: analyze-results
description: Run the pre-registered statistical analysis on a completed run. Produce effect sizes, CIs, and figures.
when_to_use: After /run-experiment.
inputs:
  - data/results/<run_id>/
  - docs/research/methodology.md
outputs:
  - docs/research/analysis.md (one ## Run <run_id> section appended per invocation)
  - data/results/<run_id>/figures/{*.png,*.pdf}
  - src/analysis/<name>_analysis.py
delegated_agent: data-analyst
next_skill: /review-figures (recommended), then /discuss-results
---

# /analyze-results

## Steps for the orchestrator

1. **Pre-flight.** `run_id` exists with valid `metadata.json`. If the user has multiple runs (replications), ask whether to analyze a single run, all of them, or a specific subset.
2. **Launch** `data-analyst` with the run(s) and the locked methodology.
3. **Receive** results. The agent labels confirmatory vs exploratory and provides effect sizes / CIs.
4. **Sanity check** in the orchestrator: every reported number traces to a file under `data/results/<run_id>/`. If any number cannot be sourced, return to `data-analyst` with the gap.
5. **Update Zone C**: `current_phase: analysis`, `next_action: "Run /review-figures, then /discuss-results"`.

## Idempotence rule

`/analyze-results` **always appends** a new `## Run <run_id>` section to `docs/research/analysis.md`. It never rewrites or removes a previously-recorded run. Use `/analyze-results --rewrite <run_id>` (or manually edit the file) if you genuinely need to replace a prior section — and document why under "Deviations" in `methodology.md`.
