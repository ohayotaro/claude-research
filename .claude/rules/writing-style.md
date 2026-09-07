# Writing style (papers and research notes)

All paper drafts and `docs/research/*` notes are written in English.

## Artifact purposes

Each written artifact serves one purpose. Write for that purpose; do not reuse text from one
artifact as another.

- **Research notes** (`docs/research/**`) are the process record. They preserve decisions,
  alternatives considered, failures, diagnostics, and enough detail to reconstruct how the
  work was done.
- **Main manuscript** (`docs/paper/<paper_id>/draft.md` or `main.tex`) is the argument for
  the intended reader. It explains the research question, the methods needed to judge the
  evidence, the relevant results, their interpretation, and the consequential limitations.
- **Supplements** hold detailed protocols, additional analyses, and condition-level results.
  Every supplement item is referenced from the main text where it supports a claim.
- **Task artifacts and changelogs** (`.claude/tasks/**`, `docs/paper/<paper_id>/changelog.md`)
  preserve orchestration and implementation history. They are not sources of manuscript prose.

## Manuscript organization

- Reorganize the accepted evidence around the research question. Do not concatenate
  research notes and do not follow the chronology of development.
- Contributions are scientific findings or methods. Quality-control procedures (calibration
  checks, exploratory/confirmatory separation, disclosure practices) and limitations are
  reported, but they are not contributions unless they establish an independent result.
- Adapt structure to the field and article type. IMRaD below is the default, not a universal
  section or page limit.

## Placement of content and caveats

Decide main text versus supplement versus research record by relevance and interpretive
importance. Never decide by whether a result is favorable or statistically significant.

- Main text always keeps: primary endpoint outcomes, consequential failures, important
  departures from the protocol, and evidence that qualifies or contradicts the central claim.
- Supplements may hold detailed breakdowns and supporting checks, with a reference from the
  main text. A central limitation is never confined to a supplement.
- Explain a caveat fully once, in the location where it applies. Elsewhere state its
  implication or refer back; do not repeat its procedural history.
- Limitations in the abstract are proportionate to their interpretive importance. Procedural
  history (which tests were excluded, which comparisons were not made) belongs in Methods or
  Discussion unless it changes how the reader should read the main finding.
- Underlying runs, research records, citations, and result-ID traceability are preserved
  regardless of where the prose lands. See `research-integrity.md`.

## Terminology

- Prefer established disciplinary terms and the user's own vocabulary.
- Do not coin project-specific labels, acronyms, or classifications for ordinary concepts.
  If an ordinary description works, use it.
- When a new term is necessary, define it on first use with its purpose and a concrete
  example, and say whether it is a study-specific definition or established usage.
- Explain the subject before showing an internal identifier (run ID, result ID, task ID).
  Identifiers are for traceability, not substitutes for meaning.

## Structure: IMRaD

- **Introduction** — context, gap, contribution claims, paper structure.
- **Related work** — survey, positioning. May come before or after methods depending on venue.
- **Methods** — what you did, in enough detail to reproduce. Cite tools and datasets.
- **Results** — what you found. Numbers, figures, tables. No interpretation here.
- **Discussion** — interpretation, implications, limitations, future work.
- **Conclusion** — short summary of contribution and impact.

## Voice and tense

- Active voice by default. "We trained the model on ..." not "The model was trained on ...".
- Past tense for what you did. Present tense for what is true / what figures show.

## Hedging

- Hedge claims to match evidence, but do not over-hedge.
- "Our results suggest X" is fine when the effect is real but not definitive.
- Avoid stacked hedges: not "may potentially possibly indicate".

## Precision

- Quantify whenever possible. "30% improvement (95% CI [25, 35])" beats "much better".
- Define every acronym on first use.
- Use the same name for the same thing throughout. Pick a term in the introduction and stick with it.

## Figures and tables

- Every figure and table is numbered and referenced in the text.
- Captions are self-contained: a reader looking only at figures should grasp the result.
- Axes labeled with units. Error bars defined in the caption (SD, SE, 95% CI?).

## Citations

- See `citation-rigor.md`. Every non-original claim cites a source.

## Length discipline

- Brevity comes from selection, not from deleting consequential content. Decide what the
  reader needs to judge the claim, then cut sentences that do not change that judgment.
- Do not shorten by removing a limitation that qualifies the main finding; relocate or
  condense it instead, following the placement rules above.
- No "In this paper, we will discuss ..." filler. Start with substance.

## Forbidden phrases

- "It is well known that" — cite it instead.
- "Recent advances" — be specific about which advances.
- "Our novel approach" — let the reader judge novelty.
