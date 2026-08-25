# 05 · Performance & scalability

Target: validate a sector bundle with 5 000 indicators × 60 value columns (≈ 300 k cells) in
< 10 s on a laptop, with memory < 1 GB, and scale linearly. Measure before/after with the benchmark
harness (PERF-009); never optimise without a number.

### PERF-001 · Row-by-row `iterrows()` / cell loops in hot paths
- Priority: P1 · Effort: M · Status: open
- Where: `validators/spreadsheets/description/description_validator.py:89,254`,
  `helpers/common/validation/tree_processing.py:37,73,75,117`,
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

### PERF-002 · Defensive full-frame copies everywhere
- Priority: P1 · Effort: S · Status: open
- Where: `validators/spreadsheets/base/base_validator.py:80` (copy per validator),
  `helpers/common/validation/dataframe_processing.py:37,103,156,196,251`,
  `helpers/common/validation/character_processing.py:45,93,153,203`,
  `legend_validator.py:187-189,243-244,412-414`, `dataframe_processing.py:57` (`astype(str)` of the
  entire frame just to search for `|`).
- Proposed fix: immutable-by-convention frames (pandas 3 Copy-on-Write is on by default); copy only
  when mutating; search `|` only in object/string columns.

### PERF-003 · The same columns are cleaned repeatedly
- Priority: P1 · Effort: M · Status: open
- Where: `DataCleaningProcessing.clean_dataframe_integers` is called for `descricao.codigo` in
  `sp_description.py`, `compostion_graph_validator.py:379`, `composition_tree_validator.py:179`,
  `legend_validator.py:246,419`, `proportionality_validator.py:352`, `value_validator.py:199,299`
  (≥ 7 passes, each a Python loop with `check_cell_integer` per cell).
- Proposed fix: normalise once per sheet into typed nullable columns (`Int64`, `Float64`,
  `string[pyarrow]`) with an `invalid_mask` per column; rules read the typed frame.
- Related: BUG-002, BUG-014

### PERF-004 · Repeated translation / config work
- Priority: P2 · Effort: S · Status: open
- Where: `ApplicationConfig.get_verify_names()` called in `base_validator.py:81` (per validator) and
  `file_report_generator.py:130-132` (twice more) → 35 catalog lookups each; `LanguageManager` JSON
  loaded in 4–5 places per run (ARC-002).
- Proposed fix: compute titles once in the context; `functools.cached_property`.

### PERF-005 · Memory: everything loaded as Python `str` objects
- Priority: P2 · Effort: M · Status: open
- Where: `readers/csv_reader.py:23` (`dtype=str, low_memory=False`), `readers/excel_reader.py:16`
  (`dtype=str`).
- Proposed fix: `dtype_backend="pyarrow"` / `pd.StringDtype("pyarrow")`; chunked validation for
  `valores` (row-independent rules can stream); optional Polars backend behind the `SheetFrame`
  Protocol for very large sectors.
- Related: SEC-003

### PERF-006 · Spell-check calls enchant per token without caching
- Priority: P2 · Effort: S · Status: open
- Where: `helpers/tools/spellchecker/spellchecker_controller.py:26-35`, `dataframe_processor.py:42-45`
- Proposed fix: deduplicate texts (`Series.unique()`), tokenise once, `lru_cache` on
  `dictionary.check`; typical sheets have < 5 k unique words.

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
