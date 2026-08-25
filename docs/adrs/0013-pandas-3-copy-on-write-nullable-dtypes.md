# ADR-0013: pandas 3 with Copy-on-Write and nullable/pyarrow dtypes as the DataFrame baseline

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`pyproject.toml` already declares `"pandas (>=3.0.1,<4.0.0)"` (line 23) as a runtime dependency —
pandas 3 ships with Copy-on-Write (CoW) semantics enabled unconditionally (it is no longer an
opt-in mode as it was in pandas 2.x). The current code, however, was written defensively against
pandas 1.x/2.x mutation semantics and has not been adapted to take advantage of CoW: `PERF-002`
documents full-frame `.copy()` calls scattered through the pipeline — `BaseValidator.__init__`
copies the entire raw frame per validator instance (`validators/spreadsheets/base/base_validator.py:80`,
`self._dataframe = self._data_model.data_loader_model.raw_data.copy() if self._data_model else
pd.DataFrame({})`), and `helpers/common/validation/dataframe_processing.py` and
`character_processing.py` copy at multiple additional call sites (lines 37, 45, 93, 103, 153, 156,
196, 203, 251) — copies that CoW makes unnecessary for read-only access, since pandas 3 defers the
actual copy until a mutation would otherwise be observed by another reference. Meanwhile, every
sheet is loaded as plain Python `str`/object dtype: `readers/csv_reader.py:23` passes
`dtype=str, low_memory=False`, and `readers/excel_reader.py:16` passes `dtype=str` — no
`pyarrow`-backed or nullable dtypes anywhere in the loading path (PERF-005). This all-object loading
forces the same cleaning work to happen repeatedly: `PERF-003` documents `DataCleaningProcessing.
clean_dataframe_integers` being invoked at ≥ 7 separate call sites across the codebase
(`models/sp_description.py`, `validators/spreadsheets/composition/compostion_graph_validator.py:379`,
`composition_tree_validator.py:179`, `validators/spreadsheets/legend/legend_validator.py:246,419`,
`validators/spreadsheets/proportionality/proportionality_validator.py:352`,
`validators/spreadsheets/value/value_validator.py:199,299`), each pass re-parsing the same `codigo`/
`nivel`-style columns cell-by-cell rather than once into a typed column. This repeated, untyped
cleaning is also the root cause of BUG-002 (models overwrite class-level `RequiredColumn` Series —
`setattr(self.RequiredColumn, "COLUMN_CODE", cleaned_series)` in `models/sp_description.py:251,263,277`
— because there is no per-instance, per-sheet typed frame to hold cleaned data instead) and BUG-014
(level comparisons against exact strings `"1"`/`"2"` silently failing on `"1.0"` or `" 1"`, because
nothing normalises the column to a typed integer once).

## Decision

Adopt pandas 3's Copy-on-Write behaviour as-is — it is already mandatory given the pinned
`pandas>=3.0.1` dependency, so this decision formalises *relying on it* rather than continuing to
work around pre-CoW assumptions. Each sheet is normalised **once**, in the `Normalizer` layer
(`.specs/architecture/target-architecture.md`), into an immutable `SheetFrame` carrying both the
never-mutated `raw: pd.DataFrame` and a `typed: pd.DataFrame` using nullable/`pyarrow`-backed dtypes
(`Int64`, `Float64`, `string[pyarrow]`) plus a per-column `invalid: Mapping[str, pd.Series]` boolean
mask recording which cells failed to convert — rules read the typed frame and the mask instead of
re-parsing text. Defensive `.copy()` calls at read sites (like `base_validator.py:80`) are removed;
a copy is taken only at genuine mutation points, which CoW makes safe and cheap by construction.
`BUG-002`'s class-level `Series` mutation is deleted in the same normalisation pass — cleaned data
lives on the instance-owned `SheetFrame`, never on a shared class attribute. `BUG-014`'s string-
literal level comparisons are replaced with comparisons against the typed integer column.

## Consequences

### Positive
- Removing defensive full-frame copies reduces peak memory and CPU for large sector bundles (the
  performance target in `05-performance.md` is 5 000 indicators × 60 columns in < 10 s), since CoW
  already guarantees safety for shared reads without an explicit `.copy()`.
- Cleaning each column exactly once (instead of ≥ 7 times per the PERF-003 evidence) turns an O(n ×
  passes) cost into O(n), and produces one reusable `invalid_mask` every rule can consult instead of
  re-deriving validity independently.
- Nullable/pyarrow dtypes give correct, vectorisable comparisons (`BUG-014`'s `"1.0"` vs `"1"`
  problem disappears once the column is genuinely `Int64`), and remove the class-level `Series`
  sharing bug (`BUG-002`) structurally, since there is no longer a class attribute to mutate.

### Negative
- Every existing validator that currently reads `self._dataframe` as raw strings must be ported to
  read the typed `SheetFrame` instead — a real migration cost, absorbed incrementally in Phase 2
  (`08-migration-roadmap.md`) alongside the `SheetSpec` (ADR-0003) and `Rule` (ADR-0006) work it
  depends on.
- `pyarrow`-backed string dtypes have some behavioural differences from plain object/`str` columns
  (e.g. certain string accessor edge cases, NA handling); this requires the golden harness (ADR-0002)
  to catch any resulting output difference before old cleaning code is deleted.

## Alternatives considered

### Keep object/`str` dtype end-to-end, keep ad hoc per-call-site cleaning
Rejected: this is the status quo the audit already flags as a performance and correctness problem
(PERF-003, PERF-005, BUG-002, BUG-014) — it does not use the pandas 3 dependency the project already
requires, and leaves the ≥ 7-pass repeated-cleaning cost and the class-level mutation bug in place.

### Adopt Polars as the primary DataFrame backend now, instead of pandas
Rejected for the current phase: pandas 3's CoW already resolves the specific defensive-copy problem
this ADR addresses, and the existing ecosystem this codebase depends on — `networkx` graph
construction from frames, the `python-calamine`/`pdfkit`/`babel` readers, and every existing
pandas-based test — is pandas-native; a full backend swap is a much larger, higher-risk change than
adopting the CoW/nullable-dtype features of the pandas version already pinned. Polars remains a
documented `.specs/future/ideas.md` candidate behind the `SheetFrame` abstraction this ADR
introduces, which is deliberately backend-agnostic in shape even though pandas is the chosen
implementation today.

### Pin pandas to the 2.x series and defer CoW adoption to a later phase
Rejected: `pyproject.toml` already requires `pandas>=3.0.1,<4.0.0`; pandas 3 does not offer an
"opt out of CoW" flag the way pandas 2.x did, so pinning to 2.x would be a downgrade that
contradicts the project's own already-declared dependency and would need to be reversed later
anyway — there is no version of "stay on pandas 2.x" that avoids eventually making this same
decision.

## Links

- Backlog: `PERF-002`, `PERF-003`, `PERF-005` (`05-performance.md`); `BUG-002`, `BUG-014`
  (`01-bugs.md`); `08-migration-roadmap.md` Phase 2
- Specs: `.specs/architecture/target-architecture.md` (`SheetFrame`, `Normalizer`),
  `.claude/rules/dataframe-conventions.md`
- Related ADRs: ADR-0003 (`SheetSpec`/`ColumnSpec` drive typed-column construction), ADR-0006 (rule
  purity assumes immutable typed frames)

---
Last synced with code: a4f76c7
