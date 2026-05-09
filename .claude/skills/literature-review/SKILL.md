---
name: literature-review
description: Run a Gemini-driven prior-art survey for the current RQ. Produces docs/research/lit-review.md and updates docs/references.bib.
when_to_use: After /init-research, or whenever the lit review needs refresh.
inputs:
  - CLAUDE.md Zone B (research_question, sub_questions)
  - Optional: seed papers from the user
outputs:
  - docs/research/lit-review.md
  - docs/references.bib (extended)
  - .claude/logs/cli/<ISO>-litrev-*.{json,md}
delegated_agent: literature-reviewer (delegates retrieval to gemini-explore / gemini CLI)
next_skill: /identify-gaps
---

# /literature-review

Delegates to the `literature-reviewer` agent. The orchestrator's job is to (a) confirm Zone B has an RQ, (b) launch the agent with clear scope, (c) integrate its handoff.

## Steps for the orchestrator

1. **Pre-flight.** Check `CLAUDE.md` Zone B has `research_question` set and non-empty. If not, suggest `/init-research`.
2. **Check Gemini availability.** Read `.claude/logs/setup-status.json`. If `gemini_available: false`, warn the user that retrieval coverage will be reduced and ask whether to proceed with the Claude `WebFetch` fallback.
3. **Launch agent** (`literature-reviewer`) with:
   - The RQ and sub-questions.
   - Any seed citations the user names.
   - Target: 30–60 papers reviewed, top 10–20 read in depth.
4. **Receive handoff** (number of papers, themes, candidate gaps, retrieval failures).
5. **Update Zone C** of `CLAUDE.md`: `current_phase: literature`, `last_skill_run: literature-review`, `next_action: "Run /identify-gaps"`.
6. **Report to user** (Japanese): theme list, retrieval coverage, suggested next step.

## Common variants

- **Sanity check on a single paper**: skip this skill; use `/ask-gemini` or `/paper-deep-read` directly.

## Mode

`/literature-review` is **rewrite-only**. It overwrites `lit-review.md` from scratch using the current RQ. For incremental coverage of a subtopic without losing the existing review, use `/extend-literature` (the append-only counterpart). Two skills, two purposes — never both for the same kind of update.
