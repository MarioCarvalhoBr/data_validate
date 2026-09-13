# `referencia_temporal` — temporal references

Purpose: the present time and the future years tied to scenarios (protocol §2.2, p.4–5).
Files: `referencia_temporal.xlsx`/`.csv`. Single header. Required.

## Columns

| Column | Kind | Type after cleaning | Constraints | Source in code |
|---|---|---|---|---|
| `nome` | required | str | short display name, unique | `models/sp_temporal_reference.py::RequiredColumn.COLUMN_NAME` |
| `descricao` | required | str | ends with `.`; spell-checked | `RequiredColumn.COLUMN_DESCRIPTION` |
| `simbolo` | required | int ≥ 0 (code) / four numeric chars (protocol) | used as `<ano>` in value columns; unique; first row = present time | `RequiredColumn.COLUMN_SYMBOL` |

## Rules

### CLEAN-005 · `simbolo` must be an integer ≥ 0
- Severity: error
- NamesEnum: FC (`verification_name_file_cleaning`)
- Protocol: §2.2 p.5 ("Quatro caracteres numéricos")
- Statement: when scenarios exist (or the table has exactly one row), each `simbolo` cell is an integer ≥ 0.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: A coluna 'simbolo' contém um valor inválido: {message}`
- Target message key: `rule.CLEAN-005.error`
- Implemented by: `models/sp_temporal_reference.py::SpTemporalReference.data_cleaning` → `DataCleaningProcessing.clean_dataframe_integers`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_data_cleaning.py`
- Notes / known defects: four-digit format not enforced here (only via the value column
  pattern). BUG-002 fixed — cleaned `simbolo` data is stored per-instance in `self.cleaned`,
  read via `cleaned_column("simbolo")`, not overwritten on the class.

### CLEAN-006 · Without scenarios the table must have exactly one row
- Severity: error
- NamesEnum: FC
- Protocol: §2.2 p.4 ("associados a uma (quando tiver zero cenários) ou mais referências temporais")
- Statement: if no scenario symbols were loaded and the row count ≠ 1, report; only the first row's symbol is kept for later rules.
- Current message (pt-BR): `{filename}: A tabela deve ter apenas um valor porque o arquivo 'cenarios' não existe ou está vazio.`
- Target message key: `rule.CLEAN-006.error`
- Implemented by: `models/sp_temporal_reference.py::SpTemporalReference.data_cleaning`
- Covered by tests: none — TST-001
- Notes / known defects: —

### TEMP-001 · Description must end with a period
- Severity: warning
- NamesEnum: MAND_PUNC_TEMP (`verification_name_mandatory_and_prohibited_punctuation_in_temporal_reference`)
- Protocol: §2.2 p.5 ("Toda descrição deverá necessariamente terminar com um ponto")
- Statement: every non-empty `descricao` cell, stripped, ends with `.`.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: O valor da coluna 'descricao' deve terminar com ponto.` · missing column → warning `{file}: A verificação foi abortada para a coluna obrigatória 'descricao' que está ausente.`
- Target message key: `rule.TEMP-001.warning`
- Implemented by: `rules/temporal_reference.py::check_description_ends_with_period` (ARC-017 Phase 3 Port 4; ported from `validators/spreadsheets/temporal_reference/temporal_reference_validator.py::SpTemporalReferenceValidator.validate_punctuation` → `CharacterProcessing.check_characters_punctuation_rules`, deleted)
- Covered by tests: `tests/unit/rules/test_temporal_reference.py::TestCheckDescriptionEndsWithPeriod`
- Notes / known defects: —

### TEMP-002 · Scenario years must be in the future
- Severity: error
- NamesEnum: YEARS_TEMP (`verification_name_years_in_temporal_reference`)
- Protocol: §2.2 p.5 ("Os símbolos que tiverem valor menor do que o ano corrente serão considerados como dados do passado e portanto não terão cenários associados")
- Statement: excluding the first row (present time), every distinct `simbolo` must be ≥ the current calendar year.
- Current message (pt-BR): `{filename}: O ano {year} não pode estar associado a cenários por não ser um ano futuro.`
- Target message key: `rule.TEMP-002.error`
- Implemented by: `rules/temporal_reference.py::check_reference_years_are_future` (ARC-017 Phase 3 Port 4; ported from `temporal_reference_validator.py::SpTemporalReferenceValidator.validate_reference_years`, deleted); the current year comes from `ctx.clock().year` rather than `ApplicationConfig.CURRENT_YEAR` directly
- Covered by tests: `tests/unit/rules/test_temporal_reference.py::TestCheckReferenceYearsAreFuture` (including the migrated BUG-007 regression cases: a non-numeric `"2030a"` symbol is skipped without raising, and two independent `RuleContext`s do not leak state)
- Notes / known defects: BUG-007 preserved (not reopened) — the rule reads the sheet's own raw `simbolo` column (`ctx.sheet(...)`, never a class-level `RequiredColumn` Series) and validates each distinct value with a vectorised `pd.to_numeric(errors="coerce")` mask before comparing years, silently skipping non-numeric symbols (already reported as data-cleaning errors by the model) instead of raising `ValueError` inside `int(year)`. BUG-002 (class-level `RequiredColumn` Series as global mutable state) is fixed for the model itself (`self.cleaned["simbolo"]`/`cleaned_column()`); this rule reads the sheet's raw frame rather than the cleaned column (unchanged by this slice); import-time clock (BUG-011) is unrelated and still open. "Future" is still `>= current year` (a symbol equal to the current year passes).

### TEMP-003 · `nome` and `simbolo` must be unique
- Severity: error
- NamesEnum: UVR_TEMP (`verification_name_unique_value_relations_in_temporal_reference`)
- Protocol: §2.2 (one row per reference)
- Statement: no duplicated values in either column.
- Current message (pt-BR): `{file_name}: A coluna '{column}' não deve conter valores repetidos.` · missing column → error with the abort text
- Target message key: `rule.TEMP-003.error`
- Implemented by: `rules/temporal_reference.py::check_name_and_symbol_are_unique` (ARC-017 Phase 3 Port 4; ported from `temporal_reference_validator.py::SpTemporalReferenceValidator.validate_unique_values` → `DataFrameProcessing.check_dataframe_unique_values`, deleted)
- Covered by tests: `tests/unit/rules/test_temporal_reference.py::TestCheckNameAndSymbolAreUnique`
- Notes / known defects: —

### TEMP-004 · `simbolo` must be exactly four numeric characters
- Severity: error
- NamesEnum: YEARS_TEMP (`verification_name_years_in_temporal_reference`)
- Protocol: §2.2 p.5 ("Quatro caracteres numéricos")
- Statement: every `simbolo` cell (raw, not the model's cleaned integer column) matches `^\d{4}$`
  — exactly four ASCII digits, no sign, no decimal separator. Independent of `CLEAN-005`'s
  "parses as an integer ≥ 0" cleaning check: a value can pass one and fail the other (e.g. `"1"`
  is a valid non-negative integer but not four digits).
- Current message (pt-BR): catalog key `rule.TEMP-004.error` — `{filename}, linha {row}: O valor
  '{value}' da coluna 'simbolo' deve conter exatamente quatro caracteres numéricos.` (present in
  both locales)
- Target message key: `rule.TEMP-004.error`
- Implemented by: `rules/temporal_reference.py::check_symbol_is_four_digits`
- Covered by tests: `tests/unit/rules/test_temporal_reference.py::TestCheckSymbolIsFourDigits`
- Notes / known defects: resolves gap G-15 (PROTO-014). `data_errors_01`'s `simbolo="2050B"` (a
  known, pre-existing defect, previously undetected by `CLEAN-005`'s looser check) newly triggers
  this rule — reviewed golden re-baseline. No other fixture's `simbolo` fails the four-digit format.

### TEMP-005 · At most one `simbolo` may be an observed (non-future) reference
- Severity: warning
- NamesEnum: YEARS_TEMP (`verification_name_years_in_temporal_reference`)
- Protocol: §2.2 p.5 (footnote): "atualmente suporta apenas uma referência temporal para dados observados"
- Statement: count every `simbolo` value (including the present-time first row, unlike TEMP-002)
  that is `<= ctx.clock().year`; more than one such value is a warning, naming every observed
  symbol found. A conservative severity (warning, not error): this is the platform's own current
  limitation, not a hard protocol requirement, matching TEMP-004's stricter format-only error and
  TEMP-002's existing per-symbol error for a genuinely past *scenario* year, which stay unchanged.
- Current message (pt-BR): catalog key `rule.TEMP-005.warning` — `{filename}: A coluna 'simbolo'
  possui mais de uma referência temporal observada (ano atual ou passado): {observed_symbols}. A
  plataforma atualmente suporta apenas uma.` (present in both locales)
- Target message key: `rule.TEMP-005.warning`
- Implemented by: `rules/temporal_reference.py::check_single_observed_reference`
- Covered by tests: `tests/unit/rules/test_temporal_reference.py::TestCheckSingleObservedReference`
- Notes / known defects: resolves gap G-16 (PROTO-014). Every fixture has exactly one symbol
  `<=` the current year (the present-time row itself), so this rule never fires against a
  shipped fixture. Silent (`[]`) when `simbolo` is absent — TEMP-002/TEMP-004 already own that
  column's missing-column abort.

## Gaps (protocol ↔ code)

- **G-15 four-digit symbol** (resolved, PROTO-014): TEMP-004 now requires exactly four numeric characters.
- **G-16 single observed time** (resolved, PROTO-014): TEMP-005 warns when more than one `simbolo` is `<=` the current year.
- CR/LF and line-break checks exist for `descricao` (DESC-008) but `LB_TEMP` is never emitted (gap G-08).

Last synced with code: Phase 6 round N2, 2026-09-13 (PROTO-014: TEMP-004/TEMP-005 added to
`rules/temporal_reference.py`)
