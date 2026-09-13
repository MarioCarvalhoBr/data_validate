# `cenarios` — scenarios

Purpose: the future scenarios (e.g. optimistic/pessimistic RCP4.5/RCP8.5) whose symbols suffix the
value and proportionality column names (protocol §2.1, p.4). Files: `cenarios.xlsx`/`.csv`. Single
header. Optional — when absent the sector has no scenarios and `descricao` must not have a
`cenario` column (DESC-011).

## Columns

| Column | Kind | Type | Constraints | Source in code |
|---|---|---|---|---|
| `nome` | required | str | short, no trailing `.`, unique; spell-checked | `models/sp_scenario.py::RequiredColumn.COLUMN_NAME` |
| `descricao` | required | str | ends with `.`; spell-checked | `RequiredColumn.COLUMN_DESCRIPTION` |
| `simbolo` | required | str | letters and digits only (protocol v1.10); unique; used as `<cenario>` suffix | `RequiredColumn.COLUMN_SYMBOL` |

The distinct `simbolo` values are read once by `SpreadsheetProcessor._read_data` and injected into
every model as `scenarios` (`SpModelABC.VAR_CONSTS.SCENARIOS`); the loader sets
`scenario_exists_file` / `scenario_read_success`.

## Rules

### SCEN-001 · A delivered scenarios file must define at least one symbol
- Severity: error
- NamesEnum: FS (`verification_name_file_structure`)
- Protocol: §2.1
- Statement: if the file exists but no `simbolo` values could be read, report a configuration error.
- Current message (pt-BR): `{filename}: Arquivo de cenários com configuração incorreta. Consulte a especificação do modelo de dados.`
- Target message key: `rule.SCEN-001.error`
- Implemented by: `models/sp_scenario.py::SpScenario.pre_processing`
- Covered by tests: none — TST-001
- Notes / known defects: —

### SCEN-002 · Symbols must not repeat (structural pass)
- Severity: error
- NamesEnum: FS
- Protocol: §2.1
- Statement: duplicated `simbolo` values are reported with the list of duplicates.
- Current message (pt-BR): `{filename}: Valores duplicados encontrados na coluna 'simbolo': [{a}, {b}]`
- Target message key: `rule.SCEN-002.error`
- Implemented by: `models/sp_scenario.py::SpScenario.pre_processing`
- Covered by tests: none — TST-001
- Notes / known defects: overlaps SCEN-004 (same condition reported twice under `FS` and `UVR_SCEN`).

### SCEN-003 · Name never ends with punctuation; description ends with a period
- Severity: warning
- NamesEnum: MAND_PUNC_SCEN (`verification_name_mandatory_and_prohibited_punctuation_in_scenarios`)
- Protocol: §2.1 p.4 ("O nome não poderá terminar com algum caracter especial do tipo '.'", "Toda descrição deverá necessariamente terminar com um ponto")
- Statement: `nome` must not end with one of `, . ; : ! ?`; `descricao` must end with `.`.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: O valor da coluna 'nome' não deve terminar com pontuação.` · `{file_name}, linha {idx + 2}: O valor da coluna 'descricao' deve terminar com ponto.` · missing column → warning with the abort text
- Target message key: `rule.SCEN-003.no_punctuation` (name) / `rule.SCEN-003.must_end_with_dot` (description)
- Implemented by: `rules/scenario.py::check_punctuation` (ARC-017 Phase 3 Port 4; ported from `validators/spreadsheets/scenario/scenario_validator.py::SpScenarioValidator.validate_punctuation` → `CharacterProcessing.check_characters_punctuation_rules`, deleted)
- Covered by tests: `tests/unit/rules/test_scenario.py::TestCheckPunctuation`
- Notes / known defects: —

### SCEN-004 · `nome` and `simbolo` must be unique
- Severity: error
- NamesEnum: UVR_SCEN (`verification_name_unique_value_relations_in_scenarios`)
- Protocol: §2.1
- Statement: no duplicated values in either column.
- Current message (pt-BR): `{file_name}: A coluna '{column}' não deve conter valores repetidos.` · missing column → error with the abort text
- Target message key: `rule.SCEN-004.error`
- Implemented by: `rules/scenario.py::check_name_and_symbol_are_unique` (ARC-017 Phase 3 Port 4; ported from `scenario_validator.py::SpScenarioValidator.validate_unique_values` → `DataFrameProcessing.check_dataframe_unique_values`, deleted)
- Covered by tests: `tests/unit/rules/test_scenario.py::TestCheckNameAndSymbolAreUnique`
- Notes / known defects: —

### SCEN-005 · `simbolo` must be exactly one ASCII letter or digit
- Severity: error
- NamesEnum: SYMB_SCEN (`verification_name_scenario_symbol_charset`)
- Protocol: §2.1 p.4 (v1.16, clarifying v1.10's gap G-17): "Um único caractere ... apenas letras e
  números, não podendo ter espaço, pontuação ou qualquer outro caracter especial."
- Statement: every `simbolo` cell must match `^[A-Za-z0-9]$` — exactly one character, an ASCII
  letter or digit (an accented letter, e.g. `"é"`, is not ASCII and is also rejected: the protocol
  means the unaccented Latin alphabet the value-column pattern `CÓDIGO-ANO[-CENÁRIO]` can
  actually match).
- Current message (pt-BR): catalog key `rule.SCEN-005.error` — `{filename}, linha {row}: O valor
  '{value}' da coluna 'simbolo' deve conter exatamente um caractere alfanumérico.` (present in
  both locales)
- Target message key: `rule.SCEN-005.error`
- Implemented by: `rules/scenario.py::check_symbol_charset`
- Covered by tests: `tests/unit/rules/test_scenario.py::TestCheckSymbolCharset`
- Notes / known defects: resolves gap G-17 (PROTO-006). Every fixture's `cenarios.simbolo` is
  already a single ASCII letter (`"O"`/`"P"`), so this rule never fires against a shipped fixture.

## Gaps (protocol ↔ code)

- **G-17 symbol charset** (resolved, PROTO-006): SCEN-005 now validates "apenas letras e números,
  não podendo ter espaço, pontuação ou qualquer outro caracter especial" (length 1, ASCII
  alphanumeric).
- **G-18 default symbols `O`/`P`**: the protocol defines defaults when the file is absent; the code treats "no file" as "no scenarios" (both the `cenario` column and scenario columns become invalid). Confirm the intended behaviour with the protocol owners.
- `LB_SCEN` title is registered but never emitted (gap G-08).

## Protocol v1.16 update (2026-09-12)

- `simbolo` is explicitly "**Um único caractere**", letters and digits only (§2.1 p.4) — resolved:
  SCEN-005 (PROTO-006) validates length 1 + ASCII alphanumeric.
- New explicit note: sheet row order = display order in the platform; the first row is the default
  scenario (documentation only, nothing to validate).

Last synced with code: Phase 6 round N2, 2026-09-13 (SCEN-005/PROTO-006 added to `rules/scenario.py`)
