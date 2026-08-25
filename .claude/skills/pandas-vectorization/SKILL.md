---
name: pandas-vectorization
description: Use when writing or reviewing a validation rule that touches a DataFrame row by row. Shows how to replace iterrows() with masks, merge/isin, groupby, and vectorised string/numeric ops, using real before/after examples from this codebase.
---

# Replacing `iterrows()` in data_validate

`iterrows()` is banned in new/changed rule code (`.claude/rules/dataframe-conventions.md`,
`PERF-001` in the backlog). It is slow (boxes every row into a Series) and it's the most common
place bugs hide in this codebase. As of the last audit, 15 files still use it — treat each as a
PERF-001 migration candidate, not a template to copy.

## Pattern 1 — regex/content check per cell → vectorised `str` accessor

Before (`data_validate/validators/spreadsheets/description/description_validator.py`,
`validate_html_in_descriptions`):

```python
for index, row in self._dataframe.iterrows():
    if re.search("<.*?>", str(row[column])):
        index = int(str(index))
        warnings.append(f"{self._filename}, linha {index + 2}: Coluna '{column}' não pode conter código HTML.")
```

After:

```python
has_html = self._dataframe[column].astype(str).str.contains(r"<.*?>", regex=True, na=False)
for idx in self._dataframe.index[has_html]:
    warnings.append(f"{self._filename}, linha {idx + 2}: Coluna '{column}' não pode conter código HTML.")
```

One `.str.contains` call replaces the per-row `re.search`; the loop that remains only builds
messages for the (usually few) matching indices — no row is ever converted to a Series.

## Pattern 2 — numeric-range check per cell → boolean mask with `to_numeric`

Before (`description_validator.py`, `validate_indicator_levels`):

```python
for index, row in self._dataframe.iterrows():
    level = row[column]
    is_valid, __ = NumberFormattingProcessing.check_cell_integer(level, min_value=1)
    if not is_valid:
        line_updated = int(index) + 2
        errors.append(f"{self._filename}, linha {line_updated}: O nível ... deve ser ... maior que 0.")
```

After:

```python
numeric_levels = pd.to_numeric(self._dataframe[column], errors="coerce")
invalid_mask = numeric_levels.isna() | (numeric_levels < 1) | (numeric_levels % 1 != 0)
for idx in self._dataframe.index[invalid_mask]:
    errors.append(f"{self._filename}, linha {idx + 2}: O nível ... deve ser ... maior que 0.")
```

`errors="coerce"` turns any non-numeric cell into `NaN`, which the mask catches in the same pass —
no per-cell try/except needed.

## Pattern 3 — cross-sheet existence check → `merge`/`isin` instead of nested loops

Never write `for parent in parents: if parent not in children_set: ...` when a set operation does
it in one line:

```python
# Before: nested loop checking every proportionality row's parent against composicao
# After:
valid_parents = set(composicao_df[SpComposition.RequiredColumn.COLUMN_PARENT_CODE.name])
missing_mask = ~proportionality_parents.isin(valid_parents)
missing_ids = proportionality_parents[missing_mask].unique().tolist()
```

For join-shaped checks (e.g. "every `valores` column combination must exist in `descricao` ×
`referencia_temporal` × `cenarios`"), build the expected combinations as a DataFrame and use
`merge(..., how="left", indicator=True)` to find `left_only` rows in one call instead of any loop.

## Pattern 4 — per-group validation → `groupby` instead of manual partitioning

`SpLegend.data_cleaning` already does this correctly — follow this shape for new per-group rules:

```python
for code_value, group in dataframe.groupby(column_name_code):
    errors.extend(legend_validator.validate_min_max_values(group, code_value, ...))
```

`groupby` gives you each group as a real (small) DataFrame, so vectorised operations still apply
inside the loop body — the loop is over groups (few), never over rows (many).

## Pattern 5 — generating issues from indices, not from a row loop

The consistent shape across all patterns above: compute a boolean **mask** over the whole column
(or several columns combined with `&`/`|`), then iterate only `dataframe.index[mask]` to format
messages. The expensive part (the check) is vectorised; the loop that remains is O(violations),
not O(rows), and never touches `row[...]` cell-by-cell.

## Dtypes and Copy-on-Write

- Prefer nullable dtypes (`Int64`, `Float64`, `string[pyarrow]`) for cleaned columns so `NaN`
  comparisons behave predictably and comparisons with `DI`/empty strings don't silently coerce.
- Under pandas 3's Copy-on-Write, avoid defensive `.copy()` calls "just in case" — only copy when
  you are about to mutate a DataFrame you don't own (e.g. before dropping a column that came from
  a shared `data_loader_model.raw_data`).
- Never assign into a slice of another DataFrame you don't own (`SettingWithCopyWarning`'s root
  cause) — return a new DataFrame/Series instead.

## When `iterrows()` is still acceptable

Only when the row-wise operation is inherently stateful across rows in a way no vectorised
primitive expresses cleanly (rare) — and even then, prefer `itertuples()` (no Series boxing) and
document why vectorisation was rejected in a comment referencing the PERF backlog item.
