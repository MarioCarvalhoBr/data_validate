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
(`LoadedSheet.header_type == "double"`); when structural errors occur the frame is cleared
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
- Target message key: `rule.PROP-003.missing_codes`
- Implemented by: `rules/proportionality.py::check_relation_indicators_in_proportionality` (ARC-017 Phase 3 Port 7; legacy `SpProportionalityValidator.validate_relation_indicators_in_proportionality` deleted)
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckRelationIndicatorsInProportionality` (table-driven: valid bundle, each direction's missing-codes error, the BUG-014 float-level regression, missing-column abort, missing-`id` level-2 abort)
- Notes / known defects: none. BUG-014 (string level comparison, e.g. `nivel = "1.0"` silently not
  matching `"1"` when building the level-1 codes to strip from P) fixed — now
  `DataFrameProcessing.numeric_equals_mask`.

### PROP-004 · A parent indicator must not appear twice on header row 1
- Severity: error
- NamesEnum: REP_IND_PROP (`verification_name_repeated_indicators_in_proportionalities`)
- Protocol: §2.7 p.14 ("basta descrever uma vez … um novo indicador deverá aparecer na primeira linha")
- Statement: after grouping consecutive identical level-0 names, each parent name must occur in exactly one group.
- Current message (pt-BR): `{proporcionalidades}: O indicador pai '{parent}' está repetido na planilha.`
- Target message key: `rule.PROP-004.error`
- Implemented by: `rules/proportionality.py::check_columns_repeated_indicators` → `CollectionsProcessing.generate_group_from_list` (ARC-017 Phase 3 Port 7; legacy `SpProportionalityValidator.validate_columns_repeated_indicators` deleted)
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_collections_processing.py`; the rule itself by `tests/unit/rules/test_proportionality.py::TestCheckColumnsRepeatedIndicators` (distinct parents, a consecutive repeat — not reported, a non-consecutive repeat — reported, missing-`id` level-2 abort)
- Notes / known defects: —

### PROP-005 · Indicator columns must match between `proporcionalidades` and `valores`
- Severity: error
- NamesEnum: IND_VAL_PROP (`verification_name_indicators_in_values_and_proportionalities`)
- Protocol: §2.7 (same indicators/times/scenarios as §2.6)
- Statement: the set of all header names (both levels, excluding `unnamed: 0_level_0` and `id`) must equal the set of `valores` columns (excluding `id`). Skipped when `valores` is empty.
- Current message (pt-BR): `{proporcionalidades}: Códigos dos indicadores ausentes em {valores}: [..].` · `{valores}: Códigos dos indicadores ausentes em {proporcionalidades}: [..].`
- Target message key: `rule.PROP-005.missing_codes`
- Implemented by: `rules/proportionality.py::check_relation_indicators_in_value_and_proportionality` (ARC-017 Phase 3 Port 7; legacy `SpProportionalityValidator.validate_relation_indicators_in_value_and_proportionality` deleted)
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckRelationIndicatorsInValueAndProportionality` (table-driven: valid bundle, each direction's missing-codes error, the BUG-006 missing-`id`-in-`proporcionalidades`/missing-`id`-in-`valores` regressions)
- Notes / known defects: fixed BUG-006 — both the `proporcionalidades` `id` (level 2, `MultiIndex`) and `valores` `id` columns are checked, as a list comprehension building the column sets, before any set comparison runs, so a missing `id` reports the abort instead of ever reaching a `list.remove`-shaped crash.

### PROP-006 · Parent/child pairs must agree with `composicao`
- Severity: error
- NamesEnum: IR_PROP (`verification_name_indicator_relations_in_proportionalities`)
- Protocol: §2.7 p.14 ("uma coluna para cada indicador de último nível que foi usado para criar o respectivo indicador")
- Statement: for each parent sub-dataset (parent code = prefix before `-`), ignoring composition rows whose parent is `1`: the parent must be a `codigo_pai` in `composicao` (unless its name contains `:`); each child column code must be a child of that parent; every composition child of that parent must appear at least once. Errors are de-duplicated and sorted. Skipped when `composicao` is empty.
- Current message (pt-BR): `{proporcionalidades}: O indicador pai '{parent}' (em '{parent_col}') não está presente na coluna 'codigo_pai' da planilha {composicao}.` · `{proporcionalidades}: O indicador '{child}' (em '{child_col}') não é filho do indicador '{parent}' (em '{parent_col}') conforme especificado em {composicao}.` · `{proporcionalidades}: Deve existir pelo menos uma relação do indicador filho '{child}' com o indicador pai '{parent}' (em '{parent_col}') conforme especificado em {composicao}.`
- Target message key: `rule.PROP-006.parent_missing`, `rule.PROP-006.child_mismatch`, `rule.PROP-006.child_missing`
- Implemented by: `rules/proportionality.py::check_parent_child_relationships` (ARC-017 Phase 3 Port 7; legacy `SpProportionalityValidator.validate_parent_child_relationships` deleted). The `codigo_pai -> [codigo_filho, …]` dict is now built via `df_composition.groupby("codigo_pai", sort=False)["codigo_filho"].apply(list)`, not `iterrows()` (PERF-001). The legacy `sorted(set(errors))` step over rendered Portuguese sentences is reproduced without ever rendering them: the three message shapes are emitted as three fixed-order buckets (child-missing, then child-mismatch, then parent-missing — the only order their common-prefix-then-first-differing-character can produce), each sorted by the exact field tuple that appears, in order, inside its own template (see the module's own docstring).
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckParentChildRelationships` (valid tree, parent missing from `composicao`, child not a valid child (mismatch), composition child missing from `proporcionalidades`, the three-bucket ordering, missing-column/missing-`id` aborts)
- Notes / known defects: correctly registers its skip under `IR_PROP` (the legacy validator's own
  `NamesEnum.IND_VAL_PROP.value` in `set_not_executed` was a copy-paste artefact of its own
  `run()` list literal — this port's `requires` gate carries no `NamesEnum` at all, so the mislabel
  had nothing to reproduce).
  BUG-014 fixed — `codigo_pai != "1"` now goes through
  `DataFrameProcessing.numeric_not_equals_mask`, though no observable-behaviour regression test
  was possible for this specific site (see BUG-014's backlog entry for why).

### PROP-007 · Cells must be numeric or `DI`
- Severity: error
- NamesEnum: SUM_PROP (`verification_name_sum_properties_in_influencing_factors`)
- Protocol: §2.7 p.14 ("Qualquer outro valor de texto ou dado ausente será considerado erro"), v1.2
- Statement: per parent sub-dataset, every child cell is `DI` or numeric (comma accepted); invalid cells are replaced by `DI` for the sum step. Single-cell and aggregated variants. Skipped when `valores` is empty.
- Current message (pt-BR): `{proporcionalidades}, linha {row + 3}: O valor não é um número válido e nem DI (Dado Indisponível) para o indicador pai '{parent}'.` · `{proporcionalidades}: {n} valores que não são número válido nem DI (Dado Indisponível) para o indicador pai '{parent}' entre as linhas {first} e {last}.`
- Target message key: `rule.PROP-007.error_single`, `rule.PROP-007.error_aggregate`
- Implemented by: `rules/proportionality.py::check_sum_properties_in_influencing_factors` → `ProportionalityProcessing.find_invalid_numeric_cells` (ARC-017 Phase 3 Port 7; legacy `SpProportionalityValidator._check_sum_equals_one`/`ProportionalityProcessing.validate_numeric_format` deleted/refactored — the helper is now message-free, returning the invalid-cell mask; the rule builds the `Issue`). PROP-007…010 share one `RuleSpec` (`rule_id="PROP-007"`, category `SUM_PROP`) — see the module's own docstring for why.
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckSumPropertiesInInfluencingFactors` (single-cell and aggregated variants, isolated from PROP-008/009/010 by construction); `tests/unit/helpers/common/validation/test_proportionality_processing.py::TestFindInvalidNumericCells` for the mask itself
- Notes / known defects: blank cells count as valid (`df_data.notna()` guard) although the protocol says "dado ausente será considerado erro" (gap G-23).

### PROP-008 · Values must have at most three decimal places
- Severity: warning
- NamesEnum: SUM_PROP
- Protocol: §2.7 p.14 ("no máximo três casas decimais"), v1.8
- Statement: cells with more than `PRECISION_DECIMAL_PLACE_TRUNCATE = 3` decimals are counted across all parents and summarised once (first affected row); sums use the truncated values.
- Current message (pt-BR): `{proporcionalidades}, linha {first_line}: Existe(m) {count} valor(es) com mais de 3 casas decimais, serão consideradas apenas as 3 primeiras casas decimais.`
- Target message key: `rule.PROP-008.warning_one`, `rule.PROP-008.warning_many` (singular/plural, matching `rules/value.py`'s VAL-005 precedent)
- Implemented by: `rules/proportionality.py::check_sum_properties_in_influencing_factors` → `ProportionalityProcessing.find_excessive_decimal_mask` (ARC-017 Phase 3 Port 7; legacy `ProportionalityProcessing.check_excessive_decimals` refactored to a message-free mask; PROP-007…010 share one `RuleSpec`, see PROP-007's entry)
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckSumPropertiesInInfluencingFactors` (single and multiple excessive-decimal cells, each isolated so the truncated row still sums to exactly 1, ruling out a simultaneous PROP-010 finding); `tests/unit/helpers/common/validation/test_proportionality_processing.py::TestFindExcessiveDecimalMask` for the mask itself
- Notes / known defects: "3" hard-coded in the message while the precision is configurable.

### PROP-009 · A zero-sum row must correspond to zero/DI values in `valores`
- Severity: error
- NamesEnum: SUM_PROP
- Protocol: §2.7 p.14 ("quando a composição … tiver apenas valores zero ou DI, os respectivos fatores influenciadores deverão ter valor zero"), v1.5
- Statement: for each row whose truncated child factors sum to 0, look up the same `id` in `valores`; every child column present there must be `DI` or 0, otherwise error.
- Current message (pt-BR): `{proporcionalidades}: A soma de fatores influenciadores para o ID '{id}' no pai '{col}' é 0 (zero). Na planilha {valores}, existe(m) valor(es) para os filhos do indicador '{col}', no mesmo ID, que não é (são) zero ou DI (Dado Indisponível).`
- Target message key: `rule.PROP-009.error`
- Implemented by: `rules/proportionality.py::check_sum_properties_in_influencing_factors` → `ProportionalityProcessing.find_zero_sum_violations` (ARC-017 Phase 3 Port 7; legacy `ProportionalityProcessing.validate_zero_sum_rows` refactored to return `(id, child_column)` violation pairs, message-free; PROP-007…010 share one `RuleSpec`, see PROP-007's entry)
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckSumPropertiesInInfluencingFactors` (a non-zero/non-DI `valores` cell is a violation; a zero or DI cell is not); `tests/unit/helpers/common/validation/test_proportionality_processing.py::TestFindZeroSumViolations` (zero/DI/non-zero cells, a non-zero-sum row never checked, an id absent from `valores`, an unparseable value — all skipped without raising)
- Notes / known defects: SEC-004 resolved for this site — the redundant `except (ValueError, TypeError, Exception): pass` (equivalent to a bare `except Exception`, since `Exception` already covers `ValueError`/`TypeError`) is now `except (ValueError, TypeError): continue`, the only exceptions `float(str(val)...)` can actually raise here; the message's `'{col}'` is still the child column, not the parent (unchanged, preserved).

### PROP-010 · Factors of a parent must sum to 1 (tolerance ±0.01)
- Severity: error (outside [0.99, 1.01] and ≠ 0) / warning (inside the band but ≠ 1)
- NamesEnum: SUM_PROP
- Protocol: §2.7 p.14 ("a soma da composição para cada indicador deve ser um, mas podem existir exceções quando os dados não estão normalizados")
- Statement: per parent and row, sum of truncated Decimal factors (DI → 0): if sum ≠ 0 and (sum < 0.99 or sum > 1.01) → error; if 0.99 ≤ sum ≤ 1.01 and sum ≠ 1 → warning. Numbers are formatted with the current locale.
- Current message (pt-BR): `{proporcionalidades}, linha {row + 3}: A soma dos valores para o indicador pai {parent} é {sum}, e não 1.` (same text for error and warning)
- Target message key: `rule.PROP-010.error`, `rule.PROP-010.warning`
- Implemented by: `rules/proportionality.py::check_sum_properties_in_influencing_factors` → `ProportionalityProcessing.convert_to_decimal_and_sum` + `ProportionalityProcessing.sum_tolerance_indices` (ARC-017 Phase 3 Port 7; legacy `ProportionalityProcessing.validate_sum_tolerance` refactored to return `(error_index, warning_index)`, message-free; the sum's locale formatting — `NumberFormattingProcessing.format_number_brazilian`, now type-hinted `float | Decimal` to match its actual accepted input — moved into the rule, which reads `ctx.options["current_language"]`; PROP-007…010 share one `RuleSpec`, see PROP-007's entry)
- Covered by tests: `tests/unit/rules/test_proportionality.py::TestCheckSumPropertiesInInfluencingFactors` (a sum outside tolerance is an error, inside-but-not-1 is a warning, the sum is formatted per `current_language`); `tests/unit/helpers/common/validation/test_proportionality_processing.py::TestSumToleranceIndices` (table-driven over the boundary values)
- Notes / known defects: tolerance not configurable; identical wording for error and warning.

## Gaps (protocol ↔ code)

- **G-23 blank cells**: protocol treats missing data as an error; code treats blanks as valid and sums them as 0.
- **G-24 first two columns are spatial**: protocol says the first two columns are the spatial representation (§3.2); code expects a single `id` sub-column and ignores `unnamed` level-0.
- Non-normalised exceptions ("podem existir exceções") have no opt-out flag.

## Protocol v1.16 update (2026-09-12)

- **Territory registry**: when the optional server file `spd_data.json` is present, every
  `proporcionalidades.id` must exist in it — TERR-002 in [territories.md](territories.md)
  (**resolved**, PROTO-013, Phase 6 round N3). Uses the same `id`-by-level-1 lookup G-24 already
  documents (`("Unnamed: 0_level_0", "id")` in a real bundle, never `("id", "id")`) —
  `rules/territories.py::_proportionality_id_column`, matching this file's own
  `_proportionality_missing_id` precedent.
- §2.7 keeps "a soma … deve ser um, mas podem existir exceções quando os dados não estão
  normalizados" — PROP-010 is stricter than the protocol; severity decision filed as PROTO-015.
- p.13 uses the singular "proporcionalidade.xlsx" once; §2 (p.3) keeps the plural file name — the
  plural remains authoritative.

Last synced with code: Phase 6 round N3, 2026-09-13 (PROTO-013: TERR-002 added to
`rules/territories.py`)
