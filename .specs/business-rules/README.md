# Business rules — index and conventions

Source documents: `assets/protocolo-v-1.16.pdf` ("Especificação de Requisitos e Formatos para
Entrega de Setores Estratégicos para o AdaptaBrasil MCTI", **v1.16, 2026-08-21** — current;
`assets/protocolo-v-1.13.pdf` is the historical baseline these files were first traced against)
and the current implementation (`data_validate/`). Each sheet has its own file; every check the
code performs today is listed as a rule with a stable ID, so that protocol → spec → code → test →
message stays traceable during the migration (backlog ARC-004, DOC-002). The v1.13 → v1.16 delta
and the code changes it requires live in [protocol-changelog.md](protocol-changelog.md) and in
backlog `09-protocol-v116.md` (`PROTO-*` items).

| File | Sheet / scope |
|---|---|
| [file-structure.md](file-structure.md) | Input folder, file names, loading, generic structural checks |
| [description.md](description.md) | `descricao` |
| [composition.md](composition.md) | `composicao` (tree/graph) |
| [values.md](values.md) | `valores` |
| [temporal-reference.md](temporal-reference.md) | `referencia_temporal` |
| [scenarios.md](scenarios.md) | `cenarios` |
| [legend.md](legend.md) | `legenda` and legend ↔ description ↔ values relations |
| [proportionality.md](proportionality.md) | `proporcionalidades` |
| [spelling.md](spelling.md) | Spell-check across sheets, `dicionario` |
| [territories.md](territories.md) | Optional server registry `spd_data.json` (maintainer decision 2026-09-12) |
| [protocol-changelog.md](protocol-changelog.md) | Protocol versions and protocol ↔ code gaps |

## Rule ID convention

`<PREFIX>-<NNN>`; IDs are stable and never reused. Prefixes:

| Prefix | Scope | Report category today |
|---|---|---|
| `STRUCT-` | Folder/file existence, loading, generic column structure | File structure (`FS`) |
| `CLEAN-` | Type/cleaning checks done inside `Sp*` models (`data_cleaning`) | File cleaning (`FC`) |
| `DESC-` | `descricao` content rules | various |
| `COMP-` | `composicao` hierarchy rules | `IR`, `TH`, `UT`, `CHILD_LVL`, `LEAF_NO_DATA` |
| `VAL-` | `valores` rules | `FS`, `IR`, `VAL_COMB`, `UNAV_INV` |
| `TEMP-` | `referencia_temporal` rules | `MAND_PUNC_TEMP`, `YEARS_TEMP`, `UVR_TEMP` |
| `SCEN-` | `cenarios` rules | `FS`, `MAND_PUNC_SCEN`, `UVR_SCEN` |
| `LEG-` | `legenda` rules and legend relations | `FC`, `LEG_REL`, `LEG_RANGE` |
| `PROP-` | `proporcionalidades` rules | `FS`, `IR`, `REP_IND_PROP`, `IND_VAL_PROP`, `IR_PROP`, `SUM_PROP` |
| `SPELL-` | Spell-check | `SPELL` |
| `TERR-` | Territory registry `spd_data.json` ↔ `valores`/`proporcionalidades` ids | dedicated new category `TERR` (`verification_name_territory_registry`), errors only, skipped when the file is absent (planned — PROTO-013, sequenced after backlog 01–07) |

Target message keys follow `rule.<RULE-ID>.<error|warning>` (see `.specs/i18n/catalog.md`).

Planned IDs reserved by the v1.16 alignment and the gap list (not yet implemented): STRUCT-013
(UTF-8, G-01), STRUCT-014 (single-worksheet xlsx, PROTO-003), DESC-013 (categoria, PROTO-004),
DESC-014 (codes ordered by level), DESC-015 (cenario domain/propagation), DESC-017 (ordem
sequence), DESC-018 (meta format — parked), DESC-019 (nome_completo length), DESC-016 (retired
unimplemented — `relacao` removed by protocol v1.15), SCEN-005 (symbol charset/length), TEMP-004,
TEMP-005, LEG-016 (>11 slices), VAL-006 (id uniqueness), TERR-001, TERR-002.

## Severity

Severity is what the code emits today: **error** = must be fixed before publication; **warning** =
may be left but must be justified (protocol preamble, p.1). The report shows both lists per
verification title, truncated to 20 messages each (`ApplicationConfig.REPORT_LIMIT_N_MESSAGES`).

## Row numbering in messages

Messages cite spreadsheet rows as the user sees them in Excel: DataFrame index + 2 for single-header
sheets, index + 3 for the double-header `proporcionalidades` (see
`.claude/rules/dataframe-conventions.md`).

## Map `NamesEnum` → verification title key → rule IDs

`data_validate/config/names_enum.py` (34 members). Titles are resolved through the i18n catalog
(`static/locales/<locale>/messages.json`), and every title is pre-registered in the report by
`SpreadsheetProcessor._prepare_statement`, so unused members still appear as empty sections.

| `NamesEnum` | Key (`verification_name_*`) | Rules |
|---|---|---|
| `FS` | `file_structure` | STRUCT-001…012, DESC-011, DESC-012, VAL-001, SCEN-001, SCEN-002, PROP-001, PROP-002 |
| `FC` | `file_cleaning` | CLEAN-001…006, LEG-001…011 |
| `IR` | `indicator_relations` | COMP-001, COMP-002, COMP-003, VAL-002, PROP-003 |
| `TH` | `tree_hierarchy` | COMP-007, COMP-008 |
| `IL` | `indicator_levels` | DESC-005 |
| `CO_UN` | `code_uniqueness` | DESC-003 |
| `HTML_DESC` | `html_codes_in_descriptions` | DESC-001 |
| `SPELL` | `spelling` | SPELL-001…005 |
| `UT` | `unique_titles` | COMP-004 |
| `SC` | `sequential_codes` | DESC-002 |
| `EF` | `empty_fields` | DESC-007 |
| `INP` | `indicator_name_pattern` | DESC-004 |
| `TITLES_N` | `titles_over_n_chars` (value=40) | DESC-010 |
| `SIMP_DESC_N` | `simple_descriptions_over_n_chars` (value=150) | DESC-009 |
| `MAND_PUNC_DESC` | `mandatory_and_prohibited_punctuation_in_descriptions` | DESC-006 |
| `MAND_PUNC_SCEN` | `mandatory_and_prohibited_punctuation_in_scenarios` | SCEN-003 |
| `MAND_PUNC_TEMP` | `mandatory_and_prohibited_punctuation_in_temporal_reference` | TEMP-001 |
| `UVR_SCEN` | `unique_value_relations_in_scenarios` | SCEN-004 |
| `UVR_TEMP` | `unique_value_relations_in_temporal_reference` | TEMP-003 |
| `VAL_COMB` | `value_combination_relations` | VAL-003 |
| `UNAV_INV` | `unavailable_and_invalid_values` | VAL-004, VAL-005 |
| `LB_DESC` | `line_break_in_description` | DESC-008 |
| `LB_SCEN` | `line_break_in_scenarios` | **none — registered, never emitted** (gap G-08) |
| `LB_TEMP` | `line_break_in_temporal_reference` | **none — registered, never emitted** (gap G-08) |
| `YEARS_TEMP` | `years_in_temporal_reference` | TEMP-002 |
| `LEG_RANGE` | `legend_data_range` | LEG-015 |
| `LEG_OVER` | `legend_value_overlap` | **none — registered, never emitted** (gap G-08; overlap is covered by LEG-010 continuity under `FC`) |
| `LEG_REL` | `legend_relations` | LEG-012, LEG-013, LEG-014 |
| `SUM_PROP` | `sum_properties_in_influencing_factors` | PROP-007, PROP-008, PROP-009, PROP-010 |
| `REP_IND_PROP` | `repeated_indicators_in_proportionalities` | PROP-004 |
| `IR_PROP` | `indicator_relations_in_proportionalities` | PROP-006 |
| `IND_VAL_PROP` | `indicators_in_values_and_proportionalities` | PROP-005 |
| `LEAF_NO_DATA` | `leaf_indicators_without_associated_data` | COMP-005, COMP-006 |
| `CHILD_LVL` | `child_indicator_levels` | COMP-009 |

## Skipped verifications

`--no-spellchecker` and `--no-warning-titles-length` list `SPELL` / `TITLES_N` as "not executed"
in the report. Validators also silently skip rules when a sheet is empty or a prerequisite column is
missing (`BaseValidator.set_not_executed` is a no-op — backlog ARC-008); the target design records
*skipped-with-reason* per rule (ADR-0006).

## Test coverage summary

No rule has a dedicated unit test today (backlog TST-001). Helper functions used by rules are
covered under `tests/unit/helpers/**`; those are cited per rule as "helper covered by …".

Last synced with code: 09279f4
