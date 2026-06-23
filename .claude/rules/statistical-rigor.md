# Statistical rigor

## Pre-registration of analysis

- Decide the primary outcome, the statistical test, the significance threshold, and the stopping rule **before** you look at the data. Record these in `docs/research/methodology.md`.
- Any test added after data inspection must be labeled "exploratory" in the analysis section. Do not present exploratory tests as confirmatory.

## Reporting standard

For every reported test:
- Effect size (Cohen's d, odds ratio, R², etc.) — not just p-values.
- 95% confidence interval (or credible interval if Bayesian).
- Sample size (n).
- Test name and assumptions checked.
- Whether the test was pre-registered or exploratory.
- A structured result ID from `data/results/<run_id>/analysis.json`.

A bare p-value with no effect size and no CI is unacceptable.

## Multiple comparisons

- If running k > 1 tests on the same dataset, apply correction (Holm–Bonferroni, BH-FDR, or report family-wise error rate explicitly).
- Document the family of tests in `methodology.md`.

## Forbidden practices

- **p-hacking.** Do not try multiple tests, exclusions, or transformations until p < 0.05 and report only the winning combination.
- **HARKing.** Do not present a hypothesis discovered after seeing the data as if it were pre-specified.
- **Cherry-picking subgroups.** Subgroup analyses are exploratory unless pre-registered.
- **Outlier removal without justification.** If you remove outliers, define the rule before looking at data and report results both with and without removal.

## Power and sample size

- Compute and report power for the primary test. Aim for power ≥ 0.8 at the smallest effect size you would consider scientifically meaningful (SESOI).
- If power is below 0.8 due to constraints, acknowledge underpowering as a limitation in `discussion.md`.

## Bayesian alternative

If you use Bayesian methods, report the prior, posterior, credible interval, and a sensitivity analysis to the prior. Do not silently switch frameworks.
