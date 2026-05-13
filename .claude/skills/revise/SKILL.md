---
name: revise
description: Apply a peer-review's comments to the resolved paper's draft. Maintain a rebuttal scaffold tracking response per review point.
when_to_use: After /peer-review.
inputs:
  - <paper_id> as optional positional argument (resolution per .claude/rules/multi-paper.md §4)
  - docs/paper/<paper_id>/review-<n>.md (the latest)
  - docs/paper/<paper_id>/draft.md or main.tex
outputs:
  - docs/paper/<paper_id>/draft.md or main.tex (revised)
  - docs/paper/<paper_id>/review-<n>.md (rebuttal scaffold filled)
  - docs/paper/<paper_id>/changelog.md (appended)
delegated_agent: paper-writer
next_skill: /peer-review <paper_id> (next round) or /checkpoint
---

# /revise

## Steps for the orchestrator

1. **Resolve paper_id** per `.claude/rules/multi-paper.md` §4. Confirm with the user even when the registry has one entry.

2. **Pre-flight.** Verify the draft (`docs/paper/<paper_id>/draft.md` or `main.tex` per `papers[id == <paper_id>].paper_format`) and at least one `docs/paper/<paper_id>/review-<n>.md` exist. If not, abort and suggest `/write-paper <paper_id>` or `/peer-review <paper_id>`. Create `docs/paper/<paper_id>/changelog.md` with a one-line header if it does not yet exist.

3. **Locate the latest review** under `docs/paper/<paper_id>/` (highest `review-<n>.md`).

4. **Launch** `paper-writer` in revise mode with `paper_id`. For each review point, the agent:
   - Either applies a change (records `file:line` in the rebuttal scaffold's "Change made" column),
   - Or declines (records "no change — reason").
   - Blockers and majors **must** be addressed (applied or explicitly justified for non-application). Minors and nits may be deferred.

5. **Re-run citation-guard logic mentally** — the hook will catch any new uncited claims when the file is written.

6. **If the revision touches numbers or methodology**, this is a deviation: must be recorded under "Deviations" in `methodology.md` per the design-experiment skill's rule. Note that `methodology.md` is shared across papers — a deviation may affect siblings.

7. **Append** to `docs/paper/<paper_id>/changelog.md`: `- <date> v<x.y>: addressed review-<n>.md (B:<count>, M:<count>, m:<count>, n:<count>)`.

8. **Recommend re-review** if any blocker remained unfixed, or if the change was substantial (> 25% of major comments addressed).

9. **Update Zone C**: `current_phase: revision`, `last_paper_id: <paper_id>`.

## Hard rules

- Only touch files under `docs/paper/<paper_id>/` (plus shared `docs/research/methodology.md` for deviation notes, with the user's confirmation).
- Use the per-paper `paper_format` from `papers[id == <paper_id>]`. Never read root values at runtime.
- Never operate on review files belonging to another paper, even if they have a numerically larger `<n>`.
