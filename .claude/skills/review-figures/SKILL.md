---
name: review-figures
description: Review static research figures for readability, data mapping, intervals, axes, and provenance.
when_to_use: After figures are generated and before discussion or manuscript submission.
context: fork
agent: scientific-author
---

# /review-figures

This is static figure review only.

Workflow:
1. `scientific-author` mode `static-figure-review` may assess readability, composition, caption clarity, and accessibility from rendered figures.
2. Codex reviewer must validate data mapping, axes, intervals, sample sizes, transformations, and provenance against code and `analysis.json`.
3. Store findings at `data/results/<run_id>/figures/review.md`.
4. Do not infer data or statistics from pixels alone.
