# Improve manuscript focus and PM communication

Status: Proposed. Implementation has not started.

## Objective and scope

Update the orchestration template so manuscripts present a focused scientific
argument and PM replies use clear, familiar language. Preserve evidence
traceability, reproducibility, uncertainty, and honest reporting of negative,
null, failed, and inconclusive findings.

This plan records user feedback and read-only inspection of this template and
`/Users/ryotaro/ieee-mic-abstract`. It does not authorize edits to that project's
manuscripts, analysis plans, or results.

## Findings and supporting evidence

The inspected materials include writing rules, drafting and review workflows,
the example project's manuscripts, changelog, existing review, and saved PM
context. Chat transcripts were not inspected. Manuscript findings are directly
observed; effects of saved context on later conversation are inferred.
Line references reflect the files as inspected and may shift after edits.

### Template weaknesses

- `.claude/rules/writing-style.md:1` applies a shared policy to papers and research
  notes. Its brevity instruction does not explain how to select material or
  distribute it between main text, supplements, and research records.
- `.claude/skills/write-paper/SKILL.md:13` takes research notes as inputs and
  requires evidence alignment, but lacks an explicit editorial selection step.
- `.claude/rules/research-integrity.md:10` requires comprehensive reporting and
  discourages placing negative results in supplements without an explicit user
  request. This can push excessive detail into the main text.
- `.claude/rules/language.md` defines language boundaries but provides little
  guidance on clear explanations or unnecessary terminology.
- The peer-review and revision skills emphasize completeness and correction
  without explicitly requiring deletion, consolidation, or relocation.

### Operational examples

Paths below are relative to `/Users/ryotaro/ieee-mic-abstract`.

- `docs/paper/trpms/main.tex:244`: the contribution list includes disclosure of
  exploratory/confirmatory separation and discussion of an unmeasured detection
  ceiling. These primarily concern credibility and limitations unless they
  establish an independent scientific contribution.
- `docs/paper/trpms/main.tex:222`: the abstract devotes substantial attention to
  excluded tests, a compound hypothesis's status, and comparisons not made.
  Important limitations must remain visible, but procedural history competes
  with the scientific question and findings.
- `docs/paper/trpms/main.tex:388` onward: statistical analysis and disclosure
  describe allocation decisions, timestamp limitations, and sequences of checks
  in detail. Related caveats recur elsewhere in the manuscript.
- Terms such as `surface`, `adjudication`, and `pillar` recur in the manuscript.
  These are not necessarily incorrect, but their project-specific use imposes
  a learning burden where ordinary descriptions may suffice.
- `CLAUDE.md:188` onward: Zone C contains lengthy retrospectives, emphatic
  self-evaluation, and dense internal identifiers. The checkpoint skill instead
  calls for a short next action and compact notes. Repeatedly loading this
  context may perpetuate opaque or defensive PM explanations.
- `.claude/tasks/trpms-review-1/review.md`: the existing independent review caught
  unsupported equality language and substantive inconsistencies. Preserve this
  useful evidence review while adding editorial assessment.

The manuscript's long opening LaTeX comments do not appear in the rendered paper
and must not be counted as visible manuscript verbosity.

## Proposed changes

### 1. Separate writing policies by artifact purpose

Targets: `.claude/rules/writing-style.md` and
`.claude/agents/scientific-author.md`.

- Research notes preserve decisions, alternatives, failures, diagnostics, and
  enough detail to reconstruct the research process.
- Main manuscripts explain the scientific question, necessary methods, relevant
  results, interpretation, and consequential limitations for the intended reader.
- Supplements contain detailed protocols, additional analyses, and condition-level
  results, with clear references from the main text.
- Task artifacts and changelogs preserve orchestration and implementation history.

Require manuscripts to reorganize accepted evidence around the research question,
rather than concatenate notes or follow development chronology. Adapt structure
to the field and article type; do not impose a universal section or page limit.

### 2. Establish a concise editorial brief before drafting

Targets: `.claude/skills/write-paper/SKILL.md`, the scientific-author definition,
and initialization/configuration instructions only if new fields are needed.

Before substantial drafting, identify:

- Intended audience, article type, and known venue constraints.
- Research question and central evidence-supported message.
- Scientific contributions, distinguished from quality-control procedures and
  limitations.
- Section outline, provisional length allocation, and essential figures/tables.
- Placement of supporting material in main text, supplements, or records.

Use existing context and reasonable provisional assumptions. Do not create a
mandatory approval gate or another extensive planning artifact. Ask only when a
missing choice would materially change scope. Editorial selection must not change
registered hypotheses, endpoints, analysis status, or multiplicity decisions
after observing results.

### 3. Preserve full reporting with appropriate placement

Targets: `.claude/rules/research-integrity.md`, writing-style rules, and
`.claude/skills/discuss-results/SKILL.md`.

- Keep primary endpoint outcomes, consequential failures, important departures,
  and evidence qualifying or contradicting the central claim visible in main text.
- Allow detailed breakdowns and supporting checks in referenced supplements.
- Select placement by relevance and interpretive importance, never favorability
  or statistical significance. Do not conceal a central limitation in a supplement.
- Preserve all underlying runs and research records, source citations, and
  result-ID traceability.
- Explain a caveat fully in its appropriate location. Elsewhere state its
  implication or refer back instead of repeating its procedural history.
- Keep abstract limitations proportionate to their interpretive importance.

### 4. Establish plain-language PM communication

Targets: `CLAUDE.md` Zone A, `.claude/rules/language.md`, and manuscript terminology
guidance in writing-style rules.

- Lead with the answer or finding, then its reason and any necessary next action.
- Prefer the user's vocabulary and established disciplinary terminology.
- Avoid inventing names, acronyms, or classifications for ordinary concepts.
- Explain necessary new definitions with their purpose and a concrete example;
  distinguish study-specific definitions from established usage.
- Explain the subject before displaying an internal identifier. Use IDs for
  traceability rather than as substitutes for meaning.
- Translate agent handoffs into reader-facing explanations.
- Provide technical depth when requested or necessary for a decision.

Illustrative wording: "The sensitivity-correction test failed its calibration
check, so we report the measurements descriptively and cannot claim an
improvement from that test."

A glossary alone is insufficient: first avoid unnecessary terminology. Do not
create a terminology registry unless the project actually needs one.

### 5. Keep persistent PM context compact and current

Targets: `.claude/skills/checkpoint/SKILL.md`, Zone C conventions, and the session
hook only if enforcement or display changes are needed.

- Store current objectives, accepted decisions, unresolved issues, next action,
  and links to detailed records.
- Keep field values consistent with the schema: run IDs are IDs and skill names
  are names, rather than retrospective narratives.
- Move detailed correction histories and retrospectives to task records or
  changelogs. Preserve unresolved caveats and approval boundaries.
- Avoid dramatic emphasis, self-evaluation, and unexplained chains of IDs.
- Reconcile superseded instructions when updating active context. The example's
  Zone B still mentions retired agents and skills; define a way to flag stale
  notes without automatically overwriting project-owned configuration.

### 6. Add editorial assessment to review and revision

Targets: peer-review and revise skills, and the scientific-author definition.

Retain independent read-only scientific review and assess whether:

- The contribution is understandable without learning project history.
- Methods and limitations are complete at the appropriate level and location.
- Repetition, unnecessary definitions, or process narratives obscure the findings.
- Figures and tables communicate the mechanism and evidence effectively.

For each substantive revision, consider correction, deletion, consolidation, or
relocation as well as addition. After resolving scientific findings, edit the
whole manuscript so local fixes do not accumulate into repetitive prose. Never
remove justified caveats merely to produce a cleaner story.

## Implementation order

1. Update writing and integrity policies together to resolve conflicting guidance.
2. Update the author and drafting workflow to apply those policies.
3. Update PM communication and checkpoint instructions.
4. Update review and revision criteria.
5. Check related instructions for contradictions and update focused contract
   tests only where they meaningfully enforce changed behavior.

Use existing roles; no additional agent is needed. Keep template implementation
separate from edits to the operational research project.

## Acceptance criteria

- A drafting brief separates contributions, validation procedures, and limitations
  and assigns supporting detail to an appropriate destination.
- A representative revised passage foregrounds the scientific message while
  retaining consequential limitations and evidence references.
- No primary or contradictory result disappears through editorial selection.
- PM examples are understandable without memorizing internal identifiers.
- Checkpoint output contains concise current state and links to detailed history,
  with schema-appropriate values.
- Review instructions detect both missing evidence and unnecessary exposition.
- Routing, independent review, approval boundaries, and reproducibility remain intact.

Evaluate prose behavior with a small before/after example during implementation;
static string checks alone cannot establish readability. Do not rewrite the
example project's canonical manuscript without a separate request.

## Validation

Run the required repository checks when implementing the changes:

```bash
uv run --extra dev pytest -q
uv run --extra dev ruff check .
uv run --extra dev mypy scripts tests .claude/hooks
python3 -m compileall -q scripts .claude/hooks tests
bash -n scripts/setup.sh scripts/update.sh
```

When analysis artifacts or canonical prose change, also use
`scripts/research_evidence.py` to validate ledgers and prose result-ID traceability.
This plan changes neither category and does not validate the example project's
scientific results.
