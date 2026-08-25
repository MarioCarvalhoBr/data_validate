# Module map (current → destination)

Paths are relative to `data_validate/`. Tests are relative to `tests/unit/`. "none" means no
test module exists today (covered by TST-001). Destination refers to `target-architecture.md`.

## `config/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `application_config.py` | Constants, fallback HTML template, localised verification titles | `ApplicationConfig`, `get_verify_names` | none (83 % incidental) | `app/options.py`, `specs/limits.py` | BUG-011, PERF-004 |
| `names_enum.py` | 35 verification keys | `NamesEnum` | none (100 % incidental) | `rules/categories.py` | — |
| `spreadsheet_info.py` | Sheet stems, extensions, required/optional | `SpreadsheetInfo`, `SHEET` | none | `specs/sheets.py` | ARC-003 |
| `metadata_info.py` | Version string, welcome banner | `MetadataInfo`, `METADATA` | `helpers/base/test_metadata_info.py` | `util/version.py` | BUG-017, TOOL-005 |

## `controllers/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `spreadsheet_processor.py` | Orchestrates load → models → validators → report | `SpreadsheetProcessor` | none | `app/pipeline.py` | ARC-001, ARC-017 |
| `context/general_context.py` | DI container: args, i18n, config, fs, logger | `GeneralContext` | none | `app/context.py` | ARC-006, BUG-021 |
| `context/data_model_context.py` | Model registry for validators | `DataModelContext.get_instance_of` | none | `rules/context.py` | ARC-006 |
| `report/validation_report.py` | Buckets of error/warning strings, truncation | `TestReportItem`, `ValidationReport` | none | `app/result.py`, `reporting/model.py` | BUG-005, BUG-020 |
| `report/file_report_generator.py` | HTML/PDF/JSON output | `FileReportGenerator` | none | `reporting/{html,pdf,json,console}.py` | SEC-001, SEC-002, BUG-010 |

## `middleware/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `bootstrap.py` | Persist `--locale` to `.config/store.locale` | `Bootstrap` | none (0 %) | deleted | BUG-004, BUG-008 |

## `main.py`

| Module | Responsibility | Tests | Destination | Backlog |
|---|---|---|---|---|
| `main.py` | Entry point; prints banner at import | none (0 %) | `cli.py` | ARC-011, ARC-012, SEC-008 |

## `helpers/base/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `constant_base.py` | Immutable-after-init attribute holder | `ConstantBase` | `test_constant_base.py` | frozen dataclasses | — |
| `data_args.py` | argparse + validation | `DataArgs`, `DataFile`, `DataAction`, `DataReport` | `test_data_args.py` | `cli.py`, `app/options.py` | ARC-011, BUG-009 |
| `file_system_utils.py` | Encoding detection, exists/remove/create with localised tuples | `FileSystemUtils` | `test_file_system_utils.py` | `util/paths.py` | ARC-014 |
| `logger_manager.py` | Console + file loggers with colour formatter | `LoggerManager`, `CustomFormatter` | `test_logger_manager.py` | `util/logging.py` | BUG-021 |

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
| `validation/graph_processing.py` | networkx graph, cycles, components, BFS, leaves | `GraphProcessing` | `validation/test_graph_processing.py` | `rules/composition/_graph.py` | PERF-001 |
| `validation/tree_processing.py` | Adjacency dict, level hierarchy, DFS cycles | `TreeProcessing` | `validation/test_tree_processing.py` | `rules/composition/_graph.py` | PERF-001 |
| `validation/legend_processing.py` | Legend group checks | `LegendProcessing` | `validation/test_legend_processing.py` | `rules/legend/` | PERF-001 |
| `validation/proportionality_processing.py` | Sub-datasets, numeric format, decimals, sums, tolerance | `ProportionalityProcessing` | none | `rules/proportionality/` | SEC-004 |
| `validation/value_processing.py` | Numeric/DI/decimal checks per column | `ValueProcessing` | `validation/test_value_processing.py` | `rules/values/` | PERF-001 |

## `helpers/tools/`

| Module | Responsibility | Key symbols | Tests | Destination | Backlog |
|---|---|---|---|---|---|
| `data_loader/api/facade.py` | Load all sheets | `DataLoaderFacade`, `DataLoaderModel` | `tools/data_loader/api/test_facade.py` | `loading/loader.py` | ARC-009, BUG-015 |
| `data_loader/engine/scanner.py` | Folder scan | `FileScanner` | `tools/data_loader/engine/test_scanner.py` | `loading/scan.py` | BUG-015 |
| `data_loader/engine/factory.py` | Reader by extension | `ReaderFactory` | `tools/data_loader/engine/test_factory.py` | `loading/readers/__init__.py` | — |
| `data_loader/readers/base_reader.py` | Template method | `BaseReader` | `tools/data_loader/readers/test_base_reader.py` | `loading/readers/base.py` | — |
| `data_loader/readers/csv_reader.py` | CSV with `\|`, MultiIndex fill | `CSVReader` | `readers/test_csv_reader.py` | `loading/readers/csv.py` | BUG-018 |
| `data_loader/readers/excel_reader.py` | XLSX via calamine | `ExcelReader` | `readers/test_excel_reader.py` | `loading/readers/xlsx.py` | SEC-003 |
| `data_loader/readers/qml_reader.py` | Raw text | `QMLReader` | `readers/test_qml_reader.py` | deleted (open question) | BUG-015 |
| `data_loader/strategies/header.py` | Header rows | `SingleHeaderStrategy`, `DoubleHeaderStrategy` | `strategies/test_header.py` | `SheetSpec.header` | — |
| `data_loader/common/config.py` | Singleton file specs | `Config`, `SingletonMeta` | none | `specs/sheets.py` | ARC-003 |
| `data_loader/common/exceptions.py` | `MissingFileError`, `ReaderNotFoundError` | — | none | `loading/errors.py` | — |
| `locale/language_manager.py` | Catalog loading, `text()` | `LanguageManager` | `tools/locale/test_language_manager.py` | `i18n/catalog.py` | BUG-004 |
| `locale/language_enum.py` | Supported languages | `LanguageEnum` | `tools/locale/test_language_enum.py` | `i18n/locale.py` | BUG-012 |
| `readme/generate_readme.py` | README from template | — | none | deleted (ADR-0009) | ARC-010 |
| `spellchecker/spellchecker.py` | Facade | `SpellChecker` | `spellchecker/test_spellchecker.py` | `spell/service.py` | ARC-015 |
| `spellchecker/spellchecker_controller.py` | Word checks, quality warnings | `SpellCheckerController` | `spellchecker/test_spellchecker_controller.py` | `rules/spelling/` | PERF-006 |
| `spellchecker/dictionary_manager.py` | enchant broker, personal words, temp cleanup | `DictionaryManager` | `spellchecker/test_dictionary_manager.py` | `spell/enchant_backend.py` | BUG-022 |
| `spellchecker/text_processor.py` | Sanitising text | `TextProcessor` | `spellchecker/test_text_processor.py` | `spell/text.py` | — |
| `spellchecker/dataframe_processor.py` | Column iteration | `DataFrameProcessor` | `spellchecker/test_dataframe_processor.py` | `rules/spelling/` | PERF-006 |
| `spellchecker/main.py` | Demo | — | `spellchecker/test_main.py` | deleted | ARC-010 |

## `models/`

| Module | Sheet | Tests | Destination | Backlog |
|---|---|---|---|---|
| `sp_model_abc.py` | base | none | `specs/` + `normalizing/` | ARC-001, ARC-007 |
| `sp_description.py` | `descricao` | none | `specs/sheets.py::DESCRICAO`, `normalizing/` | BUG-002, BUG-003 |
| `sp_composition.py` | `composicao` | none | idem | BUG-002 |
| `sp_value.py` | `valores` | none | idem | BUG-013 |
| `sp_temporal_reference.py` | `referencia_temporal` | none | idem | BUG-002 |
| `sp_proportionality.py` | `proporcionalidades` | none | idem | ARC-009 |
| `sp_scenario.py` | `cenarios` | none | idem | — |
| `sp_legend.py` | `legenda` | none | idem + `rules/legend/` | — |
| `sp_dictionary.py` | `dicionario` | none | `spell/` | — |

## `validators/`

| Module | Tests | Destination | Backlog |
|---|---|---|---|
| `spreadsheets/base/base_validator.py` | none | `rules/engine.py` | ARC-008 |
| `structure/file_structure_validator.py` | none | `rules/structure/STRUCT-00x.py` | BUG-026 |
| `spell/spellchecker_validator.py` | none | `rules/spelling/SPELL-00x.py` | BUG-023 |
| `spreadsheets/description/description_validator.py` | none | `rules/description/DESC-0xx.py` | PERF-001 |
| `spreadsheets/composition/compostion_graph_validator.py` | none | `rules/composition/COMP-0xx.py` | BUG-019, BUG-024 |
| `spreadsheets/composition/composition_tree_validator.py` | none | `rules/composition/COMP-0xx.py` | PERF-001 |
| `spreadsheets/temporal_reference/temporal_reference_validator.py` | none | `rules/temporal/TEMP-0xx.py` | BUG-007 |
| `spreadsheets/proportionality/proportionality_validator.py` | none | `rules/proportionality/PROP-0xx.py` | BUG-006 |
| `spreadsheets/value/value_validator.py` | none | `rules/values/VAL-0xx.py` | BUG-001 |
| `spreadsheets/scenario/scenario_validator.py` | none | `rules/scenarios/SCEN-0xx.py` | — |
| `spreadsheets/legend/legend_validator.py` | none | `rules/legend/LEG-0xx.py` | BUG-014 |

## `static/`

| Path | Responsibility | Destination |
|---|---|---|
| `locales/{pt_BR,en_US}/messages.json` | Message catalogs | `i18n/locales/` |
| `report/report_template.html`, `microstrap_style.css` | Report template/CSS | kept |
| `dictionaries/hunspell/*.{aff,dic}`, `extra-words.dic` | Spell dictionaries | kept |
| `templates/README.TEMPLATE.md` | README generator template | removed (ADR-0009) |

Last synced with code: 3dcfdb1
