# Orchestrator self-review #001

_Date: 2026-05-09_
_Reviewer: Codex (via 4-phase review of agents / skills / hooks / infrastructure)_
_Repo state at review: `c5fbbd9` (head before this review)_
_Raw outputs: `.claude/logs/orchestrator-review-001/phase{1-4}-*.md`_

## Aggregate

| Phase | Scope | Blocker | Major | Minor | Verdict |
|---|---|---:|---:|---:|---|
| 1 | 12 agents | 0 | 5 | 5 | needs-major-revision |
| 2 | 19 skills | 1 | 8 | 3 | needs-major-revision |
| 3 | 8 hooks + settings | 2 | 8 | 4 | needs-major-revision |
| 4 | CLAUDE.md / scripts / templates / rules / docs | 0 | 4 | 7 | needs-major-revision |
| **Total** | | **3** | **25** | **19** | needs-major-revision |

Overall verdict: **needs-major-revision**. The architecture is sound but several integration contracts are leaky and three runtime guards are effectively dead. Fixing the three blockers and the highest-leverage majors is enough to make the orchestrator operationally robust without redesign.

## Blockers (must-fix; everything else can wait)

### B1. `hypothesis-generator` agent has no "gap mode" — `/identify-gaps` skill points at it

`.claude/skills/identify-gaps/SKILL.md` says it delegates to `hypothesis-generator` in "gap mode" and writes `docs/research/gaps.md`, but `.claude/agents/hypothesis-generator.md` only documents hypothesis generation that writes `hypotheses.md`. The pipeline node that produces `gaps.md` does not actually exist as a contract.

**Fix**: Either (a) extend `hypothesis-generator.md` with an explicit "gap mode" section that takes `lit-review.md` and writes `gaps.md`, OR (b) split into a dedicated `gap-identifier.md` agent. (a) is simpler and avoids agent proliferation.

### B2. `citation-guard` hook expects relative path; Claude Code passes absolute → hook never fires

`citation-guard.py:33` (`is_doc_path`) checks `path.startswith("docs/")`. Claude Code passes `tool_input.file_path` as an absolute path (e.g. `/Users/.../docs/research/lit-review.md`). The check returns `False` for every real call. The hook is silently a no-op.

**Fix**: Resolve `file_path` against the project root (read from `CLAUDE_PROJECT_DIR`, fallback to `cwd`) and check the relative form. Add a unit test against an absolute path.

### B3. `reproducibility-check` hook same problem — silent no-op

`reproducibility-check.py:32` matches `^data/results/<run_id>` against an absolute path. Same root cause as B2. The reproducibility guard is not enforcing anything in practice.

**Fix**: Same approach as B2.

## High-priority majors

Grouped by area for batch-fixing.

### Hooks

- **H.3 / H.4**: `error-to-codex` and `log-cli-tools` are wired only to `PostToolUse`. Bash failures fire `PostToolUseFailure` (per Claude Code hooks reference). `error-to-codex` therefore misses all real failures, and `log-cli-tools` leaves a permanent `_pending_` log on every failed CLI call. → Add both to `PostToolUseFailure` matchers in settings.json; in `log-cli-tools`, add an `error` block writer for the failure case.
- **H.5**: `log-cli-tools` pre/post pairing uses a SHA-1 of the command string. Concurrent or repeated identical commands collide. → Use `tool_use_id` from the payload as the join key.
- **H.6**: Pre-log filename has second-precision timestamp; same-second collisions overwrite. → Use microsecond precision or append a `uuid4` suffix.
- **H.7**: All hooks call `json.loads(sys.stdin.read())` without try/except. Malformed JSON crashes the hook. → Wrap in try/except, return 0 silently.
- **H.10**: `log-cli-tools` writes raw stdout/stderr. CLI output may contain API keys, tokens, paths to secrets. → Add a redaction pass for known patterns (`token`, `key`, `password`, `Bearer`, `sk-`, etc.) and a hard truncation cap (e.g. 200 KB per log).
- **H.11 / H.12**: `[hint]` prefix used in two hooks but the convention adopted in `language.md` is `[hook-name]`. → Standardize to `[agent-router]` and `[research-keyword-detector]`.

### Agents

- **A.1 / A.2**: Gemini-failure policy contradicts itself between `literature-reviewer.md` (falls back to Claude `WebFetch`) and `gemini-explore.md` (fails loudly, no silent downgrade). `WebFetch` is also not in `literature-reviewer`'s `tools:`. → Pick one policy. Recommend "fail loudly + orchestrator chooses fallback explicitly", and remove `WebFetch` mention.
- **A.4**: Handoffs are prose. Downstream automation has to parse English. → Standardize a YAML handoff block at the end of every agent's "Handoff" section: `artifacts:`, `status:`, `open_risks:`, `next_agent_inputs:`. Document the schema once in `agent-routing.md`.
- **A.5**: `paper-writer.md` requires grep-based term consistency and word counts but `tools:` lacks `Bash`/`Grep`. → Add `Bash` and `Grep` to its tool list.
- **A.7 / A.8**: `gemini-explore` and `viz-reviewer` are mostly thin Gemini wrappers but provisioned at `opus`. → Downgrade to `sonnet` to cut latency and cost.
- **A.9**: `experiment-runner` assumes `error-to-codex` hook routes to `codex-debugger`, but the payload schema is implicit. → Add an explicit hook-payload schema (`run_id`, `script_path`, `traceback`, `env`, `last_commit`) to both files.

### Skills

- **S.2 / S.8**: `/literature-review` mentions a "targeted update append" mode that duplicates `/extend-literature`. → Remove the append mode from `/literature-review`; it becomes "rewrite-only", and `/extend-literature` is the only incremental path.
- **S.3**: `/analyze-results` outputs `analysis.md (or appended per run)` — ambiguous overwrite vs append. → Pick: always append `## Run <run_id>` blocks, never rewrite prior runs except with `--rewrite <run_id>`.
- **S.4**: `/discuss-results` has no preflight. → Add existence + non-trivial-content checks for the 4 input notes.
- **S.5**: `/write-paper` lists `hypotheses.md` as input but preflight only checks 4 other notes. → Either preflight `hypotheses.md` too, or remove from inputs.
- **S.7**: `/review-figures` hard rule references `data/results/raw/` which is not a real path (the project uses `data/raw/` and `data/results/<run_id>/`). → Correct the path.
- **S.9**: Pipeline doesn't gate `/review-figures` between `/analyze-results` and `/write-paper`. → Add `next_skill: /review-figures` to `/analyze-results` (or document the optional gate).

### Infrastructure

- **I.1**: `CLAUDE.md` Zone A says "every claim must carry `[@citekey]`" but `citation-rigor.md` exempts own contributions, definitions, and common knowledge. → Soften Zone A to "every non-original factual claim", defer details to `citation-rigor.md`.
- **I.2**: `language.md` permits a 2–3 line Japanese intro in README, but the README has substantial Japanese sections throughout. → Either relax `language.md` to allow bilingual sections (the user is a Japanese-speaking primary audience), or actually trim README Japanese.
- **I.3**: `reproducibility.md` schema lists `hardware.cpu/gpu/ram_gb`; `repro.py` only writes `hardware.cpu_count`. The reproducibility-check hook (once unblocked by B3) would flag every metadata.json. → Align: simplify the schema to what `repro.py` produces, or extend `repro.py` to emit cpu / gpu / ram_gb.
- **I.5**: `scripts/update.sh` is non-transactional. A failure between rsync and Zone restoration leaves CLAUDE.md as the template placeholder. → Add a `trap ERR` block that restores `CLAUDE.md.before` and aborts.

## Lower-priority majors and minors

Pulled from the per-phase reviews; defer to a later round.

### Skills — gaps

- **S.10**: No `/prepare-submission` skill (venue compliance, packaging).
- **S.11**: No `/release-artifacts` skill (data card, license, Zenodo/OSF).

### Agents — minors

- **A.6**: `viz-reviewer` uses unqualified `analysis.md`; normalize to `docs/research/analysis.md`.
- **A.10**: Document the `script-reviewer` (pre-run) vs `codex-debugger` (post-failure) boundary explicitly.

### Hooks — minors

- **H.13**: `research-keyword-detector` parses `bool(d.get(...))` and would treat the string "false" as truthy. Use `isinstance(v, bool)`.
- **H.14**: `log-cli-tools` `CLI_RE` is leading-anchored only; misses `env FOO=1 codex ...` style invocations.

### Infrastructure — minors

- **I.4**: `pyproject.toml` comment claims a PYTHONPATH bootstrap exists in `repro.py`; it doesn't. Either add it or remove the comment.
- **I.6**: `update.sh` doesn't preflight-check `rsync`, `python3`, `cmp` are present.
- **I.7**: `update.sh` self-bootstrap overwrites itself with `cp` (non-atomic). Use temp file + `mv`.
- **I.8 / I.9**: Onboarding doesn't verify `claude` CLI is installed/authenticated.
- **I.10**: README says `/init-research` copies `repro.py` but omits `viz.py`.
- **I.11**: `.codex/AGENTS.md` includes `fatal` in severity vocabulary; rest of repo uses `blocker/major/minor/nit`.

## Strengths (across all phases)

- Pipeline (lit review → hypothesis → methodology → run → analysis → discussion → paper → review) is linear and lifecycle-complete for the core research loop.
- 3-zone CLAUDE.md cleanly separates immutable rules / project config / session state.
- `update.sh` correctly preserves Zone B, Zone C, and `.claude/logs/` (after recent fixes).
- Reproducibility posture is strong on paper: metadata.json schema, seed handling, dirty git flagging, second-run byte-equality check.
- Agent role separation is clean across lifecycle stages; each agent has concrete output templates.
- External CLI partner usage is deliberate and scoped — Codex for critique, Gemini for multimodal.
- Routing rules are well-documented and centralized in `agent-routing.md` + `routing-keywords.json`.
- `viz.py` template is thoughtfully structured around named profiles + Zone B preference + per-call kwarg overrides.

## Proposed remediation phases

| Phase | Scope | Effort |
|---|---|---|
| **R1: Blockers** | B1 (hypothesis-generator gap mode), B2 (citation-guard absolute paths), B3 (reproducibility-check absolute paths) | ~2-3 file edits |
| **R2: Hook robustness** | H.3, H.4, H.5, H.6, H.7, H.10, H.11, H.12 | hooks/ + settings.json rewrite |
| **R3: Agent contract tightening** | A.1, A.2, A.4 (handoff schema), A.5, A.9 | agents/ rewrite |
| **R4: Skill consistency** | S.2, S.3, S.4, S.5, S.7, S.8, S.9 | skills/ rewrite |
| **R5: Infrastructure consistency** | I.1, I.2, I.3, I.5 | CLAUDE.md, language.md, repro.md, update.sh |
| **R6: Lifecycle gaps** | S.10 (`/prepare-submission`), S.11 (`/release-artifacts`) | new skills |
| **R7: Polish** | All minors | scattered |

R1 alone is roughly 2-3 file edits and removes silent failures. R1+R2+R5 together would close most operational risk. R3+R4 sharpen contracts. R6 is a feature expansion (different category from "fix").
