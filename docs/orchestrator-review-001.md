# Archived Orchestrator Review 001

This document is an archive marker for the pre-refactor design audit. The active architecture
is now the Claude + Codex operating model described in `README.md`, `CLAUDE.md`, and
`AGENTS.md`.

The historical audit is intentionally not treated as active guidance. Current routing is
phase/artifact based, uses exactly one Claude subagent (`scientific-author`), and sends all
Codex builder/reviewer work through `scripts/codex_research.py`.
