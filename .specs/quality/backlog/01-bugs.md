# 01 · Bugs (correctness)

Every fix here must land with a regression test under `tests/` that fails before and passes after.

### BUG-001 · Shared list mutated by `validate_value_combination_relation`
- Priority: P0 · Effort: S · Status: done
- Where: `data_validate/validators/spreadsheets/value/value_validator.py:283-285`
- Problem: `local_required_columns = self.global_required_columns.copy()` is a *shallow* copy; the
  following `.append(scenario_column_name)` mutates the shared `global_required_columns[description]`
  list. Every extra call appends `cenario` again, and `validate_relation_indicators_in_values`
  (which runs first in the same pipeline) would see the mutated list on a second run.
- Evidence: call the method twice on the same validator instance and inspect
  `self.global_required_columns[self.sp_name_description]`.
- Proposed fix: build the local list with `[*base, scenario_column_name]`; make
  `global_required_columns` a `Mapping[str, tuple[str, ...]]` (immutable).
- Tests: unit test asserting idempotency across two calls.
- Related: ARC-002
- Done: replaced the shallow `dict.copy()` with a per-key list copy
  (`local_required_columns = {model_name: list(columns) for model_name, columns in
  self.global_required_columns.items()}`) in `validate_value_combination_relation` so the
  subsequent `.append(scenario_column_name)` no longer mutates
  `self.global_required_columns[self.sp_name_description]`; `global_required_columns` stays a
  `Dict[str, List[str]]` (not a tuple-based `Mapping`) because other methods concatenate it with
  plain lists. Regression test:
  `tests/unit/validators/spreadsheets/value/test_value_validator.py`. Scanned every sibling
  validator (`proportionality_validator.py`, `legend_validator.py`, `composition_*.py`,
  `temporal_reference_validator.py`, `scenario_validator.py`, `description_validator.py`) for the
  same shallow-copy-then-append pattern; `legend_validator.py:397` also appends to a
  `required_columns[...]` list but builds that dict fresh as a local literal each call (no
  `.copy()` of a shared attribute), so it does not share the same bug and was left untouched.

### BUG-002 · Models overwrite class-level `RequiredColumn` Series (global mutable state)
- Priority: P0 · Effort: M · Status: open
- Where: `models/sp_description.py:251,263,277`, `models/sp_composition.py:142`,
  `models/sp_temporal_reference.py:131,142`; consumer `validators/spreadsheets/temporal_reference/temporal_reference_validator.py:136`
  (`SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.iloc[1:]` reads the **class** attribute).
- Problem: `setattr(self.RequiredColumn, "COLUMN_CODE", cleaned_series)` replaces the class-level
  `pd.Series` descriptor with data from the *current* file. Every instance, every later run in the
  same process (tests, library usage, batch validation of several folders) sees the previous data.
  `TemporalReferenceValidator` depends on this side effect to work at all.
- Proposed fix: keep column *definitions* immutable (`ColumnSpec` frozen dataclass with `name`,
  `dtype`, `min_value`, `required`); store cleaned data on the **instance**
  (`self.cleaned["codigo"]`) or in a typed `DataFrame` owned by the model.
- Tests: instantiate two models with different data in one process and assert isolation.
- Related: ARC-002, ARC-007, PERF-003

### BUG-003 · `SpDescription.pre_processing` mutates the shared raw DataFrame
- Priority: P1 · Effort: M · Status: open
- Where: `models/sp_description.py:178,187,193,195`
- Problem: drops `cenario`/`legenda` and injects `relacao=1`, `unidade=""` into
  `data_loader_model.raw_data`, the same object every validator later reads. Injected columns then
  show up in `EXPECTED_COLUMNS` and are scanned by `validate_cr_lf_characters`
  (`description_validator.py:352`); the extra-column warning logic sees a different frame than the
  file the user sent.
- Proposed fix: treat `raw_data` as immutable; derive a `normalized` frame on the model and expose
  defaults through accessors, not by writing columns.
- Tests: assert `raw_data` is unchanged after model construction.
- Related: ARC-007

### BUG-004 · Locale is resolved from two different `.config/store.locale` paths, in the wrong order
- Priority: P1 · Effort: M · Status: open
- Where: `middleware/bootstrap.py:41-42` (`os.path.expanduser(".config")` → relative to CWD),
  `helpers/tools/locale/language_manager.py:34` (`parents[4]/.config` → repository root, or
  `site-packages` parent when installed), `main.py:13-16` (`DataArgs()` builds a `LanguageManager`
  *before* `Bootstrap` persists `--locale`).
- Problem: `--locale en_US` is ignored on the first run (translations already loaded), is written to
  a different file than the one read when CWD ≠ repo root, and raises `PermissionError` on read-only
  installs. Running the installed `canoa-data-validate` from any directory creates a stray
  `./.config/` folder.
- Proposed fix: locale becomes an explicit constructor argument threaded through the context
  (no file persistence at all); if persistence is desired, use `platformdirs.user_config_dir`.
- Tests: run with `--locale en_US` from a temp CWD and assert English messages.
- Related: ARC-002, BUG-023, TOOL-008

### BUG-005 · `ValidationReport.flatten` crashes when `context` is `None`
- Priority: P1 · Effort: S · Status: done
- Where: `controllers/report/validation_report.py:92,208,213`
- Problem: `context` is declared `Optional` but `flatten` dereferences `self.context.language_manager`.
- Proposed fix: make `context` required or inject a `translate: Callable[[str], str]`.
- Tests: `flatten` with omitted messages and no context.
- Done: `flatten` now raises `ValueError("ValidationReport.flatten requires a context for message
  translation")` when truncation is actually needed and `context is None`; a call with no
  truncation still succeeds without a context. Tests:
  `tests/unit/controllers/report/test_validation_report.py::TestValidationReportFlatten`.

### BUG-006 · `list.remove("id")` raises when the `id` column is absent
- Priority: P1 · Effort: S · Status: done
- Where: `validators/spreadsheets/proportionality/proportionality_validator.py:506,513`
- Problem: `ValueError` propagates to `BaseValidator.build_reports`, which converts it into the
  user-facing message `Exception validation in file during validate_relation_indicators_in_value_and_proportionality: list.remove(x): x not in list`.
- Proposed fix: filter with a comprehension; add explicit column checks.
- Tests: proportionality without `id` at level 2, values without `id`.
- Related: SEC-004
- Done: replaced both `list.remove(self.column_name_id)` calls with list comprehensions
  (`[col for col in cols if col != self.column_name_id]`) in
  `validate_relation_indicators_in_value_and_proportionality`. Confirmed
  `check_columns_in_models_dataframes` (which runs first and validates `id` on both the
  MultiIndex level-2 and the flat `valores` columns) already prevents the crash in the normal
  flow — the two "missing `id`" regression tests pass even on the pre-fix code, because the
  guard reports the missing column and returns early. Added a third test that patches
  `check_columns_in_models_dataframes` to bypass the guard and feeds frames without `id`
  directly into the method, which does reproduce the pre-fix `ValueError` and is green after
  the comprehension fix. Regression tests:
  `tests/unit/validators/spreadsheets/proportionality/test_proportionality_validator.py`.

### BUG-007 · `int(year)` on raw cell text in `validate_reference_years`
- Priority: P1 · Effort: S · Status: done
- Where: `validators/spreadsheets/temporal_reference/temporal_reference_validator.py:136-141`
- Problem: reads the class-level Series (BUG-002) and calls `int()` on each unique value; any
  non-numeric symbol raises and is masked by the broad `except` in `build_reports`.
- Proposed fix: use the instance's cleaned integer column; report invalid values as issues.
- Tests: symbol column with `"2030a"`.
- Done: `validate_reference_years` now reads `self._dataframe[column_name_symbol]` (the
  validator's own raw-data copy set up by `BaseValidator.__init__`) instead of
  `SpTemporalReference.RequiredColumn.COLUMN_SYMBOL` (the class-level Series BUG-002 tracks),
  and validates each unique symbol with `NumberFormattingProcessing.check_cell_integer` before
  calling `int()`; non-numeric symbols are skipped silently in this rule (they are already
  reported as data-cleaning errors by `SpTemporalReference.data_cleaning` via
  `DataCleaningProcessing.clean_dataframe_integers`, confirmed by reading that method). Kept
  BUG-002 itself open — the model still overwrites `RequiredColumn.COLUMN_SYMBOL` on the class;
  only this rule's dependency on that global was removed. Regression tests (including a
  same-process two-validators-independent case that would have failed against the old
  class-Series read, since a fresh `SpTemporalReference` model was never actually instantiated
  in the mocked context and the class attribute stayed empty):
  `tests/unit/validators/spreadsheets/temporal_reference/test_temporal_reference_validator.py`.

### BUG-008 · `Bootstrap.run` argument checks are in the wrong order
- Priority: P2 · Effort: S · Status: done
- Where: `middleware/bootstrap.py:100-103`
- Problem: `isinstance(None, DataArgs)` is `False`, so `None` raises `TypeError` and the
  `ValueError` branch is unreachable. Also spins a `ThreadPoolExecutor` for a single task.
- Proposed fix: remove the executor; validate once; or remove `Bootstrap` entirely (see BUG-004).
- Done: `run()` now checks `args is None` (raising `ValueError`) before the `isinstance` check
  (raising `TypeError`), and calls `self._check_and_set_locale(args.data_file.locale)` directly
  instead of submitting it to a single-task `ThreadPoolExecutor`; the now-unused
  `concurrent.futures` import was removed. `Bootstrap` itself is untouched (that is BUG-004).
  Tests: `tests/unit/middleware/test_bootstrap.py`.

### BUG-009 · Output folder names containing a dot are rejected
- Priority: P2 · Effort: S · Status: done
- Where: `helpers/base/data_args.py:88`
- Problem: `"." in os.path.basename(output_folder)` rejects legitimate folders such as
  `data/output/run.2026-08` or `v1.2`.
- Proposed fix: validate with `Path.is_dir()`/`mkdir(parents=True)` semantics instead of string checks.
- Done: `DataFile._validate_arguments` no longer inspects the output-folder basename for dots or a
  file extension; it now rejects the path only when `os.path.isfile(output_folder)` is `True`
  (i.e. the path already exists as a regular file and can never become a directory). Any other
  path — including `run.2026-08`, `v1.2`, or a not-yet-created nested path — is accepted.
  `.specs/api/cli-contract.md`'s `--output_folder` row updated to match. Tests:
  `tests/unit/helpers/base/test_data_args.py::TestDataFileOutputFolderDots` (new) plus the
  pre-existing `TestDataFile`/`TestDataArgsEdgeCases` output-folder cases, updated to assert
  against an actually-existing file rather than a merely dotted/extensioned path.

### BUG-010 · JSON summary built with `str(dict).replace("'", '"')`
- Priority: P2 · Effort: S · Status: done
- Where: `controllers/report/file_report_generator.py:258-263`
- Problem: produces invalid JSON as soon as any value contains a quote; downstream (Canoa platform)
  parses `<{...}>` from stdout.
- Proposed fix: `json.dumps(summary, ensure_ascii=False)`; document the stdout contract in
  `.specs/api/cli-contract.md`; add `--json` output file option.
- Done: `_print_json_summary` now builds `json_output` with `json.dumps(summary,
  ensure_ascii=False)`; `.specs/api/cli-contract.md`'s stdout note updated accordingly. The
  `--json` output-file option remains open (tracked separately under the target CLI contract).
  Tests: `tests/unit/controllers/report/test_file_report_generator.py::TestPrintJsonSummary`.
- Related: ARC-011

### BUG-011 · `DATE_NOW` / `CURRENT_YEAR` evaluated at import time
- Priority: P2 · Effort: S · Status: done
- Where: `config/application_config.py:44-46`
- Problem: class attributes computed once per interpreter; long-lived processes and tests get a stale
  timestamp; the "future year" rule (`temporal_reference_validator.py:141`) depends on it.
- Proposed fix: inject a `Clock` (callable returning `datetime`) into the context.
- Done: `CURRENT_YEAR`/`DATE_NOW` are now per-instance attributes computed in
  `ApplicationConfig.__init__(self, clock: Callable[[], datetime] | None = None)` from an
  injectable `self._clock` (defaults to `datetime.now`), instead of class attributes evaluated
  once at import time. Every consumer (`file_report_generator.py`,
  `temporal_reference_validator.py`) already reads `CURRENT_YEAR`/`DATE_NOW` through a
  `config`/`context.config` **instance**, never the class, so no consumer changed. Regression
  tests: `tests/unit/config/test_application_config.py` — two instances built with different
  fake clocks report different `CURRENT_YEAR`/`DATE_NOW` (fails on pre-fix code with
  `TypeError: unexpected keyword argument 'clock'`, since the old class attributes could not be
  influenced by any instance-level clock), default construction still matches
  `datetime.now().year`, and `get_verify_names()` still returns all 34 `NamesEnum` titles with a
  mocked `LanguageManager` (documents the `TITLES_N`/`SIMP_DESC_N` `value=` interpolation). New
  test module coverage of `config/application_config.py`: 100 %.

### BUG-012 · `LanguageEnum.DEFAULT_LANGUAGE` is an enum alias
- Priority: P3 · Effort: S · Status: wont-fix
- Where: `helpers/tools/locale/language_enum.py:34-36`
- Problem: `DEFAULT_LANGUAGE = "pt_BR"` aliases `PT_BR`; iteration works only because Enum
  deduplicates aliases. Fragile and confusing.
- Proposed fix: `DEFAULT: ClassVar[LanguageEnum] = PT_BR` or a module constant.
- Wont-fix: the alias is deliberate, not accidental — every current call site
  (`bootstrap.py`, `language_manager.py`) reads `LanguageEnum.DEFAULT_LANGUAGE.value` and depends on
  `DEFAULT_LANGUAGE is PT_BR` for `Enum` member-equality/hash to keep working; replacing it with a
  `ClassVar`/module constant would need every one of those call sites updated in the same change,
  several of which (`language_manager.py`) belong to other in-flight backlog items. The docstring
  in `language_enum.py` now states the alias is intentional, and
  `tests/unit/helpers/tools/locale/test_language_enum.py::TestLanguageEnumBug012DeliberateAlias`
  pins `DEFAULT_LANGUAGE is PT_BR` and the exact two-entry `list_supported_languages()` result so
  a future change cannot silently break it. The real fix folds into the ARC-002/BUG-004 locale
  refactor, where locale becomes an explicit constructor argument and this enum's shape is
  revisited alongside every call site at once.

### BUG-013 · Wrong dtypes / names in column definitions
- Priority: P2 · Effort: S · Status: done
- Where: `models/sp_scenario.py:66`, `models/sp_temporal_reference.py:67` (`COLUMN_NAME` declared
  `int64` for a text column), `models/sp_value.py:57-61` (docstring says `COLUMN_CODE`, code defines
  `COLUMN_ID`).
- Proposed fix: fix with the `ColumnSpec` refactor (BUG-002).
- Done: the three declaration mismatches this item names are fixed. `SpScenario.RequiredColumn.
  COLUMN_NAME` and `SpTemporalReference.RequiredColumn.COLUMN_NAME` now declare
  `pd.Series(dtype="str", name="nome")` instead of `dtype="int64"` (grep confirms no code path
  reads `.dtype` on either attribute — only `.name` is read, by `scenario_validator.py`,
  `temporal_reference_validator.py`, and `spellchecker_validator.py` — so behaviour is unchanged).
  `sp_value.py`'s docstring now says `COLUMN_ID` instead of the stale `COLUMN_CODE`. Also fixed in
  the same slice: `SpDescription.DynamicColumn.COLUMN_LEGEND` declared `dtype="str"` while
  `SpDescription.data_cleaning` cleans it as an integer (min 1, empty allowed) — now declared
  `dtype="Int64"` (pandas' nullable integer dtype), matching the enforced cleaning and the
  placeholder `pd.Series(dtype="Int64")` `legend_validator.py:427` already used for the same
  column. `specs/sheet_specs.py`'s two matching divergence notes (module docstring and the inline
  `referencia_temporal`/`cenarios`/`descricao.legenda` `ColumnSpec` comments) are updated to record
  the mismatches as resolved; `referencia_temporal.nome`/`cenarios.nome` `ColumnSpec.dtype` changed
  from `"int"` to `"str"` to match. Regression tests:
  `tests/unit/models/test_column_declarations.py` (new module, 100 % coverage) pins the corrected
  dtypes/name for all four attributes and that `SpValue.RequiredColumn` has no `COLUMN_CODE`
  attribute. Remaining structural part (the placeholder `pd.Series`-as-column-declaration pattern
  itself, and moving these declarations into `ColumnSpec`) is BUG-002's job in Phase 2, not this
  item's.

### BUG-014 · Level comparisons rely on exact string `"1"` / `"2"`
- Priority: P2 · Effort: M · Status: open
- Where: `validators/spreadsheets/legend/legend_validator.py:267,304,313,329-330,338-339,438`,
  `validators/spreadsheets/proportionality/proportionality_validator.py:359,581`,
  `validators/spreadsheets/value/value_validator.py:205,223,228`,
  `helpers/common/validation/description_processing.py:50,53`
- Problem: readers load everything as `str`; a cell `1.0`, `" 1"` or `01` silently stops matching and
  the rule is skipped without any message.
- Proposed fix: compare against the cleaned integer column produced once by the model.
- Tests: description with `nivel` = `"1.0"`.
- Related: PERF-003

### BUG-015 · Data loader mixes types and silently prefers CSV over XLSX
- Priority: P2 · Effort: M · Status: open
- Where: `helpers/tools/data_loader/api/facade.py:139` (`data["qmls"]` is a `list` inside a dict of
  `DataLoaderModel`), `engine/scanner.py:27-33` (CSV wins silently while
  `FileStructureValidator.check_ignored_files_in_folder_root` reports the same situation as an error),
  `readers/qml_reader.py:13` (`read_text()` without encoding), `common/config.py:35` (`.qml` scanned
  although `SpreadsheetInfo.ALLOWED_EXTENSIONS` excludes it).
- Proposed fix: `LoadResult` dataclass (`models: dict[str, LoadedSheet]`, `extras`, `issues`);
  one policy for conflicts; drop QML unless the protocol requires it.

### BUG-016 · `en_US` catalog missing keys + leftover demo keys
- Priority: P2 · Effort: S · Status: done
- Where: `static/locales/en_US/messages.json` lacks `validator_structure_error_conflicting_files`,
  `validator_structure_error_files_not_in_folder`, `validator_structure_error_missing_file`,
  `validator_structure_error_unexpected_folder`; both catalogs contain `welcome` ("Calculadora
  Simples"), `menu_title`, `add_option`, … from a calculator demo.
- Proposed fix: parity test in `tests/unit/i18n/test_catalog_parity.py`; purge junk keys.
- Evidence: tools/i18n_check.py (2026-08-25) confirms the 4 missing en_US keys
- Related: DOC-003
- Done: added the 4 missing `en_US` translations (`validator_structure_error_*`); removed the
  18 unused calculator-demo keys (`welcome`, `menu_title`, `add_option`, `subtract_option`,
  `multiply_option`, `divide_option`, `exit_option`, `enter_choice`, `enter_num1`, `enter_num2`,
  `result`, `invalid_option`, `invalid_input`, `zero_division`, `goodbye`, `error_unexpected`,
  `lorem_ipsum`, `choose_language`) from both catalogs after confirming zero production
  references; kept `invalid_language`/`lang_load_error` (used by `LanguageManager`); added
  `tests/unit/i18n/test_catalog_parity.py` (key-set parity, `{"message": str}` shape,
  named-placeholder parity); `tools/i18n_check.py` now exits 0 with only the documented
  `verification_name_*` unused-key heuristic warning remaining.

### BUG-017 · `MetadataInfo` uses `assert` for validation and prints at import
- Priority: P2 · Effort: S · Status: done
- Where: `config/metadata_info.py:74,117,126-149`
- Problem: `assert` is stripped under `python -O`; `print()` side effect at import when the package
  is not installed; `_make_url` is dead code; version becomes `0.0.0b732` in editable/uninstalled
  mode.
- Proposed fix: `importlib.metadata.version()` with a clean fallback; drop hand-maintained `serial`.
- Done: `_make_version` now raises `ValueError(f"invalid release_level: {release_level!r}")` instead
  of `assert`; the `print()` on `PackageNotFoundError` was replaced by
  `logging.getLogger(__name__).debug(...)` so importing the module with the package uninstalled is
  silent; the dead `_make_url` static method was removed. The `bandit` `B101` skip in
  `pyproject.toml` was removed (confirmed zero remaining `assert` statements in `data_validate/`).
  Version composition (`serial = 732`, beta suffix, `0.0.0b732` in editable mode) is unchanged —
  that remains TOOL-005's scope. Tests:
  `tests/unit/helpers/base/test_metadata_info.py::TestMetadataInfo::test_make_version_invalid_release_level`,
  `::test_make_url_removed`, `::test_init_with_package_not_found` (now asserts empty stdout via
  `capsys`).
- Related: TOOL-005

### BUG-018 · CSV reader depends on the file *stem* to find the separator
- Priority: P2 · Effort: S · Status: open
- Where: `helpers/tools/data_loader/readers/csv_reader.py:19-22,33-35`
- Problem: separator comes from `Config().file_specs.get(stem)`; any unknown stem falls back to
  `","` although the protocol uses `|`. `filled0[0] = lvl0[0] or "Unnamed: 0_level_0"` is an
  undocumented special case.
- Proposed fix: pass `sep` and header strategy explicitly from the sheet spec; sniff with
  `csv.Sniffer` as fallback and report.

### BUG-019 · Duplicate work and hard-coded root in the graph validator
- Priority: P2 · Effort: S · Status: open
- Where: `validators/spreadsheets/composition/compostion_graph_validator.py:374,385-395,398`
- Problem: `validate_unique_titles_with_graph` re-runs `validate_relation_indicators_in_composition`
  and cycle/disconnection detection already executed by the previous rules; root node `"1"` is
  hard-coded.
- Proposed fix: compute graph facts once in `_prepare_statement`; make the root configurable in the
  sheet spec.

### BUG-020 · `TestReportItem` is collected by pytest
- Priority: P3 · Effort: S · Status: done
- Where: `controllers/report/validation_report.py:15`
- Problem: any test module importing it gets a `PytestCollectionWarning` / accidental collection.
- Proposed fix: rename to `ReportItem` (or `RuleReport`).
- Done: renamed the class to `ReportItem` (with `__test__ = False`); kept a deprecated
  `TestReportItem = ReportItem` alias for one release, also with `__test__` set to `False` so
  pytest never collects it under either name. All internal usages in
  `controllers/report/validation_report.py` updated. Tests:
  `tests/unit/controllers/report/test_validation_report.py::TestReportItemClass`.

### BUG-021 · Logger creates `data/output/logs` in CWD and leaks the file handler
- Priority: P2 · Effort: S · Status: open
- Where: `controllers/context/general_context.py:74-84,100-101`, `helpers/base/logger_manager.py:144`
- Problem: a log directory is always created relative to CWD; a log file is created and then deleted
  when not in debug mode; the `FileHandler` is never closed (deletion fails on Windows, handlers
  accumulate across runs in one process).
- Proposed fix: log to `output_folder/logs` only when `--debug`; use `logging.config.dictConfig`
  and close handlers in `finalize()`.

### BUG-022 · Spellchecker writes personal dictionaries inside the package directory
- Priority: P2 · Effort: M · Status: open
- Where: `helpers/tools/spellchecker/dictionary_manager.py:41,80-81,101,139-147`
- Problem: sets `os.environ["ENCHANT_CONFIG_DIR"]` globally, adds user words with
  `dictionary.add()` (persisted by enchant to `<package>/static/dictionaries/pt_BR.dic|.exc`), then
  deletes those files in `__del__`. Fails on read-only installs, races between concurrent runs, and
  words from one spreadsheet can leak into another run if cleanup fails.
- Proposed fix: use `dictionary.add_to_session()` (session-only) or a `DictWithPWL` pointing to a
  temp dir; no environment mutation.

### BUG-023 · Spell dictionary language taken from CLI arg, UI language from file
- Priority: P2 · Effort: S · Status: open
- Where: `validators/spell/spellchecker_validator.py:72` vs `helpers/tools/locale/language_manager.py:47-51`
- Problem: two sources of truth that can disagree (see BUG-004).
- Proposed fix: single `Locale` value in the context.

### BUG-024 · Typos in identifiers and filenames
- Priority: P3 · Effort: S · Status: open
- Where: `validators/spreadsheets/composition/compostion_graph_validator.py` (filename),
  `language_manager.py:29,33` (`_congifure_language`), `legend_processing.py:181`
  (`origina_value`), `language_manager.py:28` ("Pipiline"), `data_args.py:204` ("validaton"),
  `file_system_utils.py:95` ("dempotent").
- Proposed fix: rename during the module migration; keep a compatibility import for one release.

### BUG-025 · `check_columns_in_models_dataframes` KeyError on unknown model name
- Priority: P3 · Effort: S · Status: done
- Where: `validators/spreadsheets/base/base_validator.py:126`
- Problem: `model_dataframes[model_name]` raises `KeyError` instead of reporting; the `None` check on
  the next line can never trigger.
- Proposed fix: `.get()` + explicit issue.
- Done: replaced `model_dataframes[model_name]` with `model_dataframes.get(model_name,
  pd.DataFrame())` and dropped the now-unreachable `if dataframe is not None` guard; a missing
  model name is treated as an empty dataframe, so every one of its required columns goes through
  the same `DataFrameProcessing.column_exists` abort-message path used for a present-but-incomplete
  model, instead of raising. Regression tests:
  `tests/unit/validators/base/test_base_validator.py`.

### BUG-026 · `FileStructureValidator` duplicates its own error lists
- Priority: P3 · Effort: S · Status: done
- Where: `validators/structure/file_structure_validator.py:68-69,243-248,275`
- Problem: maintains `self.errors` and `self._errors`; `validate_all_general_structure` returns
  `self.errors` which `build_reports` then extends into `self._errors`; wrapping each check in a
  one-element list is noise.
- Proposed fix: return locals; drop the duplicate state.
- Done: removed the `self.errors`/`self.warnings` instance attributes (the base class already owns
  `self._errors`/`self._warnings`); `validate_all_general_structure` now builds a local list from
  the four `(is_valid, errors)` check tuples directly (no one-element-list wrapping) and returns
  it, so the method is idempotent — calling it twice no longer doubles/triples the accumulated
  errors as it did while `self.errors` was shared, unreset state. Message text/order is unchanged.
  Regression tests: `tests/unit/validators/structure/test_file_structure_validator.py`.

### BUG-027 · `SpellCheckerValidator._prepare_statement` is never called
- Priority: P2 · Effort: S · Status: done
- Where: `validators/spell/spellchecker_validator.py:158-171,94` (`__init__` calls `self.run()` directly,
  unlike the other validators that call `_prepare_statement()` first)
- Problem: `SpellChecker.errors_dictionary` (missing hunspell dictionary, unreadable
  `extra-words.dic`, enchant initialisation failure) is never copied into the report; a broken spell
  backend silently produces zero spelling warnings and the run looks clean.
- Proposed fix: call `_prepare_statement()` before `run()` (or, in the rules engine, surface backend
  initialisation failures as `SPELL-*` issues); regression test with a mocked broken dictionary.
- Done: `__init__` now calls `self._prepare_statement()` before `self.run()`, mirroring every other
  validator; `_prepare_statement` still extends `self._errors` with `SpellChecker.errors_dictionary`
  and now also pushes those same messages into `self._report_list` under
  `self.TITLES_INFO[NamesEnum.SPELL.value]` (the existing SPELL/Ortografia section title), so a
  broken dictionary backend is visible in the report instead of silently dropped. No new message
  text was introduced — only `DictionaryManager`'s existing strings are surfaced. Verified the e2e
  golden harness is unaffected: this dev environment's enchant install lacks the pt_BR dictionary,
  so `errors_dictionary` is non-empty on every fixture run, but `tests/e2e/test_golden.py` already
  drops the whole spelling section (`spell_skipped: true`) whenever enchant is unavailable;
  `tests/e2e/golden/*.json` is untouched (`git status --short tests/e2e/golden` empty) and
  `poetry run pytest tests/e2e -q --no-cov -m e2e` is green. Regression tests:
  `tests/unit/validators/spell/test_spellchecker_validator.py`.
- Related: SEC-004, ARC-015, spec `.specs/business-rules/spelling.md`
