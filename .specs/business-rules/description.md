# `descricao` — indicator description

Purpose: one row per index/indicator of the strategic sector: identity (`codigo`), hierarchy level,
names, descriptions, metadata used by the AdaptaBrasil UI (protocol §2.3, p.5–9, Figure 3).
Files: `descricao.xlsx` or `descricao.csv` (`|`-separated). Single header. Required.

## Columns

| Column | Kind | Type after cleaning | Constraints (protocol) | Source in code |
|---|---|---|---|---|
| `codigo` | required | int ≥ 1 | unique, sequential 1..n ordered by level | `models/sp_description.py::RequiredColumn.COLUMN_CODE` |
| `nivel` | required | int ≥ 1 | 1 = sector, 2 = impact index, … | `RequiredColumn.COLUMN_LEVEL` |
| `nome_simples` | required | str | short, unique, ABNT capitalisation, ≤ 40 chars (tool) | `RequiredColumn.COLUMN_SIMPLE_NAME` |
| `nome_completo` | required | str | unique, ABNT capitalisation, ≥ len(`nome_simples`) | `RequiredColumn.COLUMN_COMPLETE_NAME` |
| `desc_simples` | required | str | ≤ 150 chars, no spatial/temporal/scenario refs, must **not** end with `.` (protocol) | `RequiredColumn.COLUMN_SIMPLE_DESC` |
| `desc_completa` | required | str | may contain HTML, must end with `.` | `RequiredColumn.COLUMN_COMPLETE_DESC` |
| `fontes` | required | str | free text, not spell-checked | `RequiredColumn.COLUMN_SOURCES` |
| `meta` | required (code) | str | ODS targets `6.2,13.1` or blank | `RequiredColumn.COLUMN_META` |
| `cenario` | dynamic | int ≥ −1 (code) / 0 or 1 (protocol) | only when `cenarios` exists | `DynamicColumn.COLUMN_SCENARIO` |
| `legenda` | dynamic | int ≥ 1 or empty | only when `legenda` exists | `DynamicColumn.COLUMN_LEGEND` |
| `unidade` | optional | str | empty = adimensional; injected as `""` when absent | `OptionalColumn.COLUMN_UNIT` |
| `relacao` | optional | int | 1 direct / −1 inverse; injected as `1` when absent | `OptionalColumn.COLUMN_RELATION` |
| `ordem` | optional | int ≥ 1 | sibling display order | `OptionalColumn.COLUMN_ORDER` |
| `categoria` | protocol v1.13 | — | `social`/`economico`/`ambiental`/`climatico` — **not known to the code** (gap G-05) | — |

`EXPECTED_COLUMNS` is computed at runtime: required + `cenario` (if `cenarios` file exists) +
`legenda` (if `legenda` file exists) + whichever optional columns are present
(`SpDescription.pre_processing`). Pre-processing drops/injects columns on `self.frame`, this
instance's own working copy — not the shared `DataLoaderModel.raw_data` (BUG-003, fixed).

## Rules

### DESC-001 · No HTML in the simple description
- Severity: warning
- NamesEnum: HTML_DESC (`verification_name_html_codes_in_descriptions`)
- Protocol: §2.3 p.7 (only `desc_completa` may contain HTML)
- Statement: `desc_simples` must not match `<.*?>`.
- Current message (pt-BR): `{filename}, linha {index + 2}: Coluna 'desc_simples' não pode conter código HTML.` · missing column → error `{filename}: A verificação foi abortada para a coluna obrigatória 'desc_simples' que está ausente.`
- Target message key: `rule.DESC-001.warning`
- Implemented by: `validators/spreadsheets/description/description_validator.py::SpDescriptionValidator.validate_html_in_descriptions`
- Covered by tests: none — TST-001
- Notes / known defects: `iterrows` (PERF-001).

### DESC-002 · Codes must be sequential from 1
- Severity: error
- NamesEnum: SC (`verification_name_sequential_codes`)
- Protocol: §2.3 p.5–6 ("ordem crescente e sequencial (1, 2, 3, 4…)")
- Statement: after cleaning, `codigo` must equal `1, 2, …, n` in file order; if any value is non-numeric the check is aborted with an error; a first code ≠ 1 is reported separately.
- Current message (pt-BR): `{filename}: A verificação foi abortada porque a coluna 'codigo' contém valores não numéricos.` · `{filename}: A coluna 'codigo' deve começar em 1.` · `{filename}: A coluna 'codigo' deve conter valores inteiros e sequenciais (1, 2, 3, ...).`
- Target message key: `rule.DESC-002.error`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_sequential_codes` (reads the model's own cleaned data via `SpModelABC.cleaned_column("codigo")` — BUG-002, fixed)
- Covered by tests: none — TST-001
- Notes / known defects: the protocol's extra requirement "ordered by level, no lower-level code between higher-level codes" is not checked (gap G-06).

### DESC-003 · Codes must be unique
- Severity: error
- NamesEnum: CO_UN (`verification_name_code_uniqueness`)
- Protocol: §2.3 p.5 ("um valor único para cada índice ou indicador")
- Statement: no duplicated values in cleaned `codigo`.
- Current message (pt-BR): `{filename}: A coluna 'codigo' contém códigos duplicados: {duplicated_codes}.`
- Target message key: `rule.DESC-003.error`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_unique_codes`
- Covered by tests: none — TST-001
- Notes / known defects: none (BUG-002 fixed — reads `cleaned_column("codigo")`).

### DESC-004 · Names follow ABNT capitalisation and have no stray whitespace
- Severity: warning
- NamesEnum: INP (`verification_name_indicator_name_pattern`)
- Protocol: §2.3 p.6 ("apenas o primeiro caractere da primeira palavra em maiúsculo (com a exceção de acrônimos)")
- Statement: for `nome_simples` and `nome_completo`, the expected text is: strip, remove CR/LF, first word capitalised, remaining words lower-case, all-uppercase tokens of length > 1 kept as acronyms. Any difference (including double spaces shown as `(EXTRA_SPACE)`, CR as `(CR)`, LF as `(LF)`) is reported with expected vs found.
- Current message (pt-BR): `{filename}, linha {idx + 2}: Valor da coluna '{column}' fora do padrão. Esperado: '{expected_text}'. Encontrado: '{original_text}'.` · missing column → warning with the abort text
- Target message key: `rule.DESC-004.warning`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_text_capitalization` using `helpers/common/formatting/text_formatting_processing.py::TextFormattingProcessing.capitalize_text_keep_acronyms`
- Covered by tests: helper covered by `tests/unit/helpers/common/formatting/test_text_formatting.py`
- Notes / known defects: proper nouns inside names (e.g. "Brasil") are flagged as warnings by design.

### DESC-005 · Level must be an integer ≥ 1
- Severity: error
- NamesEnum: IL (`verification_name_indicator_levels`)
- Protocol: §2.3 p.6 ("Os níveis são valores inteiros a partir de 1")
- Statement: every `nivel` cell parses as an integer ≥ 1.
- Current message (pt-BR): `{filename}, linha {index + 2}: O nível do indicador na coluna 'nivel' deve ser um número inteiro maior que 0.`
- Target message key: `rule.DESC-005.error`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_indicator_levels` (`NumberFormattingProcessing.check_cell_integer`)
- Covered by tests: helper covered by `tests/unit/helpers/common/formatting/test_number_formatting.py`
- Notes / known defects: duplicates CLEAN-001 (same rows reported under `FC`).

**Cross-sheet consumer note (BUG-014, fixed):** the shared helper
`helpers/common/validation/description_processing.py::DescriptionProcessing.get_valids_codes_from_description`
(consumed by VAL-002 and PROP-003 to compute the set of description codes that require a
matching `valores`/`proporcionalidades` column) used to compare `nivel` against the literal
strings `"1"`/`"2"`, so a level cell stored as `"1.0"` silently escaped the level-1 exclusion.
It now compares via `DataFrameProcessing.numeric_not_equals_mask`/`numeric_equals_mask`
(`pd.to_numeric(series, errors="coerce")`), tolerant of `"1.0"`, `" 1"`, `"01"`, etc. Regression
test: `tests/unit/helpers/common/validation/test_description_processing.py`.

### DESC-006 · Punctuation: names never end with punctuation, descriptions end with a period
- Severity: warning
- NamesEnum: MAND_PUNC_DESC (`verification_name_mandatory_and_prohibited_punctuation_in_descriptions`)
- Protocol: §2.3 p.7 — **partially contradicts**: protocol says `desc_simples` must *not* end with a special character such as `.`, while `desc_completa` must end with `.`
- Statement (as implemented): `nome_simples`, `nome_completo` must not end with one of `, . ; : ! ?`; `desc_simples` and `desc_completa` must end with `.`.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: O valor da coluna '{column}' não deve terminar com pontuação.` · `{file_name}, linha {idx + 2}: O valor da coluna '{column}' deve terminar com ponto.`
- Target message key: `rule.DESC-006.warning`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_punctuation` → `helpers/common/validation/character_processing.py::CharacterProcessing.check_characters_punctuation_rules`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: gap G-07 — decide with the protocol owners whether `desc_simples` must or must not end with `.`; goldens currently encode the code's behaviour.

### DESC-007 · Names and descriptions must not be empty
- Severity: error
- NamesEnum: EF (`verification_name_empty_fields`)
- Protocol: §2.3 (all four are mandatory content)
- Statement: `nome_simples`, `nome_completo`, `desc_simples`, `desc_completa` must be non-null and non-empty in every row.
- Current message (pt-BR): `{filename}, linha {index + 2}: Nenhum item da coluna '{column}' pode ser vazio.`
- Target message key: `rule.DESC-007.error`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_empty_strings`
- Covered by tests: none — TST-001
- Notes / known defects: whitespace-only cells are not treated as empty.

### DESC-008 · No CR/LF characters
- Severity: warning
- NamesEnum: LB_DESC (`verification_name_line_break_in_description`)
- Protocol: §6 p.17 (explained error "caracter inválido (LF) no final do texto")
- Statement: for every expected column, text must not start or end with CR (`\x0d`) or LF (`\x0a`); additionally `nome_simples`/`nome_completo` must not contain CR/LF anywhere (position reported, 1-based).
- Current message (pt-BR): `{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido (CR|LF) no final do texto. Remova o último caractere do texto.` · `… no início do texto. Remova o primeiro caractere do texto.` · `{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido ({CR|LF}) na posição {pos}. Remova o caractere do texto.`
- Target message key: `rule.DESC-008.warning`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_cr_lf_characters` → `character_processing.py::CharacterProcessing.check_special_characters_cr_lf`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: `EXPECTED_COLUMNS` includes injected `relacao`/`unidade` — intentional
  (see the `frame`-vs-`raw_data` note above; BUG-003 fixed, behaviour unchanged).

### DESC-009 · Simple description ≤ 150 characters
- Severity: warning
- NamesEnum: SIMP_DESC_N (`verification_name_simple_descriptions_over_n_chars`, value = 150)
- Protocol: §2.3 p.6 ("no máximo 150 caracteres, incluindo os espaços em branco")
- Statement: `len(desc_simples) ≤ 150`.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: O texto da coluna "desc_simples" excede o limite de 150 caracteres (encontrado: {actual_length}).`
- Target message key: `rule.DESC-009.warning`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_simple_description_length` → `BaseValidator._check_text_length` → `DataFrameProcessing.check_dataframe_text_length`; limit `SpDescription.CONSTANTS.MAX_SIMPLE_DESC_LENGTH` (duplicated in `ApplicationConfig.SIMPLE_DESCRIPTIONS_OVER_N_CHARS`)
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_column_validation.py`
- Notes / known defects: two sources for the constant (ARC-003).

### DESC-010 · Simple name ≤ 40 characters
- Severity: warning (skippable with `--no-warning-titles-length`)
- NamesEnum: TITLES_N (`verification_name_titles_over_n_chars`, value = 40)
- Protocol: not in protocol — implemented behaviour (protocol says "deverá ser testado na plataforma pela equipe do INPE")
- Statement: `len(nome_simples) ≤ 40`.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: O texto da coluna "nome_simples" excede o limite de 40 caracteres (encontrado: {actual_length}).`
- Target message key: `rule.DESC-010.warning`
- Implemented by: `description_validator.py::SpDescriptionValidator.validate_title_length`; limit `SpDescription.CONSTANTS.MAX_TITLE_LENGTH` / `ApplicationConfig.TITLE_OVER_N_CHARS`
- Covered by tests: none — TST-001
- Notes / known defects: when skipped the report lists the title under "not executed".

### DESC-011 · `cenario` column requires the scenarios file
- Severity: error
- NamesEnum: FS
- Protocol: §2.3 p.8 ("Quando o dado não tiver o arquivo cenarios.xlsx esta coluna não deverá ser usada")
- Statement: if `cenarios` was not read successfully and `descricao` has a `cenario` column, report and drop the column. If `cenarios` exists, `cenario` becomes an expected column (STRUCT-011).
- Current message (pt-BR): `{filename}: A coluna 'cenario' não pode existir se o arquivo 'cenarios' não estiver configurado ou não existir.`
- Target message key: `rule.DESC-011.error`
- Implemented by: `models/sp_description.py::SpDescription.pre_processing`
- Covered by tests: none — TST-001
- Notes / known defects: none (BUG-003 fixed — mutates this instance's own `self.frame`, not
  the shared `DataLoaderModel.raw_data`).

### DESC-012 · `legenda` column requires the legend file
- Severity: error
- NamesEnum: FS
- Protocol: §2.3 p.9 (`legenda` refers to `legenda.xlsx`)
- Statement: symmetric to DESC-011 for `legenda`.
- Current message (pt-BR): `{filename}: A coluna 'legenda' não pode existir se o arquivo de legenda não estiver configurado ou não existir.`
- Target message key: `rule.DESC-012.error`
- Implemented by: `models/sp_description.py::SpDescription.pre_processing`
- Covered by tests: none — TST-001
- Notes / known defects: none (BUG-003 fixed, see DESC-011).

### CLEAN-001 · `codigo` and `nivel` must be integers ≥ 1
- Severity: error
- NamesEnum: FC (`verification_name_file_cleaning`)
- Protocol: §2.3 p.5–6
- Statement: each cell parses as a number (comma or dot decimal), is integral and ≥ 1; invalid rows are dropped from the cleaned frame used by later rules.
- Current message (pt-BR): `{file_name}, linha {idx + 2}: A coluna '{column}' contém um valor inválido: {message}` where `{message}` ∈ `O valor '{cell}' não é um número.` · `O valor '{value}' não é um número inteiro.` · `O valor '{int}' é menor que 1.`
- Target message key: `rule.CLEAN-001.error`
- Implemented by: `models/sp_description.py::SpDescription.data_cleaning` → `helpers/common/processing/data_cleaning_processing.py::DataCleaningProcessing.clean_dataframe_integers`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_data_cleaning.py`
- Notes / known defects: none (BUG-002 fixed — cleaned data stored per-instance in
  `self.cleaned`, read via `cleaned_column()`); still repeated by several validators (PERF-003,
  open — see `.specs/quality/backlog/05-performance.md`).

### CLEAN-002 · `cenario` must be an integer ≥ −1
- Severity: error
- NamesEnum: FC
- Protocol: §2.3 p.8 says 0 or 1 — code accepts any integer ≥ −1 (gap G-09)
- Statement: when scenarios exist, every `cenario` cell is an integer ≥ −1.
- Current message (pt-BR): as CLEAN-001 with column `cenario` and `é menor que -1`
- Target message key: `rule.CLEAN-002.error`
- Implemented by: `models/sp_description.py::SpDescription.data_cleaning`
- Covered by tests: none — TST-001
- Notes / known defects: —

### CLEAN-003 · `legenda` must be an integer ≥ 1 or empty
- Severity: error
- NamesEnum: FC
- Protocol: §2.3 p.9
- Statement: when the legend file exists and the column is present, each cell is empty or an integer ≥ 1.
- Current message (pt-BR): as CLEAN-001 with column `legenda`
- Target message key: `rule.CLEAN-003.error`
- Implemented by: `models/sp_description.py::SpDescription.data_cleaning` (`allow_empty=True`)
- Covered by tests: none — TST-001
- Notes / known defects: —

## Gaps (protocol ↔ code)

- **G-05 `categoria`** (v1.13): not read, not validated; today it is reported as an unexpected column (STRUCT-012 warning).
- **G-06 code order by level**: "não inserir um codigo de menor nível entre codigos de níveis superiores" is not checked.
- **G-07 `desc_simples` trailing period**: code demands a final `.`, protocol forbids it.
- **G-09 `cenario` domain**: protocol {0,1}; code ≥ −1. Hierarchy propagation ("se um índice possui cenário, todos os índices construídos a partir deste também deverão") is not checked.
- **G-10 `relacao`** domain {1, −1}, **`ordem`** sibling sequence, **`meta`** format, **`nome_completo` ≥ `nome_simples` length**: not validated.
- **G-11 global uniqueness of names**: protocol says two indicators may not share `nome_simples`/`nome_completo`; code checks uniqueness per level-2 subtree only (COMP-004).

## Protocol v1.16 update (2026-09-12)

- **`fontes` removed** (v1.16): the column no longer exists in the protocol; the code still
  requires it, so a v1.16-compliant bundle fails DESC-011's missing-column check → PROTO-001
  (accept silently as deprecated when present; stop requiring).
- **`relacao` removed** (v1.15): the code still injects `relacao=1` onto `SpDescription.frame`
  (BUG-003, fixed — the injection itself is unchanged, only its target moved off the shared
  `raw_data`) and the composition tree validator lists it as required → PROTO-002.
- **`categoria`** (since v1.13) is still required by the protocol with domain
  `social|economico|ambiental|climatico`; today it only triggers an unexpected-column warning →
  PROTO-004 / planned DESC-013 (staged: warning on absence first, error after the Phase 4
  re-baseline).
- **`desc_simples` trailing period**: v1.16 repeats v1.13's prohibition; DESC-006 still requires
  the period for this column → PROTO-005 flips it (G-07).
- Also reserved: DESC-014 (codes ordered by level), DESC-015 (`cenario` ∈ {0,1} + propagation),
  DESC-017 (`ordem` sibling sequence), DESC-019 (`nome_completo` ≥ `nome_simples` length);
  DESC-016 (`relacao` domain) is retired unimplemented — the column is gone.

Last synced with code: 344fef7
