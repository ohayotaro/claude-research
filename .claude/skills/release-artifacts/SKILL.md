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
1. Check licenses, data sensitivity, raw-data exclusions, reproducibility metadata, and ledger availability.
2. Require explicit approval before external deposit, DOI creation, upload, or release.
3. Do not include `data/raw/**` when Zone B data sensitivity is not `none` unless the user explicitly approves.
