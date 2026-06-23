---
name: add-paper
description: Register a new paper variant in Zone B and scaffold docs/paper/<paper_id>/.
when_to_use: When one project needs multiple manuscripts from the same research substrate.
---

# /add-paper

The Research Lead performs this deterministic update directly.

Inputs:
- Required `<paper_id>`
- Zone B `papers:` registry
- Root paper format and target-venue defaults

Workflow:
1. Require initialized Zone B. If uninitialized, stop and suggest `/init-research`.
2. Validate `<paper_id>` with `.claude/rules/multi-paper.md`: lowercase slug, no reserved names, no traversal, no duplicate registry entry.
3. If legacy flat `docs/paper/draft.md` or `docs/paper/main.tex` exists, perform the multi-paper lazy migration first, then ask the user to re-run `/add-paper`.
4. Ask the user for title, venue, format, and optional `derived_from`.
5. Append exactly one entry to Zone B `papers:` without changing existing entries.
6. Create `docs/paper/<paper_id>/draft.md` or `docs/paper/<paper_id>/main.tex` plus `changelog.md` only when absent.
7. Update Zone C `last_paper_id` as a hint.

Never copy manuscript content from `derived_from`, never silently mutate an existing entry, and never auto-run `/write-paper`.
