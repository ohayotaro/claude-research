---
name: lint
description: Run deterministic local validation for the template or current research project.
when_to_use: Before reporting completion, after code changes, or when the user asks for checks.
---

# /lint

Run:

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
uv run --extra dev mypy scripts tests .claude/hooks
python3 -m compileall -q scripts .claude/hooks tests
bash -n scripts/setup.sh scripts/update.sh
```

For analysis/manuscript changes also run:

```bash
python scripts/research_evidence.py trace-prose
```

Summarize exact outcomes. Use Codex review only when deterministic failures require independent technical diagnosis.
