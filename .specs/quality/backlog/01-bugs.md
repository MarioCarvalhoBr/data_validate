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
- Note (ARC-017 Phase 3 Port 5): `value_validator.py` (and its regression test,
  `tests/unit/validators/spreadsheets/value/test_value_validator.py`) is deleted — the shared-list
  path this bug lived on no longer exists at all. `rules/value.py::check_value_combination_relation`
  is a pure `RuleContext -> list[Issue]` function reading an immutable `RuleContext`
  (`.claude/rules/dataframe-conventions.md`) with no instance/module-level mutable state to share
  between calls, so the bug class cannot recur by construction; the regression now lives as
  `tests/unit/rules/test_value.py::TestIdempotency` (calls every VAL-002…005 check twice on one
  context and asserts equal results).

### BUG-002 · Models overwrite class-level `RequiredColumn` Series (global mutable state)
- Priority: P0 · Effort: M · Status: done
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
- Done: `SpModelABC.__init__` (`models/sp_model_abc.py`) now sets `self.cleaned: dict[str,
  pd.Series] = {}` and exposes `cleaned_column(name) -> pd.Series` (returns
  `self.cleaned.get(name, pd.Series(dtype="object"))`). `SpDescription.data_cleaning`,
  `SpComposition.data_cleaning`, and `SpTemporalReference.data_cleaning` no longer
  `setattr(self.RequiredColumn, ...)`/reassign a `DynamicColumn`/`RequiredColumn` class
  attribute — every cleaned column (`codigo`, `nivel`, `cenario`, `legenda`,
  `codigo_pai`, `codigo_filho`, `simbolo`) is stored in `self.cleaned[column_name]` instead. The
  `RequiredColumn`/`OptionalColumn`/`DynamicColumn` nested classes are now pure name/dtype
  *declarations*, never reassigned by any model. The only two call sites in `validators/` that
  actually read a model's *data* through a `RequiredColumn`/`DynamicColumn` attribute (as opposed
  to reading `.name`, a static string, which was always safe) are migrated to
  `model.cleaned_column(name)`: `description_validator.py::validate_sequential_codes`/
  `validate_unique_codes` (`self._data_model.cleaned_column("codigo")`, was
  `self._data_model.RequiredColumn.COLUMN_CODE`), and
  `compostion_graph_validator.py::validate_relation_indicators_in_composition`
  (`self.model_sp_description.cleaned_column("codigo")`,
  `self.model_sp_composition.cleaned_column("codigo_pai"/"codigo_filho")`, was
  `.RequiredColumn.COLUMN_CODE`/`COLUMN_PARENT_CODE`/`COLUMN_CHILD_CODE`).
  `temporal_reference_validator.py::validate_reference_years` already read
  `self._dataframe[column_name_symbol]` since BUG-007 and is untouched. Every other
  `RequiredColumn`/`DynamicColumn` read across `validators/` and `controllers/` is a `.name`
  access on the placeholder Series (a static string, grep-confirmed) and needed no change.
  Regression tests: `tests/unit/models/test_model_isolation.py` (new, 100 % coverage) —
  `TestSpDescriptionInstanceIsolation`/`TestSpCompositionInstanceIsolation`/
  `TestSpTemporalReferenceInstanceIsolation` build two model instances from different frames in
  one process and assert (a) the class-level `RequiredColumn` placeholder stays the pristine,
  empty declaration after both runs, and (b) each instance's `cleaned_column(...)` reflects only
  its own data. Full unit suite green (1282 passed), e2e golden harness 7/7 twice with an empty
  `git status --short tests/e2e/golden` diff.

### BUG-003 · `SpDescription.pre_processing` mutates the shared raw DataFrame
- Priority: P1 · Effort: M · Status: done
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
- Done: `SpModelABC.__init__` now sets `self.frame: pd.DataFrame = data_model.raw_data` — the
  same object initially (cheap, no copy), but every model that needs to drop/inject a column
  reassigns `self.frame` via a non-mutating operation (`self.frame = self.frame.drop(...)`,
  `self.frame = self.frame.assign(**{col: value})`) instead of writing into
  `data_loader_model.raw_data`/`self.frame` in place. `SpDescription.pre_processing`/
  `expected_structure_columns`/`data_cleaning` now read and reassign `self.frame` exclusively;
  `data_loader_model.raw_data` is never written by `SpDescription` again.
  `SpProportionality.post_processing` now sets `self.frame = pd.DataFrame()` and a new instance
  flag `self.header_layout_invalid = True` on a structural error, instead of overwriting
  `data_loader_model.raw_data`/`.header_type` (also shared with every other model/validator);
  `DataLoaderModel.header_type` is never mutated after load (confirmed by grep — no remaining
  write to `.header_type` anywhere in `data_validate/`). `BaseValidator.__init__` now builds
  `self._dataframe` from `self._data_model.frame.copy()` (was `.data_loader_model.raw_data.copy()`),
  so every validator keeps seeing `SpDescription`'s injected `relacao`/`unidade` defaults and
  `SpProportionality`'s empty-on-invalid frame — both previously relied on the raw-data mutation.
  `SpellCheckerValidator.validate_spellchecker` was switched the same way. Every
  `<model>.data_loader_model.raw_data` read in `validators/` that stood in for "this sheet's
  current working data" (as opposed to the pre-model `raw_data_map` reads in
  `spreadsheet_processor.py`, which run before any `Sp*` model exists) was audited and switched to
  `<model>.frame`: `compostion_graph_validator.py` (`model_dataframes` dict, 3 `.raw_data.empty`/
  `is_read_successful` guards), `composition_tree_validator.py` (`model_dataframes` dict — this
  validator's own `global_required_columns` requires `descricao.relacao`, which only exists on
  `.frame`, so this read was previously *silently correct by accident* of the old mutation; a
  frame-vs-raw audit here specifically was necessary for byte-identical goldens), `value_validator.py`
  (`model_dataframes` dict, including the `cenario` column `SpDescription` may drop/inject),
  `proportionality_validator.py` (`model_dataframes` dict, including the entry that must reflect
  `SpProportionality`'s invalidated frame), `legend_validator.py` (`model_dataframes` dict + two
  `.empty` guards). Every existing `mocker.MagicMock()`-based validator test that stubbed
  `model.data_loader_model.raw_data` was updated to mirror the same dataframe onto `model.frame`
  (both attributes read by production code depending on the call site). Regression tests:
  `tests/unit/models/test_model_isolation.py::TestSpDescriptionRawDataImmutability` (raw_data
  byte-identical to the original input after construction via `pd.testing.assert_frame_equal`;
  injected `relacao`/`unidade` visible on `model.frame`, absent from `raw_data`) and
  `TestSpProportionalityFrameInvalidation` (a structural error empties `model.frame` and sets
  `header_layout_invalid`, while `raw_data` and `data_loader_model.header_type` stay untouched).
  Full unit suite green (1282 passed), `make check` green, e2e golden harness 7/7 twice with an
  empty `git status --short tests/e2e/golden` diff. PERF-002 note: `BaseValidator.__init__` and
  `legend_validator.py::_prepare_statement` still `.copy()` their frame defensively — left in
  place per this item's own instruction ("keep the `.copy()` for safety"); PERF-002 itself stays
  open (CoW already protects; the remaining copies are a separate, deliberate call, not this
  bug).

### BUG-004 · Locale is resolved from two different `.config/store.locale` paths, in the wrong order
- Priority: P1 · Effort: M · Status: done
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
- Done: `Bootstrap` (`middleware/bootstrap.py`, the whole `middleware` package) is deleted; `main.py`
  now wires `DataArgs() → GeneralContext(data_args=data_args) → SpreadsheetProcessor → finalize()`
  directly, with no locale-persistence step in between. `LanguageManager.__init__` takes an explicit
  `locale: str | None` constructor argument (falls back to `LanguageEnum.DEFAULT_LANGUAGE.value`
  when `None` or unsupported) and the typo'd `_congifure_language` method — the only code path that
  ever read or wrote `.config/store.locale` — is deleted entirely; no file is read or written to
  resolve the locale any more. `GeneralContext.__init__` builds the **one** `LanguageManager`
  instance for a run from `data_args.data_file.locale` and injects it into `ApplicationConfig` and
  `FileSystemUtils` (both gained an optional `language_manager` constructor parameter, defaulting to
  building their own with `locale=None` for backwards compatibility). `DataArgs` no longer builds its
  own (unused) `LanguageManager` either. Verified with a manual CLI smoke run
  (`python -m data_validate.main --locale en_US ...` from `/tmp`): the HTML report renders in
  English (`"Structure of the input folder files"` vs the pt_BR `"Estrutura dos arquivos da pasta de
  entrada"`) and no `.config/` or `data/` directory is created under the invocation's CWD. Tests:
  `tests/unit/helpers/tools/locale/test_language_manager.py` (rewritten for the explicit-locale
  constructor, including a `no file I/O for locale resolution` regression test and two
  real-catalog end-to-end cases), `tests/unit/controllers/context/test_general_context.py` (new —
  `test_locale_en_us_produces_english_text`, shared-`LanguageManager` instance test),
  `tests/unit/config/test_application_config.py::TestApplicationConfigLanguageManagerInjection`,
  `tests/unit/helpers/base/test_file_system_utils.py::test_init_uses_injected_language_manager`.
  `middleware/bootstrap.py` and `tests/unit/middleware/` are deleted (see BUG-008, now moot).

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
  the comprehension fix. Regression tests (superseded — see the note below):
  `tests/unit/validators/spreadsheets/proportionality/test_proportionality_validator.py`.
- Note (ARC-017 Phase 3 Port 7, path moved): `SpProportionalityValidator`/
  `proportionality_validator.py` is deleted; the fix's shape is preserved in
  `rules/proportionality.py::check_relation_indicators_in_value_and_proportionality` (PROP-005) —
  both the `proporcionalidades` `id` (level 2) and `valores` `id` columns are checked, as an
  abort `Issue`, before any column-name set is built, so a missing `id` can never reach a
  `list.remove`-shaped crash. The regression tests above are deleted along with the validator;
  their scenarios (missing `id` in `proporcionalidades`'s level 2, missing `id` in `valores`) are
  now `tests/unit/rules/test_proportionality.py::TestCheckRelationIndicatorsInValueAndProportionality
  ::test_missing_proportionality_id_reports_the_level2_abort`/`::test_missing_values_id_reports_the_abort`.

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
  in the mocked context and the class attribute stayed empty). Original regression tests were in
  `tests/unit/validators/spreadsheets/temporal_reference/test_temporal_reference_validator.py`
  (deleted).
- Note (ARC-017 Phase 3 Port 4): `temporal_reference_validator.py`/`SpTemporalReferenceValidator`
  is deleted; the fix's semantics are preserved (not reopened) in
  `rules/temporal_reference.py::check_reference_years_are_future` (reads `ctx.sheet(...)`'s raw
  `simbolo` column, never a class-level `RequiredColumn` Series; a non-numeric symbol is silently
  excluded from the violation mask instead of raising). The two migrated regression cases
  (a `"2030a"` symbol skipped without raising, two independent contexts not leaking state) now
  live in `tests/unit/rules/test_temporal_reference.py::TestCheckReferenceYearsAreFuture`.

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
- Superseded: `Bootstrap` (and `tests/unit/middleware/test_bootstrap.py` with it) was deleted
  entirely by the BUG-004 fix; this item's fix is moot now that the class it patched no longer
  exists, kept here only for history.

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
- Priority: P2 · Effort: M · Status: done
- Where: `validators/spreadsheets/legend/legend_validator.py:267,304,313,329-330,338-339,438`,
  `validators/spreadsheets/proportionality/proportionality_validator.py:359,581`,
  `validators/spreadsheets/value/value_validator.py:205,223,228`,
  `helpers/common/validation/description_processing.py:50,53`
- Problem: readers load everything as `str`; a cell `1.0`, `" 1"` or `01` silently stops matching and
  the rule is skipped without any message.
- Proposed fix: compare against the cleaned integer column produced once by the model.
- Tests: description with `nivel` = `"1.0"`.
- Related: PERF-003
- Finding (Phase 2c review, not implemented that slice): reviewed adding a
  `DataFrameProcessing.numeric_mask(series, value)` helper (`pd.to_numeric(series,
  errors="coerce") == value`) to replace every `== "1"`/`!= "1"`/`== "2"`/`!= "2"` site named
  above. All ~13 call sites compare against a *locally re-cleaned or still-raw* `nivel`/
  `codigo_pai` column, not a model's `cleaned_column(...)` (BUG-002's per-instance store) — so
  this is a pure string-vs-numeric-comparison fix, unrelated to BUG-002/BUG-003's frame/cleaned
  ownership.
- Done: added `DataFrameProcessing.numeric_equals_mask(series, value)` (`pd.to_numeric(series,
  errors="coerce") == value`; a cell that fails to parse, including `NaN`, evaluates to `False`)
  and `numeric_not_equals_mask(series, value)` (`~numeric_equals_mask(...)`; a cell that fails to
  parse evaluates to `True`, mirroring the historical `series != "1"` string-comparison
  semantics) to `data_validate/helpers/common/validation/dataframe_processing.py`. Replaced all 13
  literal `"1"`/`"2"` comparisons across the four files this item names — the scenario-column
  `== "0"` comparisons alongside two of them (`description_processing.py`,
  `value_validator.py::validate_relation_indicators_in_values`) are a distinct column and were
  left untouched, out of this item's stated scope. Call-site table (old expression → new
  expression; all in the four owned files above):

  | # | File : old line(s) | Old expression | New expression |
  |---|---|---|---|
  | 1 | `description_processing.py:50` | `df[level] != "1"` | `DataFrameProcessing.numeric_not_equals_mask(df[level], 1)` |
  | 2 | `description_processing.py:53` | `df[level] == "2"` (compound with `& scenario == "0"`, scenario side untouched) | `DataFrameProcessing.numeric_equals_mask(df[level], 2)` |
  | 3 | `value_validator.py:208` (`validate_relation_indicators_in_values`) | `df[level] == "1"` | `DataFrameProcessing.numeric_equals_mask(df[level], 1)` |
  | 4 | `value_validator.py:227` | `df[level] != "1"` | `DataFrameProcessing.numeric_not_equals_mask(df[level], 1)` |
  | 5 | `value_validator.py:233` (also in `validate_relation_indicators_in_values`; `validate_value_combination_relation`'s own `level = int(row[level_column_name])` already used `int()` and needed no change) | `df[level] == "2"` (compound with `& scenario == "0"`, scenario side untouched) | `DataFrameProcessing.numeric_equals_mask(df[level], 2)` |
  | 6 | `proportionality_validator.py:367` | `df[level] == "1"` | `DataFrameProcessing.numeric_equals_mask(df[level], 1)` |
  | 7 | `proportionality_validator.py:605` | `df_composition[parent] != "1"` | `DataFrameProcessing.numeric_not_equals_mask(df_composition[parent], 1)` |
  | 8 | `legend_validator.py:269` (`validate_relation_indicators_in_legend`) | `df[level] != "1"` | `DataFrameProcessing.numeric_not_equals_mask(df[level], 1)` |
  | 9 | `legend_validator.py:308` | `df[level] == "1"` | `DataFrameProcessing.numeric_equals_mask(df[level], 1)` |
  | 10 | `legend_validator.py:317` | `df[level] == "1"` | `DataFrameProcessing.numeric_equals_mask(df[level], 1)` |
  | 11 | `legend_validator.py:333-334` | `(df[level] != "1") & (df[level] != "2")` | hoisted into a shared `is_other_level_mask = numeric_not_equals_mask(level, 1) & numeric_not_equals_mask(level, 2)`, reused at sites 11 and 12 |
  | 12 | `legend_validator.py:342-343` | `(df[level] != "1") & (df[level] != "2")` | same `is_other_level_mask` as site 11 |
  | 13 | `legend_validator.py:442` (`validate_range_multiple_legend`) | `df[level] == "1"` | `DataFrameProcessing.numeric_equals_mask(df[level], 1)` |

  Regression tests: `tests/unit/helpers/common/validation/test_column_validation.py::
  TestNumericEqualsMask` (table-driven: `"1"`, `"1.0"`, `" 1"`, `"01"`, `int`/`float`, `NaN`, junk
  strings, for both the equals and not-equals mask), new
  `tests/unit/helpers/common/validation/test_description_processing.py` (a `nivel = "1.0"` row now
  correctly excluded from `get_valids_codes_from_description`, and a `nivel = "2.0"`/`cenario = "0"`
  row correctly excluded), new `tests/unit/validators/spreadsheets/legend/test_legend_validator.py`
  (three cases: a level-1 indicator with an illegal legend reference stored as `nivel = "1.0"` is
  now caught instead of silently skipped; a level-2 indicator stored as `nivel = "2.0"` is no
  longer wrongly required to carry a legend reference; a level-1 indicator stored as `nivel = "1.0"`
  is now correctly excluded from legend-range checking even when its value sits outside the
  default `[0, 1]` range), `tests/unit/validators/spreadsheets/value/test_value_validator.py::
  TestSpValueValidatorBug014LevelComparison` (a level-1 indicator stored as `nivel = "1.0"` is no
  longer wrongly reported as missing from `valores.csv`), `tests/unit/validators/spreadsheets/
  proportionality/test_proportionality_validator.py::TestSpProportionalityValidatorBug014LevelComparison`
  (a level-1 indicator stored as `nivel = "1.0"` is no longer wrongly reported as an extra code
  present in `proporcionalidades.csv` but missing from `descricao.csv`). Site 7
  (`proportionality_validator.py:605`, the composition `codigo_pai != "1"` root-node filter) has no
  test of its own: by construction, the dict this filter builds is only ever queried with keys
  derived by splitting a *proportionality* column header on `-` (always a clean digit string, never
  `"1.0"`-shaped), so whether the stray root-formatted row is retained or dropped from that
  dictionary is unobservable through any public method's return value — the fix was still applied
  for consistency and is covered indirectly by the general `numeric_not_equals_mask` unit tests.
  Full unit suite green (1377 passed), `make check` green (ruff, mypy, bandit, unit tests), e2e
  golden harness 7/7 with an empty `git status --short tests/e2e/golden` diff (none of the
  `data/input/**` fixtures carry a non-canonical `"1.0"`/`" 1"`/`01`-formatted level or code, so no
  golden output changed). Remaining, explicitly out of scope for this slice:
  `composition_tree_validator.py` (dict-keyed level reads, a different pattern — not owned by this
  item, not audited here) and the `NEW data_validate/rules/` package (owned by a parallel migration
  slice, untouched).

### BUG-015 · Data loader mixes types and silently prefers CSV over XLSX
- Priority: P2 · Effort: M · Status: done
- Where: `helpers/tools/data_loader/api/facade.py:139` (`data["qmls"]` is a `list` inside a dict of
  `DataLoaderModel`), `engine/scanner.py:27-33` (CSV wins silently while
  `FileStructureValidator.check_ignored_files_in_folder_root` reports the same situation as an error),
  `readers/qml_reader.py:13` (`read_text()` without encoding), `common/config.py:35` (`.qml` scanned
  although `SpreadsheetInfo.ALLOWED_EXTENSIONS` excludes it).
- Proposed fix: `LoadResult` dataclass (`models: dict[str, LoadedSheet]`, `extras`, `issues`);
  one policy for conflicts; drop QML unless the protocol requires it.
- Done: `.qml` support removed entirely (ADR-0003) — `readers/qml_reader.py` and its test module are
  deleted, `.qml` dropped from `ReaderFactory._registry`, and `FileScanner` only scans
  `ALLOWED_EXTENSIONS` (`.csv`, `.xlsx`) from `data_validate.specs.sheet_specs`; `.qml` files in the
  input folder are simply not loaded (`FileStructureValidator` already flags them as unexpected, and
  the golden harness proves that behaviour is unchanged). The CSV-over-XLSX conflict policy is now
  explicit and documented in `engine/scanner.py`'s docstring: `FileScanner.scan()` returns
  `(found, ignored, missing)` — the losing path of a conflict is recorded in `ignored` instead of
  silently dropped, though nothing downstream consumes `ignored` yet (`FileStructureValidator`
  still independently detects and reports the same conflict as STRUCT-006, unchanged). `DataLoaderFacade`
  gained a real `load() -> LoadResult` method (`LoadResult(models, errors)`, see ARC-009); the
  `"qmls"` key is gone from the returned mapping (grep across `data_validate/` found no consumer of
  `raw_data_map["qmls"]`). Tests: `tests/unit/helpers/tools/data_loader/engine/test_scanner.py`,
  `tests/unit/helpers/tools/data_loader/engine/test_factory.py`,
  `tests/unit/helpers/tools/data_loader/api/test_facade.py`. Full unit suite green (1272 passed),
  `make check` green, e2e golden harness 7/7 twice with an empty `git status --short
  tests/e2e/golden` diff.

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
- Priority: P2 · Effort: S · Status: done
- Where: `helpers/tools/data_loader/readers/csv_reader.py:19-22,33-35`
- Problem: separator comes from `Config().file_specs.get(stem)`; any unknown stem falls back to
  `","` although the protocol uses `|`. `filled0[0] = lvl0[0] or "Unnamed: 0_level_0"` is an
  undocumented special case.
- Proposed fix: pass `sep` and header strategy explicitly from the sheet spec; sniff with
  `csv.Sniffer` as fallback and report.
- Done: `CSVReader.__init__` now takes an explicit `sep: str = "|"` constructor parameter instead
  of reading the deleted `data_loader.common.config.Config` singleton by file stem;
  `ReaderFactory.get_reader(file_path, header_strategy, sep="|")` passes it through only to
  `CSVReader` (ignored by `ExcelReader`, which has no separator). `DataLoaderFacade.load()` computes
  `sep` from `SHEET_SPECS[name].csv_separator` (every sheet declares `"|"` today — no user-visible
  behaviour change) instead of guessing from the stem, so an unrecognised stem can no longer reach
  the reader with a wrong `","` fallback (the facade only calls readers for names present in
  `SHEET_SPECS`). The `filled0[0] = lvl0[0] or "Unnamed: 0_level_0"` special case is untouched (out
  of this item's scope — still an undocumented fallback, now only documented via the module
  docstring's cross-reference). `csv.Sniffer`-based fallback detection was judged unnecessary: with
  `sep` always explicit from `SheetSpec`, there is no "unknown stem" path left to sniff. Tests:
  `tests/unit/helpers/tools/data_loader/readers/test_csv_reader.py`,
  `tests/unit/helpers/tools/data_loader/engine/test_factory.py`,
  `tests/unit/helpers/tools/data_loader/api/test_facade.py`.
- Related: ARC-003 (consumer migration)

### BUG-019 · Duplicate work and hard-coded root in the graph validator
- Priority: P2 · Effort: S · Status: done
- Where (legacy, now deleted): `validators/spreadsheets/composition/compostion_graph_validator.py:374,385-395,398`
- Problem: `validate_unique_titles_with_graph` re-runs `validate_relation_indicators_in_composition`
  and cycle/disconnection detection already executed by the previous rules; root node `"1"` is
  hard-coded.
- Done: ARC-017 Phase 3 Port 3 replaced both legacy composition validators with
  `data_validate/rules/composition.py`. `compute_composition_facts(ctx)` builds the graph, runs
  cycle/disconnected-component detection, the tree-cycle DFS, and the `descricao`<->`composicao`
  code comparison exactly once per run; `SpreadsheetProcessor._build_rule_context` calls it once
  and injects the result via `ctx.options["composition_facts"]`, and every `COMP-*` rule
  (including COMP-004, the former re-runner) reads that same `CompositionFacts` instead of
  recomputing anything. The hard-coded root is now `ctx.options.get("composition_root", "1")` —
  configurable, defaulting to the prior behaviour. Tests: `tests/unit/rules/test_composition.py`
  (`TestComputeCompositionFacts`, `TestCheckUniqueTitlesPerSubtree`).

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
- Priority: P2 · Effort: S · Status: done
- Where: `controllers/context/general_context.py:74-84,100-101`, `helpers/base/logger_manager.py:144`
- Problem: a log directory is always created relative to CWD; a log file is created and then deleted
  when not in debug mode; the `FileHandler` is never closed (deletion fails on Windows, handlers
  accumulate across runs in one process).
- Proposed fix: log to `output_folder/logs` only when `--debug`; use `logging.config.dictConfig`
  and close handlers in `finalize()`.
- Done: `LoggerManager.__init__` now accepts `log_folder: str | None`; when `None` (the non-debug
  path), no directory is created and `configure_logger` attaches no `FileHandler` at all — only a
  console handler. `GeneralContext.__init__` passes `log_folder=os.path.join(output_folder, "logs")`
  only when `data_args.data_action.debug` is true, and `log_folder=None` otherwise — never a
  `logs/` directory relative to the CWD (previously always `"data/output/logs"`, a literal relative
  path). `GeneralContext.finalize()` no longer calls `file_system_utils.remove_file(...)` (there is
  no file to delete when not in debug mode); instead it always closes and detaches every handler on
  `self.logger` (`handler.close()` + `logger.removeHandler(handler)`), fixing the leaked/never-closed
  `FileHandler`. `logging.config.dictConfig` was not adopted — `LoggerManager`'s existing
  imperative `configure_logger` already satisfies the "no directory unless debug, handlers closed"
  acceptance criteria without that larger refactor. Regression tests:
  `tests/unit/helpers/base/test_logger_manager.py::TestLoggerManagerNoFileLogging` (no directory, no
  file handler, `log_file is None`, all with `log_folder=None`),
  `tests/unit/controllers/context/test_general_context.py::TestGeneralContextLogging` (debug=False:
  no `logs/` directory anywhere under an isolated CWD, logger disabled; debug=True: log file created
  under `<output_folder>/logs`; `finalize()` leaves `logger.handlers == []` in both modes).

### BUG-022 · Spellchecker writes personal dictionaries inside the package directory
- Priority: P2 · Effort: M · Status: done
- Where: `helpers/tools/spellchecker/dictionary_manager.py`
- Problem (fixed): set `os.environ["ENCHANT_CONFIG_DIR"]` globally, added user words with
  `dictionary.add()` (persisted by enchant to `<package>/static/dictionaries/pt_BR.dic|.exc`), then
  deleted those files in `__del__`. Failed on read-only installs, raced between concurrent runs, and
  words from one spreadsheet could leak into another run if cleanup failed. Note: opening the
  dictionary at all (even with zero `add()` calls) was enough to make Enchant create the empty
  `.dic`/`.exc` PWL files — `add()` vs `add_to_session()` alone does not stop the file creation,
  because Enchant auto-manages a default personal word list rooted at `ENCHANT_CONFIG_DIR` as soon
  as a dictionary is requested.
- Fix shipped: `dictionary.add()` → `dictionary.add_to_session()` everywhere a user/extra word is
  added (`initialize_dictionary`, `_load_extra_words`), so a word is only ever known to the
  in-process session, never written to a personal word list file. Combined with SEC-007's
  session-scoped `ENCHANT_CONFIG_DIR` (a symlinked temp directory, not the package directory), no
  file is created under `static/dictionaries` at any point — not even the automatic PWL Enchant
  would otherwise create merely from `request_dict`. `clean_temporary_files` was rewritten to drop
  the broker/dictionary references and discard the temp directory; the old file-deletion loop
  (`Path.unlink()` on `<lang>.dic`/`<lang>.exc`) and `__del__` were both removed — there is no
  on-disk personal dictionary left to clean up. Verified with two real, un-mocked `pyenchant`
  managers running the bundled `pt_BR` dictionary concurrently in one process
  (`test_two_managers_do_not_interfere`): each manager's session words are invisible to the other.
  Regression tests: `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py` (see SEC-007
  for the full list; `TestDictionaryManagerRealEnchant.test_session_word_is_checkable` and
  `test_no_file_created_under_package_dictionaries_directory` are the ones specific to this item).

### BUG-023 · Spell dictionary language taken from CLI arg, UI language from file
- Priority: P2 · Effort: S · Status: done
- Where: `validators/spell/spellchecker_validator.py:72` vs `helpers/tools/locale/language_manager.py:47-51`
- Problem: two sources of truth that can disagree (see BUG-004).
- Proposed fix: single `Locale` value in the context.
- Done: closed by construction as part of BUG-004. `SpellCheckerValidator` already read
  `self._data_models_context.context.data_args.data_file.locale` (the parsed `--locale` value)
  directly — unchanged by this fix — and `GeneralContext.language_manager` is now built from that
  exact same `data_args.data_file.locale` value (previously `LanguageManager` resolved its language
  independently from `.config/store.locale`, a second source that could disagree with the CLI arg).
  Both the spell-check dictionary language and the UI/report language now trace back to the single
  parsed `--locale` argument. No code change was needed in `spellchecker_validator.py`; verified by
  inspection and by
  `tests/unit/controllers/context/test_general_context.py::TestGeneralContextLocale`.

### BUG-024 · Typos in identifiers and filenames
- Priority: P3 · Effort: S · Status: done
- Where: `legend_processing.py:181` (`origina_value`), `data_args.py:204` ("validaton"),
  `file_system_utils.py:95` ("dempotent").
- Proposed fix: rename during the module migration; keep a compatibility import for one release.
- Partial (BUG-004 side effect): `language_manager.py`'s `_congifure_language` method (and its
  "Pipiline" comment) is deleted entirely, not renamed — it was the sole reader/writer of
  `.config/store.locale`, removed as part of closing BUG-004.
- Partial (ARC-017 Phase 3 Port 3 side effect): `validators/spreadsheets/composition/
  compostion_graph_validator.py` (the misspelled filename) and its sibling
  `composition_tree_validator.py` are both deleted — both legacy composition validators are
  replaced by `data_validate/rules/composition.py`, so the `compostion_` typo no longer exists
  anywhere in the tree. The remaining typos (`legend_processing.py:181`'s `origina_value`,
  `data_args.py:204`'s "validaton", `file_system_utils.py:95`'s "dempotent") are untouched — out
  of this item's scope.
- Done (Phase 5 slice, ARC-013's typo cleanup — closes this item): `legend_processing.py`'s
  `origina_value` local variable is renamed to `original_value` (pure internal variable name —
  the f-string it feeds, and thus every user-facing message, is byte-identical); `data_args.py`'s
  docstring "If any validaton rule fails." is fixed to "validation"; `file_system_utils.py`'s
  docstring "dempotent operation" is fixed to "Idempotent operation". No compatibility import was
  needed for any of the three — all three are internal variable/docstring text, not an
  importable symbol. **BUG-024 is now done.**

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

### BUG-028 · `to_decimal_truncated` skips truncation for scientific-notation floats
- Priority: P1 · Effort: S · Status: done
- Where: `data_validate/helpers/common/formatting/number_formatting_processing.py:31` (splits on a
  literal `"."`), consumer `helpers/common/validation/proportionality_processing.py:177`
- Problem: `str(1e-05) == "1e-05"` has no dot, so the value bypasses truncation entirely:
  `to_decimal_truncated(1e-05, "DI", 0)` returns `Decimal('0.00001')` instead of `Decimal('0')`.
  A very small proportionality weight silently escapes the 3-decimal precision rule and can shift
  sum-to-1 results.
- Evidence: strict xfail `tests/unit/helpers/common/formatting/test_number_formatting_properties.py::TestToDecimalTruncated::test_to_decimal_truncated_scientific_notation_bug_candidate`
  (found by hypothesis, TST-005).
- Proposed fix: quantize with `Decimal` (`Decimal(s).quantize(Decimal(10) ** -precision, rounding=ROUND_DOWN)`)
  instead of string surgery; flip the xfail to a passing test.
- Done: `to_decimal_truncated` now parses `Decimal(str(value).replace(",", "."))` and quantizes with
  `value_dec.quantize(Decimal(1).scaleb(-precision), rounding=ROUND_DOWN)` inside the existing
  try/except (`InvalidOperation`/`ValueError` → `Decimal("0")`), instead of splitting the string
  representation on a literal `"."`. `ROUND_DOWN` truncates toward zero, matching the prior
  "keep first N decimals" semantics for both positive and negative values (verified:
  `to_decimal_truncated(-0.129, "DI", 2) == Decimal('-0.12')`, same as the old string-slicing
  behaviour). Scientific-notation floats are now truncated correctly
  (`to_decimal_truncated(1e-05, "DI", 0) == Decimal('0')`); huge exponents (`1e+20`) quantize without
  raising and stay integral. `check_n_decimals_places` was verified to already handle scientific
  notation correctly (`Decimal("1e-05").as_tuple().exponent == -5`) — no change needed there. The
  strict xfail `test_to_decimal_truncated_scientific_notation_bug_candidate` now passes (marker
  removed) and a new `test_to_decimal_truncated_deterministic_cases` covers scientific notation,
  negative truncation, `Decimal` inputs, and huge exponents; `test_number_formatting.py` gained a
  matching table-driven `test_to_decimal_truncated`. Full unit suite green (1253 passed, 1 unrelated
  xfail from BUG-029), `make check` green, and the 7/7 e2e golden harness is unchanged
  (`git status --short tests/e2e/golden` empty) — no fixture carries a scientific-notation
  proportionality weight small enough to be affected.
- Related: PROP-* sum rules, PERF-003

### BUG-029 · `CSVReader` silently drops whitespace-only rows in single-column sheets
- Priority: P3 · Effort: S · Status: done
- Where: `data_validate/helpers/tools/data_loader/readers/csv_reader.py` (pandas default
  `skip_blank_lines=True`)
- Problem: in a single-column CSV a row whose sole cell is whitespace collides with blank-line
  skipping and disappears (`(1,1)` frame round-trips to `(0,1)`); row numbers reported to the user
  shift. Real bundles have ≥ 2 columns so impact is low, but `dicionario.csv` is single-column.
- Evidence: strict xfail `tests/unit/helpers/tools/data_loader/readers/test_csv_roundtrip_properties.py::TestCSVReaderSingleColumnBlankLineBugCandidate::test_single_column_whitespace_row_is_dropped`
  (found by hypothesis, TST-005).
- Proposed fix: `skip_blank_lines=False` in the reader (or in the Phase 2 `SheetLoader`) plus an
  explicit empty-row policy; flip the xfail.
- Done: `CSVReader._read_file` now reads with `skip_blank_lines=False`, so a whitespace-only cell in
  a single-column sheet (not itself an NA sentinel) survives instead of colliding with pandas' own
  blank-line detection (which strips whitespace before deciding a line is blank). The former xfail
  is now a plain passing test (`test_single_column_whitespace_row_is_kept`, class renamed to
  document the fix). Trade-off handled explicitly: turning off `skip_blank_lines` also makes a
  *genuinely* empty line (0 characters, e.g. a trailing newline at EOF) round-trip as an all-NaN
  row instead of being skipped — `_read_file` now pipes its result through a new
  `_drop_trailing_blank_rows` helper that trims only a **contiguous run of fully-NaN rows at the
  end** of the frame; an interior fully-NaN row (a blank line in the middle of a file) is left
  untouched, and any trailing row with at least one non-NaN cell (including a whitespace-only one)
  is never dropped. Documented in the module docstring. Checked against the e2e golden fixtures
  (`data/input/**`): every fixture bundle is `.xlsx` only, none are `.csv`, so this change has no
  effect on any golden — `make test-e2e` stays 7/7 and `git status --short tests/e2e/golden` is
  empty. Tests: `tests/unit/helpers/tools/data_loader/readers/test_csv_reader.py::
  TestDropTrailingBlankRows` (unit tests for the trimming helper: empty frame, no-blank-rows,
  trailing-only, interior-preserved, all-blank, partially-blank-trailing-row-kept),
  `tests/unit/helpers/tools/data_loader/readers/test_csv_roundtrip_properties.py::
  TestCSVReaderTrailingBlankLineNormalisation` (trailing empty line(s) dropped, interior blank line
  preserved, via real file round-trips) and the flipped
  `TestCSVReaderSingleColumnBlankLineBugCandidate` test; existing round-trip property tests
  (multi-column, NaN normalisation) re-verified unaffected.
- Related: BUG-015, ARC-009
