# AGENTS.md - Claude + Codex Research Orchestration

This repository is a field-agnostic research orchestration template. Claude Code is the
research lead and final acceptance owner. Codex is used only through the centralized runner
in `scripts/codex_research.py` for research engineering and independent review.

## Codex Modes

Builder mode implements and validates technical work:
- May write `src/**`, `tests/**`, `data/processed/**`, `data/results/**`, and task-local
  artifacts under `.claude/tasks/<task-id>/`.
- Owns experiment code, analysis code, statistical computation, result ledgers, figures,
  tests, reproducibility metadata, packaging checks, and debugging.
- Must not write canonical literature review, hypotheses prose, discussion, manuscript
  prose, rebuttals, or `docs/references.bib`.

Reviewer mode is independent and read-only:
- Must run in a fresh Codex invocation, separate from any builder context.
- Uses `--sandbox read-only`; never edits reviewed files or applies its own recommendations.
- Returns prioritized findings with stable IDs, severity
  `blocker | major | minor | nit`, and `verdict: pass | pass_with_minor_changes | revise | blocked`.
- Distinguishes verified facts, inferences, and unverified concerns.

## Research Integrity

- Do not invent citations, identifiers, quotations, sample sizes, statistics, p-values, or run
  metadata.
- Every generated numerical claim must trace to `data/results/<run_id>/analysis.json` and be
  cited in canonical prose using `[result:<result_id>]` or `[result:<run_id>:<result_id>]`.
- Preserve negative, null, failed, and inconclusive findings.
- Keep `metadata.json` for every run and align it with the structured ledger; do not replace it.
- Human approval is required before work involving participants, regulated or sensitive data,
  uncertain-license data acquisition, confirmatory-analysis changes after seeing results,
  destructive data operations, external submission/deposit/release, credential use, or any
  external side effect.

## Worktree Safety

- Work on the current branch and preserve unrelated user changes.
- Do not commit, push, reset, clean, stash, delete user data, or run destructive Git operations
  unless the user explicitly asks.
- Do not launch two write-capable Codex jobs against the same worktree at the same time.
- Do not enable network access by default.

## Required Validation

Run the deterministic suite before reporting completion:

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
uv run --extra dev mypy scripts tests .claude/hooks
python3 -m compileall -q scripts .claude/hooks tests
bash -n scripts/setup.sh scripts/update.sh
```

Use `scripts/research_evidence.py` to validate result ledgers and prose result-ID
traceability when analysis artifacts or canonical prose change.
