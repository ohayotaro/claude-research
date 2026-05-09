# Agent routing

The orchestrator is Claude Opus. It does **not** implement; it integrates results from specialists. This file is the canonical routing matrix.

## Specialists

| Agent | Backed by | Best at |
|---|---|---|
| `literature-reviewer` | Opus + Gemini CLI | Survey, citation graph, BibTeX entry generation |
| `gemini-explore` | Gemini CLI | Multimodal: PDFs, figures, videos, web pages |
| `hypothesis-generator` | Opus (+ Codex critique) | Diverging from gaps to candidate hypotheses; framing contributions |
| `methodology-designer` | Opus (+ Codex check) | Experiment design, statistical test choice, sample size |
| `experiment-runner` | Sonnet | Writing Python, running under `uv`, capturing reproducibility metadata |
| `data-analyst` | Opus | Statistical analysis, effect sizes, CIs, plotting |
| `discussant` | Opus | Implications, limitations, future work |
| `paper-writer` | Opus | IMRaD assembly, voice consistency, narrative |
| `peer-reviewer` | Codex | Strict logical / statistical / citation review (paper draft level) |
| `script-reviewer` | Codex | Strict pre-run review of experiment / analysis scripts (statistics, leakage, reproducibility, numerical edge cases, test coverage) |
| `viz-reviewer` | Gemini | Multimodal review of rendered figures (chart choice, color, typography, composition, accessibility, data honesty) |
| `codex-debugger` | Codex | Root-cause analysis of script failures |

## Routing triggers

The `agent-router` hook (`.claude/hooks/agent-router.py`) reads `.claude/routing-keywords.json` and suggests agents based on user prompts.

| Trigger | Suggested agent |
|---|---|
| "find papers", "prior work", "literature", "survey", "PDF" | `literature-reviewer` (delegates to Gemini) |
| "figure", "image", "chart", "screenshot", "video", "audio" | `gemini-explore` |
| "hypothesis", "idea", "what if", "novel approach", "gap" | `hypothesis-generator` |
| "experiment design", "sample size", "power", "statistical test" | `methodology-designer` |
| "implement", "script", "run", "code this up", "execute" | `experiment-runner` |
| "analyze", "statistics", "p-value", "effect size", "plot" | `data-analyst` |
| "limitations", "implications", "future work", "discuss" | `discussant` |
| "paper", "draft", "introduction", "abstract", "IMRaD" | `paper-writer` |
| "review this draft", "critique", "find flaws", "rebut" | `peer-reviewer` (delegates to Codex) |
| "review my script", "code review", "leakage", "before running" | `script-reviewer` (delegates to Codex) |
| "review the figures", "figure quality", "chart looks", "color choice" | `viz-reviewer` (delegates to Gemini) |
| "error", "exception", "stacktrace", "doesn't work", "debug" | `codex-debugger` |

## When to NOT delegate

The orchestrator handles these directly:
- Short clarifying Q&A with the user.
- Choosing between two paths the user has presented.
- Reading Zone B / Zone C of `CLAUDE.md`.
- Routing decisions (which agent next).
- Anything under ~10 lines of output that doesn't require deep context.

## Parallelism

- `literature-reviewer` and `hypothesis-generator` can run in parallel during early-stage exploration: one surveys while the other brainstorms.
- `data-analyst` and `paper-writer` can run in parallel once analysis is locked: writer drafts methods/intro while analyst handles results.
- `peer-reviewer` is always serial (it reads a finished draft).

## Standard handoff schema

Every agent that completes a step appends a YAML handoff block as the **last section** of its written output (or in its reply to the orchestrator if the output is purely conversational). The orchestrator parses this to plan the next step.

```yaml
handoff:
  agent: <my-agent-name>
  status: success | partial | blocked
  artifacts:                      # files (re-)written this turn
    - path: docs/research/...
      kind: lit-review | gaps | hypotheses | methodology | analysis | discussion | paper | review | run-output | log
      summary: <one-line>
  open_risks:                     # list[str] — short
    - "..."
  next_agent_inputs:              # what the next agent needs from me
    primary_input: <path or null>
    notes: "..."
  recommended_next:               # may be null if the orchestrator decides
    skill: /<skill-name>
    rationale: <one-sentence>
```

`status: blocked` means the agent stopped because of an upstream contract issue and is asking the orchestrator for a decision before continuing. Always-required fields are `agent`, `status`. Other fields are optional but encouraged.

## Hook → agent payload schemas

When a hook surfaces a delegation suggestion, it implies the orchestrator will pass a structured payload to the target agent. These contracts are documented in the relevant agent + the hook source:

- `error-to-codex` → `codex-debugger`: `{run_id, script_path, traceback, env, last_commit}`.
- `agent-router` / `research-keyword-detector` → user-facing hint only; no payload contract.

## Fallback policy (single source of truth)

When an external CLI partner is unavailable (`codex_available: false` or `gemini_available: false` in `.claude/logs/setup-status.json`):

1. The agent that needs the partner **fails loudly** with a clear `status: blocked` handoff and reports the missing dependency.
2. The orchestrator (not the agent) then decides whether to (a) ask the user to install/auth the CLI, (b) substitute a Claude subagent acting in the missing role with a reduced quality warning, or (c) pause the pipeline.

Agents must NOT silently degrade to a Claude `WebFetch` or other in-process fallback. Silent degradation has produced inconsistent retrieval policy across the codebase. The `research-keyword-detector` hook prints a warning but does not enact a fallback.
