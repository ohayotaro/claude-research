---
name: peer-review
description: Strict, structured peer review of the current draft via Codex. Produces docs/paper/<paper_id>/review-N.md.
when_to_use: After /write-paper, before submission, and after each major revision.
inputs:
  - <paper_id> as optional positional argument (resolution per .claude/rules/multi-paper.md §4)
  - docs/paper/<paper_id>/draft.md or docs/paper/<paper_id>/main.tex
  - docs/research/{methodology,analysis}.md
  - docs/references.bib
outputs:
  - docs/paper/<paper_id>/review-<n>.md
  - .claude/logs/cli/<ISO>-codex-review-<paper_id>-<n>.md
delegated_agent: peer-reviewer
next_skill: /revise <paper_id>
---

# /peer-review

## Steps for the orchestrator

1. **Resolve paper_id** per `.claude/rules/multi-paper.md` §4. Always confirm with the user even if the registry has only one entry.

2. **Pre-flight.**
   - The resolved paper's draft exists at `docs/paper/<paper_id>/{draft.md|main.tex}` per its `paper_format`. If missing, abort and suggest `/write-paper <paper_id>`.
   - Codex available — if not, warn the user that the review will fall back to a Claude critic and is weaker.

3. **Launch** `peer-reviewer` with `paper_id` in the delegation prompt. The agent:
   - Picks the next `review-<n>.md` filename **scoped to this paper** (highest existing under `docs/paper/<paper_id>/` plus 1).
   - Reads the resolved paper's draft (format from `papers[id == <paper_id>].paper_format`).
   - Uses `papers[id == <paper_id>].venue` as the target venue in the Codex prompt.
   - Drives Codex and verifies Codex's claims against the actual files.
   - Logs Codex I/O to `.claude/logs/cli/<ISO>-codex-review-<paper_id>-<n>.md`.

4. **Receive** the structured review. Surface to the user (Japanese):
   - Paper id and review number.
   - Overall recommendation (accept / minor / major / reject).
   - Counts: blockers, majors, minors, nits.
   - Top 3 issues to address first.

5. **Update Zone B status** for this paper: `papers[id == <paper_id>].status: review` (if currently `drafting`).

6. **Update Zone C**: `current_phase: review`, `last_paper_id: <paper_id>`, `next_action: "Run /revise <paper_id> to address review-<n>.md"`.

## Hard rules

- Review numbering is scoped per `paper_id`. `docs/paper/main/review-3.md` and `docs/paper/workshop-x/review-1.md` are independent counters.
- Use the per-paper `venue` and `paper_format` from Zone B `papers[id == <paper_id>]`. Never read root values at runtime.
- Never review another paper's draft by mistake. The agent must verify the path it reads matches the resolved `paper_id`.
