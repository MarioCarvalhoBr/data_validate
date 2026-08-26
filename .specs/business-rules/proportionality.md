# `proporcionalidades` — influencing factors

Purpose: for each parent indicator/time/scenario, the weight of every last-level indicator that
composes it, per spatial feature (protocol §2.7, p.13–14). Files: `proporcionalidades.xlsx`/`.csv`.
**Double header**: row 1 = parent column names (`CÓDIGO-ANO[-CENÁRIO]`, written once and left blank
across its span → forward-filled), row 2 = child column names in the same format plus `id`. Optional.

## Columns

| Header level | Name | Kind | Type | Constraints | Source in code |
|---|---|---|---|---|---|
| 1 (row 2) | `id` | required | str | feature id matching `valores.id` | `models/sp_proportionality.py::RequiredColumn.COLUMN_ID` |
| 0 (row 1) | `<parent>-<ano>[-<cenario>]` | dynamic | — | parent indicator, appears once | `CollectionsProcessing.categorize_strings_by_id_pattern_from_list` |
| 1 (row 2) | `<child>-<ano>[-<cenario>]` | dynamic | numeric (≤ 3 decimals) or `DI` | child of the parent above per `composicao` | same |

The model runs only when the frame is non-empty and the header is double
(`DataLoaderModel.header_type == "double"`); when structural errors occur the frame is cleared
and `header_type` set to `"invalid"` so validators skip (ARC-009). Sub-datasets per parent are built
by `helpers/common/validation/proportionality_processing.py::ProportionalityProcessing.build_subdatasets`
(id column + the parent's child columns). Row numbers in messages use `index + 3`.

## Rules

### PROP-001 · Header names must follow `CÓDIGO-ANO[-CENÁRIO]` on both levels
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2.7 p.14 ("o índice ou indicador deve ser descrito no formato '[codigo]-[ano]-[cenario]'")
- Statement: level-0 names (excluding `unnamed: 0_level_0`) and level-1 names (excluding `id`) must match the pattern with the loaded scenario symbols.
- Current message (pt-BR): `{filename}, linha 1: Colunas de nível 1 fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): [..]` · `{filename}, linha 2: Colunas de nível 2 fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): [..]`
- Target message key: `rule.PROP-001.error`
- Implemented by: `models/sp_proportionality.py::SpProportionality.pre_processing`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_collections_processing.py`
- Notes / known defects: user-facing "nível 1/2" means header row 1/2 (not indicator levels).

### PROP-002 · `id` must exist on header row 2; no unexpected columns
- Severity: error
- NamesEnum: FS
- Protocol: §2.7 p.14
- Statement: with a double header, every level-0 and level-1 name not matching the pattern (ignoring `unnamed*` and, on level 1, `id`) is unexpected; `id` must be present on level 1.
- Current message (pt-BR): `{filename}: A coluna de nível 1 '{col}' não é esperada.` · `{filename}: A coluna de nível 2 '{col}' não é esperada.` · `{filename}: Coluna de nível 2 'id' esperada mas não foi encontrada.`
- Target message key: `rule.PROP-002.error`
- Implemented by: `models/sp_proportionality.py::SpProportionality.expected_structure_columns`
- Covered by tests: none — TST-001
- Notes / known defects: duplicates PROP-001 for the same columns; on any structural error the sheet is discarded (`post_processing`).

### PROP-003 · Proportionality codes and description codes must match
- Severity: error
- NamesEnum: IR (`verification_name_indicator_relations`)
- Protocol: §2.7 (parents and children are indicators from §2.3)
- Statement: D = valid description codes excluding level 1 and level-2-with-`cenario == 0`
  (`DescriptionProcessing.get_valids_codes_from_description`); P = codes (prefix before `-`) from
  pattern-matching names on both header levels minus level-1 codes. Report D − P and P − D. Skipped when `descricao` is empty.
- Current message (pt-BR): `{descricao}: Códigos dos indicadores ausentes em {proporcionalidades}: [..].` · `{proporcionalidades}: Códigos dos indicadores ausentes em {descricao}: [..].`
- Target message key: `rule.PROP-003.error`
- Implemented by: `validators/spreadsheets/proportionality/proportionality_validator.py::SpProportionalityValidator.validate_relation_indicators_in_proportionality`
- Covered by tests: none — TST-001
- Notes / known defects: string level comparison (BUG-014).

### PROP-004 · A parent indicator must not appear twice on header row 1
- Severity: error
- NamesEnum: REP_IND_PROP (`verification_name_repeated_indicators_in_proportionalities`)
- Protocol: §2.7 p.14 ("basta descrever uma vez … um novo indicador deverá aparecer na primeira linha")
- Statement: after grouping consecutive identical level-0 names, each parent name must occur in exactly one group.
- Current message (pt-BR): `{proporcionalidades}: O indicador pai '{parent}' está repetido na planilha.`
- Target message key: `rule.PROP-004.error`
- Implemented by: `proportionality_validator.py::SpProportionalityValidator.validate_columns_repeated_indicators` → `CollectionsProcessing.generate_group_from_list`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_collections_processing.py`
- Notes / known defects: —

### PROP-005 · Indicator columns must match between `proporcionalidades` and `valores`
- Severity: error
- NamesEnum: IND_VAL_PROP (`verification_name_indicators_in_values_and_proportionalities`)
- Protocol: §2.7 (same indicators/times/scenarios as §2.6)
- Statement: the set of all header names (both levels, excluding `unnamed: 0_level_0` and `id`) must equal the set of `valores` columns (excluding `id`). Skipped when `valores` is empty.
- Current message (pt-BR): `{proporcionalidades}: Códigos dos indicadores ausentes em {valores}: [..].` · `{valores}: Códigos dos indicadores ausentes em {proporcionalidades}: [..].`
- Target message key: `rule.PROP-005.error`
- Implemented by: `proportionality_validator.py::SpProportionalityValidator.validate_relation_indicators_in_value_and_proportionality`
- Covered by tests: none — TST-001
- Notes / known defects: `list.remove("id")` raises when absent (BUG-006).

### PROP-006 · Parent/child pairs must agree with `composicao`
- Severity: error
- NamesEnum: IR_PROP (`verification_name_indicator_relations_in_proportionalities`)
- Protocol: §2.7 p.14 ("uma coluna para cada indicador de último nível que foi usado para criar o respectivo indicador")
- Statement: for each parent sub-dataset (parent code = prefix before `-`), ignoring composition rows whose parent is `1`: the parent must be a `codigo_pai` in `composicao` (unless its name contains `:`); each child column code must be a child of that parent; every composition child of that parent must appear at least once. Errors are de-duplicated and sorted. Skipped when `composicao` is empty.
- Current message (pt-BR): `{proporcionalidades}: O indicador pai '{parent}' (em '{parent_col}') não está presente na coluna 'codigo_pai' da planilha {composicao}.` · `{proporcionalidades}: O indicador '{child}' (em '{child_col}') não é filho do indicador '{parent}' (em '{parent_col}') conforme especificado em {composicao}.` · `{proporcionalidades}: Deve existir pelo menos uma relação do indicador filho '{child}' com o indicador pai '{parent}' (em '{parent_col}') conforme especificado em {composicao}.`
- Target message key: `rule.PROP-006.error`
- Implemented by: `proportionality_validator.py::SpProportionalityValidator.validate_parent_child_relationships`
- Covered by tests: none — TST-001
- Notes / known defects: raw string comparison `codigo_pai != "1"` (BUG-014); `iterrows` (PERF-001); wrongly registers its skip under `IND_VAL_PROP`.

### PROP-007 · Cells must be numeric or `DI`
- Severity: error
- NamesEnum: SUM_PROP (`verification_name_sum_properties_in_influencing_factors`)
- Protocol: §2.7 p.14 ("Qualquer outro valor de texto ou dado ausente será considerado erro"), v1.2
- Statement: per parent sub-dataset, every child cell is `DI` or numeric (comma accepted); invalid cells are replaced by `DI` for the sum step. Single-cell and aggregated variants. Skipped when `valores` is empty.
- Current message (pt-BR): `{proporcionalidades}, linha {row + 3}: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '{parent}'.` · `{proporcionalidades}: {n} valores que não são número válido nem DI (Dado Indisponível) para o indicador pai '{parent}' entre as linhas {first} e {last}.`
- Target message key: `rule.PROP-007.error`
- Implemented by: `proportionality_validator.py::SpProportionalityValidator._check_sum_equals_one` → `ProportionalityProcessing.validate_numeric_format`
- Covered by tests: none — TST-001 (`ProportionalityProcessing` has no unit tests)
- Notes / known defects: blank cells count as valid (`df_data.notna()` guard) although the protocol says "dado ausente será considerado erro" (gap G-23).

### PROP-008 · Values must have at most three decimal places
- Severity: warning
- NamesEnum: SUM_PROP
- Protocol: §2.7 p.14 ("no máximo três casas decimais"), v1.8
- Statement: cells with more than `PRECISION_DECIMAL_PLACE_TRUNCATE = 3` decimals are counted across all parents and summarised once (first affected row); sums use the truncated values.
- Current message (pt-BR): `{proporcionalidades}, linha {first_line}: Existe(m) {count} valor(es) com mais de 3 casas decimais, serão consideradas apenas as 3 primeiras casas decimais.`
- Target message key: `rule.PROP-008.warning`
- Implemented by: `proportionality_validator.py::SpProportionalityValidator._check_sum_equals_one` → `ProportionalityProcessing.check_excessive_decimals`
- Covered by tests: none — TST-001
- Notes / known defects: "3" hard-coded in the message while the precision is configurable.

### PROP-009 · A zero-sum row must correspond to zero/DI values in `valores`
- Severity: error
- NamesEnum: SUM_PROP
- Protocol: §2.7 p.14 ("quando a composição … tiver apenas valores zero ou DI, os respectivos fatores influenciadores deverão ter valor zero"), v1.5
- Statement: for each row whose truncated child factors sum to 0, look up the same `id` in `valores`; every child column present there must be `DI` or 0, otherwise error.
- Current message (pt-BR): `{proporcionalidades}: A soma de fatores influenciadores para o ID '{id}' no pai '{col}' é 0 (zero). Na planilha {valores}, existe(m) valor(es) para os filhos do indicador '{col}', no mesmo ID, que não é (são) zero ou DI (Dado Indisponível).`
- Target message key: `rule.PROP-009.error`
- Implemented by: `ProportionalityProcessing.validate_zero_sum_rows`
- Covered by tests: none — TST-001
- Notes / known defects: `except (…, Exception): pass` swallows parse errors (SEC-004); the message's `'{col}'` is the child column, not the parent.

### PROP-010 · Factors of a parent must sum to 1 (tolerance ±0.01)
- Severity: error (outside [0.99, 1.01] and ≠ 0) / warning (inside the band but ≠ 1)
- NamesEnum: SUM_PROP
- Protocol: §2.7 p.14 ("a soma da composição para cada indicador deve ser um, mas podem existir exceções quando os dados não estão normalizados")
- Statement: per parent and row, sum of truncated Decimal factors (DI → 0): if sum ≠ 0 and (sum < 0.99 or sum > 1.01) → error; if 0.99 ≤ sum ≤ 1.01 and sum ≠ 1 → warning. Numbers are formatted with the current locale.
- Current message (pt-BR): `{proporcionalidades}, linha {row + 3}: A soma dos valores para o indicador pai {parent} é {sum}, e não 1.` (same text for error and warning)
- Target message key: `rule.PROP-010.error`, `rule.PROP-010.warning`
- Implemented by: `ProportionalityProcessing.convert_to_decimal_and_sum` + `validate_sum_tolerance`
- Covered by tests: none — TST-001
- Notes / known defects: tolerance not configurable; identical wording for error and warning.

## Gaps (protocol ↔ code)

- **G-23 blank cells**: protocol treats missing data as an error; code treats blanks as valid and sums them as 0.
- **G-24 first two columns are spatial**: protocol says the first two columns are the spatial representation (§3.2); code expects a single `id` sub-column and ignores `unnamed` level-0.
- Non-normalised exceptions ("podem existir exceções") have no opt-out flag.

Last synced with code: 09279f4
