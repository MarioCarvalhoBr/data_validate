# `legenda` — legends and legend relations

Purpose: colour classes (slices) used to render indicator values; several legends per sector, each
identified by `codigo` and referenced from `descricao.legenda` (protocol §2.5, p.10–12). Files:
`legenda.xlsx`/`.csv`. Single header. Optional — when absent every indicator uses the default
legend (six classes over [0, 1], sixth = "Dado indisponível").

## Columns

| Column | Kind | Type after cleaning | Constraints | Source in code |
|---|---|---|---|---|
| `codigo` | required | int ≥ 1 | same value for all rows of one legend; legends numbered 1..n | `models/sp_legend.py::RequiredColumn.COLUMN_CODE` |
| `label` | required | str | unique within a legend; exactly one `Dado indisponível` per legend | `RequiredColumn.COLUMN_LABEL` |
| `cor` | required | str | `#RRGGBB` (code also accepts `#RGB`) | `RequiredColumn.COLUMN_COLOR` |
| `minimo` | required | float, 2 decimals | blank for `Dado indisponível`; intervals contiguous by +0.01 | `RequiredColumn.COLUMN_MINIMUM` |
| `maximo` | required | float, 2 decimals | > `minimo`; blank for `Dado indisponível` | `RequiredColumn.COLUMN_MAXIMUM` |
| `ordem` | required | int ≥ 1 | 1..n within a legend | `RequiredColumn.COLUMN_ORDER` |

Constants: `LABEL_DATA_UNAVAILABLE = "Dado indisponível"`, default range
`MIN_LOWER_LEGEND_DEFAULT = 0`, `MAX_UPPER_LEGEND_DEFAULT = 1` (`SpLegend.CONSTANTS`,
`ApplicationConfig`).

Model-level checks (LEG-001…011) run in `SpLegend.data_cleaning` only when
`is_sanity_check_passed` (file exists, non-empty, no structural errors). They are grouped by
`codigo`; LEG-007…011 run for a group only when LEG-002…006 produced no error for it.

## Rules

### LEG-001 · Legend codes must be sequential from 1
- Severity: error
- NamesEnum: FC (`verification_name_file_cleaning`)
- Protocol: §2.5 p.12 ("O codigo deve ser um número inteiro, começando em 1 … valores um, dois e três")
- Statement: `codigo` must be numeric everywhere (else abort with the offending values); the sequence of distinct codes in file order must equal `1..n`, and the first must be 1.
- Current message (pt-BR): `{filename}: A coluna 'codigo' contém valores não numéricos e não pode ser validada para sequencialidade.` + `{filename}: Valores não numéricos encontrados na coluna 'codigo': [..]` · `{filename}: A sequência de códigos de legenda deve começar em 1. Código inicial encontrado: {first}` · `{filename}: Os códigos de legenda não são sequenciais. Códigos encontrados: [..]`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-001.non_numeric` /
  `.non_numeric_values` / `.must_start_at_one` / `.not_sequential` (four distinct templates, one
  per branch — not one shared `rule.LEG-001.error` key)
- Implemented by: `helpers/common/validation/legend_processing.py::LegendProcessing.validate_code_sequence` from `models/sp_legend.py::SpLegend.data_cleaning` (both now catalog-rendered via a `translate` parameter, `.claude/rules/i18n.md`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateCodeSequence`, including `translate`-wiring tests), `tests/unit/models/test_sp_legend.py` (proves `SpLegend.data_cleaning` forwards `self.context.language_manager.text`, not just the helper's cached default)
- Notes / known defects: —

### LEG-002 · Labels must not be empty
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 (`label`: "Nome da fatia")
- Statement: within a legend, `label` is non-null and non-empty; rows listed.
- Current message (pt-BR): `{filename} [código: {code}, linha(s): {rows}]: A coluna 'label' contém valores vazios ou nulos.`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-002.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 1, catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateLegendColumnsDtypesNumeric`, including `translate`-wiring tests)
- Notes / known defects: —

### LEG-003 · `codigo`, `minimo`, `maximo`, `ordem` must be numeric (except the DI row)
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12
- Statement: for rows whose label ≠ `Dado indisponível`, the four columns parse as numbers; offending rows and original values are listed per column.
- Current message (pt-BR): `{filename} [código: {code}, linha(s): {rows}]: A coluna '{col}' contém valores não numéricos: [..]`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-003.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 2, catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateLegendColumnsDtypesNumeric`, including `translate`-wiring tests)
- Notes / known defects: —

### LEG-004 · The DI row must have empty `minimo`/`maximo`
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("Para Dado indisponível, o valor deve ser deixado em branco")
- Statement: rows labelled `Dado indisponível` must have null `minimo` and null `maximo`.
- Current message (pt-BR): `{filename} [código: {code}, linha(s): {rows}]: A coluna 'minimo' deve estar vazia quando o label é 'Dado indisponível'.` (and `maximo`)
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-004.error` (one shared, parameterised key for both `minimo`/`maximo` — `column` param names which)
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 2.2, catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateLegendColumnsDtypesNumeric`, including a dedicated `translate`-wiring test for this branch)
- Notes / known defects: —

### LEG-005 · Exactly one `Dado indisponível` label per legend
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.11 ("O sexto grupo indica que o dado não está disponível")
- Statement: each `codigo` group contains exactly one row with label `Dado indisponível` (case-sensitive).
- Current message (pt-BR): `{filename} [código: {code}]: Deve existir um label 'Dado indisponível' por código, mas nenhum foi encontrado.` · `{filename} [código: {code}, linha(s): {rows}]: Deve existir exatamente um label 'Dado indisponível' por código, mas foram encontrados {n}.`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-005.error_missing` (no DI row) / `.error_multiple` (more than one)
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 2.3, catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateLegendColumnsDtypesNumeric`, including a dedicated `translate`-wiring test for the "multiple" branch)
- Notes / known defects: —

### LEG-006 · `codigo` and `ordem` must be integers ≥ 1
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12
- Statement: every cell in both columns is an integer ≥ 1 (checked for the DI row too).
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: A coluna '{col}' contém um valor inválido: O valor '{value}' não é um número inteiro válido.`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-006.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 3, catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateLegendColumnsDtypesNumeric`, including a `translate`-wiring test)
- Notes / known defects: —

### LEG-007 · Labels must be unique within a legend
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("Os nomes não podem ser repetidos dentro de uma mesma legenda")
- Statement: no duplicated `label` inside a `codigo` group.
- Current message (pt-BR): `{filename} [código: {code}]: O label '{label}' está duplicado. Labels devem ser únicos para cada código de legenda.`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-007.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_labels` (catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateLegendLabels`, including a `translate`-wiring test)
- Notes / known defects: —

### LEG-008 · Colours must be hexadecimal
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("formato hexadecimal começando com # e seguido de seis valores hexadecimais")
- Statement: `cor` matches `^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$`.
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: O formato da cor '{color}' é inválido. Use o formato hexadecimal (ex: #RRGGBB).`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-008.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_color_format` (catalog-rendered via `translate`; PERF-001: vectorised — a single `Series.str.match()` mask replaces the legacy `.iterrows()` loop)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateColorFormat`, including a `translate`-wiring test)
- Notes / known defects: 3-digit form accepted although the protocol requires six digits (gap G-19). `iterrows` fixed (PERF-001, Phase 5 round L2, 2026-09-13).

### LEG-009 · `minimo`/`maximo` must have at most two decimals
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.11–12 ("todos os valores dos indicadores devem possuir duas casas decimais")
- Statement: excluding the DI row, each numeric bound has ≤ 2 decimals; when violated the platform falls back to the default range.
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: Legenda inválida. O valor mínimo '{min}' possui mais de duas casas decimais. Será considerado o intervalo padrão (0 a 1).` (and `máximo`)
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-009.error_minimum` / `.error_maximum`
- Implemented by: `legend_processing.py::LegendProcessing.validate_min_max_has_excessive_decimals` (catalog-rendered via `translate`; PERF-001: vectorised — `Series.apply(check_two_decimals_places)` per column replaces the legacy `.iterrows()` loop)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateMinMaxHasExcessiveDecimals` — new, this rule had zero direct test coverage before Phase 5 round L2)
- Notes / known defects: `iterrows` fixed (PERF-001, Phase 5 round L2, 2026-09-13).

### LEG-010 · `minimo` < `maximo` and intervals are contiguous (+0.01)
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.11–12 ("O valor máximo deve ser maior do que o valor mínimo"; "se um intervalo vai até o valor 25,38, o próximo intervalo deverá começar no valor 25,39")
- Statement: excluding the DI row and sorting slices by `minimo`: each `minimo < maximo`; each `minimo` equals the previous `maximo + 0.01` (Decimal arithmetic). Skipped entirely for a legend when LEG-009 fails.
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: O valor mínimo ({min}) deve ser menor que o valor máximo ({max}).` · `{filename} [código: {code}, linha: {row}]: O intervalo não é contínuo. O valor mínimo {min} deveria ser {prev_max + 0.01} para seguir o valor máximo anterior.` · `{filename} [código: {code}, linha: {row}]: Valor inválido para operação de mínimo/máximo.`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-010.range_error` / `.continuity_error` / `.invalid_operation_error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_min_max_values` (catalog-rendered via `translate`; PERF-001: vectorised — `invalid_range_mask = min_col >= max_col` and `previous_max = max_col.shift(1)` replace the legacy stateful `.iterrows()` loop that carried `prev_max_val` by hand; the remaining loop `zip()`s plain values and is verified to preserve the historical range-then-continuity-per-row message order)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateMinMaxValues`, plus `test_validate_min_max_values_interleaved_order_preserved` pinning the PERF-001 rewrite's message order)
- Notes / known defects: this is the effective "no overlap" rule; the `LEG_OVER` title exists but is unused (gap G-08). `{prev_max_val + 0.01}` uses float formatting.

### LEG-011 · `ordem` must be 1..n within a legend
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("uma legenda com cinco fatias deve ter valores de um a cinco na ordem")
- Statement: sorted `ordem` values equal `[1, …, n]` for the group; non-numeric aborts.
- Current message (pt-BR): `{filename}: A coluna 'ordem' da legenda '{code}' contém valores não numéricos.` · `{filename} [código: {code}]: A coluna 'ordem' da legenda não é sequencial ou não começa em 1. Valores encontrados: [..]`
- Message key (implemented, Phase 5 round L2, 2026-09-13): `rule.LEG-011.non_numeric` / `.not_sequential`
- Implemented by: `legend_processing.py::LegendProcessing.validate_order_sequence` (catalog-rendered via `translate`)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py` (`TestValidateOrderSequence`, including `translate`-wiring tests)
- Notes / known defects: —

### LEG-012 · Legend references in `descricao` must exist; unreferenced legends are warned
- Severity: error (missing) / warning (unreferenced)
- NamesEnum: LEG_REL (`verification_name_legend_relations`)
- Protocol: §2.3 p.9, §2.5
- Statement: preconditions — legend sanity passed and `descricao` has `codigo`, `nivel`, `legenda`. Let A = numeric `legenda` values of description rows with level ≠ 1; B = distinct `legenda.codigo`. A − B → error; B − A → warning.
- Current message (pt-BR): `{descricao}: Códigos de legenda ausentes em {legenda}: [..].` · `{legenda}: Códigos de legenda não referenciados em {descricao}: [..].` · missing column → error with the abort text
- Target message key: `rule.LEG-012.error`, `rule.LEG-012.warning`
- Implemented by: `rules/legend.py::check_relation_missing_and_unreferenced_codes`/`_analyze_relation_indicators` (ARC-017 Phase 3 Port 6; owns the shared `rule.legend.missing_required_column` abort for LEG-012…014)
- Covered by tests: `tests/unit/rules/test_legend.py` (table-driven: missing code, unreferenced code, missing-column abort, `legend_sanity_ok` gate)
- Notes / known defects: none. BUG-014 (string comparison of `nivel`, e.g. `"1.0"` silently not
  matching `"1"`) fixed — `nivel` is now compared via
  `DataFrameProcessing.numeric_equals_mask`/`numeric_not_equals_mask`.

### LEG-013 · Level-1 indicators must not reference a legend
- Severity: error
- NamesEnum: LEG_REL
- Protocol: §1 p.1 (level 1 "sem qualquer dado associado")
- Statement: no description row with level 1 has a non-empty `legenda`.
- Current message (pt-BR): `{descricao}: Indicadores de nível 1 não podem ter referência de legenda. Códigos com referência em {legenda}: [..].`
- Target message key: `rule.LEG-013.error`
- Implemented by: `rules/legend.py::check_level_one_must_not_reference_legend`/`_analyze_relation_indicators` (ARC-017 Phase 3 Port 6; silent when LEG-012's shared abort fired)
- Covered by tests: `tests/unit/rules/test_legend.py` (table-driven: no legend reference, BUG-014 float-level regression, missing-column silence)
- Notes / known defects: the message lists *all* level-1 codes, not only the offending ones.
  BUG-014 (string comparison of `nivel`, e.g. `"1.0"` silently not matching `"1"` and skipping this
  rule entirely) fixed.

### LEG-014 · Indicators at levels other than 1 and 2 must reference a legend
- Severity: error
- NamesEnum: LEG_REL
- Protocol: not in protocol — implemented behaviour (protocol says empty cells use the default legend)
- Statement: every description row with level ∉ {1, 2} has a non-empty `legenda`.
- Current message (pt-BR): `{descricao}: Indicadores de níveis diferentes de 1 e 2 devem ter referência de legenda. Indicadores sem referência em {legenda}: [..].`
- Target message key: `rule.LEG-014.error`
- Implemented by: `rules/legend.py::check_other_levels_must_reference_legend`/`_analyze_relation_indicators` (ARC-017 Phase 3 Port 6; silent when LEG-012's shared abort fired)
- Covered by tests: `tests/unit/rules/test_legend.py` (table-driven: missing reference, has reference, BUG-014 float-level regression, missing-column silence)
- Notes / known defects: conflicts with protocol §2.3 p.9 "todos os valores vazios serão associados à legenda default" (gap G-20).
  BUG-014 (compound `nivel != "1" & nivel != "2"` string comparison, e.g. `"2.0"` wrongly treated
  as "some other level") fixed — both sides now use `DataFrameProcessing.numeric_not_equals_mask`.

### LEG-015 · Values must fall inside their legend's range
- Severity: error
- NamesEnum: LEG_RANGE (`verification_name_legend_data_range`)
- Protocol: §2.5 p.11 ("a legenda deverá contemplar os valores máximo e mínimo dos dados para todos os tempos disponíveis"), §2.6 p.13 (normalised values in [0, 1])
- Statement: for each pattern-matching `valores` column whose indicator is not level 1: resolve the indicator's `legenda` code → [min(minimo), max(maximo)] over non-DI slices; without a legend (or unparsable bounds) use [0, 1]. Every numeric cell (skipping `DI` and non-numeric) must satisfy min ≤ value ≤ max. Runs even when the legend file is absent. Skipped when `valores` or `descricao` is empty.
- Current message (pt-BR): `{valores}, linha {index + 2}: O valor {value} está fora do intervalo da legenda de código '{legend_id}' ({min} a {max}) para a coluna '{column}'.` · `… fora do intervalo da legenda padrão (0 a 1) …`
- Target message key: `rule.LEG-015.error_coded` (named-legend branch), `rule.LEG-015.error_default`
  (default-range branch) — two catalog keys, not one key with a pre-formatted "de código
  'X'"/"padrão" fragment param, so `en_US` renders a genuine English sentence in both cases
  (`.claude/rules/i18n.md`)
- Implemented by: `rules/legend.py::check_value_range_within_legend`/`_legend_range_for_column` (ARC-017 Phase 3 Port 6, replacing `ModelMappingLegend`)
- Covered by tests: `tests/unit/rules/test_legend.py` (table-driven: default range, coded range, `DI` cells, missing column, `legend_read_success`/`legend_sanity_ok` gates, BUG-014 float-level regression)
- Notes / known defects: cell-by-cell loop resolved (PERF-001) — `rules/legend.py`'s
  `out_of_range_mask` is one `pd.to_numeric(errors="coerce")` mask per matching column. BUG-014
  (string comparison of `nivel`) fixed — level 1 exclusion now uses
  `DataFrameProcessing.numeric_equals_mask`.

## Gaps (protocol ↔ code)

- **G-19 colour format**: protocol requires six hex digits; code accepts three.
- **G-20 empty `legenda` cells**: protocol assigns the default legend; code errors for levels ≥ 3 (LEG-014).
- **G-21 grey for DI** and **max 11 slices / 5–7 advised**: not validated.
- **G-22 legend ≤ data minimum**: protocol demands the smallest `minimo` be ≤ the indicator's minimum; code reports out-of-range values (LEG-015) — equivalent in effect, different wording.

Last synced with code: Phase 5 round L2, 2026-09-13 (ARC-005/PERF-001: LEG-001…011's messages are
catalog keys and its four `.iterrows()` loops are vectorised — see each rule's entry above; still
not ported to `rules/legend.py`, unlike LEG-012…015, which were ported by ARC-017 Phase 3 Port 6,
legacy `SpLegendValidator`/`ModelMappingLegend` deleted)
