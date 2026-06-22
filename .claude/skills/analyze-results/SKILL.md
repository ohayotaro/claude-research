---
name: analyze-results
description: Use Codex builder to compute statistics and ledgers, Codex reviewer to verify them, then author the canonical analysis narrative.
when_to_use: After /run-experiment has produced a run directory with metadata.
---

# /analyze-results

This skill has three phases:

1. Codex builder computes analysis code, figures, `analysis.json`, and optional `analysis-report.md`.
2. Fresh Codex reviewer checks statistics, assumptions, ledger traceability, and figure provenance.
3. `scientific-author` mode `analysis-narrative` writes or appends canonical prose only after review findings are resolved.

Required outputs:
- `src/analysis/**`
- `tests/**`
- `data/results/<run_id>/analysis.json`
- `data/results/<run_id>/analysis-report.md` when useful
- `data/results/<run_id>/figures/**`
- `docs/research/analysis.md`

Workflow:
1. Validate `metadata.json` exists before analysis starts.
2. Run builder with `python scripts/codex_research.py build <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
3. Validate the ledger with `python scripts/research_evidence.py validate-ledger data/results/<run_id>/analysis.json`.
4. Run reviewer with `python scripts/codex_research.py review <review-task-id> --prompt-file .claude/tasks/<review-task-id>/brief.md`.
5. Author canonical prose with `[result:<result_id>]` references only after blocker/major findings are resolved.
6. Run `python scripts/research_evidence.py trace-prose`.
