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
- Target message key: `rule.LEG-001.error`
- Implemented by: `helpers/common/validation/legend_processing.py::LegendProcessing.validate_code_sequence` from `models/sp_legend.py::SpLegend.data_cleaning`
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-002 · Labels must not be empty
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 (`label`: "Nome da fatia")
- Statement: within a legend, `label` is non-null and non-empty; rows listed.
- Current message (pt-BR): `{filename} [código: {code}, linha(s): {rows}]: A coluna 'label' contém valores vazios ou nulos.`
- Target message key: `rule.LEG-002.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 1)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-003 · `codigo`, `minimo`, `maximo`, `ordem` must be numeric (except the DI row)
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12
- Statement: for rows whose label ≠ `Dado indisponível`, the four columns parse as numbers; offending rows and original values are listed per column.
- Current message (pt-BR): `{filename} [código: {code}, linha(s): {rows}]: A coluna '{col}' contém valores não numéricos: [..]`
- Target message key: `rule.LEG-003.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 2)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-004 · The DI row must have empty `minimo`/`maximo`
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("Para Dado indisponível, o valor deve ser deixado em branco")
- Statement: rows labelled `Dado indisponível` must have null `minimo` and null `maximo`.
- Current message (pt-BR): `{filename} [código: {code}, linha(s): {rows}]: A coluna 'minimo' deve estar vazia quando o label é 'Dado indisponível'.` (and `maximo`)
- Target message key: `rule.LEG-004.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 2.2)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-005 · Exactly one `Dado indisponível` label per legend
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.11 ("O sexto grupo indica que o dado não está disponível")
- Statement: each `codigo` group contains exactly one row with label `Dado indisponível` (case-sensitive).
- Current message (pt-BR): `{filename} [código: {code}]: Deve existir um label 'Dado indisponível' por código, mas nenhum foi encontrado.` · `{filename} [código: {code}, linha(s): {rows}]: Deve existir exatamente um label 'Dado indisponível' por código, mas foram encontrados {n}.`
- Target message key: `rule.LEG-005.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 2.3)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-006 · `codigo` and `ordem` must be integers ≥ 1
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12
- Statement: every cell in both columns is an integer ≥ 1 (checked for the DI row too).
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: A coluna '{col}' contém um valor inválido: O valor '{value}' não é um número inteiro válido.`
- Target message key: `rule.LEG-006.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_columns_dtypes_numeric` (step 3)
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-007 · Labels must be unique within a legend
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("Os nomes não podem ser repetidos dentro de uma mesma legenda")
- Statement: no duplicated `label` inside a `codigo` group.
- Current message (pt-BR): `{filename} [código: {code}]: O label '{label}' está duplicado. Labels devem ser únicos para cada código de legenda.`
- Target message key: `rule.LEG-007.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_legend_labels`
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-008 · Colours must be hexadecimal
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("formato hexadecimal começando com # e seguido de seis valores hexadecimais")
- Statement: `cor` matches `^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$`.
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: O formato da cor '{color}' é inválido. Use o formato hexadecimal (ex: #RRGGBB).`
- Target message key: `rule.LEG-008.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_color_format`
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: 3-digit form accepted although the protocol requires six digits (gap G-19); `iterrows`.

### LEG-009 · `minimo`/`maximo` must have at most two decimals
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.11–12 ("todos os valores dos indicadores devem possuir duas casas decimais")
- Statement: excluding the DI row, each numeric bound has ≤ 2 decimals; when violated the platform falls back to the default range.
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: Legenda inválida. O valor mínimo '{min}' possui mais de duas casas decimais. Será considerado o intervalo padrão (0 a 1).` (and `máximo`)
- Target message key: `rule.LEG-009.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_min_max_has_excessive_decimals`
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-010 · `minimo` < `maximo` and intervals are contiguous (+0.01)
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.11–12 ("O valor máximo deve ser maior do que o valor mínimo"; "se um intervalo vai até o valor 25,38, o próximo intervalo deverá começar no valor 25,39")
- Statement: excluding the DI row and sorting slices by `minimo`: each `minimo < maximo`; each `minimo` equals the previous `maximo + 0.01` (Decimal arithmetic). Skipped entirely for a legend when LEG-009 fails.
- Current message (pt-BR): `{filename} [código: {code}, linha: {row}]: O valor mínimo ({min}) deve ser menor que o valor máximo ({max}).` · `{filename} [código: {code}, linha: {row}]: O intervalo não é contínuo. O valor mínimo {min} deveria ser {prev_max + 0.01} para seguir o valor máximo anterior.` · `{filename} [código: {code}, linha: {row}]: Valor inválido para operação de mínimo/máximo.`
- Target message key: `rule.LEG-010.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_min_max_values`
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: this is the effective "no overlap" rule; the `LEG_OVER` title exists but is unused (gap G-08). `{prev_max_val + 0.01}` uses float formatting.

### LEG-011 · `ordem` must be 1..n within a legend
- Severity: error
- NamesEnum: FC
- Protocol: §2.5 p.12 ("uma legenda com cinco fatias deve ter valores de um a cinco na ordem")
- Statement: sorted `ordem` values equal `[1, …, n]` for the group; non-numeric aborts.
- Current message (pt-BR): `{filename}: A coluna 'ordem' da legenda '{code}' contém valores não numéricos.` · `{filename} [código: {code}]: A coluna 'ordem' da legenda não é sequencial ou não começa em 1. Valores encontrados: [..]`
- Target message key: `rule.LEG-011.error`
- Implemented by: `legend_processing.py::LegendProcessing.validate_order_sequence`
- Covered by tests: `tests/unit/helpers/common/validation/test_legend_processing.py`
- Notes / known defects: —

### LEG-012 · Legend references in `descricao` must exist; unreferenced legends are warned
- Severity: error (missing) / warning (unreferenced)
- NamesEnum: LEG_REL (`verification_name_legend_relations`)
- Protocol: §2.3 p.9, §2.5
- Statement: preconditions — legend sanity passed and `descricao` has `codigo`, `nivel`, `legenda`. Let A = numeric `legenda` values of description rows with level ≠ 1; B = distinct `legenda.codigo`. A − B → error; B − A → warning.
- Current message (pt-BR): `{descricao}: Códigos de legenda ausentes em {legenda}: [..].` · `{legenda}: Códigos de legenda não referenciados em {descricao}: [..].` · missing column → error with the abort text
- Target message key: `rule.LEG-012.error`, `rule.LEG-012.warning`
- Implemented by: `validators/spreadsheets/legend/legend_validator.py::SpLegendValidator.validate_relation_indicators_in_legend`
- Covered by tests: none — TST-001
- Notes / known defects: string comparison of `nivel` (BUG-014).

### LEG-013 · Level-1 indicators must not reference a legend
- Severity: error
- NamesEnum: LEG_REL
- Protocol: §1 p.1 (level 1 "sem qualquer dado associado")
- Statement: no description row with level 1 has a non-empty `legenda`.
- Current message (pt-BR): `{descricao}: Indicadores de nível 1 não podem ter referência de legenda. Códigos com referência em {legenda}: [..].`
- Target message key: `rule.LEG-013.error`
- Implemented by: `legend_validator.py::SpLegendValidator.validate_relation_indicators_in_legend`
- Covered by tests: none — TST-001
- Notes / known defects: the message lists *all* level-1 codes, not only the offending ones.

### LEG-014 · Indicators at levels other than 1 and 2 must reference a legend
- Severity: error
- NamesEnum: LEG_REL
- Protocol: not in protocol — implemented behaviour (protocol says empty cells use the default legend)
- Statement: every description row with level ∉ {1, 2} has a non-empty `legenda`.
- Current message (pt-BR): `{descricao}: Indicadores de níveis diferentes de 1 e 2 devem ter referência de legenda. Indicadores sem referência em {legenda}: [..].`
- Target message key: `rule.LEG-014.error`
- Implemented by: `legend_validator.py::SpLegendValidator.validate_relation_indicators_in_legend`
- Covered by tests: none — TST-001
- Notes / known defects: conflicts with protocol §2.3 p.9 "todos os valores vazios serão associados à legenda default" (gap G-20).

### LEG-015 · Values must fall inside their legend's range
- Severity: error
- NamesEnum: LEG_RANGE (`verification_name_legend_data_range`)
- Protocol: §2.5 p.11 ("a legenda deverá contemplar os valores máximo e mínimo dos dados para todos os tempos disponíveis"), §2.6 p.13 (normalised values in [0, 1])
- Statement: for each pattern-matching `valores` column whose indicator is not level 1: resolve the indicator's `legenda` code → [min(minimo), max(maximo)] over non-DI slices; without a legend (or unparsable bounds) use [0, 1]. Every numeric cell (skipping `DI` and non-numeric) must satisfy min ≤ value ≤ max. Runs even when the legend file is absent. Skipped when `valores` or `descricao` is empty.
- Current message (pt-BR): `{valores}, linha {index + 2}: O valor {value} está fora do intervalo da legenda de código '{legend_id}' ({min} a {max}) para a coluna '{column}'.` · `… fora do intervalo da legenda padrão (0 a 1) …`
- Target message key: `rule.LEG-015.error`
- Implemented by: `legend_validator.py::SpLegendValidator.validate_range_multiple_legend` (`ModelMappingLegend`)
- Covered by tests: none — TST-001
- Notes / known defects: cell-by-cell loop (PERF-001); string comparison of `nivel` (BUG-014).

## Gaps (protocol ↔ code)

- **G-19 colour format**: protocol requires six hex digits; code accepts three.
- **G-20 empty `legenda` cells**: protocol assigns the default legend; code errors for levels ≥ 3 (LEG-014).
- **G-21 grey for DI** and **max 11 slices / 5–7 advised**: not validated.
- **G-22 legend ≤ data minimum**: protocol demands the smallest `minimo` be ≤ the indicator's minimum; code reports out-of-range values (LEG-015) — equivalent in effect, different wording.

Last synced with code: 3dcfdb1
