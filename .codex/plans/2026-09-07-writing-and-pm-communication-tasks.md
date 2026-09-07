# Task breakdown: manuscript focus and PM communication

Source plan: `2026-09-07-writing-and-pm-communication.md`
Status: Proposed. Tasks are ordered so that each later task builds on an earlier one.
Owner: Research Lead (template maintenance). No Codex builder needed; all edits are
Markdown policy/skill files plus focused contract tests. Nothing in the example project
`/Users/ryotaro/ieee-mic-abstract` is touched.

Constraints observed from the current repository:

- `tests/test_repository_contract.py` requires `context: fork` + `agent: scientific-author`
  in `write-paper`, `revise`, `discuss-results`; these skills must not mention
  `codex_research.py`. `peer-review` is a Codex-runner skill and must stay that way.
- `checkpoint` writes only between `<!-- ZONE_C_BEGIN -->` / `<!-- ZONE_C_END -->`;
  `session-start.py` prints `next_action` from Zone C. Zone C keys must stay unchanged so
  `update.sh` backup/restore and the hook keep working.
- Language rule: all edited files are English; only chat replies are Japanese.

---

## T1. Writing policy split by artifact purpose

Plan section: 1 (and part of 3).
Files: `.claude/rules/writing-style.md`

Changes:
1. Add a top section "Artifact purposes" with four short entries:
   research notes (process record), main manuscript (argument for the reader),
   supplements (detailed protocols, condition-level results, referenced from main text),
   task artifacts / changelogs (orchestration history).
2. Add "Manuscript organization": reorganize accepted evidence around the research
   question; do not concatenate notes or follow development chronology; adapt structure to
   field and article type; no universal section/page limit.
3. Add "Placement of caveats": explain a caveat fully once in its proper location; elsewhere
   state its implication or refer back. Abstract limitations proportionate to interpretive
   importance. Placement is chosen by relevance, never by favorability or significance.
4. Add "Terminology": prefer established disciplinary terms; do not coin project-specific
   labels for ordinary concepts; define a new term with purpose and example on first use;
   distinguish study-specific definitions from established usage.
5. Keep existing IMRaD, voice, hedging, precision, figure, citation, length, and forbidden
   phrase sections. Reword "Length discipline" so brevity is about selection, not deletion
   of consequential limitations.

Acceptance: the file states where each kind of content goes and gives a decision rule for
main text vs supplement that is independent of result direction.

## T2. Research-integrity: full reporting with appropriate placement

Plan section: 3.
Files: `.claude/rules/research-integrity.md`

Changes:
1. Replace the "Negative results" bullet that discourages supplements with:
   - primary endpoint outcomes, consequential failures, important departures from protocol,
     and evidence qualifying or contradicting the central claim stay in main text;
   - detailed breakdowns and supporting checks may go in referenced supplements;
   - placement never depends on favorability or significance; a central limitation is never
     confined to a supplement;
   - all runs, records, citations, and result-ID traceability are preserved regardless of
     placement.
2. Add a one-line cross-reference to `writing-style.md` "Artifact purposes".
3. Leave "No selective reporting", data handling, and authorship untouched.

Acceptance: no contradiction between `research-integrity.md` and `writing-style.md` on
where negative/null results may live.

## T3. Scientific-author: editorial brief and purpose-aware drafting

Plan sections: 1, 2, 6.
Files: `.claude/agents/scientific-author.md`

Changes:
1. Add section "Editorial brief" used in `manuscript-drafting` and `revision-and-rebuttal`
   modes. Before substantial drafting, record (in the handoff or at the top of the working
   notes, not a new mandatory artifact):
   audience / article type / venue constraints; research question and central
   evidence-supported message; contributions vs quality-control procedures vs limitations;
   section outline with provisional length allocation and essential figures/tables;
   destination of each supporting item (main / supplement / research record).
   Use existing context and provisional assumptions; ask only when a missing choice would
   materially change scope.
2. Add guard: editorial selection must not alter registered hypotheses, endpoints,
   analysis status, or multiplicity decisions after results are observed.
3. Add "Revision operations": for each finding consider correction, deletion,
   consolidation, or relocation, not only addition; after resolving findings, pass over the
   whole manuscript to remove accumulated repetition; never remove a justified caveat for a
   cleaner story.
4. Reference `writing-style.md` artifact purposes for mode-to-artifact mapping
   (research modes write process records; manuscript modes write the argument).

Acceptance: the agent definition names the brief items and the four revision operations;
evidence rules section unchanged.

## T4. write-paper and discuss-results skills

Plan sections: 2, 3.
Files: `.claude/skills/write-paper/SKILL.md`, `.claude/skills/discuss-results/SKILL.md`

Changes:
1. `write-paper` workflow: insert a step after paper_id resolution: "Produce the editorial
   brief (see scientific-author) and state main/supplement/record placement for each result
   family before drafting." Add step: "Reorganize around the research question; do not
   transcribe research notes." Keep steps 2-5 and frontmatter unchanged.
2. `discuss-results` workflow: add "Rank limitations by interpretive importance; state the
   implication of each once; do not restate procedural history already in
   `methodology.md` / `analysis.md`." Keep frontmatter unchanged.
3. Do not add `codex_research.py` references (contract test).

Acceptance: both skills still pass `test_author_skills_use_explicit_agent_fork` and
`test_no_skill_mixes_author_fork_with_codex_runner`.

## T5. Plain-language PM communication

Plan section: 4.
Files: `CLAUDE.md` Zone A (Operating Model), `.claude/rules/language.md`

Changes:
1. Zone A, after "Speak with the user in Japanese by default": add a short
   "Communication" paragraph: lead with the answer/finding, then reason, then next action;
   use the user's vocabulary and disciplinary terms; do not invent names, acronyms, or
   classifications; explain the subject before showing an internal ID; translate agent
   handoffs into reader-facing explanations; give technical depth when asked or when a
   decision needs it.
2. `language.md`: add section "Clarity (applies to the Japanese chat surface)" with the same
   rules plus one illustrative sentence (the plan's sensitivity-correction example, rendered
   in Japanese as the chat example and English as the manuscript example). State that a
   glossary is not a substitute for avoiding unnecessary terminology and that no terminology
   registry is created unless a project needs one.
3. Keep Zone A edit minimal; this is a template-maintenance change and must remain inside
   the immutable-zone text that `update.sh` replaces.

Acceptance: a reader can follow a PM reply without memorizing run IDs or task IDs.

## T6. Checkpoint and Zone C hygiene

Plan section: 5.
Files: `.claude/skills/checkpoint/SKILL.md`; `CLAUDE.md` Zone C comment line only if
needed; `.claude/hooks/session-start.py` only if a display change is required (default:
no change).

Changes:
1. Add "Content rules" to `checkpoint`: Zone C holds current objectives, accepted
   decisions, unresolved issues, next action, and links to detailed records. Field values
   are schema-typed: `last_run_id` is an ID, `last_skill_run` is a skill name, `notes` is at
   most 4 lines. No retrospectives, self-evaluation, emphatic language, or bare chains of
   IDs; move history to `.claude/tasks/**` or the paper changelog and link it.
2. Add "Stale context": when a note references a retired skill/agent/field, the checkpoint
   marks it `stale:` in `notes` with the replacement, and never edits Zone B automatically.
3. Optional: add a `stale_notes` flag consideration for `session-start.py` display. Decide
   during implementation; default is to skip to keep the hook unchanged.

Acceptance: checkpoint output example in the skill file fits the schema and is under
15 lines; `session-start.py` tests unchanged.

## T7. Editorial assessment in peer-review and revise

Plan section: 6.
Files: `.claude/skills/peer-review/SKILL.md`, `.claude/skills/revise/SKILL.md`

Changes:
1. `peer-review`: extend the rubric in step 2 with an "Editorial assessment" block the
   reviewer must answer in addition to the scientific review:
   contribution understandable without project history; methods and limitations complete at
   the right level and location; repetition / unnecessary definitions / process narrative
   obscuring findings; figures and tables communicate mechanism and evidence.
   Reviewer stays read-only; keep the `codex_research.py review` invocation unchanged.
2. `revise`: add step "For each finding choose correction, deletion, consolidation, or
   relocation; after all findings, do a whole-manuscript pass for accumulated repetition."
   Keep step 4 (do not weaken limitations).

Acceptance: review output template lists both evidence findings and editorial findings.

## T8. Consistency sweep and contract tests

Plan section: implementation order step 5.
Files: `tests/test_repository_contract.py`; other `.claude/rules/*.md`, `.claude/skills/**`
only where a contradiction is found; `README.md` skill table only if a description changed.

Changes:
1. Grep for guidance that contradicts T1/T2 (e.g. any remaining "do not bury in
   supplementary material" phrasing, or `checkpoint` descriptions elsewhere) and align.
2. Add focused contract tests only where they enforce changed behavior:
   - `writing-style.md` contains "Artifact purposes";
   - `scientific-author.md` contains "Editorial brief" and the words "relocation" and
     "consolidation";
   - `peer-review` SKILL contains "Editorial assessment";
   - `checkpoint` SKILL contains the notes line limit.
   Do not add readability string checks beyond these markers.
3. Write one before/after passage (in the task record or PR description, not in the
   repository docs) to check that the revised policy foregrounds the scientific message
   while keeping consequential limitations and result references.

## Validation (run after T8)

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
uv run --extra dev mypy scripts tests .claude/hooks
python3 -m compileall -q scripts .claude/hooks tests
bash -n scripts/setup.sh scripts/update.sh
```

`scripts/research_evidence.py` is not needed: no ledgers or canonical prose change.

## Suggested batching

- Batch 1 (policy): T1, T2 — one commit, resolves the guidance conflict first.
- Batch 2 (author workflow): T3, T4.
- Batch 3 (PM surface): T5, T6.
- Batch 4 (review loop + tests): T7, T8, then validation and a fresh Codex read-only
  review of the whole diff through `scripts/codex_research.py review`.
