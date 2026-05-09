# Research Orchestrator

> Claude Code (Opus 4.7, 1M context) as orchestrator, coordinating Codex CLI and Gemini CLI as specialized agents for the full research lifecycle — literature review through archival release. Field-agnostic — bring your own discipline.

```
Claude Code (Orchestrator) ─┬─ Codex CLI       (logical critique, statistics, debugging)
                             ├─ Gemini CLI      (papers, PDFs, figures, multimodal)
                             └─ Opus subagents  (lit synthesis, hypothesis, analysis, writing)
```

- **12 role-based agents** (literature-reviewer, hypothesis-generator, methodology-designer, experiment-runner, data-analyst, discussant, paper-writer, peer-reviewer, script-reviewer, viz-reviewer, codex-debugger, gemini-explore)
- **21 skills** across 4 buckets — 12 main pipeline (lit review → release), 3 pipeline-adjacent (`/review-script`, `/review-figures`, `/lint`), 2 post-pipeline (`/prepare-submission`, `/release-artifacts`), 4 ad-hoc (`/ask-gemini`, `/ask-codex`, `/paper-deep-read`, `/extend-literature`)
- **7 rules** for research integrity, citation rigor, statistical rigor, reproducibility, writing style, agent routing, and language policy
- **8 hooks** with absolute-path resolution, secret redaction, JSON-safe parsing, and `tool_use_id` pairing — citation guard, reproducibility check, agent router, CLI logger
- **Field-agnostic via `/init-research`**: discipline, theme, RQ, paper format (Markdown+BibTeX or LaTeX), runtime, and figure-style preferences all chosen at init time and recorded in `CLAUDE.md` Zone B

## Quick start

Install prerequisites first (see [Prerequisites](#prerequisites)). Then, in your project directory:

```bash
cd /path/to/your-project
git clone --depth 1 https://github.com/ohayotaro/claude-research.git .starter \
  && cp -r .starter/.claude .starter/.codex .starter/.gemini .starter/CLAUDE.md \
        .starter/scripts .starter/pyproject.toml .starter/.gitignore . \
  && rm -rf .starter
bash scripts/setup.sh
claude
```

Inside Claude Code:

```
/init-research    # discipline / theme / RQ / paper format / runtime / viz preference
```

After the wizard, `CLAUDE.md` Zone B describes your project, `src/utils/{repro.py,viz.py}` are placed from `.claude/templates/python/`, and `docs/`, `src/`, `data/`, `tests/`, `notebooks/` are scaffolded.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Claude Code | latest | `npm i -g @anthropic-ai/claude-code` |
| Codex CLI | ≥0.105 | `brew install codex` (macOS) or `npm i -g @openai/codex` |
| Gemini CLI | latest | `npm i -g @google/gemini-cli` |
| Git | any | system package manager |
| Python | ≥3.12 | for hooks (`.claude/hooks/*.py`) and experiments |
| `uv` | latest | `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

After install:

```bash
claude --version
codex --version  && codex login
gemini --version && gemini login
uv --version
```

Codex and Gemini are recommended but not blocking. Without Codex, `/peer-review`, `/review-script`, `/ask-codex`, and `codex-debugger` fall back to Claude subagents acting as critics (weaker). Without Gemini, `/literature-review`, `/extend-literature`, `/paper-deep-read`, `/ask-gemini`, and `/review-figures` emit a `status: blocked` handoff and let the orchestrator decide. `bash scripts/setup.sh` writes detection results to `.claude/logs/setup-status.json`; hooks read this and warn the user when a delegation target is missing.

## What gets copied into your project

```
your-project/
├── CLAUDE.md                  # 3-Zone orchestrator contract
├── pyproject.toml             # uv non-package mode + dev deps
├── .gitignore                 # data/raw, data/processed, .claude/logs, .update-backup-*
├── .claude/
│   ├── settings.json          # hook wiring (PostToolUseFailure, ${CLAUDE_PROJECT_DIR})
│   ├── routing-keywords.json  # keyword → agent / skill suggestions
│   ├── paper-template-config.json
│   ├── agents/                # 12 role-based agents
│   ├── hooks/                 # 8 Python hooks
│   ├── rules/                 # 7 domain rules
│   ├── skills/                # 21 skill definitions
│   └── templates/python/      # repro.py + viz.py copied into src/utils/ on /init-research
├── .codex/AGENTS.md           # Codex CLI contract
├── .gemini/GEMINI.md          # Gemini CLI contract
└── scripts/{setup,update}.sh  # detect deps; pull template updates with Zone B/C preservation
```

Your research outputs (`docs/`, `src/`, `data/`, `tests/`, `notebooks/`) are left alone by `update.sh`. The template owns nothing outside the four paths above plus `CLAUDE.md` Zones A.

## Workflow

```
/init-research → /literature-review → /identify-gaps → /generate-hypothesis →
/design-experiment → /review-script → /run-experiment → /analyze-results →
/review-figures → /discuss-results → /write-paper → /peer-review → /revise →
/prepare-submission → /release-artifacts
```

Detailed groupings:

```
Discovery:    /literature-review → /identify-gaps → /generate-hypothesis
Experiment:   /design-experiment → /review-script → /run-experiment
Analysis:     /analyze-results → /review-figures → /discuss-results
Writing:      /write-paper → /peer-review → /revise
Publication:  /prepare-submission → /release-artifacts
Operations:   /lint, /checkpoint, /ask-codex, /ask-gemini, /paper-deep-read, /extend-literature
```

See `docs/orchestrator-review-001.md` for the design audit and resulting fixes (R1–R7).

## Skills

21 skills organized by purpose. Full spec for each is at `.claude/skills/<name>/SKILL.md`. The "Owner" column lists the agent or external CLI that performs the heavy work; the orchestrator drives the flow but does not implement.

### Setup

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/init-research` | Discipline, theme, RQ, paper format (Markdown+BibTeX or LaTeX), runtime language, viz-style preference. Populates Zone B and copies starter scripts into `src/utils/`. | — |

### Discovery

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/literature-review` | Gemini-driven prior-art survey. Rewrites `docs/research/lit-review.md` and extends `docs/references.bib`. | literature-reviewer + Gemini |
| `/identify-gaps` | Extract concrete research gaps from the literature review into `docs/research/gaps.md`. | hypothesis-generator (gap mode) |
| `/generate-hypothesis` | Diverge to 10–15 candidates → Codex critique → converge to 3–6 testable hypotheses in `docs/research/hypotheses.md`. | hypothesis-generator + Codex |

### Experiment

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/design-experiment` | Operationalize variables, choose statistical test, compute power, pre-register. Codex validates. Locks `docs/research/methodology.md`. | methodology-designer + Codex |
| `/review-script` | Pre-run review of `src/experiments/*.py` or `src/analysis/*.py`: statistics, leakage, reproducibility, numerical edge cases, test coverage. | script-reviewer + Codex |
| `/run-experiment` | Implement methodology as a Python script under `uv`; capture full reproducibility metadata into `data/results/<run_id>/`. | experiment-runner |

### Analysis

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/analyze-results` | Pre-registered statistical analysis with effect sizes + 95% CIs; appends `## Run <run_id>` section to `docs/research/analysis.md`. Generates figures via `src/utils/viz.py`. | data-analyst |
| `/review-figures` | Multimodal review of rendered figures: chart choice, color, typography, accessibility, data honesty. Output `data/results/<run_id>/figures/review.md`. | viz-reviewer + Gemini |
| `/discuss-results` | Implications, mechanisms, limitations, future work. Cross-references analysis with literature. Writes `docs/research/discussion.md`. | discussant |

### Writing

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/write-paper` | Assemble IMRaD draft from the five research notes. Markdown+BibTeX or LaTeX per Zone B. | paper-writer |
| `/peer-review` | Codex-driven strict review of the draft; produces `docs/paper/review-<n>.md` with severity-tagged comments and rebuttal scaffold. | peer-reviewer + Codex |
| `/revise` | Apply review comments to the draft; fill rebuttal scaffold; append entry to `docs/paper/changelog.md`. | paper-writer |

### Publication

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/prepare-submission` | Package the draft for venue submission: length / cite-key / figure / anonymization / required-statements checks. Self-contained bundle under `docs/paper/submissions/<venue>-<round>/`. Never auto-submits. | paper-writer |
| `/release-artifacts` | Code + data archival release prep: license check, data card, manifest, `CITATION.cff`, Zenodo deposition payload under `docs/release/<release-tag>/`. Excludes `data/raw/` if Zone B `data_sensitivity ≠ none`. Never auto-uploads. | orchestrator + paper-writer + literature-reviewer |

### Operations

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/lint` | Run `ruff` + `mypy` + `pytest` (touched modules) and present a tidy summary. Logs to `.claude/logs/lint/<ISO>.md`. | — |
| `/checkpoint` | Snapshot current phase, last `run_id`, recent artifacts, and next action into `CLAUDE.md` Zone C. | — |

### Adapters

| Skill | Purpose | Owner |
|-------|---------|-------|
| `/ask-gemini` | One-shot Gemini call for quick web / PDF / image / video lookup. Does not write to `docs/`. | Gemini |
| `/ask-codex` | One-shot Codex call for quick logic / proof / statistics check. Does not write to `docs/`. | Codex |
| `/paper-deep-read` | Deep-read one paper (URL / DOI / PDF) → structured note at `docs/research/papers/<slug>.md`. | gemini-explore |
| `/extend-literature` | Append-only subtopic survey to `lit-review.md`. Never rewrites existing sections. | literature-reviewer (extend mode) |

## Updating the template

Run `scripts/update.sh` from your project root with a path to a fresh template checkout. It backs up `CLAUDE.md` Zone B (project config) and Zone C (session progress), preserves `.claude/logs/`, then overlays the rest. Self-bootstraps if the template ships a newer `update.sh`.

```bash
# First time only — clone the template into a sibling directory
git clone https://github.com/ohayotaro/claude-research.git ../template

# Subsequent updates — pull then overlay
git -C ../template pull
bash scripts/update.sh --source ../template
```

After `update.sh`, restart your Claude Code session (`/exit` → `claude`) — agent / skill / hook definitions are loaded at session startup.

What `update.sh` preserves vs overwrites:

| Path | Behavior | Why |
|------|----------|-----|
| `docs/`, `src/`, `data/`, `tests/`, `notebooks/` | never touched | research outputs |
| `pyproject.toml`, `README.md`, `.gitignore`, `uv.lock` | never touched | project-owned |
| `CLAUDE.md` Zone B | preserved (backup → restore) | `/init-research` output |
| `CLAUDE.md` Zone C | preserved (backup → restore) | `/checkpoint` accumulated state |
| `.claude/logs/` | preserved (`rsync --exclude`) | CLI history, review files, lint logs |
| `.claude/{agents,skills,hooks,rules,templates}/`, `.claude/*.json` | overwritten (`rsync --delete`) | template layer |
| `.codex/`, `.gemini/`, `scripts/` | overwritten | template layer |

Backups land at `.update-backup-<timestamp>/` (gitignored) including a full `CLAUDE.md.before` so you can `diff` afterward.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│      Claude Code (Opus 4.7, 1M)  — Orchestrator            │
├──────────────────┬──────────────┬──────────────────────────┤
│  Opus Subagents  │  Codex CLI   │  Gemini CLI              │
│ lit synthesis    │ critique     │ web / paper PDFs         │
│ hypothesis       │ statistics   │ figures / images         │
│ analysis         │ debugging    │ video / audio            │
│ writing          │ contracts    │ multimodal extraction    │
└──────────────────┴──────────────┴──────────────────────────┘
```

- **Codex** receives English-only structured prompts (see `.codex/AGENTS.md`) and returns severity-tagged comments (`blocker | major | minor | nit`) with `id`, `category`, `comment`, `suggested_fix` per issue.
- **Gemini** receives multimodal input (URLs, file paths) and returns markdown with explicit source URLs / DOIs, or strict JSON when the caller specifies (see `.gemini/GEMINI.md`).
- **Opus subagents** are role-named (e.g. `data-analyst`, `paper-writer`), discipline-agnostic, and read `CLAUDE.md` Zone B at runtime.
- All agents emit a YAML `handoff:` block (schema in `.claude/rules/agent-routing.md`) with `agent`, `status`, `artifacts`, `recommended_next` so the orchestrator can plan downstream work.
- When an external CLI is unavailable, agents emit `status: blocked` — they never silently degrade. The orchestrator decides whether to fall back, ask the user to install the CLI, or pause.

## Language protocol

| Channel | Language |
|---------|----------|
| Orchestrator ↔ User | Japanese (default) — polite form, no emojis |
| Agent ↔ Agent | English (fixed) |
| Agent ↔ Codex / Gemini | English (fixed) |
| Code / commit / paper draft / docs | English (fixed) |
| Hook user-facing strings | Japanese (polite, `[hook-name]` prefix) |

The single Japanese surface is the user-orchestrator dialogue. Everything else is English so logs, handoffs, and the paper itself are uniform. See `.claude/rules/language.md`.

## Provenance

Modeled after the same author's [`claude-orchestrator`](https://github.com/ohayotaro/claude-orchestrator) (financial-trading specialization) and [`claude-fullstack-orchestrator`](https://github.com/ohayotaro/claude-fullstack-orchestrator) (web/mobile/backend specialization), with structural cues from [`DeL-TaiseiOzaki/claude-code-orchestra`](https://github.com/DeL-TaiseiOzaki/claude-code-orchestra) (multi-agent dev environment) and the harness pattern from [`affaan-m/everything-claude-code`](https://github.com/affaan-m/everything-claude-code). The current orchestrator design (R1–R7) was produced by a 4-phase Codex review of the template; the audit and resulting fixes are recorded in `docs/orchestrator-review-001.md`.

## License

This template is yours to use however you like. The agents, skills, rules, prompts, and starter scripts are released into your project alongside your own license — pick one that suits the project (MIT / Apache 2.0 / CC-BY for data, etc.).
