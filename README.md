# Research Orchestrator

A field-agnostic Claude + Codex research orchestration template.

```text
Main Claude session     Research Lead, PM, user dialogue, scientific acceptance
scientific-author       Canonical literature, methods, analysis narrative, paper prose
Codex builder           Code, experiments, statistics, ledgers, figures, tests
Fresh Codex reviewer    Independent read-only critique
```

The design is intentionally small: one Claude subagent, one centralized Codex runner, and
explicit phase/artifact routing. Claude owns scientific judgment and prose. Codex owns
research engineering and independent review. Reviewer work always uses a fresh read-only
Codex invocation distinct from builder work.

## Quick Start

```bash
cd /path/to/your-project
git clone --depth 1 https://github.com/ohayotaro/claude-research.git .starter
cp -r .starter/.claude .starter/AGENTS.md .starter/CLAUDE.md \
      .starter/scripts .starter/pyproject.toml .starter/.gitignore .
rm -rf .starter
bash scripts/setup.sh
claude
```

Inside Claude Code:

```text
/init-research
```

The init flow records project configuration in `CLAUDE.md` Zone B and scaffolds
`docs/`, `src/`, `data/`, `tests/`, and `notebooks/` without overwriting user content.

## Prerequisites

| Tool | Purpose |
|---|---|
| Claude Code | Main Research Lead session and `scientific-author` subagent |
| Codex CLI | Builder and fresh reviewer phases through `scripts/codex_research.py` |
| Git | Reproducibility metadata and update flow |
| Python >= 3.12 | Hooks, runner, tests, and research scripts |
| uv | Deterministic dev/test environment |

Check:

```bash
claude --version
codex --version
uv --version
```

If Codex is missing, Codex builder/reviewer tasks are blocked until it is installed. There is
no hidden model fallback for independent review.

## Repository Layout

```text
CLAUDE.md                  Three-zone Research Lead contract
AGENTS.md                  Root Codex builder/reviewer contract
scripts/codex_research.py  Central Codex runner
scripts/research_evidence.py
                           Ledger and prose result-ID validator
.claude/agents/scientific-author.md
                           Single specialized Claude subagent
.claude/skills/**          Explicit phase workflows
.claude/hooks/**           Deterministic citation, reproducibility, session, and debug hints
.claude/rules/**           Citation, integrity, statistics, multi-paper, language, reproducibility
docs/                      Research and paper artifacts owned by the user/project
src/                       Experiment and analysis code
data/                      Raw, processed, and result artifacts
tests/                     Project and template tests
```

`.claude/tasks/` is runtime state for Codex task briefs, plans, build results, reviews,
state JSON, and sanitized event logs. It is gitignored.

## Workflow

```text
/init-research -> /literature-review -> /identify-gaps -> /generate-hypothesis
-> /design-experiment -> /run-experiment -> /analyze-results -> /review-figures
-> /discuss-results -> /write-paper -> /peer-review -> /revise
-> /prepare-submission -> /release-artifacts
```

Common operational skills:

```text
/lint
/checkpoint
/ask-codex
/review-script
/paper-deep-read
/extend-literature
```

Literature search, PDF reading, and static figure review are Claude-native author workflows.
Static figure review may inspect rendered figures for readability and composition; Codex
reviews data mapping, axes, intervals, and provenance from code and ledgers.

## Codex Runner

All Codex calls go through:

```bash
python scripts/codex_research.py plan <task-id> --prompt-file .claude/tasks/<task-id>/brief.md
python scripts/codex_research.py build <task-id> --prompt-file .claude/tasks/<task-id>/brief.md
python scripts/codex_research.py review <task-id> --prompt-file .claude/tasks/<task-id>/brief.md
python scripts/codex_research.py debug <task-id> --prompt-file .claude/tasks/<task-id>/brief.md
python scripts/codex_research.py status <task-id>
python scripts/codex_research.py collect <task-id>
```

Task directories live at `.claude/tasks/<task-id>/` and may contain:

```text
brief.md
plan.md
build-result.md
review.md
debug-result.md
state.json
events.jsonl
```

Runner behavior:

- `plan` and `review` use read-only sandboxing.
- `build` and `debug` use workspace-write sandboxing.
- Background runs use non-interactive approval policy and finish as failed/blocked instead of waiting for permission.
- Prompts are read from files or stdin, not placed in process arguments.
- Model overrides are optional; if no model is supplied, the user's Codex default is inherited.
- Effort can be selected with CLI flags or `CODEX_*_EFFORT` environment variables.
- Network access is not enabled by default.

## Evidence Ledger

Completed analyses should write:

```text
data/results/<run_id>/metadata.json
data/results/<run_id>/analysis.json
data/results/<run_id>/analysis-report.md
```

`metadata.json` preserves the reproducibility contract. `analysis.json` is the structured
claim ledger. Canonical prose cites result IDs with:

```text
[result:<result_id>]
[result:<run_id>:<result_id>]
```

Validate:

```bash
python scripts/research_evidence.py validate-ledger data/results/<run_id>/analysis.json
python scripts/research_evidence.py trace-prose
```

## Approval Gates

The Research Lead must get explicit user approval before work involving human participants,
IRB/ethics changes, sensitive or regulated data, uncertain-license data acquisition,
post-results confirmatory-analysis changes, destructive data operations, external
submission/deposit/release, credential use, or any external side effect.

No skill auto-submits, auto-deposits, or silently converts exploratory work into
confirmatory work.

## Updating The Template

Run:

```bash
git clone https://github.com/ohayotaro/claude-research.git ../template
bash scripts/update.sh --source ../template
```

The updater preserves Zone B, Zone C, `.claude/logs/**`, `.claude/tasks/**`, `docs/**`,
`src/**`, `data/**`, `notebooks/**`, and `tests/**`. It syncs the template-owned Claude
layer, root `AGENTS.md`, and scripts, and removes known obsolete legacy paths. Restart
Claude Code after updating so agents, skills, and hooks are reloaded.

If a protected environment prevents deletion of an obsolete `.codex` directory, remove it
manually:

```bash
rm -rf .codex
```

## Validation

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
uv run --extra dev mypy scripts tests .claude/hooks
python3 -m compileall -q scripts .claude/hooks tests
bash -n scripts/setup.sh scripts/update.sh
```

## License

This template is yours to use with your project license. Research outputs, data, and papers
remain project-owned state.
