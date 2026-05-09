---
name: revise
description: Apply a peer-review's comments to the draft. Maintain a rebuttal scaffold tracking response per review point.
when_to_use: After /peer-review.
inputs:
  - docs/paper/review-<n>.md (the latest)
  - docs/paper/draft.md or main.tex
outputs:
  - docs/paper/draft.md or main.tex (revised)
  - docs/paper/review-<n>.md (rebuttal scaffold filled)
  - docs/paper/changelog.md (appended)
delegated_agent: paper-writer
next_skill: /peer-review (next round) or /checkpoint
---

# /revise

## Steps for the orchestrator

1. **Pre-flight.** Verify the draft (`docs/paper/draft.md` or `main.tex`) and at least one `docs/paper/review-<n>.md` exist. If not, abort and suggest `/write-paper` or `/peer-review`. Create `docs/paper/changelog.md` with a one-line header if it does not yet exist.
2. **Locate the latest review** (`review-<n>.md`).
3. **Launch** `paper-writer` in revise mode. For each review point, the agent:
   - Either applies a change (records `file:line` in the rebuttal scaffold's "Change made" column),
   - Or declines (records "no change — reason").
   - Blockers and majors **must** be addressed (applied or explicitly justified for non-application). Minors and nits may be deferred.
4. **Re-run citation-guard logic mentally** — the hook will catch any new uncited claims when the file is written.
5. **If the revision touches numbers or methodology**, this is a deviation: must be recorded under "Deviations" in `methodology.md` per the design-experiment skill's rule.
6. **Append** to `changelog.md`: `- <date> v<x.y>: addressed review-<n>.md (B:<count>, M:<count>, m:<count>, n:<count>)`.
7. **Recommend re-review** if any blocker remained unfixed, or if the change was substantial (> 25% of major comments addressed).
8. **Update Zone C**: `current_phase: revision`.
