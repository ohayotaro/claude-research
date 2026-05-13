# Multi-paper layout

A single research repository may produce multiple papers (main paper + workshop spin-off, journal extension, methods short paper). This file is the **single source of truth** for how papers are identified, where their files live, and how skills/agents/hooks resolve a paper from a user prompt.

Every paper-touching skill (`write-paper`, `peer-review`, `revise`, `prepare-submission`, `release-artifacts`, `add-paper`, `init-research`, `checkpoint`) and every paper-touching agent (`paper-writer`, `peer-reviewer`) MUST follow this rule. Hooks (`citation-guard`) consume the path contract defined here.

`docs/research/` is unchanged: it is the shared experimental substrate across all papers in the same repo.

## 1. Paper identity

### 1.1 Slug

A paper is identified by a `paper_id` string. Rules:

- Regex: `^[a-z0-9][a-z0-9-]{0,31}$` (1–32 chars, lowercase, digits, hyphens; must start with a letter or digit).
- Lowercase only. Reject any input that contains uppercase before normalization (do not silently lowercase — it hides typos).
- No leading/trailing hyphen.
- No dots, underscores, spaces, or path separators.

### 1.2 Reserved slugs (denylist)

These slugs MUST be rejected as `paper_id`, regardless of regex validity:

- Structural directory names that already appear under `docs/paper/` or that may appear as `paper-writer` scaffolds: `submissions`, `figures`, `_template`, `template`, `assets`.
- Reserved literals: `main` is **allowed and is the conventional default**, but `release`, `releases`, `latest`, `current` are reserved.
- Path traversal / filesystem ambiguity: `.`, `..`, `con`, `prn`, `aux`, `nul`, `com1`–`com9`, `lpt1`–`lpt9` (Windows reserved device names).
- Reserved suffix: any slug ending in `-r<digits>` (would collide with submission round suffixes inside the bundle path).

### 1.3 Uniqueness

`paper_id` is unique within a repository. Two entries in Zone B `papers:` with the same `id` is an integrity violation — skills MUST abort with a clear error rather than guess.

## 2. Directory layout

```
docs/paper/<paper_id>/
  draft.md              # if paper.paper_format == markdown_bibtex
  main.tex              # if paper.paper_format == latex
  review-<n>.md         # n = 1, 2, ... — scoped to this paper
  changelog.md          # appended on every write
  rebuttal.md           # post-review rebuttal scaffold
  submissions/
    <venue-slug>-r<round>/
      manifest.json
      checklist.md
      <copied artefacts>
docs/release/
  <release-tag>/        # FLAT — releases are not paper-nested
    manifest.json       # includes "papers": ["<id1>", "<id2>", ...]
    datacard.md
    CITATION.cff
    zenodo.json
docs/research/          # SHARED across all papers — not paper-nested
  lit-review.md
  gaps.md
  hypotheses.md
  methodology.md
  analysis.md
  discussion.md
docs/references.bib     # SHARED across all papers
```

Releases are flat (not `docs/release/<paper_id>/<tag>/`) so a single Zenodo deposit can cover one or more papers. The `manifest.json` records which `paper_id`s the deposit covers.

## 3. Zone B `papers:` registry

```yaml
papers:
  - id: main
    title: null
    venue: null
    paper_format: markdown_bibtex   # or: latex
    status: drafting                # drafting | review | submitted | accepted | published
    derived_from: null              # null OR another paper_id in this same registry
```

### 3.1 Fields

- `id` — required. Slug per §1.
- `title` — string or null. The paper title; informational, not used as a path.
- `venue` — string or null. The target venue for this paper. May differ from the root `target_venue` default.
- `paper_format` — required. `markdown_bibtex` or `latex`. **Per-paper override is authoritative at runtime** (see §4).
- `status` — required. One of the listed values. Skills update this when they transition (e.g. `/peer-review` sets it to `review` on first run; `/prepare-submission` sets it to `submitted`).
- `derived_from` — optional, weak lineage hint. Either `null` or the `id` of another paper in the same registry. Used by `release-artifacts` and human orientation. Does NOT trigger any automatic file inheritance.

### 3.2 Root defaults

The root-level `paper_format` and `target_venue` in Zone B remain, but their role changes:

- **At init**: `/init-research` uses them as the seed values for the initial `papers: [{id: main, ...}]` entry.
- **At `/add-paper`**: used as defaults in the questionnaire (the user can override per-paper).
- **At runtime**: NEVER read by paper-touching skills/agents/hooks. Runtime path and format resolution MUST come from `papers[id == <paper_id>]`. Reading the root at runtime is a bug — it will produce split-brain behavior when a repo has mixed-format papers.

The `paper-template-config.json` is similarly init-time only. Skills do not read it at runtime.

## 4. paper_id resolution

Every paper-touching skill receives an optional `paper_id` argument. Resolution proceeds in this order:

### 4.1 Decision tree

```
INPUT: optional paper_id from user, Zone B papers: registry, filesystem state.

1. If user passed paper_id:
   a. Validate against §1 (slug + denylist). Reject if invalid.
   b. If paper_id IS in registry → use it.
   c. If paper_id IS NOT in registry:
      - If skill is /add-paper or /write-paper → enter add-paper flow (questionnaire,
        append to registry). /write-paper MAY delegate to /add-paper or inline the
        questionnaire; either is acceptable as long as the registry is updated
        BEFORE any file is written.
      - Otherwise → abort with "unknown paper_id <id>; available: [...]" and suggest
        /add-paper.

2. If user did NOT pass paper_id:
   a. If registry is empty → abort. Do NOT silently create `main`. Suggest /add-paper
      or /init-research. (Exception: /init-research itself, which creates main.)
   b. If registry has exactly 1 entry → confirm with the user before proceeding.
      Show the entry's id and title (Japanese). The user can accept or cancel.
      Auto-selecting without confirmation is forbidden — even with a single entry,
      stale registry state is a known footgun.
   c. If registry has multiple entries → AskUserQuestion to pick. Show id + title +
      status for each. Zone C `last_paper_id` MAY be surfaced as a hint ("前回は
      <id> を編集していました") but MUST NOT be auto-selected.
```

### 4.2 Non-interactive contexts

Hooks and automations cannot use `AskUserQuestion`. When a hook needs to resolve a paper from a file path, it does so by **path inference**: extract the path segment immediately after `docs/paper/`. This works because the layout in §2 guarantees the `<paper_id>` segment is always at depth 1 under `docs/paper/`.

If path inference fails (legacy flat layout, ambiguous nesting), the hook MUST log a warning and skip — never guess and never block.

## 5. Lazy migration

Legacy single-paper repos have `docs/paper/draft.md` (or `main.tex`) at the flat top level. Migration to the per-paper layout is **lazy**: it happens the first time a paper-touching skill is invoked, OR the first time `paper-writer` / `peer-reviewer` agent is delegated to. Hooks never trigger migration.

### 5.1 Filesystem state matrix

Before resolving paper_id, inspect the filesystem under `docs/paper/` and Zone B `papers:`. Four states:

| State | Flat files (`docs/paper/draft.md` or `main.tex` at depth 0) | Nested dirs (`docs/paper/<id>/` with content) | Zone B `papers:` | Action |
|---|---|---|---|---|
| **A: clean legacy** | yes | no | absent or empty | Offer migration: `git mv docs/paper/draft.md docs/paper/main/draft.md` (and review-*, changelog.md, rebuttal.md, submissions/). Then append `papers: [{id: main, ...}]` to Zone B using the root `paper_format` as the entry's `paper_format`. Require user confirmation before mutating files. |
| **B: already migrated** | no | yes | present, matches dirs | Proceed normally. No migration. |
| **C: partially manual** | no | yes | absent or doesn't list the dirs | Infer: for each `docs/paper/<id>/` containing a `draft.md` or `main.tex`, propose appending a registry entry to Zone B with inferred `paper_format` (from the file extension present). Show the diff to the user; require confirmation. Do NOT silently scan-and-write. |
| **D: ambiguous** | yes | yes | any | STOP. Refuse to proceed until the user resolves. Surface both layouts in the error message and recommend choosing one. Never auto-merge. |
| **E: orphan registry** | no | no for some `id` | present, lists `id` with no dir | Treat as not-yet-scaffolded. `/write-paper <id>` will scaffold; other skills abort with "paper `<id>` has no draft yet". |

### 5.2 Migration mechanics (state A)

The skill driving migration (whichever paper-skill the user invoked first) MUST:

1. Show the user the planned `git mv` commands and the planned Zone B patch.
2. Wait for explicit confirmation.
3. Execute `git mv` per file (preserves history). Files to move:
   - `docs/paper/draft.md` → `docs/paper/main/draft.md`
   - `docs/paper/main.tex` → `docs/paper/main/main.tex` (if it exists instead of `draft.md`)
   - `docs/paper/review-*.md` → `docs/paper/main/review-*.md`
   - `docs/paper/changelog.md` → `docs/paper/main/changelog.md`
   - `docs/paper/rebuttal.md` → `docs/paper/main/rebuttal.md`
   - `docs/paper/submissions/` → `docs/paper/main/submissions/`
4. Append `papers: [{id: main, title: <from front matter if any>, venue: <root target_venue>, paper_format: <root paper_format>, status: drafting, derived_from: null}]` to Zone B.
5. Re-run the original skill against the new layout.

If `git mv` is unavailable (no git repo) — abort migration. The user should `git init` first.

## 6. citation-guard contract

The `citation-guard` hook runs on Write/Edit/MultiEdit. It SHOULD warn on uncited claims for:

- `docs/research/**/*.md`
- `docs/paper/<paper_id>/draft.md`
- `docs/paper/<paper_id>/main.tex`
- `docs/paper/<paper_id>/review-*.md`
- `docs/paper/<paper_id>/rebuttal.md`

It MUST NOT warn on:

- `docs/paper/<paper_id>/submissions/**` — submission bundle copies (would double-flag the same content).
- `docs/paper/<paper_id>/changelog.md` — bullet log, not prose claims.
- `docs/release/**` — release manifests / data cards.

The hook implements this via path-segment inspection (after `docs/paper/`, the second path segment must be `draft.md` / `main.tex` / `review-*.md` / `rebuttal.md`, not `submissions/`). The exact regex lives in `.claude/hooks/citation-guard.py` and is the only place that hardcodes it.

## 7. Format precedence (mixed-format repos)

If two papers in the same repo have different `paper_format` (one Markdown, one LaTeX), every runtime path must branch on the **resolved per-paper format**, never the root. Specifically:

- `paper-writer` reads `papers[id == <paper_id>].paper_format` and chooses `draft.md` vs `main.tex` accordingly.
- `peer-reviewer` reads the same to know which file to load.
- `prepare-submission` bundles the correct file extension.
- `release-artifacts` includes only the paper directories listed in the release manifest, using each one's resolved format.

Reading root `paper_format` at runtime is a bug. If you see it in a skill or agent file, fix the skill/agent — don't paper over with a fallback.

## 8. Cross-paper coupling under docs/research/

`docs/research/*.md` is shared. If two papers report substantially different subsets of the same experiment (e.g. one focuses on accuracy, the other on robustness), the recommended pattern is:

- Keep the canonical analysis in `docs/research/analysis.md`.
- Each paper's `draft.md` / `main.tex` is free to select a subset and re-narrate. The paper is the narrative; the research notes are the substrate.
- If a paper needs notes that are genuinely paper-specific (an opinion piece, a position paper not backed by the main experiment), create `docs/research/_paper-<paper_id>/<name>.md`. This is the only paper-scoped subtree under `docs/research/`. The underscore prefix prevents the directory from being mistaken for a research-note name.

This pattern is **opt-in**. Most multi-paper repos won't need it.

## 9. Skill argument summary

| Skill | Argument | Required? | Notes |
|---|---|---|---|
| `/add-paper` | `<paper_id>` | yes | Validates slug, interactive questionnaire, appends Zone B |
| `/write-paper` | `[paper_id]` | no | Resolution per §4. Unknown id → /add-paper flow |
| `/peer-review` | `[paper_id]` | no | Review numbering scoped per paper |
| `/revise` | `[paper_id]` | no | |
| `/prepare-submission` | `<paper_id> [--venue=<slug>]` | paper_id yes, venue no | `--venue` is a one-shot override; does NOT mutate Zone B `papers[].venue`. To change the persistent venue, edit Zone B directly or re-run /add-paper |
| `/release-artifacts` | `[--papers=<id1>,<id2>] [--tag=<tag>]` | no, no | If `--papers` omitted: ask the user which paper_ids to include. Release is repo-level, not paper-level |

## 10. Failure modes to avoid

- **Silent paper creation**: a write-path skill must not mint a new paper without user confirmation. This rule overrides any "be helpful" instinct.
- **Auto-selection with one paper**: even when only one paper exists, confirm. Stale Zone B state is the most common surprise in multi-paper repos.
- **Root format fallback**: never `getattr(zone_b.papers[id], "paper_format", zone_b.paper_format)`. The per-paper field is mandatory once the registry exists.
- **Migration during read**: hooks and read-only flows MUST NOT migrate. Only the skill the user invoked may move files, and only after confirmation.
- **Releasing without registry**: `/release-artifacts` must verify each paper_id in the deposit exists in Zone B `papers:` and has at least a draft.

## 11. Why this design

- **Per-paper directory**: makes filesystem state mirror Zone B 1:1. A `ls docs/paper/` is the registry.
- **Flat release**: matches how archives (Zenodo / OSF) actually deposit — one DOI per archive, archives may cover multiple artefacts. Paper-nested releases would force redundant deposits.
- **Confirm-on-resolution**: the dominant failure mode in single-paper workflows is "wrote to the wrong file". In multi-paper repos that risk compounds. Confirmation costs one extra prompt and prevents data loss.
- **Lazy migration**: avoids forcing existing repos to adopt the new layout until they actually need multi-paper support. A repo that only ever produces one paper can sit in the flat layout indefinitely.
