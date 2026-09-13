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

VAL-002…005 below are registered in `VALUE_REGISTRY` (`rules/value.py`, ARC-017 Phase 3 Port 5),
replacing the deleted `SpValueValidator`/`validators/spreadsheets/value/value_validator.py` and its
message-building helper `ValueProcessing`/`helpers/common/validation/value_processing.py` (also
deleted — its logic is reproduced as `Issue`s directly in `rules/value.py`, never reused, per
`.claude/rules/architecture-boundaries.md`'s "no hardcoded-string-building helper"). VAL-001 (the
column-name-pattern structural check) stays in `models/sp_value.py` — out of this port's scope.
VAL-003's per-code loop was rewritten `.iterrows()`-free (PERF-001) and VAL-004/VAL-005's per-cell
loop was rewritten as vectorised `pd.to_numeric` masks (PERF-001); see each rule's entry below and
`.specs/quality/backlog/05-performance.md`'s PERF-001 entry for the before/after shape.

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
- Implemented by: `rules/value.py::check_relation_indicators_in_values` (ARC-017 Phase 3 Port 5;
  ported from `validators/spreadsheets/value/value_validator.py::SpValueValidator.
  validate_relation_indicators_in_values`, deleted)
- Covered by tests: helpers covered by `tests/unit/helpers/common/processing/test_collections_processing.py`;
  `tests/unit/rules/test_value.py::TestCheckRelationIndicatorsInValues` (table-driven per failure
  mode, including the migrated BUG-014 regression)
- Notes / known defects: BUG-014 (string comparison of `nivel`, e.g. `"1.0"` silently not matching
  `"1"`) fixed — now `DataFrameProcessing.numeric_equals_mask`/`numeric_not_equals_mask`. The
  `cenario == "0"` comparison alongside it is a distinct column and was left untouched, out of
  BUG-014's scope.

### VAL-003 · Each indicator must have exactly the expected time/scenario columns
- Severity: error
- NamesEnum: VAL_COMB (`verification_name_value_combination_relations`)
- Protocol: §2.6 p.13 ("toda vez que algum índice ou indicador existir para algum cenário, deverão existir colunas para cada cenário … bem como para todos os anos futuros")
- Statement: with `T` = sorted distinct `referencia_temporal.simbolo` and `S` = scenario symbols, for each description row with level ≥ 2: if `cenario == 0` (or no scenarios) the only expected column is `<code>-<T[0]>`; if `cenario == 1` expected = `<code>-<T[0]>` ∪ {`<code>-<t>-<s>` for t in T[1:], s in S}. Missing expected columns are errors (except level 2 with `cenario == 0`, silently tolerated); any actual `<code>-…` column not in the expected set is "unnecessary" (level-1 message variant). Skipped when `descricao` or `referencia_temporal` is empty.
- Current message (pt-BR): `{valores}: A coluna '{combination}' é obrigatória.` · `{valores}: A coluna '{extra_column}' é desnecessária.` · `{valores}: A coluna '{extra_column}' é desnecessária para o indicador de nível 1.`
- Target message key: `rule.VAL-003.error`
- Implemented by: `rules/value.py::check_value_combination_relation` (ARC-017 Phase 3 Port 5;
  ported from `value_validator.py::SpValueValidator.validate_value_combination_relation`, deleted)
  → `helpers/common/generation/combinations_processing.py::CombinationsProcessing.generate_combinations`,
  `find_extra_combinations`
- Covered by tests: helper covered by `tests/unit/helpers/common/generation/test_combinations.py`;
  `tests/unit/rules/test_value.py::TestCheckValueCombinationRelation` (table-driven: missing/extra
  combinations, the level-2/scenario-0 special case, gap G-09, missing-required-column abort)
- Notes / known defects: `iterrows` fixed (PERF-001) — the legacy `for _, row in
  df_description.iterrows(): code = str(row[...]); ...` loop is now a `zip()` over plain Python
  lists extracted once via `.tolist()`, no `.iterrows()`, no per-row `Series` construction (see
  `.specs/quality/backlog/05-performance.md`'s PERF-001 entry); `cenario` values other than 0/1
  still yield no expected columns (gap G-09, preserved). BUG-001 (shared-list mutation) does not
  apply to the ported rule — `RuleContext` is frozen and the rule holds no shared mutable state
  across calls; idempotency is pinned by `tests/unit/rules/test_value.py::TestIdempotency`.

### VAL-004 · Cells must be numeric or `DI`
- Severity: error
- NamesEnum: UNAV_INV (`verification_name_unavailable_and_invalid_values`)
- Protocol: §2.6 p.13 ("Qualquer outro valor de texto ou dado ausente será considerado erro")
- Statement: in every pattern-matching column, each cell is `DI` or parses as a number (comma accepted). One message when a column has a single invalid cell, one aggregated message otherwise.
- Current message (pt-BR): `{filename}, linha {row + 2}: O valor {value} não é um número válido e nem DI (Dado Indisponível) para a coluna '{column}'.` · `{filename}: {n} valores que não são número válido nem DI (Dado Indisponível) para a coluna '{column}', entre as linhas {first} e {last}.`
- Target message key: `rule.VAL-004.error`
- Implemented by: `rules/value.py::check_unavailable_and_invalid_values` (ARC-017 Phase 3 Port 5;
  ported from `value_validator.py::SpValueValidator.validate_unavailable_codes_values` →
  `value_processing.py::ValueProcessing.validate_data_values_in_columns`, both deleted — the
  message-building helper's logic is reproduced directly as `Issue`s, never reused)
- Covered by tests: `tests/unit/rules/test_value.py::TestCheckUnavailableAndInvalidValues`
  (table-driven: `DI`, single vs. aggregated invalid cells, the literal-`inf`/textual-`"inf"`
  edge cases — see the Notes below —, missing-scenario-column abort)
- Notes / known defects: cell-by-cell loop fixed (PERF-001) — vectorised
  `pd.to_numeric(errors="coerce")` masks per column replace the legacy per-cell loop (see
  `.specs/quality/backlog/05-performance.md`'s PERF-001 entry); `DI` is still a local string
  constant (`rules/value.py::_DI_MARKER`), not read from `ApplicationConfig` — `rules` does not
  depend on `config` for this literal, out of this port's scope. The legacy
  `ValueProcessing.check_numeric_value`'s two infinity sub-cases are both preserved: a literal
  Python `float('inf')`/`-inf` cell is counted invalid with an empty message
  (`rule.VAL-004.silent`, not "fixed"); a textual `"inf"`/`"Infinity"` cell (which
  `pd.to_numeric` parses as a finite-looking, non-`NaN` float, but whose `Decimal` exponent is
  the special value `'F'`, raising `TypeError` in the legacy code's `except (ValueError,
  TypeError)` branch) renders `rule.VAL-004.decimal_parse_error`.

### VAL-005 · Values must have at most two decimal places
- Severity: warning
- NamesEnum: UNAV_INV
- Protocol: §2.6 p.12 ("usando no máximo duas casas decimais"); v1.8
- Statement: numeric cells with more than two decimals are counted across all value columns and summarised in one warning (first/last affected row); extra decimals are truncated by the platform.
- Current message (pt-BR): `{filename}: Existe(m) {count} valor(es) com mais de 2 casas decimais, serão consideradas apenas as 2 primeiras casas decimais. Entre as linhas {first_row} e {last_row}.`
- Target message key: `rule.VAL-005.warning`
- Implemented by: `rules/value.py::check_excessive_decimal_places` (ARC-017 Phase 3 Port 5;
  ported from `value_processing.py::ValueProcessing.generate_decimal_warning`, deleted) via
  `NumberFormattingProcessing.check_two_decimals_places`, now run once per *unique* candidate
  value (`Series.map`) instead of once per cell (PERF-001)
- Covered by tests: `tests/unit/rules/test_value.py::TestCheckExcessiveDecimalPlaces`
  (table-driven: singular/plural message, cross-column count/row-range aggregation, `DI`/invalid
  cells excluded, missing-scenario-column abort)
- Notes / known defects: —

### VAL-006 · `id` must contain no duplicated value
- Severity: error
- NamesEnum: UNIQ_VAL (`verification_name_value_id_uniqueness`)
- Protocol: §2.6 p.11 ("identificador único")
- Statement: `valores.id` must contain no duplicated value; duplicates are listed. No registry
  (`spd_data.json`, PROTO-013/TERR-002) is needed for this half of gap G-13 — uniqueness is a
  property of `valores` alone; completeness (every registry id present in `valores`) remains out
  of scope, tracked separately as TERR-001/TERR-002.
- Current message (pt-BR): catalog key `rule.VAL-006.error` — `{filename}: A coluna '{column}'
  contém valores de 'id' duplicados: {duplicated_ids}.` (present in both locales)
- Target message key: `rule.VAL-006.error`
- Implemented by: `rules/value.py::check_id_uniqueness`
- Covered by tests: `tests/unit/rules/test_value.py::TestCheckIdUniqueness`
- Notes / known defects: resolves the uniqueness half of gap G-13 (PROTO-017). No fixture's
  `valores.id` has a duplicate, so this rule never fires against a shipped fixture.

## Gaps (protocol ↔ code)

- **G-13 `id` completeness/uniqueness**: "Nesta coluna deverão ter todos os objetos descritos no shapefile ou … todos os municípios brasileiros" (full completeness — every registry id present in `valores`) cannot be checked without the spatial layer — remains open (an owner decision, not part of PROTO-013); the **subset direction is resolved** — TERR-001 (PROTO-013, done: every `valores.id` must exist in the optional `spd_data.json` registry, when present); uniqueness is **resolved** — VAL-006 (PROTO-017).
- **G-14 normalised range**: the [0,1] expectation is enforced only through the legend range rule (LEG-015) with default bounds 0–1.

## Protocol v1.16 update (2026-09-12)

- **Gap G-28**: §2.6 (p.12) still explains value orientation via the `relacao` column that v1.15
  removed from `descricao`; per the v1.15 history the information now lives in the legend. Until
  the owners fix the text, value orientation is treated as legend-defined (PROTO-016).
- **Territory registry**: when the optional server file `spd_data.json` is present, every
  `valores.id` must exist in it — TERR-001 in [territories.md](territories.md) (**resolved**,
  PROTO-013, Phase 6 round N3). `id` uniqueness is **resolved** — VAL-006 (PROTO-017).

Last synced with code: Phase 6 round N3, 2026-09-13 (PROTO-013: TERR-001 added to
`rules/territories.py`)
