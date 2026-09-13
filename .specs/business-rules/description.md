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
| `meta` | required (code) | str | ODS targets `6.2,13.1` or blank | `RequiredColumn.COLUMN_META` |
| `cenario` | dynamic | int ≥ −1 (code) / 0 or 1 (protocol) | only when `cenarios` exists | `DynamicColumn.COLUMN_SCENARIO` |
| `legenda` | dynamic | int ≥ 1 or empty | only when `legenda` exists | `DynamicColumn.COLUMN_LEGEND` |
| `unidade` | optional | str | empty = adimensional; injected as `""` when absent | `OptionalColumn.COLUMN_UNIT` |
| `ordem` | optional | int ≥ 1 | sibling display order | `OptionalColumn.COLUMN_ORDER` |
| `fontes` | **deprecated** (PROTO-001) | str | removed by protocol v1.16 ("não é usada"); accepted silently, never required, never injected | `DeprecatedColumn.COLUMN_SOURCES` |
| `relacao` | **deprecated** (PROTO-002) | int | removed by protocol v1.15 ("parâmetro desnecessário"); accepted silently, never required, no longer injected | `DeprecatedColumn.COLUMN_RELATION` |
| `categoria` | optional (staged, PROTO-004) | str | `social`/`economico`/`ambiental`/`climatico`; absent → warning (staged step 1); present + invalid → error | `OptionalColumn.COLUMN_CATEGORY` |

`EXPECTED_COLUMNS` is computed at runtime: required + `cenario` (if `cenarios` file exists) +
`legenda` (if `legenda` file exists) + whichever optional columns are present + whichever
deprecated columns (`fontes`/`relacao`) are present (`SpDescription.pre_processing`).
Pre-processing drops/injects columns on `self.frame`, this instance's own working copy — not the
shared `LoadedSheet.raw_data` (BUG-003, fixed).

## Rules

### DESC-001 · No HTML in the simple description
- Severity: warning
- NamesEnum: HTML_DESC (`verification_name_html_codes_in_descriptions`)
- Protocol: §2.3 p.7 (only `desc_completa` may contain HTML)
- Statement: `desc_simples` must not match `<.*?>`.
- Current message (pt-BR): `{filename}, linha {row}: Coluna 'desc_simples' não pode conter código HTML.` · missing column → error, shared `rule.description.missing_required_column` text: `{filename}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente.`
- Target message key: `rule.DESC-001.warning` (missing column: `rule.description.missing_required_column`, `Severity.ERROR`)
- Implemented by: `rules/description.py::check_html_in_simple_description` (vectorised: `Series.str.contains(r"<.*?>", regex=True, na=False)` — PERF-001, done)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckHtmlInSimpleDescription`
- Notes / known defects: none — the `iterrows()` loop this rule used to run (PERF-001) is gone.

### DESC-002 · Codes must be sequential from 1
- Severity: error
- NamesEnum: SC (`verification_name_sequential_codes`)
- Protocol: §2.3 p.5–6 ("ordem crescente e sequencial (1, 2, 3, 4…)")
- Statement: after cleaning, `codigo` must equal `1, 2, …, n` in file order; if any value is non-numeric the check is aborted with an error; a first code ≠ 1 is reported separately.
- Current message (pt-BR): `{filename}: A verificação foi abortada porque a coluna 'codigo' contém valores não numéricos.` · `{filename}: A coluna 'codigo' deve começar em 1.` · `{filename}: A coluna 'codigo' deve conter valores inteiros e sequenciais (1, 2, 3, ...).`
- Target message key: `rule.DESC-002.non_numeric` / `rule.DESC-002.must_start_at_one` / `rule.DESC-002.must_be_sequential` (missing column: `rule.description.missing_required_column`, `Severity.ERROR`)
- Implemented by: `rules/description.py::check_sequential_codes` (reads `ctx.cleaned["descricao"]["codigo"]`, populated by `SpDescription.data_cleaning` — BUG-002, fixed)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckSequentialCodes`
- Notes / known defects: the protocol's extra requirement "ordered by level, no lower-level code between higher-level codes" is not checked (gap G-06).

### DESC-003 · Codes must be unique
- Severity: error
- NamesEnum: CO_UN (`verification_name_code_uniqueness`)
- Protocol: §2.3 p.5 ("um valor único para cada índice ou indicador")
- Statement: no duplicated values in cleaned `codigo`.
- Current message (pt-BR): `{filename}: A coluna 'codigo' contém códigos duplicados: {duplicated_codes}.`
- Target message key: `rule.DESC-003.error` (missing column: `rule.description.missing_required_column`, `Severity.ERROR`)
- Implemented by: `rules/description.py::check_unique_codes`
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckUniqueCodes`
- Notes / known defects: none (BUG-002 fixed — reads `ctx.cleaned["descricao"]["codigo"]`).

### DESC-004 · Names follow ABNT capitalisation and have no stray whitespace
- Severity: warning
- NamesEnum: INP (`verification_name_indicator_name_pattern`)
- Protocol: §2.3 p.6 ("apenas o primeiro caractere da primeira palavra em maiúsculo (com a exceção de acrônimos)")
- Statement: for `nome_simples` and `nome_completo`, the expected text is: strip, remove CR/LF, first word capitalised, remaining words lower-case, all-uppercase tokens of length > 1 kept as acronyms. Any difference (including double spaces shown as `(EXTRA_SPACE)`, CR as `(CR)`, LF as `(LF)`) is reported with expected vs found.
- Current message (pt-BR): `{filename}, linha {row}: Valor da coluna '{column}' fora do padrão. Esperado: '{expected_text}'. Encontrado: '{original_text}'.` · missing column → warning with the shared abort text
- Target message key: `rule.DESC-004.warning` (missing column: `rule.description.missing_required_column`, `Severity.WARNING`)
- Implemented by: `rules/description.py::check_name_capitalization` using `helpers/common/formatting/text_formatting_processing.py::TextFormattingProcessing.capitalize_text_keep_acronyms`
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckNameCapitalization`; helper also covered by `tests/unit/helpers/common/formatting/test_text_formatting.py`
- Notes / known defects: proper nouns inside names (e.g. "Brasil") are flagged as warnings by design.

### DESC-005 · Level must be an integer ≥ 1
- Severity: error
- NamesEnum: IL (`verification_name_indicator_levels`)
- Protocol: §2.3 p.6 ("Os níveis são valores inteiros a partir de 1")
- Statement: every `nivel` cell parses as an integer ≥ 1.
- Current message (pt-BR): `{filename}, linha {row}: O nível do indicador na coluna 'nivel' deve ser um número inteiro maior que 0.`
- Target message key: `rule.DESC-005.error` (missing column: `rule.description.missing_required_column`, `Severity.ERROR`)
- Implemented by: `rules/description.py::check_indicator_levels` (vectorised: `pd.to_numeric` mask over a comma-to-dot-normalised column, reproducing `NumberFormattingProcessing.check_cell_integer(min_value=1)`'s semantics exactly, including comma decimals like `"1,0"` — PERF-001, done)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckIndicatorLevels`; helper also covered by `tests/unit/helpers/common/formatting/test_number_formatting.py`
- Notes / known defects: duplicates CLEAN-001 (same rows reported under `FC`); the `iterrows()` loop this rule used to run (PERF-001) is gone.

**Cross-sheet consumer note (BUG-014, fixed):** the shared helper
`helpers/common/validation/description_processing.py::DescriptionProcessing.get_valids_codes_from_description`
(consumed by VAL-002 and PROP-003 to compute the set of description codes that require a
matching `valores`/`proporcionalidades` column) used to compare `nivel` against the literal
strings `"1"`/`"2"`, so a level cell stored as `"1.0"` silently escaped the level-1 exclusion.
It now compares via `DataFrameProcessing.numeric_not_equals_mask`/`numeric_equals_mask`
(`pd.to_numeric(series, errors="coerce")`), tolerant of `"1.0"`, `" 1"`, `"01"`, etc. Regression
test: `tests/unit/helpers/common/validation/test_description_processing.py`.

### DESC-006 · Punctuation: names and `desc_simples` never end with punctuation, `desc_completa` ends with a period
- Severity: warning
- NamesEnum: MAND_PUNC_DESC (`verification_name_mandatory_and_prohibited_punctuation_in_descriptions`)
- Protocol: §2.3 p.7 (v1.13 and v1.16 agree): "Toda descrição simples não pode terminar com um caractere especial como o ponto." — `desc_completa` must end with `.`.
- Statement (as implemented, PROTO-005 done): `nome_simples`, `nome_completo`, `desc_simples` must not end with one of `, . ; : ! ?`; `desc_completa` must end with `.`.
- Current message (pt-BR): `{filename}, linha {row}: O valor da coluna '{column}' não deve terminar com pontuação.` · `{filename}, linha {row}: O valor da coluna '{column}' deve terminar com ponto.`
- Target message key: `rule.DESC-006.no_punctuation` / `rule.DESC-006.must_end_with_dot` (missing column: `rule.description.missing_required_column`, `Severity.WARNING`)
- Implemented by: `rules/description.py::check_punctuation` — no longer calls `helpers/common/validation/character_processing.py::CharacterProcessing.check_characters_punctuation_rules` (that helper still builds its own hardcoded pt-BR strings and is out of this port's scope; it remains in use by `scenario_validator.py`/`temporal_reference_validator.py`), reimplemented with the same `.str[-1].isin(...)`/`.str.endswith(".")` masks; `_NO_PUNCTUATION_COLUMNS = (nome_simples, nome_completo, desc_simples)`, `_MUST_END_WITH_DOT_COLUMNS = (desc_completa,)`
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckPunctuation`; the still-used helper is covered by `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: gap G-07 resolved (PROTO-005, done, 2026-09-13) — `desc_simples` moved from `_MUST_END_WITH_DOT_COLUMNS` to `_NO_PUNCTUATION_COLUMNS`; goldens re-baselined (`tests/e2e/golden/CHANGELOG.md`).

### DESC-007 · Names and descriptions must not be empty
- Severity: error
- NamesEnum: EF (`verification_name_empty_fields`)
- Protocol: §2.3 (all four are mandatory content)
- Statement: `nome_simples`, `nome_completo`, `desc_simples`, `desc_completa` must be non-null and non-empty in every row.
- Current message (pt-BR): `{filename}, linha {row}: Nenhum item da coluna '{column}' pode ser vazio.`
- Target message key: `rule.DESC-007.error` (missing column: `rule.description.missing_required_column`, `Severity.ERROR`)
- Implemented by: `rules/description.py::check_empty_strings`
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckEmptyStrings`
- Notes / known defects: whitespace-only cells are not treated as empty.

### DESC-008 · No CR/LF characters
- Severity: warning
- NamesEnum: LB_DESC (`verification_name_line_break_in_description`)
- Protocol: §6 p.17 (explained error "caracter inválido (LF) no final do texto")
- Statement: for every expected column, text must not start or end with CR (`\x0d`) or LF (`\x0a`); additionally `nome_simples`/`nome_completo` must not contain CR/LF anywhere (position reported, 1-based).
- Current message (pt-BR): `{filename}, linha {row}: O texto da coluna '{column}' possui um caracter inválido ({char_type}) no final do texto. Remova o último caractere do texto.` · `… no início do texto. Remova o primeiro caractere do texto.` · `{filename}, linha {row}: O texto da coluna '{column}' possui um caracter inválido ({char_type}) na posição {position}. Remova o caractere do texto.`
- Target message key: `rule.DESC-008.end` / `rule.DESC-008.start` / `rule.DESC-008.anywhere` (missing column: `rule.description.missing_required_column`, `Severity.WARNING`)
- Implemented by: `rules/description.py::check_no_cr_lf_characters` — no longer calls `character_processing.py::CharacterProcessing.check_special_characters_cr_lf` (out of this port's scope, still used by `scenario_validator.py`/`temporal_reference_validator.py`), reimplemented with the same `.str.endswith`/`.str.startswith`/`re.finditer` shape; `columns_start_end` is `ctx.options["expected_columns"]`, the caller-supplied `SpDescription.EXPECTED_COLUMNS` for this run
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckNoCrLfCharacters`; the still-used helper is covered by `tests/unit/helpers/common/validation/test_dataframe_character_processing.py`
- Notes / known defects: `EXPECTED_COLUMNS` includes injected `relacao`/`unidade` — intentional
  (see the `frame`-vs-`raw_data` note above; BUG-003 fixed, behaviour unchanged).

### DESC-009 · Simple description ≤ 150 characters
- Severity: warning
- NamesEnum: SIMP_DESC_N (`verification_name_simple_descriptions_over_n_chars`, value = 150)
- Protocol: §2.3 p.6 ("no máximo 150 caracteres, incluindo os espaços em branco")
- Statement: `len(desc_simples) ≤ 150`.
- Current message (pt-BR): `{filename}, linha {row}: O texto da coluna "desc_simples" excede o limite de 150 caracteres (encontrado: {actual_length}).`
- Target message key: `rule.DESC-009.warning` (missing column: `rule.description.missing_required_column`, `Severity.WARNING`)
- Implemented by: `rules/description.py::check_simple_description_length`; limit read from `ctx.options["simple_desc_max_length"]` (`SpreadsheetProcessor._build_rule_context`, sourced from `ApplicationConfig.SIMPLE_DESCRIPTIONS_OVER_N_CHARS` — the rule no longer reads `SpDescription.CONSTANTS.MAX_SIMPLE_DESC_LENGTH` directly, since `rules` must not depend on `models`, `.claude/rules/architecture-boundaries.md`)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckSimpleDescriptionLength`
- Notes / known defects: two sources for the constant (ARC-003) — unchanged by this port.

### DESC-010 · Simple name ≤ 40 characters
- Severity: warning (skippable with `--no-warning-titles-length`)
- NamesEnum: TITLES_N (`verification_name_titles_over_n_chars`, value = 40)
- Protocol: not in protocol — implemented behaviour (protocol says "deverá ser testado na plataforma pela equipe do INPE")
- Statement: `len(nome_simples) ≤ 40`.
- Current message (pt-BR): `{filename}, linha {row}: O texto da coluna "nome_simples" excede o limite de 40 caracteres (encontrado: {actual_length}).`
- Target message key: `rule.DESC-010.warning` (missing column: `rule.description.missing_required_column`, `Severity.WARNING`)
- Implemented by: `rules/description.py::check_title_length`, returns `[]` immediately when `ctx.options["no_warning_titles_length"]` is set; limit read from `ctx.options["title_max_length"]` (sourced from `ApplicationConfig.TITLE_OVER_N_CHARS`)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckTitleLength`
- Notes / known defects: when skipped the report lists the title under "not executed" (`FileReportGenerator`, independent of this rule).

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
  the shared `LoadedSheet.raw_data`).

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

### DESC-013 · `categoria` domain (PROTO-004, staged)
- Severity: warning (column absent) / error (invalid value present)
- NamesEnum: CATEG_DESC (`verification_name_indicator_category`)
- Protocol: §2.3 p.8 (since v1.13): `categoria` ∈ `{social, economico, ambiental, climatico}`.
- Statement: when `categoria` is absent, report a single sheet-level warning (staged rollout —
  step 1; a future re-baseline promotes this to a missing-required-column error). When present,
  every non-blank cell must equal one of the four domain values exactly (unaccented, lower-case
  — an accented or mis-cased variant does not match); each mismatch is reported with the
  offending value and row.
- Current message (pt-BR): `{filename}: A coluna 'categoria' está ausente; o protocolo exige uma categoria (social, economico, ambiental ou climatico) para cada indicador.` · `{filename}, linha {row}: O valor '{value}' da coluna '{column}' deve ser um dos seguintes: {allowed_values}.`
- Target message key: `rule.DESC-013.warning` / `rule.DESC-013.error`
- Implemented by: `rules/description.py::check_category_domain` (vectorised `.isin(_CATEGORY_DOMAIN)` mask)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckCategoryDomain`
- Notes / known defects: staged (PROTO-004 step 1) — blank cells are not themselves flagged (DESC-007 does not cover `categoria`, so a blank cell in a present column currently passes silently); goldens re-baselined 2026-09-13 (every current fixture lacks the column, so every fixture gained the absence warning — see `tests/e2e/golden/CHANGELOG.md`).

### DESC-014 · Codes ordered by hierarchy level (PROTO-008)
- Severity: error
- NamesEnum: IL (`verification_name_indicator_levels`)
- Protocol: §2.3 p.6: "Não inserir um codigo de menor nível entre codigos de níveis superiores."
- Statement: after cleaning (`ctx.cleaned["descricao"]["codigo"]`/`["nivel"]`), sorted by ascending `codigo`, `nivel` must be non-decreasing — a row whose `nivel` is lower than the immediately preceding (in code order) row's `nivel` is an error. Reports nothing when either cleaned column is a different length than the raw frame (a cleaning failure DESC-002/CLEAN-001 already report).
- Current message (pt-BR): `{filename}, linha {row}: O indicador {codigo} (nível {nivel}) não pode ter um nível menor que o indicador anterior {previous_codigo} (nível {previous_nivel}); os níveis devem ser não decrescentes em ordem crescente de código.`
- Target message key: `rule.DESC-014.error` (missing column: `rule.description.missing_required_column`, `Severity.ERROR`)
- Implemented by: `rules/description.py::check_codes_ordered_by_level` (vectorised `.sort_values()` + `.shift()`, no `iterrows()`)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckCodesOrderedByLevel`
- Notes / known defects: resolves gap G-06. Goldens re-baselined 2026-09-13: `data_errors_09`/`data_errors_11` gain one new error each (pre-existing, previously undetected level-ordering defects); no other fixture is affected — see `tests/e2e/golden/CHANGELOG.md`.

### DESC-015 · `cenario` domain {0, 1} plus downward propagation (PROTO-009)
- Severity: error (domain half) / **warning** (propagation half — staged, see notes)
- NamesEnum: TH (`verification_name_tree_hierarchy`)
- Protocol: §2.3 p.8: `cenario` ∈ {0, 1}; "se um índice possui cenário, todos os índices construídos a partir deste também deverão" (hierarchy propagation).
- Statement: (1) domain — every cleaned `cenario` cell (`CLEAN-002` itself stays permissive, accepting any integer ≥ −1) outside `{0, 1}` is an **error**; (2) propagation — for every DIRECT `composicao` edge, a parent whose `cenario == 1` must have every child also `== 1`; a child with `cenario == 1` whose parent lacks it is **not** flagged (directional, one-way, matching the backlog's own worked example "parent with scenario whose child lacks it → error" — not a full transitive ancestor/descendant closure). The propagation half is a **warning**, staged down from an error (orchestrator decision, 2026-09-13) — see notes below.
- Current message (pt-BR): `{filename}, linha {row}: O valor '{value}' da coluna '{column}' deve ser 0 ou 1.` · `{filename}, linha {row}: O indicador pai {parent} (cenario {parent_cenario}) e o indicador filho {child} (cenario {child_cenario}) devem compartilhar o mesmo valor de 'cenario'.`
- Target message key: `rule.DESC-015.domain_error` / `rule.DESC-015.propagation_warning`
- Implemented by: `rules/description.py::check_scenario_domain_and_propagation`, reading `ctx.options["composition_facts"]` (`rules/composition.py::CompositionFacts`, computed once per run — BUG-019) for the cleaned `composicao` edges
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckScenarioDomainAndPropagation`
- Notes / known defects: resolves gap G-09 (domain half; propagation scoped to direct edges, not the full transitive closure — a documented, deliberately narrower slice). Goldens re-baselined 2026-09-13: **every** current fixture's `descricao` has a level-2 indicator (`codigo=2`, `cenario=1`) whose two direct `composicao` children both have `cenario=0` — each fixture gains two new **warnings** in "Hierarquia como árvore". The propagation half was initially shipped as an error, which flipped `data_ground_truth_01`'s `exit_code` from `0` to `1` for the first time (`errors` `0` → `2`) — an unacceptable regression risk for production bundles whose data predates this rule, since `data_ground_truth_01` is documented elsewhere (`CLAUDE.md`'s `make run FIXTURE=data_ground_truth_01`) as the "everything passes" example. Staged like PROTO-004 (`categoria`'s absence-warning step): the propagation half is now a warning (message text unchanged), so `data_ground_truth_01`'s `exit_code` stays `0`; promoting it back to an error is a future owner decision. See `tests/e2e/golden/CHANGELOG.md`'s PROTO-008/009/010 entry (and its same-day amendment) and `.specs/business-rules/protocol-changelog.md`'s PROTO-009/DESC-015 maintainer note.

### DESC-017 · `ordem` sibling sequence (PROTO-010)
- Severity: error
- NamesEnum: CHILD_LVL (`verification_name_child_indicator_levels`)
- Protocol: §2.3 pp.7-8 / `#202`: sibling display order.
- Statement: when `ordem` is present, for every `composicao` parent whose children's `ordem` values (looked up via cleaned `codigo`) are ALL parseable integers, that set must equal `{1, ..., n}` (`n` = number of children); a parent group with any missing/non-numeric `ordem` among its children is silently skipped (out of this rule's scope — that cell may still be reported by other checks). Reports nothing when `ordem` is absent (optional column) or `codigo`'s cleaning failed entirely.
- Current message (pt-BR): `{filename}: Os indicadores filhos do pai {parent} devem ter a coluna 'ordem' com valores sequenciais de 1 a n; valores encontrados: {observed_orders}.`
- Target message key: `rule.DESC-017.error`
- Implemented by: `rules/description.py::check_order_sibling_sequence`, reading `ctx.options["composition_facts"]`
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckOrderSiblingSequence`
- Notes / known defects: resolves part of gap G-10 (`ordem` sequence half). Goldens unchanged 2026-09-13 — every current fixture's `ordem` values already form a valid `1..n` sequence per parent.

### DESC-019 · `nome_completo` must be at least as long as `nome_simples` (PROTO-010)
- Severity: warning
- NamesEnum: INP (`verification_name_indicator_name_pattern`)
- Protocol: p.7.
- Statement: `len(nome_completo) >= len(nome_simples)` per row; missing-column abort mirrors DESC-004's own two-column shape (both columns' missing-column issues reported before any length is compared).
- Current message (pt-BR): `{filename}, linha {row}: O texto da coluna 'nome_completo' ({complete_length} caracteres) deve ter pelo menos o tamanho do texto da coluna 'nome_simples' ({simple_length} caracteres).`
- Target message key: `rule.DESC-019.warning` (missing column: `rule.description.missing_required_column`, `Severity.WARNING`)
- Implemented by: `rules/description.py::check_complete_name_length` (vectorised `.str.len()` comparison)
- Covered by tests: `tests/unit/rules/test_description.py::TestCheckCompleteNameLength`
- Notes / known defects: resolves part of gap G-10 (name-length half). Goldens re-baselined 2026-09-13: `data_errors_xss` gains one new warning — its known `<Script>` payload (appended to row 1's `nome_simples`) makes `nome_simples` longer than `nome_completo`, which no prior rule detected; no other fixture is affected.

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
- Notes / known defects: intentionally stays permissive at ≥ −1 (PROTO-009, done) — DESC-015 (rule layer) is the one that flags the protocol's stricter {0,1} domain as an error; keeping the model's own cleaning permissive avoids dropping a `cenario=-1` row from every other DESC-*/COMP-* rule's cleaned data before DESC-015 gets a chance to report it.

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

- **G-05 `categoria`** (v1.13): resolved (PROTO-004 step 1, done) — DESC-013 validates the domain when present and warns (not errors) when absent; step 2 (a future re-baseline promoting the absence to an error) is still open.
- **G-06 code order by level**: resolved (PROTO-008, done) — DESC-014 checks "não inserir um codigo de menor nível entre codigos de níveis superiores".
- **G-07 `desc_simples` trailing period**: resolved (PROTO-005, done) — the code now forbids the trailing period, matching the protocol.
- **G-09 `cenario` domain**: resolved (PROTO-009, done) — DESC-015 flags values outside {0,1} (`CLEAN-002` itself stays permissive at ≥ −1) and checks direct-edge downward propagation ("se um índice possui cenário, todos os índices construídos a partir deste também deverão"), scoped to direct `composicao` edges (not the full transitive closure — a documented, narrower slice).
- **G-10 `relacao`** domain {1, −1} (retired unimplemented — the column itself was removed, PROTO-002), **`ordem`** sibling sequence (resolved, PROTO-010, done — DESC-017), **`meta`** format (still parked, no owner decision), **`nome_completo` ≥ `nome_simples` length** (resolved, PROTO-010, done — DESC-019).
- **G-11 global uniqueness of names**: protocol says two indicators may not share `nome_simples`/`nome_completo`; code checks uniqueness per level-2 subtree only (COMP-004).

## Protocol v1.16 update (2026-09-12)

- **`fontes` removed** (v1.16, PROTO-001, done): the column no longer exists in the protocol.
  `fontes` moved from `RequiredColumn` to `DeprecatedColumn`/`ColumnKind.DEPRECATED` in
  `specs/sheet_specs.py`: a v1.16-compliant bundle without it reports no missing-column error;
  a bundle still carrying it (pre-v1.16 delivery) reports no unexpected-column warning either —
  `SpDescription.pre_processing` only adds it to `EXPECTED_COLUMNS` when present, never injects
  a default. Goldens byte-identical (every current fixture already carries `fontes`).
- **`relacao` removed** (v1.15, PROTO-002, done): `SpDescription.pre_processing` no longer
  injects `relacao=1` onto `self.frame`; the column moved to `DeprecatedColumn` the same way as
  `fontes` (accepted silently, never required). `rules/composition.py::_tree_required_column_issues`
  (COMP-007/008/009) no longer lists `relacao` among `descricao`'s required columns. Goldens
  byte-identical: `EXPECTED_COLUMNS` (and therefore DESC-008's CR/LF scan set) still includes
  `relacao` whenever a fixture's raw file carries it, exactly as when it was injected.
- **`categoria`** (since v1.13, PROTO-004 step 1, done): the protocol requires domain
  `social|economico|ambiental|climatico`; DESC-013 now validates it when present (error on an
  invalid value) and warns (not errors) when absent, staged to protect current sectors — step 2
  (absence becomes an error) is a future re-baseline, not part of this slice. Goldens
  re-baselined 2026-09-13 (every current fixture lacks `categoria`, so every fixture gained the
  one new absence warning — see `tests/e2e/golden/CHANGELOG.md`).
- **`desc_simples` trailing period** (PROTO-005, done): v1.16 repeats v1.13's prohibition;
  DESC-006 no longer requires the period for this column — flipped, re-baselined 2026-09-13
  (G-07 resolved).
- **DESC-014/DESC-015/DESC-017/DESC-019** (PROTO-008/PROTO-009/PROTO-010, all done 2026-09-13):
  codes ordered by level, `cenario` ∈ {0,1} + direct-edge downward propagation, `ordem` sibling
  sequence, and `nome_completo` ≥ `nome_simples` length are all implemented — see their own
  entries above and `tests/e2e/golden/CHANGELOG.md`'s PROTO-008/009/010 entry for the reviewed
  re-baseline (note in particular: `data_ground_truth_01`'s `exit_code` flips `0` → `1`, flagged
  there for explicit maintainer sign-off). DESC-016 (`relacao` domain) is retired unimplemented
  — the column itself is gone (PROTO-002). DESC-018 (`meta` format) stays parked, no owner
  decision yet.

Last synced with code: cf5ddaa
