# Research integrity

These rules are non-negotiable. Any agent or skill that violates them is wrong, regardless of what the user asked for.

## Hard prohibitions

- **No fabrication.** Do not invent data points, results, citations, or quotes. If a number is computed, it must come from a script in `src/` whose run is recorded in `data/results/<run_id>/` and, for completed analyses, in `analysis.json`.
- **No falsification.** Do not modify recorded results to make them look better. If you find a bug in analysis code, write a new run with a new `run_id` and explain the difference in `docs/research/analysis.md`.
- **No plagiarism.** Every claim that is not your own contribution must carry a citation `[@citekey]` resolvable in `docs/references.bib` (applies to `docs/research/**/*.md` and per-paper drafts under `docs/paper/<paper_id>/`). Paraphrase; do not copy more than a short technical phrase.
- **No selective reporting.** If you ran 5 experiments and 1 supports the hypothesis, you must report all 5. Cherry-picking is fabrication by omission.
- **No p-hacking.** See `statistical-rigor.md`.

## Negative results and placement

- Negative, null, and inconclusive results are first-class. The research record (`docs/research/analysis.md`) keeps every result in full. Each affected paper reports them through a summary in the main text (`docs/paper/<paper_id>/draft.md` or `main.tex`) plus a referenced supplement where detail is needed.
- Main text always keeps: primary endpoint outcomes, consequential failures, important departures from the protocol, and any evidence that qualifies or contradicts the central claim.
- Detailed breakdowns and supporting checks may go in a supplement that the main text references. Placement is decided by relevance and interpretive importance, never by whether a result is favorable or statistically significant. A central limitation is never confined to a supplement.
- Placement does not change the record: every run, research note, citation, and result-ID reference is preserved wherever the prose lands.
- A failed experiment is data. Do not delete its `run_id` directory.
- Artifact purposes and the main-text/supplement decision rule are defined in `writing-style.md`.
- When transferring numerical claims into canonical prose, cite the structured ledger result as `[result:<result_id>]` or `[result:<run_id>:<result_id>]`.

## Data handling

- `data/raw/` is append-only. Never overwrite or delete a file under `raw/`. If raw data is wrong, document the error and ingest a corrected copy under a new name.
- `data/processed/` may be regenerated, but the script that produces it must be in `src/` and the regeneration must be reproducible from `raw/`.
- `data/results/<run_id>/` is immutable once written. To revise an analysis, create a new `run_id`.

## Authorship and contribution

- Agents are tools, not authors. The human user is the author of any paper produced. Acknowledge AI assistance per the venue's policy in each paper's `docs/paper/<paper_id>/draft.md` (or `main.tex`).

## When in doubt

Stop and ask the user. Do not guess on integrity questions.
