# Module map (current → destination)

Paths are relative to `data_validate/`. Tests are relative to `tests/unit/`. "none" means no
test module exists today (covered by TST-001). Destination refers to `target-architecture.md`.

## `config/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `application_config.py` | Constants, fallback HTML template, localised verification titles; optional injected `LanguageManager` | `ApplicationConfig`, `get_verify_names` | `tests/unit/config/test_application_config.py` | `app/options.py`, `specs/limits.py` | PERF-004 |
| `names_enum.py` | 34 verification keys | `NamesEnum` | none (100 % incidental) | `rules/categories.py` | — |
| `spreadsheet_info.py` | Sheet stems, extensions, required/optional | `SpreadsheetInfo`, `SHEET` | none | `specs/sheet_specs.py` (implemented, consumers pending) | ARC-003 |
| `metadata_info.py` | Version string, welcome banner | `MetadataInfo`, `METADATA` | `helpers/base/test_metadata_info.py` | `util/version.py` | BUG-017, TOOL-005 |

## `controllers/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `spreadsheet_processor.py` | Orchestrates load → models → rule registries → report | `SpreadsheetProcessor` | `tests/unit/controllers/test_spreadsheet_processor.py` | `app/pipeline.py` | ARC-017 (ARC-001 done: construction only stores dependencies, `run()` called explicitly by `main.py`) |
| `context/general_context.py` | DI container: args, i18n, config, fs, logger; builds one `LanguageManager` from `data_args.data_file.locale` and injects it into `config`/`file_system_utils`; opens a log file only in debug mode | `GeneralContext` | `tests/unit/controllers/context/test_general_context.py` | `app/context.py` | ARC-006 |
| `context/data_model_context.py` | Model registry for validators | `DataModelContext.get_instance_of` | none | `rules/context.py` | ARC-006 |
| `report/validation_report.py` | Buckets of error/warning strings, truncation | `ReportItem`, `ValidationReport` | `tests/unit/controllers/report/test_validation_report.py` | `app/result.py`, `reporting/model.py` | none |
| `report/file_report_generator.py` | HTML/PDF/JSON output | `FileReportGenerator` | `tests/unit/controllers/report/test_file_report_generator.py` | `reporting/{html,pdf,json,console}.py` | SEC-001, SEC-002 |

## `middleware/`

Deleted (BUG-004): `bootstrap.py` (`Bootstrap`) and the whole `middleware` package no longer exist.
Locale is now an explicit `LanguageManager(locale=...)` constructor argument built once by
`GeneralContext` — no persistence step, no `.config/store.locale`.

## `main.py`

| Module | Responsibility | Tests | Destination | Backlog |
|---|---|---|---|---|
| `main.py` | Entry point; wires `DataArgs → GeneralContext → SpreadsheetProcessor → finalize`, no `Bootstrap` step; prints banner at import | none (0 %) | `cli.py` | ARC-011, ARC-012, SEC-008 |

## `helpers/base/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `constant_base.py` | Immutable-after-init attribute holder | `ConstantBase` | `test_constant_base.py` | frozen dataclasses | — |
| `data_args.py` | argparse + validation (no longer builds its own unused `LanguageManager`) | `DataArgs`, `DataFile`, `DataAction`, `DataReport` | `test_data_args.py` | `cli.py`, `app/options.py` | ARC-011, BUG-009 |
| `file_system_utils.py` | Encoding detection, exists/remove/create with localised tuples; optional injected `LanguageManager` | `FileSystemUtils` | `test_file_system_utils.py` | `util/paths.py` | ARC-014 |
| `logger_manager.py` | Console + file loggers with colour formatter; `log_folder=None` skips directory creation and the file handler entirely | `LoggerManager`, `CustomFormatter` | `test_logger_manager.py` | `util/logging.py` | — |

## `helpers/common/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `formatting/message_formatting_processing.py` | Missing/extra column messages | `MessageFormattingProcessing` | `formatting/test_message_formatting_processing.py` | catalog | ARC-005 |
| `formatting/number_formatting_processing.py` | Decimal truncation, decimal-place checks, Brazilian formatting, integer checks | `NumberFormattingProcessing` | `formatting/test_number_formatting.py` | `util/numbers.py` | — |
| `formatting/text_formatting_processing.py` | Acronym-aware capitalisation | `TextFormattingProcessing` | `formatting/test_text_formatting.py` | `rules/description/_text.py` | — |
| `generation/combinations_processing.py` | `CODE-YEAR[-SCENARIO]` expected combinations | `CombinationsProcessing` | `generation/test_combinations.py` | `rules/values/_combinations.py` | — |
| `processing/collections_processing.py` | Grouping, ID pattern categorisation, set diffs with messages | `CollectionsProcessing` | `processing/test_collections_processing.py` | `specs/patterns.py`, `util/collections.py` | — |
| `processing/data_cleaning_processing.py` | Integer column cleaning (row filtering) | `DataCleaningProcessing` | `processing/test_data_cleaning.py` | `normalizing/normalizer.py` | PERF-003 |
| `validation/dataframe_processing.py` | `\|` check, unnamed columns, column names, unique titles/values, text length | `DataFrameProcessing` | `validation/test_column_validation.py`, `test_dataframe_character_processing.py` | `rules/structure/`, `normalizing/` | PERF-002 |
| `validation/character_processing.py` | Punctuation, CR/LF checks | `CharacterProcessing` | `validation/test_dataframe_character_processing.py` | `rules/_shared/text_checks.py` | PERF-001 |
| `validation/description_processing.py` | Valid codes excluding level 1 / level 2 scenario 0 | `DescriptionProcessing` | none | `rules/description/_codes.py` | BUG-014 |
| `validation/graph_processing.py` | networkx graph, cycles, components, BFS, leaves; `create_graph_structure` vectorised via `nx.from_pandas_edgelist` (ARC-017 Phase 3 Port 3) | `GraphProcessing` | `validation/test_graph_processing.py` | consumed by `rules/composition.py` | PERF-001 (done) |
| `validation/tree_processing.py` | Adjacency dict (`create_tree_structure`, vectorised via `groupby`), DFS cycles; `validate_level_hierarchy`/`validate_missing_codes_in_description` deleted (inlined/vectorised in `rules/composition.py`, ARC-017 Phase 3 Port 3) | `TreeProcessing` | `validation/test_tree_processing.py` | consumed by `rules/composition.py` | PERF-001 (done) |
| `validation/legend_processing.py` | Legend group checks (LEG-001…011, model-level, out of ARC-017 Phase 3 Port 6's scope) | `LegendProcessing` | `validation/test_legend_processing.py` | consumed by `models/sp_legend.py` | PERF-001 |
| `validation/proportionality_processing.py` | Sub-datasets, invalid-cell/excessive-decimal masks, decimal sums, zero-sum/tolerance row indices — message-free since ARC-017 Phase 3 Port 7 | `ProportionalityProcessing` | `validation/test_proportionality_processing.py` (98.68 % coverage) | consumed by `rules/proportionality.py` | SEC-004 (its `except (…, Exception): pass` site is gone, narrowed to `except (ValueError, TypeError)`) |
| ~~`validation/value_processing.py`~~ | ~~Numeric/DI/decimal checks per column~~ | ~~`ValueProcessing`~~ | ~~`validation/test_value_processing.py`~~ | **deleted (ARC-017 Phase 3 Port 5) — reproduced as vectorised `pd.to_numeric` masks in `rules/value.py`, never reused (message-building helper)** | PERF-001 (done) |

## `helpers/tools/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `data_loader/api/facade.py` | Load all sheets | `DataLoaderFacade` (`.load()` → `LoadResult`, deprecated `.load_all` shim), `LoadedSheet` (renamed from `DataLoaderModel` in Phase 5, ARC-009/ARC-013; `DataLoaderModel` kept one release as a plain class alias), `LoadResult` | `tools/data_loader/api/test_facade.py` | `loading/loader.py` | ARC-009 (done) |
| `data_loader/engine/scanner.py` | Folder scan, spec-driven | `FileScanner` (reads `SHEET_SPECS`/`ALLOWED_EXTENSIONS`) | `tools/data_loader/engine/test_scanner.py` | `loading/scan.py` | — (BUG-015 done) |
| `data_loader/engine/factory.py` | Reader by extension | `ReaderFactory` (`.csv`/`.xlsx` only, explicit `sep`) | `tools/data_loader/engine/test_factory.py` | `loading/readers/__init__.py` | — |
| `data_loader/readers/base_reader.py` | Template method | `BaseReader` | `tools/data_loader/readers/test_base_reader.py` | `loading/readers/base.py` | — |
| `data_loader/readers/csv_reader.py` | CSV with explicit `sep`, MultiIndex fill | `CSVReader` (`sep` constructor param) | `readers/test_csv_reader.py` | `loading/readers/csv.py` | — (BUG-018 done) |
| `data_loader/readers/excel_reader.py` | XLSX via calamine | `ExcelReader` | `readers/test_excel_reader.py` | `loading/readers/xlsx.py` | SEC-003 |
| `data_loader/strategies/header.py` | Header rows | `SingleHeaderStrategy`, `DoubleHeaderStrategy` | `strategies/test_header.py` | `SheetSpec.header` | — |
| `data_loader/common/exceptions.py` | `ReaderNotFoundError` | — | none | `loading/errors.py` | — |
| `locale/language_manager.py` | Explicit-`locale` constructor (no file I/O), catalog loading, `text()` | `LanguageManager` | `tools/locale/test_language_manager.py` | `i18n/catalog.py` | — (BUG-004 done) |
| `locale/language_enum.py` | Supported languages | `LanguageEnum` | `tools/locale/test_language_enum.py` | `i18n/locale.py` | BUG-012 |
| ~~`readme/generate_readme.py`~~ | ~~README from template~~ | — | none | **deleted (ADR-0009, ARC-010 — physically removed in Phase 5, along with `readme/__init__.py`)** | ARC-010 (done) |
| `spellchecker/spellchecker.py` | Facade | `SpellChecker` | `spellchecker/test_spellchecker.py` | `spell/service.py` | ARC-015 |
| `spellchecker/spellchecker_controller.py` | Word checks, quality warnings | `SpellCheckerController` | `spellchecker/test_spellchecker_controller.py` | `rules/spelling/` | PERF-006 |
| `spellchecker/dictionary_manager.py` | enchant broker, personal words, temp cleanup | `DictionaryManager` | `spellchecker/test_dictionary_manager.py` | `spell/enchant_backend.py` | BUG-022 |
| `spellchecker/text_processor.py` | Sanitising text | `TextProcessor` | `spellchecker/test_text_processor.py` | `spell/text.py` | — |
| `spellchecker/dataframe_processor.py` | Column iteration | `DataFrameProcessor` | `spellchecker/test_dataframe_processor.py` | `rules/spelling/` | PERF-006 |
| ~~`spellchecker/main.py`~~ | ~~Demo~~ | — | none | **deleted (ARC-010 — physically removed in Phase 5, along with its `test_main.py`)** | ARC-010 (done) |

## `models/`

| Module | Sheet | Tests | Destination | Backlog |
|---|---|---|---|---|
| `sp_model_abc.py` | base | `tests/unit/models/test_model_isolation.py` | `specs/` (implemented, consumers pending) + `normalizing/` | ARC-001, ARC-007 |
| `sp_description.py` | `descricao` | `test_column_declarations.py`, `test_model_isolation.py` | `specs/sheet_specs.py::SHEET_SPECS["descricao"]` (implemented, consumers pending), `normalizing/` | ARC-007 |
| `sp_composition.py` | `composicao` | `test_model_isolation.py` | idem | ARC-007 |
| `sp_value.py` | `valores` | none | idem | BUG-013 |
| `sp_temporal_reference.py` | `referencia_temporal` | `test_column_declarations.py`, `test_model_isolation.py` | idem | ARC-007 |
| `sp_proportionality.py` | `proporcionalidades` | `test_model_isolation.py` | idem | ARC-009 (done — `header_type` mutation resolved, `LoadedSheet` naming resolved) |
| `sp_scenario.py` | `cenarios` | none | idem | — |
| `sp_legend.py` | `legenda` | none | idem + `rules/legend.py` (LEG-012…015) | — |
| `sp_dictionary.py` | `dicionario` | none | `spell/` | — |

## `validators/` — package deleted (ARC-008, ARC-017 Phase 3 Port 8)

Every module below is deleted; `data_validate/validators/` no longer exists as a package. Kept
as a historical map from the last validator that lived at each path to the `rules/` module that
replaced it.

| Former module | Destination | Backlog |
|---|---|---|
| ~~`spreadsheets/base/base_validator.py`~~ | **deleted (ARC-008, ARC-017 Phase 3 Port 8) — `rules/engine.py`/`rules/registry.py`** | ARC-008 (done: `RuleSpec.requires`/`depends_on` + `Engine._unmet_prerequisite` replace `set_not_executed`/triplicated `column_exists*`) |
| ~~`structure/file_structure_validator.py`~~ | **deleted (ARC-017 Phase 3b) — `rules/structure.py`** | BUG-026 (its "no duplicate errors/warnings instance state" concern no longer applies: each check is a pure function, no instance to duplicate state on) |
| ~~`spell/spellchecker_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 8, the last validator ported) — `rules/spell.py`** | BUG-023, BUG-027 (preserved, not reopened) |
| ~~`spreadsheets/description/description_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 2) — `rules/description.py`** | PERF-001 (its two `iterrows()` sites are gone, see `05-performance.md`) |
| ~~`spreadsheets/composition/compostion_graph_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 3) — `rules/composition.py`** | BUG-019 (done), BUG-024 (the `compostion_` filename typo is gone) |
| ~~`spreadsheets/composition/composition_tree_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 3) — `rules/composition.py`** | PERF-001 (its `iterrows()` sites are gone/vectorised, see `05-performance.md`) |
| ~~`spreadsheets/temporal_reference/temporal_reference_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 4) — `rules/temporal_reference.py`** | BUG-007 (preserved, not reopened) |
| ~~`spreadsheets/proportionality/proportionality_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 7) — `rules/proportionality.py`** | BUG-006 (preserved, not reopened), BUG-014 (preserved, not reopened), PERF-001 (its `iterrows()` composition-dict-building site is gone, see `05-performance.md`) |
| ~~`spreadsheets/value/value_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 5) — `rules/value.py`** | BUG-001 (preserved as a rule test, `tests/unit/rules/test_value.py::TestIdempotency` — the validator path itself is gone) |
| ~~`spreadsheets/scenario/scenario_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 4) — `rules/scenario.py`** | — |
| ~~`spreadsheets/legend/legend_validator.py`~~ | **deleted (ARC-017 Phase 3 Port 6) — `rules/legend.py`** | BUG-014 (preserved, not reopened), PERF-001 (its cell-by-cell loop is gone, see `05-performance.md`) |

## `static/`

| Path | Responsibility | Destination |
|---|---|---|
| `locales/{pt_BR,en_US}/messages.json` | Message catalogs | `i18n/locales/` |
| `report/report_template.html`, `microstrap_style.css` | Report template/CSS | kept |
| `dictionaries/hunspell/*.{aff,dic}`, `extra-words.dic` | Spell dictionaries | kept |
| ~~`templates/README.TEMPLATE.md`~~ | ~~README generator template~~ | **deleted (ADR-0009, ARC-010 — physically removed in Phase 5; the now-empty `static/templates/` directory is gone too)** |

## `specs/` and `i18n/` (target modules implemented ahead of their consumers)

These already live at their target-architecture path (`specs/`, `i18n/`) rather than a legacy
path with a "Destination" column, so they get their own table: what exists, and what still reads
from the legacy source instead.

| Module | Responsibility | Key symbols | Tests | Backlog |
|---|---|---|---|---|
| `specs/sheet_specs.py` | Single source of truth for sheet/column shape | `SHEET_SPECS`, `SheetSpec`, `ColumnSpec` | `specs/test_sheet_specs.py` | ARC-003 (implemented, consumers pending) |
| `specs/issues.py` | Structured validation finding + result grouping/truncation | `Issue`, `Severity`, `ValidationResult` | `specs/test_issues.py` (100 % coverage) | ARC-004 (model implemented, not wired into any validator/model/`ValidationReport` yet — Phase 3) |
| `i18n/catalog.py` | Locale-scoped message lookup and `Issue` rendering | `MessageCatalog`, `default_catalog_dir`, `CatalogNotFoundError`, `CatalogInvalidError` | `i18n/test_message_catalog.py` (100 % coverage) | ARC-004 (implemented; `helpers/tools/locale/language_manager.py::LanguageManager` remains the module every current call site actually uses) |

## `rules/` (new package, Phase 3a engine core + Phase 3b/3 Port 2–8 — every legacy validator ported, ARC-017, ARC-001, ARC-008)

Brand new at its target-architecture path (no legacy predecessor to map the registry/engine core
from): ADR-0006's engine, plus (Phase 3b/Phase 3 Port 2–8) all eight ported validators —
`structure.py`, `description.py`, `composition.py`, `temporal_reference.py`, `scenario.py`,
`value.py`, `legend.py`, `proportionality.py`, and `spell.py` (the last one, Port 8) — and the
reusable legacy-report adapter, `legacy_adapter.py`. Every one of these eight deviates from the
target architecture's aspirational "one `Rule` per module under `rules/<sheet>/<RULE-ID>.py`"
(ADR-0006) by declaring every rule for their sheet in one flat module — the sheet-level
`rules/<sheet>/` subpackage split is deferred to a later phase (no port needed it). With `spell.py`
landed, `data_validate/validators/` is deleted entirely (ARC-008) and every model's `run()` /
`SpreadsheetProcessor.run()` is called explicitly by its caller instead of automatically from
`__init__` (ARC-001).

| Module | Responsibility | Key symbols | Tests | Backlog |
|---|---|---|---|---|
| `context.py` | Immutable, per-run view of a bundle handed to every `Rule.check` | `RuleContext` (`has_sheet`, `sheet`) | `rules/test_context.py` (100 % coverage) | ARC-017 |
| `registry.py` | Declares one rule (prerequisites + check function); resolves execution order | `RuleSpec`, `RuleRegistry` (`register`, `get`, `topological_order`, `@rule(...)` decorator), `RegistryCycleError` | `rules/test_registry.py` (100 % coverage) | ARC-017, ARC-008 |
| `engine.py` | Runs a registry over a context: skipped-with-reason, crash isolation, issue flattening | `Engine`, `RuleOutcome`, `RuleStatus`, `SkipReason`, `EngineResult` | `rules/test_engine.py` (100 % coverage) | ARC-017, ARC-001, ARC-008 |
| `structure.py` | STRUCT-001…006: input-folder structural checks, ported from `FileStructureValidator` | `STRUCTURE_REGISTRY`, `check_input_directory_not_empty`, `check_files_not_zipped_inside_a_folder`, `check_no_unexpected_folders`, `check_no_unexpected_files`, `check_required_files_present`, `check_no_csv_xlsx_conflict` | `rules/test_structure.py` (100 % coverage) | ARC-017, ARC-001, ARC-005, TST-001 |
| `description.py` | DESC-001…010: `descricao` content checks, ported from `SpDescriptionValidator` | `DESCRIPTION_REGISTRY`, `check_html_in_simple_description`, `check_sequential_codes`, `check_unique_codes`, `check_name_capitalization`, `check_indicator_levels`, `check_punctuation`, `check_empty_strings`, `check_no_cr_lf_characters`, `check_simple_description_length`, `check_title_length` | `rules/test_description.py` (95.24 % coverage) | ARC-017, ARC-001, ARC-005, PERF-001, TST-001 |
| `composition.py` | COMP-001…009: `composicao` hierarchy checks, ported from `SpCompositionGraphValidator`/`SpCompositionTreeValidator` | `COMPOSITION_REGISTRY`, `CompositionFacts`, `compute_composition_facts`, `check_relation_indicators_in_composition`, `check_composition_graph_acyclic`, `check_composition_no_disconnected_groups`, `check_unique_titles_per_subtree`, `check_leaf_indicators_have_values`, `check_leaf_indicators_have_proportionality`, `check_composition_tree_acyclic`, `check_parent_level_below_child_level`, `check_children_share_parent_level` | `rules/test_composition.py` (96.72 % coverage) | ARC-017, ARC-001, ARC-005, ARC-008, BUG-019, BUG-024, PERF-001, TST-001 |
| `temporal_reference.py` | TEMP-001…003: `referencia_temporal` content checks, ported from `SpTemporalReferenceValidator` | `TEMPORAL_REGISTRY`, `check_description_ends_with_period`, `check_reference_years_are_future`, `check_name_and_symbol_are_unique` | `rules/test_temporal_reference.py` (98.41 % coverage) | ARC-017, ARC-001, ARC-005, BUG-007, TST-001 |
| `scenario.py` | SCEN-003…004: `cenarios` content checks, ported from `SpScenarioValidator` | `SCENARIO_REGISTRY`, `check_punctuation`, `check_name_and_symbol_are_unique` | `rules/test_scenario.py` (98.48 % coverage) | ARC-017, ARC-001, ARC-005, TST-001 |
| `value.py` | VAL-002…005: `valores` content checks, ported from `SpValueValidator`/`ValueProcessing` | `VALUE_REGISTRY`, `check_relation_indicators_in_values`, `check_value_combination_relation`, `check_unavailable_and_invalid_values`, `check_excessive_decimal_places` | `rules/test_value.py` (100 % coverage) | ARC-017, ARC-001, ARC-005, BUG-001, PERF-001, TST-001 |
| `legend.py` | LEG-012…015: `legenda` relation/range checks, ported from `SpLegendValidator`/`ModelMappingLegend` | `LEGEND_REGISTRY`, `check_relation_missing_and_unreferenced_codes`, `check_level_one_must_not_reference_legend`, `check_other_levels_must_reference_legend`, `check_value_range_within_legend` | `rules/test_legend.py` (98.93 % coverage) | ARC-017, ARC-001, ARC-005, BUG-014, PERF-001, TST-001 |
| `proportionality.py` | PROP-003…010: `proporcionalidades` content checks, ported from `SpProportionalityValidator` | `PROPORTIONALITY_REGISTRY`, `check_relation_indicators_in_proportionality`, `check_columns_repeated_indicators`, `check_relation_indicators_in_value_and_proportionality`, `check_parent_child_relationships`, `check_sum_properties_in_influencing_factors` | `rules/test_proportionality.py` (97.84 % coverage) | ARC-017, ARC-001, ARC-005, BUG-006, BUG-014, PERF-001, TST-001 |
| `spell.py` | SPELL-001…005: dictionary/backend errors + `descricao`/`referencia_temporal`/`cenarios` spell-check, ported from `SpellCheckerValidator` (the last validator port — `data_validate/validators/` is now deleted entirely) | `SPELL_REGISTRY`, `check_dictionary_backend`, `check_spelling_description`, `check_spelling_temporal_reference`, `check_spelling_scenario` | `rules/test_spell.py` (98.63 % coverage) | ARC-017, ARC-001, ARC-005 (in-progress: models' structural/cleaning messages and report labels are still hardcoded pt-BR), ARC-008, BUG-027, TST-001 |
| `legacy_adapter.py` | Renders `Engine.run(...)`'s outcomes into the legacy `ValidationReport`, reused by every later port | `extend_report_from_outcomes` | `rules/test_legacy_adapter.py` (100 % coverage) | ARC-017 |

Last synced with code: ARC-017 Phase 3 Port 8 (SPELL-001…005 ported to `rules/spell.py`; legacy
`SpellCheckerValidator` deleted; `data_validate/validators/` deleted entirely, closing ARC-008;
every model/`SpreadsheetProcessor` constructor stops running its pipeline automatically, closing
ARC-001 except for `DataArgs`'s argparse-in-`__init__`, an accepted CLI-boundary exception)
