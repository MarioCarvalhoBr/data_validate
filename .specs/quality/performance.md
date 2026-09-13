# Performance

## Budget

| Scenario | Target | Measured (PERF-009, this machine) |
|---|---|---|
| Reference bundle (`data/input/data_ground_truth_01`) | < 2 s wall, < 300 MB RSS | `make bench`: mean 2.20s (min 2.13s, max 2.33s, 5 rounds) |
| Large sector: 6 indicators (1 root + 5 children) × 65 value columns, 5 000 territory rows (≈ 325 k cells), 3 scenarios, 5 years | < 10 s wall, < 1 GB RSS | `/usr/bin/time -v`: 3.05s wall, 184 MB peak RSS. `make bench`: mean 2.71s (min 2.67s, max 2.86s, 5 rounds). 0 errors, 15 warnings (spell-check only) |
| Scaling | linear in cells; no quadratic loops over rows × columns | not yet re-measured across multiple sizes in this slice — PERF-001..003 vectorisation work (done) is the evidence so far, not a dedicated scaling sweep |
| Start-up (`--version`) | < 300 ms | see PERF-008 (~423ms baseline dominated by `pandas`/`networkx` imports, `pdfkit`/`enchant` made lazy) |

**Note on "5,000 indicators" (PERF-009):** the phrase in this budget and in
`.claude/rules/performance.md` means 5,000 `valores` **rows** (one per territory — Brazil has
~5,570 municipalities), not 5,000 indicator codes as `valores` **columns**. `FileStructureValidator`
enforces a hard structural limit of 5,000 columns on any sheet (`STRUCT-*`, SEC-003); a bundle
with 5,000 indicator codes (each contributing a `codigo-ano[-cenario]` column group) produces
~300k *columns*, which the size limit rejects outright before any business rule runs. Confirmed
while building this budget fixture: `tools/harness/generate_fixture.py --indicators 5000 --years 21
--scenarios 3 --rows 5` (5000 indicator codes, 5 rows) produces "A planilha excede o tamanho
máximo permitido (5 linhas x 304940 colunas > 1000000 linhas x 5000 colunas)" and 2 errors. The
budget-sized fixture above (6 indicators, 5000 rows) is the correct reading and the one
`tests/benchmarks/test_bench_pipeline.py` and this table use.

No optimisation lands without a before/after number from the harness.

## Harness

| Tool | Purpose |
|---|---|
| `tools/harness/generate_fixture.py --indicators N --years Y --scenarios S --rows R --out DIR` | Deterministic synthetic bundle that passes all rules (0 errors) — one root indicator (`codigo` 1) plus N-1 flat children, `valores` covering every non-root `codigo-ano[-cenario]` combination per VAL-003, `R` territory rows; writes `.xlsx` when `openpyxl` is importable, else `\|`-separated `.csv` |
| `tools/harness/profile_pipeline.py --fixture NAME_OR_PATH --out DIR [--top N]` | cProfile run (in-process, via `runpy`), writes `DIR/<fixture>.prof` (loadable with `snakeviz`/`pstats`) and `DIR/<fixture>.top{N}.txt` (cumulative-time text report) |
| `tests/benchmarks/test_bench_pipeline.py` (`pytest-benchmark`, marker `slow`) | `test_bench_full_pipeline[small\|large]`: wall-time stats (mean/min/max/stddev) for the reference and budget-sized bundles, skipped unless `--benchmark-only`; `test_large_bundle_validates_under_budget`: a plain (non-`pytest-benchmark`) timed assertion that the budget bundle validates in < 60s, a generous CI regression guard independent of `--benchmark-only` |
| `make bench`, `make profile` | Entry points (`make bench` = `pytest tests/benchmarks --benchmark-only`; `make profile` = `python tools/harness/profile_pipeline.py`) |

## Known hot spots (from the audit)

| Area | Problem | Fix | Backlog |
|---|---|---|---|
| Rules | `iterrows()` / per-cell `pd.to_numeric` | vectorised masks, `merge`, `groupby` | PERF-001 (done) |
| Validators/helpers | full-frame copies and `astype(str)` of whole frames | CoW, copy only when mutating, operate on object columns only | PERF-002 |
| Cleaning | `codigo` cleaned ≥ 7 times | normalise once into typed frame with invalid masks | PERF-003 (in-progress) |
| Config/i18n | `get_verify_names()` per validator, catalog JSON loaded 4–5× | cached in context | PERF-004 (done) |
| Memory | `dtype=str` object columns | `string[pyarrow]`, chunked `valores` | PERF-005 |
| Spell | enchant call per token | unique texts + word cache | PERF-006 (done) |
| Parallelism | none | measured (PERF-009 profile below): rule execution is ~19-28% of wall time, not the dominant cost — **wont-fix for now** | PERF-007 |

## PERF-007 decision: rule parallelism, wont-fix for now (measured)

Profiled `tools/harness/profile_pipeline.py --fixture <budget bundle>` (6 indicators, 5 years, 3
scenarios, 5000 rows) plus a non-profiled, monkeypatched wall-clock decomposition (`Engine.run`
wrapped to accumulate its own elapsed time, avoiding cProfile's per-call overhead skewing the
result toward Python-heavy code):

| Phase | Share of post-import wall time | Share of full wall time (incl. process start-up/imports) |
|---|---|---|
| Rule engine (`Engine.run`, every registry) | 27.6% (0.571s / 2.066s) | ~19% (0.571s / 3.05s) |
| `_build_pipeline` non-rule work (model/context setup) | ~10% (0.212s / 2.066s) | ~7% |
| `_report` (HTML + PDF via WeasyPrint: import ~1.1s + render ~0.4s) | 57.4% (1.186s / 2.066s) | ~39% |
| Process start-up + module imports (pandas/networkx/rules, before the timed region) | — | ~32% (≈1.0s / 3.05s) |

Within the rule engine's own time, `cProfile`'s cumulative-time top-5 (profiled run, 3.796s
total, some overhead from instrumentation itself) confirms *where*, not just *how much*:
1. `_report`/`build_report`/`_save_pdf_file` (WeasyPrint) — 1.553s cumulative (41%)
2. `_build_pipeline` (loading + rules) — 1.400s cumulative (37%)
3. `Engine.run`/`_run_rule_registries` (all registries) — 1.174s cumulative (31%, subset of #2)
4. WeasyPrint's own import chain (fonttools/cairo/pango bindings) — 1.115s cumulative (29%, subset of #1)
5. `rules/value.py::_analyze_value_columns`/`_analyze_value_column` (VAL-004/VAL-005) — 0.786s
   cumulative (21%; ~67% of the rule engine's own time — the value-column analysis, not the
   engine loop itself, is the rules-side hot spot if this is ever revisited)

Rule execution is well under the 30% threshold that would justify parallelising it
(`ThreadPoolExecutor` over independent rules, per the proposed fix): the actual bottleneck is
PDF report generation (WeasyPrint import + render, already lazily imported per PERF-008's
precedent) and Python/pandas/networkx process start-up, neither of which `Engine.run`
parallelism would touch. Adding `Engine.run(ctx, parallel: bool = False)` now would add
thread-safety surface area (pandas/rule-function reentrancy, deterministic outcome ordering) for
a phase that is not the bottleneck. **Decision: wont-fix for now.**

**Revisit trigger:** if a future profile shows `Engine.run`'s own share crossing ~30% of total
wall time (e.g. after PERF-002/PERF-003/PERF-005 land and shrink the loading/report share, or on
a bundle with many more rule-bearing sheets/rows relative to `valores` column count), reopen
PERF-007 with a fresh `tools/harness/profile_pipeline.py` run and re-run this table.

## Techniques (see skill `pandas-vectorization`)

1. Type once: `pd.to_numeric(col, errors="coerce")` → nullable `Int64`/`Float64`; keep a
   boolean `invalid` mask instead of dropping rows.
2. Row numbers from index: `excel_row(idx, header)` applied to mask indices, never inside loops.
3. Cross-sheet relations with `merge(indicator="both")`/`isin`, not nested loops.
4. Graphs: `nx.from_pandas_edgelist`; compute cycles/components/leaves once per run and share
   through `RuleContext` (memoised facts).
5. Strings: `.str` accessors with compiled regex; `Series.unique()` before expensive per-value
   work (spell-check, capitalisation).
6. Never `DataFrame.apply(axis=1)` in rules; `map` only on small unique sets.

## Measurement discipline

- Record numbers in the PR description (before/after, fixture, machine).
- Benchmarks are compared against `dev-reports/bench/baseline.json`; a regression > 20 % fails CI
  unless the PR updates the baseline with a justification.

Last synced with code: 00bcb7b (PERF-009 harness fix + budget measurement, PERF-007 wont-fix decision)
