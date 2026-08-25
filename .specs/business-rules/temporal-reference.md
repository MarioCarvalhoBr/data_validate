# `referencia_temporal` — temporal references

Purpose: the present time and the future years tied to scenarios (protocol §2.2, p.4–5).
Files: `referencia_temporal.xlsx`/`.csv`. Single header. Required.

## Columns

| Column | Kind | Type after cleaning | Constraints | Source in code |
|---|---|---|---|---|
| `nome` | required | str (declared `int64` in code — BUG-013) | short display name, unique | `models/sp_temporal_reference.py::RequiredColumn.COLUMN_NAME` |
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
- Notes / known defects: four-digit format not enforced here (only via the value column pattern); BUG-002.

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
- Implemented by: `validators/spreadsheets/temporal_reference/temporal_reference_validator.py::SpTemporalReferenceValidator.validate_punctuation` → `CharacterProcessing.check_characters_punctuation_rules`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: —

### TEMP-002 · Scenario years must be in the future
- Severity: error
- NamesEnum: YEARS_TEMP (`verification_name_years_in_temporal_reference`)
- Protocol: §2.2 p.5 ("Os símbolos que tiverem valor menor do que o ano corrente serão considerados como dados do passado e portanto não terão cenários associados")
- Statement: excluding the first row (present time), every distinct `simbolo` must be ≥ the current calendar year.
- Current message (pt-BR): `{filename}: O ano {year} não pode estar associado a cenários por não ser um ano futuro.`
- Target message key: `rule.TEMP-002.error`
- Implemented by: `temporal_reference_validator.py::SpTemporalReferenceValidator.validate_reference_years`; year from `ApplicationConfig.CURRENT_YEAR`
- Covered by tests: none — TST-001
- Notes / known defects: reads the class-level Series mutated by the model (BUG-002); `int(year)` on raw text (BUG-007); import-time clock (BUG-011). "Future" is `>= current year` (a symbol equal to the current year passes).

### TEMP-003 · `nome` and `simbolo` must be unique
- Severity: error
- NamesEnum: UVR_TEMP (`verification_name_unique_value_relations_in_temporal_reference`)
- Protocol: §2.2 (one row per reference)
- Statement: no duplicated values in either column.
- Current message (pt-BR): `{file_name}: A coluna '{column}' não deve conter valores repetidos.` · missing column → error with the abort text
- Target message key: `rule.TEMP-003.error`
- Implemented by: `temporal_reference_validator.py::SpTemporalReferenceValidator.validate_unique_values` → `DataFrameProcessing.check_dataframe_unique_values`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_column_validation.py`
- Notes / known defects: —

## Gaps (protocol ↔ code)

- **G-15 four-digit symbol**: `simbolo` must be exactly four digits per protocol; code accepts any integer ≥ 0.
- **G-16 single observed time**: "atualmente suporta apenas uma referência temporal para dados observados" — the code assumes row 1 is the present time but does not verify that only one symbol is ≤ current year.
- CR/LF and line-break checks exist for `descricao` (DESC-008) but `LB_TEMP` is never emitted (gap G-08).

Last synced with code: 3dcfdb1
