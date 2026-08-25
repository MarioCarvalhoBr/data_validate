---
paths: ["data_validate/**"]
---

# DataFrame conventions

## Immutability and dtypes

- Treat DataFrames as immutable once loaded: pandas 3 Copy-on-Write is the
  baseline, but new/migrated code must not rely on CoW alone — a rule
  function receives a frame and returns issues, it does not mutate the
  frame it was given.
- Use nullable, typed dtypes end to end: `Int64`, `Float64`,
  `string[pyarrow]` — not the legacy `object`/`float64`-with-`NaN`
  combination. Normalize dtypes once, at load time, not per-rule.

## No `iterrows`

- Never use `.iterrows()` (or `.itertuples()` as a substitute for real
  vectorisation) inside a validation rule. Use boolean masks,
  `pd.to_numeric(errors="coerce")`, `.str` accessors, `merge`/`isin`,
  `groupby`, or a `MultiIndex` by level. Build the list of issues from the
  masked/failing index, not from a Python loop over rows.

## Spreadsheet row numbers

- A pandas index is 0-based and excludes header rows; the number a user
  sees in Excel/LibreOffice is not `idx`. Convert only through the shared
  helper — never write `idx + 2` (or `+ 3`) inline at a call site:
  - Single-header sheets (`descricao`, `composicao`, `valores`,
    `referencia_temporal`, `cenarios`, `legenda`, `dicionario`): spreadsheet
    row = `idx + 2` (1 for the header, 1 because spreadsheets are 1-based).
  - `proporcionalidades` (double header): spreadsheet row = `idx + 3`.
  - Both conversions live in one helper, `excel_row(idx, sheet_name)` (or a
    per-sheet-kind overload) — every rule and formatter calls it instead of
    doing the arithmetic itself.

## Domain conventions

- Value columns follow the pattern `CÓDIGO-ANO[-CENÁRIO]`.
- `DI` means "dado indisponível" (data unavailable) — a valid, expected
  token, not a parsing failure; do not coerce it to `NaN` before checking
  for it explicitly where the rule cares about the distinction.
- CSV input uses `|` as the field separator, never `,` or `;`.

## Never do

- Never call `.iterrows()`/`.itertuples()` inside a rule.
- Never compute a spreadsheet row number without going through the shared
  `excel_row()` helper.
- Never mutate a DataFrame a rule function was handed; return new data or
  issues instead.
