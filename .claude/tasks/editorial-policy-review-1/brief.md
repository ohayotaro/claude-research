# Review brief: editorial policy and PM communication template changes

Read-only review. Do not modify files.

## Context

Plan: `.codex/plans/2026-09-07-writing-and-pm-communication.md`
Task breakdown: `.codex/plans/2026-09-07-writing-and-pm-communication-tasks.md`
Diff under review: `.claude/tasks/editorial-policy-review-1/diff.patch` (also visible via `git diff`)

Files changed: `.claude/rules/writing-style.md`, `.claude/rules/research-integrity.md`,
`.claude/rules/language.md`, `.claude/agents/scientific-author.md`,
`.claude/skills/{write-paper,discuss-results,checkpoint,peer-review,revise}/SKILL.md`,
`CLAUDE.md` Zone A, `tests/test_repository_contract.py`.

## Questions

1. Contradictions: does any rule, skill, or agent file now conflict with another on where
   negative/null results may be placed, on brevity vs completeness, or on Zone C content?
2. Integrity: could any new wording be read as permission to hide unfavorable results,
   weaken limitations, or change hypotheses/endpoints after seeing results?
3. Routing and permissions: are the role boundaries (Research Lead, scientific-author,
   Codex builder, Codex reviewer), approval gates, and reproducibility contract unchanged?
4. Workability: are the editorial brief, revision operations, and checkpoint rules concrete
   enough for an agent to follow without a further planning artifact? Any step that would
   block or create an unwanted approval gate?
5. Tests: does the new contract test enforce changed behavior without over-constraining
   wording? Any marker that is fragile?

## Before/after example (evaluate whether the new policy produces the "after")

Before (abstract-style sentence under old guidance):
"We pre-registered three confirmatory tests; two were excluded after the sensitivity-
correction test failed its calibration check (run 2026-08-30T09-11-42_f0e1d2c3, results
R-07, R-08), the compound hypothesis H2 therefore remains unassessed, and no comparison with
the vendor baseline was performed; descriptive statistics are reported for all surfaces."

After (intended under new guidance):
"Detection efficiency improved by 12% (95% CI [8, 16]) [result:R-05]. The
sensitivity-correction test failed its calibration check, so we report those measurements
descriptively and cannot claim an improvement from that test [result:R-07]; details are in
the Methods."

## Output format

Findings grouped by question, each with severity (blocker / major / minor), file and line,
and a concrete suggested fix. End with an overall verdict: accept / accept with minor edits /
revise.
