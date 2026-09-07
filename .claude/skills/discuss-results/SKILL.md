---
name: discuss-results
description: Draft implications, limitations, mechanisms, and future work from reviewed results.
when_to_use: After /analyze-results and any required figure/static review.
context: fork
agent: scientific-author
---

# /discuss-results

Use `scientific-author` mode `discussion-writing`.

Inputs:
- `docs/research/analysis.md`
- reviewed `data/results/<run_id>/analysis.json`
- `docs/research/lit-review.md`
- unresolved limitations and reviewer findings

Output:
- `docs/research/discussion.md`

Workflow:
1. Discuss what the results support, do not support, and leave unresolved.
2. Include negative, null, failed, and inconclusive findings.
3. Ground literature comparisons in cite keys and numerical claims in result IDs.
4. Rank limitations by interpretive importance and state the implication of each once. Do not restate procedural history already recorded in `methodology.md` or `analysis.md`; refer to it.
5. Update Zone C with `current_phase: discussion` and next action.
