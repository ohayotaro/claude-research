---
name: release-artifacts
description: Prepare a local archival release package for code, data cards, manifests, and citation metadata; never deposit externally.
when_to_use: After paper artifacts are accepted for release preparation.
---

# /release-artifacts

This is a PM-orchestrated multi-phase skill. Codex builder handles deterministic packaging
and validation. `scientific-author` writes human-facing citation, data-card, and limitation
prose. The PM never deposits externally from this skill.

Outputs:
- `docs/release/<release-tag>/`
- optional `CITATION.cff`
- manifests and data cards

Workflow:
1. Resolve `--papers` argument: if omitted, ask the user which `paper_id`s to include. Validate each against Zone B `papers:` registry per multi-paper.md §4.
2. PM validates registry and pre-conditions: selected papers exist, release tag is resolved,
   licenses are known, data sensitivity and raw-data exclusions are clear, reproducibility
   metadata exists, result ledgers are available, and required manuscript artifacts are local.
3. PM creates `.claude/tasks/<task-id>/brief.md` for Codex builder with selected paper IDs,
   release tag, output directory, inclusion/exclusion rules, data sensitivity constraints,
   and validation requirements for manifest generation, package integrity, checksums,
   reproducibility metadata, ledger availability, and raw-data exclusions.
4. PM runs `python scripts/codex_research.py build <task-id> --prompt-file .claude/tasks/<task-id>/brief.md`.
5. PM invokes `scientific-author` with mode `release-prose` for
   `docs/release/<release-tag>/datacard.md`, prose fields in
   `docs/release/<release-tag>/CITATION.cff`, and limitation prose. The invocation must
   exclude manifests, checksums, package artifacts, deposit payloads, and generated evidence.
6. PM reruns package validation and evidence traceability checks when release prose changes.
7. Require final explicit user approval before any external deposit, DOI creation, upload,
   credential use, or release. Do not include `data/raw/**` when Zone B data sensitivity is
   not `none` unless the user explicitly approves.
8. PM updates Zone C with `current_phase: release`, `last_skill_run: release-artifacts`,
   and next action.
