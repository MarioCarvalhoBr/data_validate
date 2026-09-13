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
| `DESC-` | `descricao` content rules | various, incl. `CATEG_DESC` |
| `COMP-` | `composicao` hierarchy rules | `IR`, `TH`, `UT`, `CHILD_LVL`, `LEAF_NO_DATA` |
| `VAL-` | `valores` rules | `FS`, `IR`, `VAL_COMB`, `UNAV_INV`, `UNIQ_VAL` |
| `TEMP-` | `referencia_temporal` rules | `MAND_PUNC_TEMP`, `YEARS_TEMP`, `UVR_TEMP` |
| `SCEN-` | `cenarios` rules | `FS`, `MAND_PUNC_SCEN`, `UVR_SCEN`, `SYMB_SCEN` |
| `LEG-` | `legenda` rules and legend relations | `FC`, `LEG_REL`, `LEG_RANGE` |
| `PROP-` | `proporcionalidades` rules | `FS`, `IR`, `REP_IND_PROP`, `IND_VAL_PROP`, `IR_PROP`, `SUM_PROP` |
| `SPELL-` | Spell-check | `SPELL` |
| `TERR-` | Territory registry `spd_data.json` ↔ `valores`/`proporcionalidades` ids | dedicated `TERR` category (`verification_name_territory_registry`), errors only, skipped when the file is absent — **implemented, PROTO-013/PROTO-018, Phase 6 round N3** |

Target message keys follow `rule.<RULE-ID>.<error|warning>` (see `.specs/i18n/catalog.md`).

Planned IDs reserved by the v1.16 alignment and the gap list (not yet implemented): DESC-018
(meta format — parked, no owner decision), DESC-016 (retired unimplemented — `relacao` removed by
protocol v1.15).

`DESC-013` (categoria domain, PROTO-004 step 1), `DESC-014` (codes ordered by level, PROTO-008),
`DESC-015` (cenario domain/propagation, PROTO-009), `DESC-017` (ordem sequence, PROTO-010), and
`DESC-019` (nome_completo length, PROTO-010) are all implemented — see the `CATEG_DESC`/`IL`/
`TH`/`CHILD_LVL`/`INP` rows below. Phase 6 round N2 implements **STRUCT-013** (proactive UTF-8
check, PROTO-007), **STRUCT-014** (single-worksheet xlsx, PROTO-003), **SCEN-005** (symbol
charset, PROTO-006, new category `SYMB_SCEN`), **LEG-008** tightened to six-hex-only and
**LEG-016** (>11 slices warning, both PROTO-011), **LEG-014** narrowed to a permanent no-op
(PROTO-012 — an empty `legenda` cell is the protocol's default-legend case, not an error;
non-empty dangling references remain `LEG-012`'s concern), **TEMP-004**/**TEMP-005** (four-digit
symbol / single observed reference, PROTO-014, both under `YEARS_TEMP`), and **VAL-006** (`id`
uniqueness, PROTO-017, new category `UNIQ_VAL`). Phase 6 round N3 implements **TERR-001**/
**TERR-002** (optional `spd_data.json` territory registry, PROTO-013, new category `TERR`,
sequenced last in the pipeline) and the JSON summary's **`spatial_data_validated`** flag
(PROTO-018) — see `territories.md`.

## Severity

Severity is what the code emits today: **error** = must be fixed before publication; **warning** =
may be left but must be justified (protocol preamble, p.1). The report shows both lists per
verification title, truncated to 20 messages each (`ApplicationConfig.REPORT_LIMIT_N_MESSAGES`).

## Row numbering in messages

Messages cite spreadsheet rows as the user sees them in Excel: DataFrame index + 2 for single-header
sheets, index + 3 for the double-header `proporcionalidades` (see
`.claude/rules/dataframe-conventions.md`).

## Map `NamesEnum` → verification title key → rule IDs

`data_validate/config/names_enum.py` (38 members: PROTO-004 added `CATEG_DESC`; Phase 6 round N2
added `SYMB_SCEN` (PROTO-006/SCEN-005) and `UNIQ_VAL` (PROTO-017/VAL-006); Phase 6 round N3 added
`TERR` (PROTO-013/TERR-001/TERR-002)). Titles are resolved through the i18n catalog
(`static/locales/<locale>/messages.json`), and every title is pre-registered in the report by
`SpreadsheetProcessor._prepare_statement`, so unused members still appear as empty sections.

| `NamesEnum` | Key (`verification_name_*`) | Rules |
|---|---|---|
| `FS` | `file_structure` | STRUCT-001…015 (STRUCT-013/014 loader-level, not `RuleSpec`-registered), DESC-011, DESC-012, VAL-001, SCEN-001, SCEN-002, PROP-001, PROP-002 |
| `FC` | `file_cleaning` | CLEAN-001…006, LEG-001…011, LEG-016 |
| `IR` | `indicator_relations` | COMP-001, COMP-002, COMP-003, VAL-002, PROP-003 |
| `TH` | `tree_hierarchy` | COMP-007, COMP-008, DESC-015 |
| `IL` | `indicator_levels` | DESC-005, DESC-014 |
| `CO_UN` | `code_uniqueness` | DESC-003 |
| `HTML_DESC` | `html_codes_in_descriptions` | DESC-001 |
| `SPELL` | `spelling` | SPELL-001…005 |
| `UT` | `unique_titles` | COMP-004 |
| `SC` | `sequential_codes` | DESC-002 |
| `EF` | `empty_fields` | DESC-007 |
| `INP` | `indicator_name_pattern` | DESC-004, DESC-019 |
| `TITLES_N` | `titles_over_n_chars` (value=40) | DESC-010 |
| `SIMP_DESC_N` | `simple_descriptions_over_n_chars` (value=150) | DESC-009 |
| `MAND_PUNC_DESC` | `mandatory_and_prohibited_punctuation_in_descriptions` | DESC-006 |
| `MAND_PUNC_SCEN` | `mandatory_and_prohibited_punctuation_in_scenarios` | SCEN-003 |
| `MAND_PUNC_TEMP` | `mandatory_and_prohibited_punctuation_in_temporal_reference` | TEMP-001 |
| `UVR_SCEN` | `unique_value_relations_in_scenarios` | SCEN-004 |
| `UVR_TEMP` | `unique_value_relations_in_temporal_reference` | TEMP-003 |
| `VAL_COMB` | `value_combination_relations` | VAL-003 |
| `UNAV_INV` | `unavailable_and_invalid_values` | VAL-004, VAL-005 |
| `UNIQ_VAL` | `value_id_uniqueness` | VAL-006 |
| `SYMB_SCEN` | `scenario_symbol_charset` | SCEN-005 |
| `LB_DESC` | `line_break_in_description` | DESC-008 |
| `LB_SCEN` | `line_break_in_scenarios` | **none — registered, never emitted** (gap G-08) |
| `LB_TEMP` | `line_break_in_temporal_reference` | **none — registered, never emitted** (gap G-08) |
| `YEARS_TEMP` | `years_in_temporal_reference` | TEMP-002, TEMP-004, TEMP-005 |
| `LEG_RANGE` | `legend_data_range` | LEG-015 |
| `LEG_OVER` | `legend_value_overlap` | **none — registered, never emitted** (gap G-08; overlap is covered by LEG-010 continuity under `FC`) |
| `LEG_REL` | `legend_relations` | LEG-012, LEG-013, LEG-014 (retired-by-v1.16 no-op, PROTO-012) |
| `SUM_PROP` | `sum_properties_in_influencing_factors` | PROP-007, PROP-008, PROP-009, PROP-010 |
| `REP_IND_PROP` | `repeated_indicators_in_proportionalities` | PROP-004 |
| `IR_PROP` | `indicator_relations_in_proportionalities` | PROP-006 |
| `IND_VAL_PROP` | `indicators_in_values_and_proportionalities` | PROP-005 |
| `LEAF_NO_DATA` | `leaf_indicators_without_associated_data` | COMP-005, COMP-006 |
| `CHILD_LVL` | `child_indicator_levels` | COMP-009, DESC-017 |
| `CATEG_DESC` | `indicator_category` | DESC-013 |
| `TERR` | `territory_registry` | TERR-001, TERR-002 |

## Skipped verifications

`--no-spellchecker` and `--no-warning-titles-length` list `SPELL` / `TITLES_N` as "not executed"
in the report. `data_validate/validators/` (and its `BaseValidator.set_not_executed` no-op) is
deleted entirely (ARC-008, ARC-017 Phase 3 Port 8): every rule now runs through
`rules/engine.py::Engine`, whose `RuleSpec.requires`/`depends_on` (checked once per rule by
`Engine._unmet_prerequisite`) record *skipped-with-reason* (`RuleOutcome.status is SKIPPED`,
`SkipReason`) exactly as ADR-0006 targeted — closing the gap the old placeholder left open.
PROTO-013 is the first consumer of the engine's third prerequisite kind,
`RuleSpec.requires_options` (`SkipReason.DISABLED_BY_OPTION`, `engine.skipped.disabled_by_option`
— sketched but unimplemented in `.specs/architecture/error-model.md` until now): an absent or
malformed `spd_data.json` engine-skips TERR-001/TERR-002 this way, and
`SpreadsheetProcessor._finalize_territory_registry_status` additionally lists the `TERR` title in
`GeneralContext.skipped_validations` (the same list `FileReportGenerator._collect_skipped_tests`
already reads for `--no-spellchecker`/`--no-warning-titles-length`) so it shows in the report's
"not executed" list too.

## Test coverage summary

Every rule ID in this map is now ported onto the `rules` engine (ARC-017 Phase 3, Ports 2–8) with
a dedicated, table-driven unit test module: `tests/unit/rules/test_structure.py` (STRUCT-001…006,
Phase 3b), `test_description.py` (DESC-001…010 Port 2, plus DESC-013/014/015/017/019 from the v1.16
alignment — PROTO-004/008/009/010), `test_composition.py` (COMP-001…009, Port
3), `test_temporal_reference.py`/`test_scenario.py` (TEMP-001…003/SCEN-003…004, Port 4),
`test_value.py` (VAL-002…005, Port 5), `test_legend.py` (LEG-012…015, Port 6),
`test_proportionality.py` (PROP-003…010, Port 7), `test_spell.py` (SPELL-001…005, Port 8, the
last validator ported — `data_validate/validators/` no longer exists), and `test_territories.py`
(TERR-001…002, Phase 6 round N3 — the first rule module with no legacy validator to port). This
closes backlog TST-001 (`.specs/quality/backlog/04-testing.md`) for models/validators/controllers;
helper functions used by rules are covered under `tests/unit/helpers/**`, cited per rule as "helper
covered by …".

Last synced with code: Phase 6 round N3 (PROTO-013/PROTO-018 — territory registry,
`spatial_data_validated`)
