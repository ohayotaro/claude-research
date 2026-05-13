# Research integrity

These rules are non-negotiable. Any agent or skill that violates them is wrong, regardless of what the user asked for.

## Hard prohibitions

- **No fabrication.** Do not invent data points, results, citations, or quotes. If a number is computed, it must come from a script in `src/` whose run is recorded in `data/results/<run_id>/`.
- **No falsification.** Do not modify recorded results to make them look better. If you find a bug in analysis code, write a new run with a new `run_id` and explain the difference in `docs/research/analysis.md`.
- **No plagiarism.** Every claim that is not your own contribution must carry a citation `[@citekey]` resolvable in `docs/references.bib` (applies to `docs/research/**/*.md` and per-paper drafts under `docs/paper/<paper_id>/`). Paraphrase; do not copy more than a short technical phrase.
- **No selective reporting.** If you ran 5 experiments and 1 supports the hypothesis, you must report all 5. Cherry-picking is fabrication by omission.
- **No p-hacking.** See `statistical-rigor.md`.

## Negative results

- Negative, null, and inconclusive results are first-class. Report them in `docs/research/analysis.md` and in each affected paper's `docs/paper/<paper_id>/draft.md` (or `main.tex`). Do not bury them in supplementary material unless the user explicitly asks.
- A failed experiment is data. Do not delete its `run_id` directory.

## Data handling

- `data/raw/` is append-only. Never overwrite or delete a file under `raw/`. If raw data is wrong, document the error and ingest a corrected copy under a new name.
- `data/processed/` may be regenerated, but the script that produces it must be in `src/` and the regeneration must be reproducible from `raw/`.
- `data/results/<run_id>/` is immutable once written. To revise an analysis, create a new `run_id`.

## Authorship and contribution

- Agents are tools, not authors. The human user is the author of any paper produced. Acknowledge AI assistance per the venue's policy in each paper's `docs/paper/<paper_id>/draft.md` (or `main.tex`).

## When in doubt

Stop and ask the user. Do not guess on integrity questions.
