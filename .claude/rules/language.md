# Language policy

There is exactly one Japanese-language surface in this repository: **the chat between the user and the orchestrator**. Everything else is English.

## Japanese (Japanese-speaking user only)

- Orchestrator's chat replies to the user.
- `AskUserQuestion` question text and option labels.
- `/init-research` interactive Q&A.
- Hook user-facing warning / status strings (e.g. citation-guard's "引用が見つかりません" message).
- Skill execution status output shown to the user.
- `session-start.py` screen output.

## English (everything else)

- All code: Python in `src/`, `tests/`, `scripts/`, hooks under `.claude/hooks/`. Including comments and variable names.
- All agent definitions under `.claude/agents/*.md` (frontmatter, body, handoff contracts).
- All skill definitions under `.claude/skills/**/SKILL.md`.
- All rules under `.claude/rules/*.md` including this file.
- `CLAUDE.md` (Zones A, B, C).
- `README.md` is bilingual by exception: the primary user audience is Japanese-speaking, so onboarding sections (Quick start, update flow explanations, troubleshooting) may be primarily Japanese. Authoritative reference content (skill / agent tables, layout, Credits) stays in English so it matches the source-of-truth files those tables describe.
- All `docs/research/*.md` (lit-review, gaps, hypotheses, methodology, analysis, discussion).
- All `docs/paper/<paper_id>/*` (draft.md / main.tex / review-N.md / changelog.md / rebuttal.md). See `.claude/rules/multi-paper.md` for the per-paper layout.
- `docs/references.bib`.
- All agent → agent and agent → Codex delegation prompts and responses.
- All logs under `.claude/logs/`.
- Root `AGENTS.md`.
- Commit messages and PR descriptions.
- Agent scratch / chain-of-thought notes.

## Boundary cases

- **Hook code with user-facing strings.** Python source is English; only the literal user-facing string is Japanese. Example: `print("[citation-guard] 引用が見つかりません: " + claim_text)` — variable names and surrounding code stay English. Avoid emojis in user-facing strings; prefix with a bracketed tag like `[hook-name]` or `[hint]` instead.
- **User free-text input.** When the user types a research theme or RQ in Japanese, store it verbatim in `CLAUDE.md` Zone B. Agents translate to English when they materialize content under `docs/research/`.
- **When unsure, choose English.** Keep the rule simple.

## Clarity (applies to the Japanese chat surface)

The chat is where the user makes decisions. Its language must be plain regardless of how
much internal structure produced the result.

- Lead with the answer or finding, then the reason, then the next action if any.
- Prefer the user's own vocabulary and established disciplinary terminology. Do not invent
  names, acronyms, or classifications for ordinary concepts.
- When a new definition is necessary, give its purpose and a concrete example, and say
  whether it is study-specific or established usage.
- Explain the subject before displaying an internal identifier. IDs support traceability;
  they do not replace meaning.
- Translate agent handoffs into what was done, what was found, and what is unresolved.
- Provide technical depth when requested or when a decision needs it.

Illustrative wording. Chat (Japanese):
「感度補正の検定は校正チェックに失敗したので、測定値は記述統計として報告し、その検定に
基づく改善は主張できません。」
Manuscript (English): "The sensitivity-correction test failed its calibration check, so we
report the measurements descriptively and cannot claim an improvement from that test."

A glossary is not a substitute for avoiding unnecessary terminology. Do not create a
terminology registry unless the project actually needs one.

## Why this split

- Specialist agents and Codex receive English task briefs.
- Logs are searched by other agents; consistency matters.
- The paper is the artifact; it is in English (paper output language is configurable in Zone B but defaults to English).
- The user reads chat replies in their native language for speed.
