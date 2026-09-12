# 05 · Performance & scalability

Target: validate a sector bundle with 5 000 indicators × 60 value columns (≈ 300 k cells) in
< 10 s on a laptop, with memory < 1 GB, and scale linearly. Measure before/after with the benchmark
harness (PERF-009); never optimise without a number.

### PERF-001 · Row-by-row `iterrows()` / cell loops in hot paths
- Priority: P1 · Effort: M · Status: open
- Where: `helpers/common/validation/tree_processing.py:37,73,75,117`,
  `helpers/common/validation/graph_processing.py:57`,
  `validators/spreadsheets/composition/composition_tree_validator.py:242,253`,
  `validators/spreadsheets/proportionality/proportionality_validator.py:584`,
  `validators/spreadsheets/value/value_validator.py:316`,
  `helpers/common/validation/legend_processing.py:202,249,313`,
  `helpers/common/validation/value_processing.py:125` (cell by cell, `pd.to_numeric` per cell),
  `validators/spreadsheets/legend/legend_validator.py:514-527` (cell by cell),
  `helpers/tools/spellchecker/dataframe_processor.py:42-45`.
- Proposed fix: vectorised masks (`pd.to_numeric(errors="coerce")`, `str.contains`, `isin`,
  `merge`), `nx.from_pandas_edgelist`, `groupby` aggregations; produce issues from mask indices.
- Done (description slice, ARC-017 Phase 3 Port 2): the two `description_validator.py` sites
  (`validate_html_in_descriptions:89`'s `for index, row in self._dataframe.iterrows(): re.search(...)`
  and `validate_indicator_levels:254`'s per-cell `NumberFormattingProcessing.check_cell_integer`
  loop) are gone — the file was deleted along with the rest of `SpDescriptionValidator` when
  DESC-001…010 moved onto the rules engine (`rules/description.py::check_html_in_simple_
  description` uses `Series.str.contains(r"<.*?>", regex=True, na=False)`;
  `check_indicator_levels` uses a `pd.to_numeric` mask reproducing `check_cell_integer`'s
  comma-decimal/integer/min-value semantics, per `.claude/skills/pandas-vectorization/SKILL.md`
  patterns 1/2). Regression/behaviour coverage: `tests/unit/rules/test_description.py`.

### PERF-002 · Defensive full-frame copies everywhere
- Priority: P1 · Effort: S · Status: open
- Where: `validators/spreadsheets/base/base_validator.py:80` (copy per validator),
  `helpers/common/validation/dataframe_processing.py:37,103,156,196,251`,
  `helpers/common/validation/character_processing.py:45,93,153,203`,
  `legend_validator.py:187-189,243-244,412-414`, `dataframe_processing.py:57` (`astype(str)` of the
  entire frame just to search for `|`).
- Proposed fix: immutable-by-convention frames (pandas 3 Copy-on-Write is on by default); copy only
  when mutating; search `|` only in object/string columns.
- Note (BUG-002/BUG-003 Phase 2c slice): `SpModelABC.frame` now gives every model an
  instance-owned, CoW-cheap working frame (aliases `data_loader_model.raw_data` until a subclass
  reassigns it via `.drop()`/`.assign()`, never mutates in place) — the underlying mechanism this
  item's "immutable-by-convention frames" fix needs already exists. `base_validator.py:80` and
  `legend_validator.py`'s three `.copy()` calls were deliberately *kept* in this slice (only their
  source switched from `data_loader_model.raw_data` to `self._data_model.frame`) per this item's
  own instruction to defer the copy removal; this item stays open for that follow-up.

### PERF-003 · The same columns are cleaned repeatedly
- Priority: P1 · Effort: M · Status: in-progress
- Where: `DataCleaningProcessing.clean_dataframe_integers` is called for `descricao.codigo` in
  `sp_description.py`, `compostion_graph_validator.py:379`, `composition_tree_validator.py:179`,
  `legend_validator.py:246,419`, `proportionality_validator.py:352`, `value_validator.py:199,299`
  (≥ 7 passes, each a Python loop with `check_cell_integer` per cell).
- Proposed fix: normalise once per sheet into typed nullable columns (`Int64`, `Float64`,
  `string[pyarrow]`) with an `invalid_mask` per column; rules read the typed frame.
- Related: BUG-002, BUG-014
- Reviewed (BUG-002/BUG-003 Phase 2c slice — "reuse `model.cleaned_column(...)` where a
  validator re-cleans with the same parameters as the model" candidates). Now that BUG-002 gives
  every model a `cleaned_column(name)` accessor, every remaining local
  `clean_dataframe_integers`/`clean_column_integer` call site in `validators/` was re-examined
  against the model's own cleaning parameters:

  | Call site | Column(s) | Local params | Model's own params | Decision |
  |---|---|---|---|---|
  | `compostion_graph_validator.py::_prepare_statement` (parent) | `codigo_pai` | `min_value=0` | `min_value=1` (`SpComposition`) | Keep local — parameters differ (admits the virtual root `0`) |
  | `compostion_graph_validator.py::_prepare_statement` (child) | `codigo_filho` | `min_value=1`, cleaned *after* the parent step on the already-parent-filtered frame | `min_value=1` (`SpComposition`) | Keep local — same `min_value`, but the local pipeline needs parent+child cleaned together on one index-aligned frame (`GraphProcessing` reads both columns off the same, sequentially-filtered `df_composition`); swapping in `cleaned_column("codigo_filho")` would mix two independently-filtered Series with different row sets |
  | `compostion_graph_validator.py::validate_unique_titles_with_graph` | `codigo` | `min_value=1` | `min_value=1` (`SpDescription`) | Keep local — same `min_value`, but the result is used as a column *inside* `df_description` (subtree filtering + title-uniqueness columns), and `clean_dataframe_integers` also *drops* invalid rows; reusing `cleaned_column("codigo")` would require re-deriving which rows of `df_description` survived cleaning, not just swapping a Series |
  | `value_validator.py::validate_relation_indicators_in_values` | `codigo` | default `min_value=0` (not passed) | `min_value=1` (`SpDescription`) | Keep local — parameters differ |
  | `value_validator.py::validate_value_combination_relation` | `codigo`, `nivel`, (`cenario` if scenarios exist) | default `min_value=0` for all three | `min_value=1`/`1`/`-1` respectively (`SpDescription`) | Keep local — parameters differ |
  | `value_validator.py::validate_value_combination_relation` | `simbolo` | default `min_value=0` | `min_value=0` (`SpTemporalReference`), but only when scenarios exist/row count ≠ 1 — the "single row, no scenarios" branch takes `.iloc[0:1]` with **no** integer validation at all | Keep local — same nominal `min_value`, but the model's `cleaned_column("simbolo")` is not always validated (see BUG-002's `SpTemporalReference` note); the validator's own always-validates |
  | `legend_validator.py` (×2, `codigo`) | `codigo` | `min_value=1` (matches) | `min_value=1` (`SpDescription`) | Keep local — same `min_value`, but the result feeds `.groupby`/`.dropna` pipelines built on the locally-cleaned+filtered frame, not a bare Series |

  No call site was changed: every one either uses different cleaning parameters than the model,
  or depends on `clean_dataframe_integers`'s row-dropping/index-alignment semantics that a bare
  `cleaned_column(...)` Series (cleaned independently, no row alignment guarantee with the local
  frame) cannot safely replace without a larger refactor of the call site's surrounding pipeline.
  This item stays in-progress: the `cleaned_column()` accessor this optimisation needs now exists
  (BUG-002), but applying it safely to any of the sites above is follow-up work, not a drive-by
  change bundled with BUG-002/BUG-003.

### PERF-004 · Repeated translation / config work
- Priority: P2 · Effort: S · Status: done
- Where: `ApplicationConfig.get_verify_names()` (called in `base_validator.py:81` per validator and
  `file_report_generator.py:130-132` twice more) → previously 34 catalog lookups on *every* call;
  `LanguageManager` JSON loaded in 4–5 places per run (ARC-002, unrelated, still open).
- Fix shipped: `get_verify_names()` computes the `MappingProxyType` once and caches it on
  `self._verify_names_cache`; every call after the first returns the cached mapping with zero
  additional `LanguageManager.text()` calls. Regression test:
  `tests/unit/config/test_application_config.py::TestApplicationConfigClock::test_get_verify_names_caches_after_first_call`
  asserts exactly 34 total `text()` calls across two `get_verify_names()` invocations (would be 68
  without the cache).

### PERF-005 · Memory: everything loaded as Python `str` objects
- Priority: P2 · Effort: M · Status: open
- Where: `readers/csv_reader.py:23` (`dtype=str, low_memory=False`), `readers/excel_reader.py:16`
  (`dtype=str`).
- Proposed fix: `dtype_backend="pyarrow"` / `pd.StringDtype("pyarrow")`; chunked validation for
  `valores` (row-independent rules can stream); optional Polars backend behind the `SheetFrame`
  Protocol for very large sectors.
- Related: SEC-003

### PERF-006 · Spell-check calls enchant per token without caching
- Priority: P2 · Effort: S · Status: done
- Where: `helpers/tools/spellchecker/spellchecker_controller.py:26-35`, `dataframe_processor.py:42-45`
- Proposed fix: deduplicate texts (`Series.unique()`), tokenise once, `lru_cache` on
  `dictionary.check`; typical sheets have < 5 k unique words.
- Done: `SpellCheckerController` gained an explicit `self._check_cache: dict[str, bool]`
  consulted/populated in `find_spelling_errors` (not `functools.lru_cache` — the dictionary
  instance is per-run session state, not a pure function to memoise) plus a
  `evaluate_text_quality(text) -> (has_multiple_spaces, spelling_errors)` /
  `format_quality_warnings(...)` split so the row-independent signals are cacheable while
  `check_text_quality`'s row-specific message formatting is unchanged. `DataFrameProcessor
  .process_dataframe` now calls `evaluate_text_quality` once per `Series.unique()` text per
  column and maps the cached result back to every row via `format_quality_warnings`, keeping
  today's per-row messages, "linha N" numbering, and ordering identical. Measured with a
  counting fake replacing `enchant.Dict.check` over a synthetic 2 000-row × 2-column frame of
  repeated pt-BR sentences (4 unique texts): 46 000 → 41 `Dict.check` calls (~1122×), wall time
  0.1692 s → 0.0041 s (~41×) for `check_spelling_text`/`process_dataframe`. Regression tests:
  `tests/unit/helpers/tools/spellchecker/test_spellchecker_controller.py::TestSpellCheckerControllerCaching`
  (counting-fake call-count assertions) and
  `tests/unit/helpers/tools/spellchecker/test_dataframe_processor.py::TestDataFrameProcessorDeduplication`
  (dedup call counts + a real-controller test proving per-row "linha N" messages and order are
  unchanged for duplicate/multi-space texts).

### PERF-007 · No real parallelism where it matters
- Priority: P2 · Effort: L · Status: open
- Where: `middleware/bootstrap.py:105-110` (thread pool for one task); rules run sequentially in
  `spreadsheet_processor.py:200-215`.
- Proposed fix: once rules are pure (ARC-001/ARC-017), run independent rule groups with
  `concurrent.futures.ProcessPoolExecutor` (or threads with Arrow/NumPy releasing the GIL); measure.

### PERF-008 · Start-up overhead
- Priority: P3 · Effort: S · Status: open
- Where: `config/metadata_info.py` (importlib metadata at import), `data_validate/__init__.py`
  (`__getattr__` indirection), heavy imports (`networkx`, `pdfkit`, `enchant`) at module import.
- Proposed fix: lazy import renderers/spell backend; `python -X importtime` budget in CI.

### PERF-009 · No benchmark or profiling harness
- Priority: P2 · Effort: M · Status: open
- Proposed fix: `tools/harness/generate_fixture.py --indicators 5000 --years 5 --scenarios 3`,
  `tools/harness/profile_pipeline.py` (cProfile + `pyinstrument` output to `dev-reports/`),
  `tests/benchmarks/test_bench_pipeline.py` with `pytest-benchmark` and a regression threshold.
- Related: TST-005
