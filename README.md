# Claude Research Orchestrator

研究分野を問わず使える、Claude Code を司令塔とした **multi-agent research orchestrator** テンプレートです。

A field-agnostic research orchestrator template. Claude Code (Opus) coordinates a small team of specialized agents and external CLI partners (Codex, Gemini) across the full research lifecycle:

> **literature review → gap identification → hypothesis generation → experiment design → script-based verification → results analysis → figure review → discussion → paper writing → peer review → revision → submission packaging → archival release**

## Philosophy

- **Orchestrator delegates only — it does not implement.** The main Claude session preserves context and routes work to specialists.
- **Right tool for right task.**
  - **Claude Opus** — orchestration, hypothesis generation, large-context analysis & discussion
  - **Claude Sonnet** — light implementation, edits, formatting
  - **Codex CLI** — logical verification, statistical rigor, strict review, debugging
  - **Gemini CLI** — web research, paper PDFs, figures, multimodal exploration
- **Field-agnostic.** `/init-research` collects domain, theme, research question, and writes them into Zone B of `CLAUDE.md`. The same template works for physics, biology, social science, CS, etc.
- **English everywhere except the user-facing dialogue.** See `.claude/rules/language.md`.

## Quick start

```bash
# 1. Clone or copy this repo into your research project directory
# 2. Install dependencies
bash scripts/setup.sh
# 3. Open in Claude Code
claude
# 4. Inside Claude, initialize the research project
/init-research
```

`/init-research` will ask you (in Japanese) about the research domain, theme, RQ, paper output language, paper format (Markdown+BibTeX or LaTeX), and writes those into `CLAUDE.md` Zone B and `pyproject.toml`.

### Clone with a project-specific name (recommended)

研究プロジェクトごとに別ディレクトリで使い、テンプレ起源の `origin` を自分の repo に張り替えるパターン:

```bash
git clone https://github.com/ohayotaro/claude-research-orchestrator.git my-research-project
cd my-research-project

# Detach from the template's origin
git remote remove origin

# Point to your own research repo (create it on GitHub first, then):
# git remote add origin https://github.com/<you>/my-research-project.git

bash scripts/setup.sh
claude
# Inside Claude:
/init-research
```

これでテンプレ本体（このリポジトリ）と個別の研究プロジェクトの履歴が混ざらず、テンプレ更新は `scripts/update.sh --source <template-path>` 経由で取り込めます。

### Pulling template updates into an existing research project

このテンプレ（`claude-research-orchestrator`）に修正・改善が入ったとき、すでに走っている研究プロジェクトにそれを取り込む手順:

```bash
# 1. Get the latest template into a sibling directory (first time only)
git clone https://github.com/ohayotaro/claude-research-orchestrator.git ../template

# Subsequent updates: just pull
git -C ../template pull

# 2. Inside your research project, overlay the template
cd ~/path/to/my-research-project
bash scripts/update.sh --source ../template
```

`scripts/update.sh` が以下を行います:

- **Zone B / Zone C の自動退避・復元**: `CLAUDE.md` のプロジェクト固有設定（Zone B、`/init-research` の出力）と進捗状態（Zone C、`/checkpoint` の蓄積）を退避し、テンプレ更新後に再注入します。
- **テンプレ層のみ上書き**: `.claude/`, `.codex/`, `.gemini/`, `scripts/` を `rsync --delete` で同期します。**ただし `.claude/logs/` は除外**されるため、CLI 呼出履歴・script レビュー・lint・debug ログ等のセッション成果物は保全されます。
- **セルフブートストラップ**: ソース側の `update.sh` がローカルと異なる場合、自動的にローカルを置き換えて再実行します。`update.sh` 自身のバグ修正もこのフローで取り込めます。
- **バックアップ**: 退避ファイルは repo root の `.update-backup-<timestamp>/` に残り、`CLAUDE.md.before` も含むため diff によるレビューが可能です（`.gitignore` 済み、削除しても問題ありません）。

#### 保全 / 上書きの一覧

| パス | 挙動 | 用途 |
|---|---|---|
| `docs/`, `src/`, `data/`, `tests/`, `notebooks/` | **完全に touch しない** | 研究成果物 |
| `pyproject.toml`, `README.md`, `.gitignore`, `uv.lock` | **完全に touch しない** | プロジェクト所有 |
| `CLAUDE.md` Zone B | **保全**（退避 → 復元） | `/init-research` の出力（分野・テーマ・RQ・viz_preferences 等） |
| `CLAUDE.md` Zone C | **保全**（退避 → 復元） | `/checkpoint` で蓄積されたセッション進捗（current_phase, last_run_id, next_action 等） |
| `CLAUDE.md` Zone A | 上書き（テンプレ更新を反映） | 不変ルール（テンプレ層） |
| `.claude/logs/` | **保全**（rsync exclude） | CLI 呼出履歴、`/review-script` レビュー、`/lint` 結果、debug 報告 |
| `.claude/agents/`, `.claude/skills/`, `.claude/hooks/`, `.claude/rules/`, `.claude/templates/`, `.claude/*.json` | 上書き（rsync --delete） | テンプレ層 — 改良はテンプレ側に push する設計 |
| `.codex/AGENTS.md`, `.gemini/GEMINI.md` | 上書き | テンプレ層 |
| `scripts/` | 上書き（self-bootstrap 含む） | テンプレ層 |

> **注意**: `.claude/agents/` 等にプロジェクト独自のカスタムファイルを直接置くと update 時に消去されます。汎用化できるならテンプレ側に PR を、プロジェクト専用にしたい場合は別ディレクトリに保管した上で update 後に手動で配置してください。

更新後は念のため:

```bash
bash scripts/setup.sh        # 依存に変更があれば反映
git status                    # 何が変わったか確認
git add -A && git commit -m "Sync template @ <commit-sha>"
```

> **重要**: テンプレ更新で agents / skills / hooks / settings.json が変わった場合、Claude Code セッションの**再起動が必要**です（agent / hook 定義はセッション起動時にロードされるため）。`/exit` してから `claude` を再実行してください。

## Skills (the research pipeline)

Run them in order, or jump in at any phase:

| Skill | Purpose |
|---|---|
| `/init-research` | Initialize a new research project (writes Zone B, scaffolds `docs/`, `src/`, `data/`) |
| `/literature-review` | Gemini-driven prior-art survey → `docs/research/lit-review.md` + `references.bib` |
| `/identify-gaps` | Extract research gaps from the review |
| `/generate-hypothesis` | Generate solution candidates, critiqued by Codex |
| `/design-experiment` | Design experiment, choose statistics, sample size |
| `/run-experiment` | Implement and run Python scripts under `uv` with full reproducibility metadata |
| `/analyze-results` | Statistical tests, effect sizes, CIs, figures |
| `/discuss-results` | Implications, limitations, future work |
| `/write-paper` | Assemble IMRaD draft (Markdown or LaTeX, per Zone B) |
| `/peer-review` | Codex-driven strict review |
| `/revise` | Apply review comments, log changelog |
| `/checkpoint` | Persist current phase / next action into Zone C |

### Pipeline-adjacent skills (recommended at specific points)

| Skill | When to insert |
|---|---|
| `/review-script` | Before `/run-experiment` — Codex-backed pre-run review (statistics, leakage, reproducibility, numerical, test coverage). |
| `/review-figures` | Between `/analyze-results` and `/discuss-results` — Gemini-backed multimodal review of rendered figures (chart choice, color, typography, accessibility, data honesty). |
| `/lint` | Anywhere — runs `ruff` + `mypy` + `pytest` on the project (or a path) and presents a tidy summary. |

### Post-pipeline skills (after `/revise`)

| Skill | Purpose |
|---|---|
| `/prepare-submission` | Package the draft for venue submission with mechanical checks (length, anonymization, figure embedding, required statements). Produces a self-contained bundle under `docs/paper/submissions/<venue>-<round>/`. |
| `/release-artifacts` | Prepare code + data for archival release (Zenodo / OSF / Dryad). Generates data card, manifest, `CITATION.cff`, license check, and Zenodo deposition payload under `docs/release/<release-tag>/`. |

### Ad-hoc utility skills

| Skill | Purpose |
|---|---|
| `/ask-gemini` | One-shot Gemini call for quick web/PDF/image lookups; does not touch `docs/`. |
| `/ask-codex` | One-shot Codex call for quick logic/statistics/proof checks; does not touch `docs/`. |
| `/paper-deep-read` | Deep-read a single paper (URL/DOI/PDF) and persist a structured note under `docs/research/papers/<slug>.md`. |
| `/extend-literature` | Append a focused subtopic survey to the existing `lit-review.md` without rewriting it. |

## Specialized agents

12 agents under `.claude/agents/`. See `.claude/rules/agent-routing.md` for the full routing matrix and the standard handoff schema.

| Agent | Backed by | Best at |
|---|---|---|
| `literature-reviewer` | Opus + Gemini CLI | Survey, citation graph, BibTeX entry generation |
| `gemini-explore` | Gemini CLI | Multimodal: PDFs, figures, videos, web pages |
| `hypothesis-generator` | Opus (+ Codex critique) | From gaps to candidate hypotheses; framing contributions |
| `methodology-designer` | Opus (+ Codex check) | Experiment design, statistical test choice, sample size |
| `experiment-runner` | Sonnet | Writing Python, running under `uv`, capturing reproducibility metadata |
| `data-analyst` | Opus | Statistical analysis, effect sizes, CIs, plotting (uses `src/utils/viz.py`) |
| `discussant` | Opus | Implications, limitations, future work |
| `paper-writer` | Opus | IMRaD assembly, voice consistency, narrative |
| `peer-reviewer` | Codex | Strict logical / statistical / citation review (paper draft) |
| `script-reviewer` | Codex | Strict pre-run review of experiment / analysis scripts |
| `viz-reviewer` | Gemini | Multimodal review of rendered figures (chart choice, color, typography, accessibility, data honesty) |
| `codex-debugger` | Codex | Root-cause analysis of script failures |

## Requirements

- [Claude Code](https://claude.com/code) (Opus 4.x). Authenticate via `claude` once before running `/init-research`.
- [`uv`](https://github.com/astral-sh/uv) for Python environment management.
- [Codex CLI](https://github.com/openai/codex) (recommended). Provides Codex-backed strict review and debugging. Without it, `/peer-review`, `/script-review`, `/ask-codex`, and `codex-debugger` fall back to Claude subagents acting as critics — weaker, not blocking.
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) (recommended). Provides multimodal retrieval. Without it, `/literature-review`, `/extend-literature`, `/paper-deep-read`, `/ask-gemini`, and `/review-figures` will emit a `status: blocked` handoff and let the orchestrator decide between asking the user to install/auth Gemini or substituting a weaker Claude fallback.

`bash scripts/setup.sh` detects which CLIs are available and writes the result to `.claude/logs/setup-status.json`. Hooks read this file and warn the user when a delegation target is missing.

## Layout

```
.claude/
  agents/         12 specialized agent definitions
  skills/         21 skills — 12 pipeline + 3 pipeline-adjacent + 2 post-pipeline + 4 ad-hoc utility
  hooks/          8 Python hooks (routing, citation guard, repro check, logging, ...)
  rules/          7 domain rules (research-integrity, citation-rigor, ...)
  templates/      Starter scripts copied into src/utils/ on /init-research
    README.md     Structure, design principles, how to add another language
    python/       Python recipes (default — uv-managed)
      repro.py    Reproducibility metadata helper
      viz.py      Visualization helpers — Okabe-Ito palette, save_figure(),
                  STYLE_PROFILES (default / publication / presentation),
                  apply_style() that reads viz_preferences from Zone B
    # r/, julia/, etc. — placeholders for future expansion
  logs/           Runtime artifacts — preserved across template updates
    cli/          Codex / Gemini call I/O
    review/       /review-script outputs
    lint/         /lint outputs
    debug/        codex-debugger reports
    sessions.log  session-end breadcrumbs
  settings.json
  routing-keywords.json
  paper-template-config.json
.codex/AGENTS.md  Contract loaded by Codex CLI
.gemini/GEMINI.md Contract loaded by Gemini CLI

docs/
  research/       lit-review, gaps, hypotheses, methodology, analysis, discussion (English)
  paper/          draft.md or main.tex, review-N.md, changelog.md
  references.bib

src/
  experiments/    Experiment scripts (Python, run via uv)
  analysis/       Analysis scripts (use src/utils/viz.py for styling)
  utils/          Shared helpers — repro.py and viz.py

data/
  raw/            Append-only raw inputs (gitignored)
  processed/      Regenerated from raw via scripts (gitignored)
  results/<run_id>/   Immutable per-run outputs with metadata.json

notebooks/        Optional Jupyter
tests/            pytest tests for src/
scripts/
  setup.sh        Detect uv / codex / gemini, sync deps
  update.sh       Pull template updates with Zone B and logs preservation

CLAUDE.md         3-zone config (immutable rules / project / session)
pyproject.toml    Non-package uv project (package = false), with pytest pythonpath = src
```

`/init-research` を実行すると `docs/`, `src/`, `data/`, `tests/`, `notebooks/` 配下のスケルトンが生成され、`src/utils/repro.py` と `src/utils/viz.py` が `.claude/templates/python/` から自動配置されます。

## Credits

Built on patterns from:
- [`affaan-m/everything-claude-code`](https://github.com/affaan-m/everything-claude-code) — agent harness pattern
- [`DeL-TaiseiOzaki/claude-code-orchestra`](https://github.com/DeL-TaiseiOzaki/claude-code-orchestra) — Codex / Gemini delegation contract
- [`ohayotaro/claude-orchestrator`](https://github.com/ohayotaro/claude-orchestrator) — domain-specialized 3-zone template
