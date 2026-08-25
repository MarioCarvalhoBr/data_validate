---
paths: ["data_validate/**"]
---

# Performance

## Measure, don't guess

- Measure before and after any change claimed to improve performance —
  `make bench` (pytest-benchmark) or `tools/harness/profile_pipeline.py`.
  A performance PR without before/after numbers is not reviewable as one.

## Budget

- Target: a full validation run over a ~5,000-indicator bundle completes in
  under 10 seconds on CI hardware. A change that regresses this budget
  needs either a fix or an explicit, reviewed trade-off note in its ADR/PR.

## Techniques

- Vectorise: pandas mask/`merge`/`groupby`/`str` operations over
  `.iterrows()` — see `.claude/rules/dataframe-conventions.md`.
- Normalize each sheet's data once, at load time, into its typed
  `SheetFrame`; rules read the normalized frame, they never re-parse or
  re-coerce it.
- Cache expensive, repeated lookups: translation/message-catalog lookups
  and spell-check dictionary lookups are memoised per run, not repeated per
  cell.
- Avoid defensive copies (`.copy()` "just in case") in hot paths — pandas 3
  Copy-on-Write already protects against accidental mutation; a manual copy
  in a rule function is usually redundant and costs memory and time on
  large sheets.

## Never do

- Never claim a performance improvement without a `make bench` number.
- Never add `.iterrows()` or a per-cell Python loop to a rule that could be
  vectorised.
- Never re-normalize or re-parse a column inside a rule that already
  receives a normalized `SheetFrame`.
