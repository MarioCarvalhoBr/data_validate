# ADR-0003: Single `SheetSpec` registry as the source of truth for sheet definitions

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

Sheet definitions — which files exist, whether they are required, their header layout, CSV
separator and column set — are currently declared in **three places that can and do disagree**
(ARC-003):

1. `data_validate/config/spreadsheet_info.py` — the `SpreadsheetInfo` class (module singleton
   `SHEET = SpreadsheetInfo()` at line 53) declares `SP_NAME_*` string constants, `ALLOWED_EXTENSIONS
   = [".csv", ".xlsx"]` (line 30), and `EXPECTED_FILES` / `OPTIONAL_FILES` dicts (lines 34-47)
   mapping each sheet name to that same two-extension list.
2. `data_validate/helpers/tools/data_loader/common/config.py` — the `Config` singleton
   (`SingletonMeta`, lines 9-38) declares `file_specs`, a dict of
   `nome_base: (obrigatório: bool, tipo_cabeçalho, separador_csv)` tuples (lines 25-34), **and**
   `self.extensions = [".csv", ".xlsx", ".qml"]` (line 35) — a third extension, `.qml`, that
   `SpreadsheetInfo.ALLOWED_EXTENSIONS` does not know about, which is exactly the mismatch BUG-015
   documents (`engine/scanner.py:27-33` lets CSV silently win over XLSX while
   `FileStructureValidator.check_ignored_files_in_folder_root` reports the same situation as an
   error using the *other* source's extension list).
3. Each model's nested `INFO` class — e.g. `models/sp_description.py:52`,
   `self.SP_NAME = SHEET.SP_NAME_DESCRIPTION` inside `CONSTANTS = INFO()` (line 58) — re-derives the
   sheet name from `SpreadsheetInfo` but then independently declares its own `RequiredColumn` /
   `OptionalColumn` / `DynamicColumn` enums with column names, types and defaults that exist nowhere
   in either `SpreadsheetInfo` or `Config.file_specs`.

No test or type checks these three sources for consistency; drift is discovered only by symptom
(BUG-015, BUG-013 — wrong dtypes/names, e.g. `models/sp_scenario.py:66` declaring `COLUMN_NAME` as
`int64` for a text column).

## Decision

Introduce a single registry, `data_validate/specs/sheets.py`, as described in
`.specs/architecture/target-architecture.md`: frozen dataclasses `ColumnSpec` (`name`, `kind`,
`required`, `min_value`, `allow_empty`, `pattern`) and `SheetSpec` (`key`, `required`, `header`
[`"single"|"double"`], `csv_separator`, `columns`, `dynamic_columns`, `optional_columns`), collected
in `SHEETS: Mapping[str, SheetSpec]`. This becomes the **only** place a sheet name, required flag,
header layout, separator or column set is declared. `SpreadsheetInfo`, `Config.file_specs` and each
model's `RequiredColumn`/`OptionalColumn`/`DynamicColumn` enums are deleted (Phase 1,
`08-migration-roadmap.md`); the loader (`SheetLoader`), the normalizer, the file-structure rules
(`STRUCT-*`) and `.specs/business-rules/README.md`'s generated tables all derive their behaviour
from `SHEETS` instead of duplicating it. The `.qml` extension is dropped from the registry unless
the protocol is confirmed to require it; if evidence is found that it's needed, the question is
tracked in `.specs/future/open-questions.md` rather than silently reintroduced.

## Consequences

### Positive
- One place to add or change a sheet: the loader, the normalizer, the structural checks and the
  generated docs all stay consistent by construction instead of by convention.
- BUG-015's silent CSV-over-XLSX/`.qml` inconsistency and BUG-013's dtype mismatches become
  impossible to reintroduce — there is no second place to declare a conflicting definition.
- `SheetSpec` is a plain, typed, testable value object: `mypy --strict` can verify every rule and
  loader function against it, and unit tests can construct in-memory `SheetSpec` fixtures without
  touching the filesystem.

### Negative
- A large, mechanical migration is required to move every current `RequiredColumn`/`OptionalColumn`
  definition (8 models × 3-4 column groups each) into `ColumnSpec` tuples; risk of transcription
  errors is mitigated by the golden harness (ADR-0002) catching any resulting behaviour change.
- Until Phase 2 completes, some legacy code still reads `SpreadsheetInfo`/`Config` — the registry
  and the legacy sources must be kept in sync for one phase, a temporary duplication accepted as
  the cost of an incremental (non-big-bang) migration.

## Alternatives considered

### Keep the three existing sources and add a consistency test between them
Rejected: this treats the symptom, not the cause — a passing "sources agree" test still leaves
three places to edit for every new sheet or column, and the current `.qml` drift shows that even a
simple two-source mismatch went unnoticed for an unknown amount of time; a single source removes
the possibility of drift rather than detecting it after the fact.

### External YAML/JSON sheet-spec file loaded at runtime
Rejected: an externally editable spec file adds a parsing/validation layer, loses static typing and
IDE/mypy support for column names used throughout the rule code, and does not fit the project's
own target of "immutable, typed" data (`CLAUDE.md` pillar 3); the protocol (v1.13) is not expected
to change per-deployment, so runtime configurability solves a problem this project doesn't have.

### Let each model self-declare its spec, aggregated into a registry built from model classes
Rejected: this is closer to the status quo (option 3 above) and keeps the coupling ARC-007 already
flags between "models validate, clean, and mutate" — models are being retired as classes in favour
of `SheetSpec` + `Normalizer` (target-architecture.md's module map), so building the registry *from*
model classes would recreate the dependency the migration is trying to remove.

## Links

- Backlog: `ARC-003` (`03-architecture.md`); `BUG-013`, `BUG-015` (`01-bugs.md`);
  `08-migration-roadmap.md` Phase 1 item 1
- Specs: `.specs/architecture/target-architecture.md` (`ColumnSpec`/`SheetSpec` definitions),
  `.specs/business-rules/README.md`
- Related ADRs: ADR-0002, ADR-0004, ADR-0009 (both retire duplicated per-sheet metadata)

---
Last synced with code: a4f76c7
