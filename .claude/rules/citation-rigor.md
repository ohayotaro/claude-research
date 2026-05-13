# Citation rigor

## When to cite

Cite whenever you make a factual claim that is not (a) your own current contribution, (b) a definition you are introducing, or (c) common knowledge in the field. When in doubt, cite.

Examples that **require** a citation:
- "Transformer-based models have surpassed RNNs on machine translation."
- "The standard treatment for X is Y."
- "Prior work has shown that Z."

Examples that **do not** require a citation:
- "We propose ..."
- "In this paper we define ..."
- "2 + 2 = 4."

## Citation format

- All citations use Pandoc / BibTeX inline syntax: `[@authoryear_keyword]`. Multiple: `[@a2024_attn; @b2023_scaling]`.
- Cite keys follow the pattern `<firstauthorlastname><year>_<short-tag>`, lowercase: `vaswani2017_attention`, `hinton2015_distillation`.
- Every cite key in any `.md` or `.tex` file under `docs/research/` or under `docs/paper/<paper_id>/{draft.md,main.tex,review-*.md,rebuttal.md}` **must** resolve to an entry in `docs/references.bib`. The `citation-guard` hook checks this on every Write/Edit. Submission bundle copies under `docs/paper/<paper_id>/submissions/` and per-paper `changelog.md` are exempt — see `.claude/rules/multi-paper.md` §6.

## BibTeX entries

- Prefer `@article` / `@inproceedings` / `@book` / `@misc` (for arXiv preprints, with `archivePrefix = {arXiv}`).
- Always include: `author`, `title`, `year`. Include `journal` / `booktitle`, `volume`, `pages`, `doi` when available.
- Use double-braced titles to preserve casing: `title = {{BERT}: Pre-training of Deep Bidirectional Transformers}`.
- Sort by cite key. The `literature-reviewer` agent maintains sort order.

## Secondary citations are forbidden

If paper X cites paper Y and you want to refer to a claim in Y, read Y. Do not write `[as cited in X]` unless Y is unobtainable, in which case say so explicitly.

## Self-plagiarism

If reusing wording from the user's prior work, cite it like any other source.
