# 05 · Performance & scalability

Target: validate a sector bundle with 5 000 indicators × 60 value columns (≈ 300 k cells) in
< 10 s on a laptop, with memory < 1 GB, and scale linearly. Measure before/after with the benchmark
harness (PERF-009); never optimise without a number.

### PERF-001 · Row-by-row `iterrows()` / cell loops in hot paths
- Priority: P1 · Effort: M · Status: in-progress
- Where (re-verified by grep, Phase 5, 2026-09-13 — line numbers drifted from this item's
  original text, current file confirmed):
  `helpers/common/validation/legend_processing.py:208` (`validate_color_format`, LEG-008),
  `:255` (`validate_min_max_has_excessive_decimals`, LEG-009), `:315`/`:320`
  (`validate_min_max_values`, LEG-010, two loops: one read-only pass computing whether *any*
  slice in the group has excessive decimals, one stateful pass carrying `prev_max_val` between
  iterations to check interval continuity). All four are per-*legend-code-group* loops (one
  small group per `codigo`, typically single-digit-to-low-tens rows — a `legenda` sheet's total
  row count, not `valores`' ~300k-cell width) rather than a loop over the whole sheet; `LEG-001…
  011` are not yet ported to the rules engine (ARC-007/ARC-017 follow-up), so they were out of
  every prior port's scope, not overlooked.
  (`helpers/tools/spellchecker/dataframe_processor.py`'s two `.iterrows()`-shaped sites named in
  this item's original text are confirmed gone — PERF-006 replaced them with
  `Series.unique()`-deduplicated `.items()` loops over one row-per-*unique-text*, not one
  row-per-cell; `validators/spreadsheets/value/value_validator.py:316` and
  `helpers/common/validation/value_processing.py:125` removed — see the "Done (value slice)"
  note below; `validators/spreadsheets/legend/legend_validator.py:514-527` removed — see the
  "Done (legend slice)" note below; `validators/spreadsheets/proportionality/
  proportionality_validator.py:584` removed — see the "Done (proportionality slice)" note below.)
- Not done (Phase 5, 2026-09-13): the four `legend_processing.py` sites above were not vectorised
  in this slice — `validate_min_max_values`'s continuity check carries `prev_max_val` across
  iterations (an inherently sequential comparison against the *previous* row once sorted by
  `minimo`, not an independent per-row check), so vectorising it is a real, non-mechanical
  rewrite (a shifted-comparison via `Series.shift(1)` is the likely shape, not attempted here to
  avoid a rushed, undertested change to a still-error-reporting code path), not a drive-by
  change bundled with the ARC-005/i18n slice this round otherwise focused on for
  `legend_processing.py`. No fresh `tools/harness/profile_pipeline.py` measurement was taken for
  this specific residual (the existing PERF-002/PERF-003 budget numbers cover overall wall time,
  not this one function in isolation) — left honestly **in-progress**, not marked done or
  wont-fix without a number behind either claim (`.claude/rules/performance.md`).
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
- Done (composition slice, ARC-017 Phase 3 Port 3): every `iterrows()` site above previously
  attributed to composition is gone. `helpers/common/validation/graph_processing.py::
  create_graph_structure:57` now builds the whole edge list in one
  `nx.from_pandas_edgelist(...)` call instead of an `add_edge`-per-row loop (node ids via
  `.map(str)`, not `.astype(str)`, so `NaN` cells still stringify to `"nan"` and
  `parent_column == child_column` self-loops still work).
  `helpers/common/validation/tree_processing.py::create_tree_structure:37` now builds the
  adjacency dict via `groupby(..., sort=False)["child"].apply(list)` (`sort=False` preserves
  each parent's first-seen order, matching the old loop's insertion order exactly).
  `validate_level_hierarchy`/`validate_missing_codes_in_description` (the other three
  `tree_processing.py` iterrows sites, plus the dead helper never called by production code) are
  deleted outright: COMP-008's level-hierarchy check is now a `.map()`-based vectorised mask
  inline in `rules/composition.py::check_parent_level_below_child_level`, and
  `composition_tree_validator.py:242,253`'s two nested `iterrows()` loops (the file itself is
  deleted) are now `rules/composition.py::check_children_share_parent_level`, vectorised via
  `groupby`/`isin`/`.map()` (`.claude/skills/pandas-vectorization/SKILL.md` patterns 3/4).
  Regression/behaviour coverage: `tests/unit/rules/test_composition.py`,
  `tests/unit/helpers/common/validation/test_graph_processing.py`,
  `tests/unit/helpers/common/validation/test_tree_processing.py`.
- Done (value slice, ARC-017 Phase 3 Port 5): both `value_validator.py`/`value_processing.py`
  sites are gone — the files were deleted along with the rest of `SpValueValidator`/
  `ValueProcessing` when VAL-002…005 moved onto the rules engine.
  `value_validator.py:335`'s `for _, row in df_description.iterrows(): code = str(row[...]); ...`
  is now `rules/value.py::check_value_combination_relation`'s `zip()` over three plain lists
  extracted once via `.tolist()` (no `.iterrows()`, no per-row `Series` construction).
  `value_processing.py:125`'s `for index, value in dataframe[column].items(): ...` (cell by
  cell, `pd.to_numeric` per cell) is now `rules/value.py::_analyze_value_column`'s
  `pd.to_numeric(errors="coerce")` masks over the whole column at once, plus a `Series.map`
  that runs the `Decimal` exponent check once per *unique* candidate value instead of once per
  cell. Regression/behaviour coverage: `tests/unit/rules/test_value.py`.
- Done (legend slice, ARC-017 Phase 3 Port 6): `legend_validator.py:514-527`'s
  `for index, value_numeric in df_values_numeric[col].items(): ...` (cell by cell, per-cell
  min/max comparison) is gone — the file was deleted along with the rest of
  `SpLegendValidator`/`ModelMappingLegend` when LEG-012…015 moved onto the rules engine. It is
  now `rules/legend.py::check_value_range_within_legend`'s `out_of_range_mask` — one
  `pd.to_numeric(errors="coerce")` mask per matching `valores` column, built once, `~is_unavailable
  & numeric.notna() & ((numeric < min_value) | (numeric > max_value))` — the column-level
  indicator → legend → min/max mapping loop stays a Python `for` (it iterates over the handful of
  matching columns, not over rows, same as the legacy code). Regression/behaviour coverage:
  `tests/unit/rules/test_legend.py`.
- Done (proportionality slice, ARC-017 Phase 3 Port 7): `proportionality_validator.py:584`'s
  `for __, row in df_composition.iterrows(): parent = row[...]; child = row[...]; ...` (building a
  `codigo_pai -> [codigo_filho, …]` dict) is gone — the file was deleted along with the rest of
  `SpProportionalityValidator` when PROP-003…010 moved onto the rules engine. It is now
  `rules/proportionality.py::check_parent_child_relationships`'s
  `df_composition.groupby("codigo_pai", sort=False)["codigo_filho"].apply(list)`. Every other
  `ProportionalityProcessing` method (build_subdatasets, decimal truncation/summation, mask
  building) was already frame-level, not per-cell/per-row, and stays that way — only its
  message-building was removed (see `.specs/business-rules/proportionality.md`'s PROP-007…010
  entries). Regression/behaviour coverage: `tests/unit/rules/test_proportionality.py`,
  `tests/unit/helpers/common/validation/test_proportionality_processing.py`.

### PERF-002 · Defensive full-frame copies everywhere
- Priority: P1 · Effort: S · Status: done (with note — residual copies kept, budget-immaterial)
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
- Done (Phase 5 close, 2026-09-13 — with note): the two exact sites named above no longer exist —
  `base_validator.py` and `legend_validator.py` are both deleted (ARC-008/ARC-017 Phase 3 Port 8,
  Port 6 respectively; every validator was ported off `base_validator.py` and the legend copies
  went with `SpLegendValidator`). A fresh repo-wide grep (`grep -rn "\.copy(" data_validate/`)
  finds 23 remaining `.copy()` calls, all inside pure `helpers/common/{validation,processing}/*.py`
  frame-level functions (`dataframe_processing.py`, `character_processing.py`,
  `legend_processing.py`, `proportionality_processing.py`, `graph_processing.py`,
  `data_cleaning_processing.py`, `description_processing.py`) and
  `helpers/tools/spellchecker/spellchecker.py` — each is a defensive copy at the top of a function
  that goes on to build/mutate a *local* working frame, still reused by one or more `rules/*.py`
  modules per each port's own docstring (not dead code to delete outright). Measured cost: the
  PERF-009 budget run (6-indicator/5-year/3-scenario/5000-row bundle, ≈325k cells) completes in
  3.05s wall / 184MB peak RSS against a < 10s / < 1GB budget — a ≥3.2x time and ≥5.4x memory
  margin — so these 23 residual copies (each at most one extra frame-sized allocation, on sheets
  far smaller than the wide `valores` frame the budget number is dominated by) are not a threat to
  the budget at current or several-times-larger scale. Removing them fully would require auditing
  each function's internal mutation pattern one by one (a nontrivial, low-value refactor at this
  margin) rather than a drive-by deletion — left as accepted residual debt, not reopened as blocking.
  Revisit if a future profile shows frame copies as a material fraction of wall time/memory (see
  PERF-005's/PERF-007's revisit triggers for the same "budget breach or 10x data growth" bar).

### PERF-003 · The same columns are cleaned repeatedly
- Priority: P1 · Effort: M · Status: wont-fix (residual — measured budget-immaterial, see revisit trigger)
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
- Decision (Phase 5 close, 2026-09-13 — wont-fix, residual): note the table above already reviewed
  every call site named in this item's original "Where" (it predates the ARC-017 rule ports, so
  the file names are stale — `compostion_graph_validator.py`/`composition_tree_validator.py`/
  `legend_validator.py`/`proportionality_validator.py`/`value_validator.py` are all deleted; the
  same cleaning parameters and pipeline shapes now live in the corresponding `rules/*.py` modules,
  the table's per-site verdicts are unaffected by the file rename since the *reason* each site
  stays local — different `min_value`, or row-alignment with a locally-filtered frame — is a data
  shape argument, not a file-location one). Measured cost of leaving the ≥7 re-cleaning passes as
  they are: the PERF-009 budget run (≈325k cells) validates in 3.05s wall / 184MB peak RSS against
  a < 10s / < 1GB budget (≥3.2x/≥5.4x margin); `descricao.codigo` (the most-repeated column) is a
  single indicator-count-sized column re-cleaned a handful of times, not a `valores`-sized column,
  so its contribution to that 3.05s is not separately measurable above profiler noise in
  `tools/harness/profile_pipeline.py`'s existing trace (PERF-007's decision note). Building a
  proper per-sheet `Normalizer`/typed `SheetFrame` (this item's actual proposed fix) is Phase 2
  roadmap scope that was never done, and is not justified by the numbers above at current scale —
  **wont-fix for now**, matching PERF-007's precedent. Revisit trigger (shared with PERF-005): a
  future profile showing cleaning/normalisation as a material fraction of wall time, a budget
  breach, or roughly a 10x data-volume increase over the PERF-009 fixture.

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
- Priority: P2 · Effort: M · Status: wont-fix (for now, measured — see revisit trigger)
- Where: `readers/csv_reader.py:23` (`dtype=str, low_memory=False`), `readers/excel_reader.py:16`
  (`dtype=str`).
- Proposed fix: `dtype_backend="pyarrow"` / `pd.StringDtype("pyarrow")`; chunked validation for
  `valores` (row-independent rules can stream); optional Polars backend behind the `SheetFrame`
  Protocol for very large sectors.
- Related: SEC-003
- Decision (Phase 5 close, 2026-09-13): measured against the same PERF-009 budget bundle (≈325k
  cells, every cell a Python `str`): 3.05s wall, 184MB peak RSS versus the < 10s / < 1GB target —
  a ≥5.4x memory margin at the size this backlog's own budget defines as "large". Switching the
  reader dtype to `pyarrow`-backed strings or a Polars backend is a real, correctly-identified
  future lever, but implementing it now (a change that touches every reader, every model's
  cleaning code that assumes plain Python `str`/`object` columns, and the `SheetSpec` dtype
  declarations) is not justified by any measured pressure at the current or a several-times-larger
  bundle size — no evidence this backlog requires "why did you optimise a thing with no number
  behind it" (`.claude/rules/performance.md`). **Wont-fix for now**, not open, so it stops
  appearing as unaddressed migration debt. Revisit trigger: a real bundle breaches the < 10s / <
  1GB budget, or sector data grows roughly 10x past the PERF-009 fixture's ≈325k cells — re-run
  `make bench`/`tools/harness/profile_pipeline.py` and reopen with the new numbers before starting
  the `pyarrow`/Polars work, per the same discipline `PERF-007`'s wont-fix decision documents.

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
- Priority: P2 · Effort: L · Status: wont-fix (for now, measured — see revisit trigger)
- Where: `middleware/bootstrap.py:105-110` (thread pool for one task); rules run sequentially in
  `data_validate/rules/engine.py::Engine.run`.
- Proposed fix: once rules are pure (ARC-001/ARC-017 — now done), run independent rule groups with
  `concurrent.futures.ThreadPoolExecutor` (or a process pool); measure.
- Measured (PERF-009 slice): profiled `tools/harness/profile_pipeline.py` against the 6-indicator/
  5-year/3-scenario/5000-row budget bundle, plus a non-profiled wall-clock decomposition
  (`Engine.run` wrapped to time itself directly, avoiding `cProfile`'s per-call overhead). Rule
  execution (`Engine.run`, every registry) is ~27.6% of post-import wall time (0.571s/2.066s) and
  ~19% of full wall time including process start-up (0.571s/3.05s) — well under the "rules
  dominate" bar. The actual bottleneck is `_report`'s PDF generation (WeasyPrint import ~1.1s +
  render ~0.4s, ~57% of post-import time) and Python/pandas/networkx process start-up (~32% of
  full wall time), neither of which rule parallelism touches. Full table and top-5 cumulative
  functions: `.specs/quality/performance.md`'s "PERF-007 decision" section.
- Decision: **wont-fix for now** — implementing `Engine.run(ctx, parallel: bool = True)` would add
  thread-safety surface area (pandas/rule-function reentrancy, deterministic `EngineResult`
  ordering via gather-then-sort-by-registration-order) for a phase that measured at ~19-28% of
  wall time, not the dominant cost. Revisit if a future profile shows `Engine.run`'s own share
  crossing ~30% of total wall time (e.g. after PERF-002/PERF-003/PERF-005 shrink the
  loading/report share, or on a bundle with many more rule-bearing sheets/rows relative to
  `valores` column count) — re-run `tools/harness/profile_pipeline.py` and the table before
  reopening.

### PERF-008 · Start-up overhead
- Priority: P3 · Effort: S · Status: done
- Where: `config/metadata_info.py` (importlib metadata at import), `data_validate/__init__.py`
  (`__getattr__` indirection), heavy imports (`networkx`, `pdfkit`, `enchant`) at module import.
- Proposed fix: lazy import renderers/spell backend; `python -X importtime` budget in CI.
- Done (this slice — `pdfkit`/`enchant` only): measured with
  `poetry run python -X importtime -c "import data_validate.main"` (`awk`/`sort` on the trace).
  Before: `enchant` cumulative 5757 µs (`enchant._enchant` alone 3291 µs self / 3505 µs
  cumulative — the native libenchant/hunspell backend load), `pdfkit` cumulative 709 µs; total
  `data_validate.main` import ≈ 422.7 ms. `controllers/report/file_report_generator.py`'s
  top-level `import pdfkit` moved into `_save_pdf_file` (the only call site), and
  `helpers/tools/spellchecker/dictionary_manager.py`'s top-level `from enchant import Broker,
  Dict` became a `TYPE_CHECKING`-only import for the `Dict`/`Broker` type hints plus a local
  `from enchant import Broker` inside `validate_dictionary`/`initialize_dictionary` (the only two
  methods that construct a `Broker`). After: three consecutive
  `python -X importtime -c "import data_validate.main"` runs (373–499 ms total, pandas import
  jitter dominates the run-to-run variance) show **zero** `pdfkit`/`enchant` entries in the trace
  — confirmed by `grep -iE "pdfkit|enchant"` returning nothing on all three traces — so a run that
  never reaches PDF generation or spell-check no longer pays either import. `enchant`/`pdfkit`'s
  combined ~6.5 ms was already a small fraction (~1.5 %) of the ~423 ms baseline dominated by
  `pandas` (≈225 ms) and `networkx`/`rules`/`controllers` (≈121–200 ms combined); this item's
  `networkx` half and `config/metadata_info.py`'s importlib-metadata-at-import are deliberately
  left open (out of this slice's scope — the former needs `rules`' registries to stop importing
  it eagerly, the latter is a separate, larger change to `data_validate/__init__.py`'s
  `__getattr__` indirection). End-to-end PDF generation was re-verified unaffected: `poetry run
  canoa-data-validate --input_folder data/input/data_ground_truth_01 --output_folder ...` still
  produces both the HTML and PDF report, and all 7 `tests/e2e/test_golden.py` goldens stay green.
  Regression tests:
  `tests/unit/controllers/report/test_file_report_generator.py::TestLazyPdfkitImport::test_module_import_does_not_import_pdfkit`,
  `tests/unit/helpers/tools/spellchecker/test_dictionary_manager.py::TestLazyEnchantImport::test_module_import_does_not_import_enchant`
  and `::test_construction_does_not_import_enchant` (each spawns a fresh subprocess importing/
  constructing and asserts `'pdfkit'`/`'enchant'` are absent from `sys.modules`).

### PERF-009 · No benchmark or profiling harness
- Priority: P2 · Effort: M · Status: done
- Proposed fix: `tools/harness/generate_fixture.py --indicators 5000 --years 5 --scenarios 3`,
  `tools/harness/profile_pipeline.py` (cProfile + `pyinstrument` output to `dev-reports/`),
  `tests/benchmarks/test_bench_pipeline.py` with `pytest-benchmark` and a regression threshold.
- Done:
  - **`generate_fixture.py` correctness fix** (it existed but produced an *invalid* bundle,
    contradicting its own module docstring — every generated bundle failed real validation): (1)
    the root indicator (`codigo` 1, `nivel` 1) was getting `valores` columns generated for it,
    which VAL-003 always flags as unnecessary for a level-1 indicator — fixed by excluding the
    root from `_build_values` entirely; (2) `valores` column names were built from
    `referencia_temporal.nome` instead of `.simbolo` (VAL-003's `CombinationsProcessing.
    generate_combinations` uses `simbolo`) and `simbolo` itself was a 0-based offset instead of
    an actual calendar year, so TEMP-002 ("scenario years must be in the future") failed on every
    non-first row — fixed by anchoring `simbolo`/`nome` on `date.today().year` and using
    `simbolo` for column names; (3) every generated value was an out-of-`[0,1]`-range float
    (e.g. `1.0`, `2.0`, ...), and LEG-015's protocol-default legend range (`[0, 1]`, applied
    whenever no `legenda` sheet exists, which this harness never generates) flagged every one —
    fixed by generating 2-decimal string values in `[0.01, 1.00]`. Verified: a generated 20-
    indicator/3-year/2-scenario/5-row bundle now validates with **0 errors** (was 579 before the
    fix), and the 6-indicator/5-year/3-scenario/5000-row budget bundle also validates with 0
    errors (only 15 spell-check warnings, from the synthetic pt-BR text). Regression tests:
    `tests/unit/tools/harness/test_generate_fixture.py::TestBuildValues` (root exclusion,
    `simbolo`-not-`nome` column naming, scenario-suffix-only-after-the-first-year, 2-decimal
    `[0,1]`-range values).
  - **`generate_fixture.py` perf fix** (a genuine PERF-001-shaped bug in the harness itself, not
    the validated pipeline): building the wide `valores` frame via `pd.DataFrame(dict_of_lists)`
    left every column as its own single-column `ExtensionBlock` (pandas 3's default string dtype
    never consolidates object/string columns constructed this way into one 2-D block), so
    `to_csv` called `get_values_for_csv` once per column. At 5000 indicators x ~61 columns
    (≈305k columns) this made *generating* the fixture alone take ~48s (measured via `cProfile`,
    85s of which was inside `to_csv`'s per-block iteration). Fix: build one dense
    `np.ndarray(dtype=object)` up front (one assignment per column into a pre-allocated 2-D
    array) and hand pandas a single consolidated block via `pd.DataFrame(array, dtype="object")`
    — cuts the same generation to ~2.5s (~19x).
  - **`profile_pipeline.py` bug fix**: `profile_pipeline()` ran `data_validate.main` via
    `runpy.run_module(..., run_name="__main__")`, which always raises `SystemExit` (`main.py`'s
    own `if __name__ == "__main__": sys.exit(main())`) — uncaught, this `SystemExit` propagated
    straight out of `profile_pipeline()`, so the `.prof`/top-N text report were **never written**
    for any run (verified: `dev-reports/profile/` didn't exist anywhere in this repo's history
    before this fix). Fixed by catching `SystemExit` (only) around the `runpy.run_module` call.
    Regression tests: `tests/unit/tools/harness/test_profile_pipeline.py::
    TestProfilePipelineSystemExit` (artifacts written for exit codes 0/1/2; a non-`SystemExit`
    error still propagates and `sys.argv` is still restored).
  - **Corrected fixture sizing** (see `.specs/quality/performance.md`'s budget-table note): "5,000
    indicators" in this backlog and in `.claude/rules/performance.md` means 5,000 `valores`
    **rows** (territories), not 5,000 indicator codes as columns — `FileStructureValidator`'s own
    5,000-column structural size limit rejects the literal reading outright (confirmed: 5000
    indicator codes x 5 rows produces ~305k columns and 2 structural errors, no business rule
    ever runs). The budget fixture used throughout is 6 indicators (1 root + 5 children) x 5
    years x 3 scenarios (65 value columns) x 5000 rows (≈325k cells).
  - **`tests/benchmarks/test_bench_pipeline.py`**: `test_bench_full_pipeline` parametrised over
    `["small", "large"]` (`data_ground_truth_01` vs. the generated budget bundle, built once per
    session via a `large_fixture_dir` fixture), still skipped unless `--benchmark-only`;
    `test_large_bundle_validates_under_budget`, a plain (non-`pytest-benchmark`) timed assertion
    that the budget bundle validates in < 60s (measured ~3.05s — a ~20x CI margin), independent
    of `--benchmark-only`. Both marked `slow`.
  - **Measured numbers** (`make bench`, this machine): small (`data_ground_truth_01`) mean
    2.20s (min 2.13s, max 2.33s, 5 rounds); large (budget bundle) mean 2.71s (min 2.67s, max
    2.86s, 5 rounds). `/usr/bin/time -v` on the large bundle (single run, no `pytest-benchmark`
    overhead): 3.05s wall, 184 MB peak RSS — both well inside the < 10s / < 1GB budget. Full
    numbers and the profile-derived phase breakdown: `.specs/quality/performance.md`.
- Related: TST-005, PERF-007 (the profile this item produced is what PERF-007's wont-fix decision
  is based on)
