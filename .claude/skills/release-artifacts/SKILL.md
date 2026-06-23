---
name: release-artifacts
description: Prepare a local archival release package for code, data cards, manifests, and citation metadata; never deposit externally.
when_to_use: After paper artifacts are accepted for release preparation.
---

# /release-artifacts

Codex builder handles deterministic packaging and validation. `scientific-author` writes
human-facing citation, data-card, and limitation prose.

Outputs:
- `docs/release/<release-tag>/`
- optional `CITATION.cff`
- manifests and data cards

Workflow:
1. Resolve `--papers` argument: if omitted, ask the user which `paper_id`s to include. Validate each against Zone B `papers:` registry per multi-paper.md §4.
2. Check licenses, data sensitivity, raw-data exclusions, reproducibility metadata, and ledger availability.
3. Require explicit approval before external deposit, DOI creation, upload, or release.
4. Do not include `data/raw/**` when Zone B data sensitivity is not `none` unless the user explicitly approves.
5. Update Zone C with `current_phase: release` and next action.
