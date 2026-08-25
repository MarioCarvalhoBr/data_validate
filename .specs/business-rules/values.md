# `valores` — indicator values

Purpose: one row per spatial feature (`id`), one column per indicator/time/scenario combination
(protocol §2.6, p.12–13). Files: `valores.xlsx`/`.csv`. Single header. Required.

## Columns

| Column | Kind | Type | Constraints | Source in code |
|---|---|---|---|---|
| `id` | required | str (feature id) | unique feature identifier (IBGE 2018 code or custom) | `models/sp_value.py::RequiredColumn.COLUMN_ID` |
| `<codigo>-<ano>` | dynamic | numeric or `DI` | `^\d+-\d{4}$`; present-time column | pattern in `helpers/common/processing/collections_processing.py::categorize_strings_by_id_pattern_from_list` |
| `<codigo>-<ano>-<cenario>` | dynamic | numeric or `DI` | `^\d+-\d{4}-(<symbol>)$` with symbols from `cenarios.simbolo` | same |

`DI` = `ApplicationConfig.VALUE_DATA_UNAVAILABLE`. Values may use `,` or `.` as decimal separator.

## Rules

### VAL-001 · Column names must follow `CÓDIGO-ANO[-CENÁRIO]`
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2.6 p.12–13
- Statement: every column other than `id` must match the pattern (scenario suffix allowed only when it is one of the loaded scenario symbols); `id` must exist. Columns starting with `unnamed` are ignored in the "not expected" pass.
- Current message (pt-BR): `{filename}, linha 1: Colunas fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): [..]` · `{filename}: A coluna '{extra_column}' não é esperada.` · `{filename}: Coluna 'id' esperada mas não foi encontrada.`
- Target message key: `rule.VAL-001.error`
- Implemented by: `models/sp_value.py::SpValue.pre_processing` and `SpValue.expected_structure_columns`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_collections_processing.py`
- Notes / known defects: the same offending column is reported twice (pattern list + "não é esperada").

### VAL-002 · Value columns and description codes must match
- Severity: error
- NamesEnum: IR (`verification_name_indicator_relations`)
- Protocol: §2.6 p.13 ("Para cada índice ou indicador … pelo menos uma coluna")
- Statement: let D = description codes excluding level 1 and, when scenarios exist and the `cenario` column is present, excluding level-2 codes with `cenario == 0`; let V = codes extracted from pattern-matching value columns (ignoring `id` and level-1 codes). Report D − V and V − D. Also report value columns that match no pattern, except names containing `:` (Excel date artefacts such as `abr/2017`). Skipped when `descricao` is empty.
- Current message (pt-BR): `{valores}: Colunas inválidas: [..].` · `{descricao}: Códigos dos indicadores ausentes em {valores}: [..].` · `{valores}: Códigos dos indicadores ausentes em {descricao}: [..].`
- Target message key: `rule.VAL-002.error`
- Implemented by: `validators/spreadsheets/value/value_validator.py::SpValueValidator.validate_relation_indicators_in_values`
- Covered by tests: helpers covered by `tests/unit/helpers/common/processing/test_collections_processing.py`
- Notes / known defects: string comparison of `nivel`/`cenario` (BUG-014).

### VAL-003 · Each indicator must have exactly the expected time/scenario columns
- Severity: error
- NamesEnum: VAL_COMB (`verification_name_value_combination_relations`)
- Protocol: §2.6 p.13 ("toda vez que algum índice ou indicador existir para algum cenário, deverão existir colunas para cada cenário … bem como para todos os anos futuros")
- Statement: with `T` = sorted distinct `referencia_temporal.simbolo` and `S` = scenario symbols, for each description row with level ≥ 2: if `cenario == 0` (or no scenarios) the only expected column is `<code>-<T[0]>`; if `cenario == 1` expected = `<code>-<T[0]>` ∪ {`<code>-<t>-<s>` for t in T[1:], s in S}. Missing expected columns are errors (except level 2 with `cenario == 0`, silently tolerated); any actual `<code>-…` column not in the expected set is "unnecessary" (level-1 message variant). Skipped when `descricao` or `referencia_temporal` is empty.
- Current message (pt-BR): `{valores}: A coluna '{combination}' é obrigatória.` · `{valores}: A coluna '{extra_column}' é desnecessária.` · `{valores}: A coluna '{extra_column}' é desnecessária para o indicador de nível 1.`
- Target message key: `rule.VAL-003.error`
- Implemented by: `value_validator.py::SpValueValidator.validate_value_combination_relation` → `helpers/common/generation/combinations_processing.py::CombinationsProcessing.generate_combinations`, `find_extra_combinations`
- Covered by tests: helper covered by `tests/unit/helpers/common/generation/test_combinations.py`
- Notes / known defects: shared-list mutation (BUG-001); `iterrows` (PERF-001); `cenario` values other than 0/1 yield no expected columns (gap G-09).

### VAL-004 · Cells must be numeric or `DI`
- Severity: error
- NamesEnum: UNAV_INV (`verification_name_unavailable_and_invalid_values`)
- Protocol: §2.6 p.13 ("Qualquer outro valor de texto ou dado ausente será considerado erro")
- Statement: in every pattern-matching column, each cell is `DI` or parses as a number (comma accepted). One message when a column has a single invalid cell, one aggregated message otherwise.
- Current message (pt-BR): `{filename}, linha {row + 2}: O valor {value} não é um número válido e nem DI (Dado Indisponível) para a coluna '{column}'.` · `{filename}: {n} valores que não são número válido nem DI (Dado Indisponível) para a coluna '{column}', entre as linhas {first} e {last}.`
- Target message key: `rule.VAL-004.error`
- Implemented by: `value_validator.py::SpValueValidator.validate_unavailable_codes_values` → `helpers/common/validation/value_processing.py::ValueProcessing.validate_data_values_in_columns`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_value_processing.py`
- Notes / known defects: cell-by-cell loop (PERF-001); `DI` literal hard-coded in `ValueProcessing.check_numeric_value` instead of config.

### VAL-005 · Values must have at most two decimal places
- Severity: warning
- NamesEnum: UNAV_INV
- Protocol: §2.6 p.12 ("usando no máximo duas casas decimais"); v1.8
- Statement: numeric cells with more than two decimals are counted across all value columns and summarised in one warning (first/last affected row); extra decimals are truncated by the platform.
- Current message (pt-BR): `{filename}: Existe(m) {count} valor(es) com mais de 2 casas decimais, serão consideradas apenas as 2 primeiras casas decimais. Entre as linhas {first_row} e {last_row}.`
- Target message key: `rule.VAL-005.warning`
- Implemented by: `value_processing.py::ValueProcessing.generate_decimal_warning` via `NumberFormattingProcessing.check_two_decimals_places`
- Covered by tests: `tests/unit/helpers/common/validation/test_value_processing.py`
- Notes / known defects: —

## Gaps (protocol ↔ code)

- **G-13 `id` completeness**: "Nesta coluna deverão ter todos os objetos descritos no shapefile ou … todos os municípios brasileiros" cannot be checked without the spatial layer; uniqueness of `id` is also not checked.
- **G-14 normalised range**: the [0,1] expectation is enforced only through the legend range rule (LEG-015) with default bounds 0–1.

Last synced with code: 3dcfdb1
