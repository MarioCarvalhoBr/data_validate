# Performance

## Budget

| Scenario | Target | Measured baseline |
|---|---|---|
| Reference bundle (`data/input/data_ground_truth_01`) | < 2 s wall, < 300 MB RSS | to be recorded by `make bench` in Phase 0 |
| Large sector: 5 000 indicators × 60 value columns (~300 k cells), 3 scenarios, 5 years | < 10 s wall, < 1 GB RSS | to be recorded (synthetic fixture) |
| Scaling | linear in cells; no quadratic loops over rows × columns | — |
| Start-up (`--version`) | < 300 ms | to be recorded (`python -X importtime`) |

No optimisation lands without a before/after number from the harness.

## Harness

| Tool | Purpose |
|---|---|
| `tools/harness/generate_fixture.py --indicators N --years Y --scenarios S --territories T --out DIR` | Deterministic synthetic bundle (seeded) that passes all rules; flags to inject defects |
| `tools/harness/profile_pipeline.py --input DIR [--pyinstrument]` | cProfile/pyinstrument run, writes `dev-reports/profile/<ts>.{prof,html}` and a top-20 table |
| `tests/benchmarks/test_bench_pipeline.py` (`pytest-benchmark`, marker `slow`) | Wall time and peak memory (`tracemalloc`) per fixture size; JSON stored in `dev-reports/bench/`; CI compares against `--benchmark-compare-fail=mean:20%` |
| `make bench`, `make profile` | Entry points |

## Known hot spots (from the audit)

| Area | Problem | Fix | Backlog |
|---|---|---|---|
| Rules | `iterrows()` / per-cell `pd.to_numeric` | vectorised masks, `merge`, `groupby` | PERF-001 |
| Validators/helpers | full-frame copies and `astype(str)` of whole frames | CoW, copy only when mutating, operate on object columns only | PERF-002 |
| Cleaning | `codigo` cleaned ≥ 7 times | normalise once into typed frame with invalid masks | PERF-003 |
| Config/i18n | `get_verify_names()` per validator, catalog JSON loaded 4–5× | cached in context | PERF-004 |
| Memory | `dtype=str` object columns | `string[pyarrow]`, chunked `valores` | PERF-005 |
| Spell | enchant call per token | unique texts + word cache | PERF-006 |
| Parallelism | none | independent rule groups in a process pool | PERF-007 |

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

Last synced with code: 09279f4
