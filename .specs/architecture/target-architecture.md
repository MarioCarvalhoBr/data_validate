# Target architecture

Design goal: pure rules over immutable typed sheets, explicit dependencies, structured issues,
one source of truth for sheet definitions, zero global state, renderers as plugins. The migration
path is in `../quality/backlog/08-migration-roadmap.md`; decisions are recorded as ADRs 0002–0008
and 0013.

## Layers

```mermaid
flowchart TD
  CLI[cli<br/>argument parsing, exit codes, output selection] --> APP[app<br/>AppContext, Pipeline, options]
  APP --> LOAD[loading<br/>SheetLoader, readers]
  APP --> MODELS["models/ (normalizing layer — ADR-0015)<br/>SpModelABC subclasses: structural checks + typed cleaning"]
  APP --> ENGINE[rules<br/>registry, engine, rule modules per sheet]
  APP --> REP[reporting<br/>ReportModel, renderers html/json/console/pdf]
  LOAD --> SPECS[specs<br/>SheetSpec, ColumnSpec, registry]
  MODELS --> SPECS
  ENGINE --> SPECS
  ENGINE --> I18N[i18n<br/>MessageCatalog]
  REP --> I18N
  ENGINE --> SPELL[spell<br/>SpellBackend protocol, enchant, pure-python]
  LOAD --> UTIL[util<br/>paths, clock, logging, numbers]
  MODELS --> UTIL
  ENGINE --> UTIL
  REP --> UTIL
```

**ARC-007 (Phase 5, 2026-09-13, ADR-0015)**: the standalone `normalizing/` package/`Normalizer`
class this diagram originally sketched (see the commented-out dataclass/Protocol in "Core
interfaces" below) is descoped, not implemented — `models/sp_*.py` plays that role today by
design: one `SpModelABC` subclass per sheet owns both the structural check and the typed-cleaning
pass (`self.cleaned`/`cleaned_column()`), and every rule reads the resulting typed columns through
`RuleContext` without re-parsing them. A second, parallel abstraction over the same
responsibility was not justified once ARC-005 (catalog-only messages) and the ARC-017 rule ports
were both done — see ADR-0015 for the full rationale.

Allowed imports (enforced by `.claude/rules/architecture-boundaries.md` and a future
import-linter contract): `cli → app`; `app → loading, models, rules, reporting`;
`loading/models/rules/reporting → specs, i18n, util`; `rules → spell`; `specs, i18n, util,
spell` import nothing from the other layers.

Package layout:

```
data_validate/
  cli.py                 # entry point `canoa-data-validate`
  app/                   # AppContext, Options, Pipeline, ValidationResult
  specs/                 # SheetSpec registry (the only place sheet names/columns/headers live)
  loading/               # SheetLoader, readers (csv, xlsx), LoadResult
  models/                # SpModelABC subclasses — the normalizing layer (ADR-0015); no separate
                          # normalizing/ package
  rules/                 # engine.py, registry.py, <sheet>/<RULE_ID>.py
  reporting/             # ReportModel, html.py, json.py, console.py, pdf.py (optional extra)
  i18n/                  # MessageCatalog, locales/*.json
  spell/                 # SpellBackend, EnchantBackend, PurePythonBackend
  util/                  # clock, paths, numbers, logging
  static/                # templates, css, dictionaries
```

## Core interfaces

```python
# specs
@dataclass(frozen=True)
class ColumnSpec:
    name: str                      # "codigo"
    kind: Literal["int", "float", "str", "pattern"]
    required: bool = True
    min_value: int | None = None
    allow_empty: bool = False
    pattern: str | None = None     # e.g. r"^\d+-\d{4}(-(?P<scenario>\w+))?$"

@dataclass(frozen=True)
class SheetSpec:
    key: str                       # "descricao"
    required: bool
    header: Literal["single", "double"]
    csv_separator: str = "|"
    columns: tuple[ColumnSpec, ...] = ()
    dynamic_columns: tuple[ColumnSpec, ...] = ()   # present only with scenarios/legend
    optional_columns: tuple[ColumnSpec, ...] = ()

SHEETS: Mapping[str, SheetSpec]   # registry; FileStructure rules, loader and normalizer derive from it

# loading
@dataclass(frozen=True)
class LoadedSheet:
    spec: SheetSpec
    path: Path | None              # None when the file is absent
    frame: pd.DataFrame | None     # raw, all-string, None when unreadable
    issues: tuple[Issue, ...]      # read errors (STRUCT-*)

@dataclass(frozen=True)
class LoadResult:
    sheets: Mapping[str, LoadedSheet]
    unexpected_files: tuple[Path, ...]

class SheetLoader(Protocol):
    def load(self, folder: Path, options: LoadOptions) -> LoadResult: ...

# normalizing — DESCOPED (ARC-007, Phase 5, 2026-09-13, ADR-0015): this sketch (a standalone
# `Normalizer`/`SheetFrame` layer separate from the models) is retired, not implemented. See
# ADR-0015 for the full rationale; in one line — `models/sp_*.py` already *is* the normalizing
# layer (structural checks + typed cleaning, one instance per sheet, `self.cleaned`/
# `cleaned_column()` as the typed-column store), and a second parallel abstraction over the
# same responsibility was not justified by any measured or structural gap once ARC-005
# (catalog-only messages) and the ARC-017 rule ports (pure `check_*` functions reading typed
# columns via `RuleContext`) were both done. The dataclass/Protocol sketch below is kept as a
# historical record of the alternative considered, not a pending TODO.
#
# @dataclass(frozen=True)
# class SheetFrame:
#     spec: SheetSpec
#     raw: pd.DataFrame              # never mutated
#     typed: pd.DataFrame            # nullable Int64/Float64/string[pyarrow]
#     invalid: Mapping[str, pd.Series]   # column -> boolean mask of cells that failed typing
#     exists: bool
#     readable: bool
#
# class Normalizer(Protocol):
#     def normalize(self, sheet: LoadedSheet, ctx: RuleContext) -> tuple[SheetFrame, tuple[Issue, ...]]: ...

# errors (see error-model.md)
class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"

@dataclass(frozen=True, slots=True)
class Issue:
    rule_id: str                   # "DESC-004"
    severity: Severity
    sheet: str | None              # "descricao.xlsx"
    row: int | None                # spreadsheet row (1-based, header-aware)
    column: str | None
    message_key: str               # "rule.DESC-004.error"
    params: Mapping[str, object] = field(default_factory=dict)

# rules
@dataclass(frozen=True)
class RuleContext:
    sheets: Mapping[str, SheetFrame]
    options: Options               # flags such as no_spellchecker, no_warning_titles_length
    catalog: MessageCatalog
    clock: Clock
    scenarios: tuple[str, ...]
    spell: SpellBackend | None

class Rule(Protocol):
    rule_id: str                   # unique, stable
    category: str                  # NamesEnum-compatible report bucket
    requires: Mapping[str, tuple[str, ...]]   # {"descricao": ("codigo", "nivel")}
    depends_on: tuple[str, ...]    # rule IDs that must have produced no error
    def check(self, ctx: RuleContext) -> Iterable[Issue]: ...

@dataclass(frozen=True)
class RuleOutcome:
    rule_id: str
    status: Literal["executed", "skipped"]
    reason: str | None             # message key when skipped
    issues: tuple[Issue, ...]
    duration_ms: float

# reporting
class Renderer(Protocol):
    format: str                    # "html" | "json" | "console" | "pdf"
    def render(self, model: ReportModel, target: Path | None) -> Path | str: ...

# spell
class SpellBackend(Protocol):
    language: str
    def check(self, word: str) -> bool: ...
    def add_session_words(self, words: Iterable[str]) -> None: ...
```

## Rule engine semantics

1. **Registration**: every rule module registers one `Rule` in `rules/registry.py` with a unique
   `rule_id`; the registry is the list shown by `--list-rules` and rendered in the report in a
   fixed order (category order = today's `NamesEnum` order).
2. **Prerequisites**: before `check()`, the engine verifies `requires` (sheet exists, readable,
   columns present) and `depends_on` (no error issues from those rules). If unmet, the rule is
   reported as **skipped with reason** (`RuleOutcome.status == "skipped"`, reason = catalog key
   such as `engine.skipped.missing_column`). This replaces today's per-validator column checks and
   the unused `set_not_executed` placeholder.
3. **Purity**: `check()` receives an immutable `RuleContext` and returns issues; it never mutates
   frames, never performs I/O, never reads globals. This makes rules unit-testable with in-memory
   frames and safe to run concurrently.
4. **Ordering**: topological on `depends_on`; ties keep registry order. Independent groups may
   run in a `ProcessPoolExecutor` when `Options.parallel` is set (PERF-007); output order is
   deterministic regardless.
5. **Failure isolation**: an unexpected exception inside a rule is recorded as an
   `engine.rule_crashed` issue **and** makes the process exit with code 2 (never silently 0).
6. **Truncation** happens only in reporting (`ReportModel`), never in the engine.

## Pipeline

```python
def validate(folder: Path, options: Options) -> ValidationResult:
    ctx = AppContext.build(options)                  # locale, catalog, clock, logger, spell
    loaded = SheetLoader().load(folder, options)
    frames, norm_issues = Normalizer().normalize_all(loaded, ctx)
    outcomes = RuleEngine(registry).run(RuleContext(frames, ...))
    return ValidationResult(loaded, norm_issues, outcomes)
```

`cli.main()` maps `ValidationResult` to renderers and exit codes (see `../api/cli-contract.md`).

## Current module → target module

Note (ADR-0015): any `normalizing/` cell below predates the ARC-007 closure decision to descope
the standalone `Normalizer`/`SheetFrame` package — read every such cell as "the typed-cleaning
responsibility stays in the corresponding `models/sp_*.py`", not as a still-pending destination
folder.

| Current | Target | Notes |
|---|---|---|
| `main.py` | `cli.py` | banner removed; `main()` returns exit code |
| `helpers/base/data_args.py` | `cli.py` + `app/options.py` | argparse with explicit aliases; `Options` frozen dataclass |
| `middleware/bootstrap.py` | — (deleted) | locale is an option (ADR-0005) |
| `controllers/context/general_context.py` | `app/context.py` (`AppContext`) | no file/env side effects |
| `controllers/context/data_model_context.py` | `rules/context.py` (`RuleContext`) | mapping by sheet key |
| `controllers/spreadsheet_processor.py` | `app/pipeline.py` | explicit `run`, no work in `__init__` |
| `controllers/report/validation_report.py` | `app/result.py` (`ValidationResult`, `RuleOutcome`) + `reporting/model.py` | truncation in reporting |
| `controllers/report/file_report_generator.py` | `reporting/html.py`, `reporting/pdf.py`, `reporting/json.py`, `reporting/console.py` | autoescape; PDF optional |
| `config/application_config.py` | `app/options.py` + `specs/limits.py` | constants become options/limits; `DATE_NOW` → `Clock` |
| `config/names_enum.py` | `rules/categories.py` | category order preserved for report compatibility |
| `config/spreadsheet_info.py` | `specs/sheet_specs.py` | **Partially implemented** (ARC-003): `SHEET_SPECS` registry exists; the loader consumer (`FileScanner`, `DataLoaderFacade`) is migrated to read from it, but `SpreadsheetInfo` itself and the model/file-structure-validator consumers are not yet — pending Phase 3 |
| `helpers/tools/data_loader/common/config.py` | `specs/sheet_specs.py` | **Done** (BUG-018/ARC-003): `Config`/`SingletonMeta` deleted; `FileScanner`/`DataLoaderFacade` read header layout, CSV separator and required flag straight from `SHEET_SPECS` |
| `config/metadata_info.py` | `util/version.py` | `importlib.metadata` only |
| `helpers/tools/data_loader/api/facade.py` | `loading/loader.py` | **Done** (ARC-009): `DataLoaderFacade.load() -> LoadResult` is a real method; `load_all` is a deprecated one-release property shim |
| `helpers/tools/data_loader/engine/{scanner,factory}.py` | `loading/scan.py`, `loading/readers/__init__.py` | **Done**: conflict policy (CSV wins, loser recorded in `ignored`) documented and implemented in `FileScanner.scan()`; `ReaderFactory` derives no config, takes `sep` explicitly |
| `helpers/tools/data_loader/readers/{csv,excel}_reader.py` | `loading/readers/{csv,xlsx}.py` | **Partially done**: `CSVReader` takes an explicit `sep`; SEC-003 size limits already enforced by the facade; pyarrow strings still pending |
| `helpers/tools/data_loader/readers/qml_reader.py` | — (deleted) | **Done** (BUG-015/ADR-0003): no evidence the protocol needs `.qml`; deleted along with `.qml` scanning |
| `helpers/tools/data_loader/strategies/header.py` | `specs/SheetSpec.header` | Unchanged module; already selected via `SheetSpec.header` at the call site (`DataLoaderFacade.load()`) |
| `helpers/tools/locale/{language_manager,language_enum}.py` | `i18n/catalog.py`, `i18n/locale.py` | no file persistence |
| `helpers/base/file_system_utils.py` | `util/paths.py` | exceptions instead of tuples |
| `helpers/base/logger_manager.py` | `util/logging.py` | `dictConfig`, handlers closed |
| `helpers/base/constant_base.py` | — (frozen dataclasses) | — |
| `helpers/common/formatting/number_formatting_processing.py` | `util/numbers.py` | vectorised helpers |
| `helpers/common/formatting/text_formatting_processing.py` | `rules/description/_text.py` | — |
| `helpers/common/formatting/message_formatting_processing.py` | — (catalog) | — |
| `helpers/common/generation/combinations_processing.py` | `rules/values/_combinations.py` | — |
| `helpers/common/processing/collections_processing.py` | `specs/patterns.py` + `util/collections.py` | ID pattern compiled once from spec; `find_differences_in_two_set_with_message` (dead — zero production callers) deleted Phase 5, 2026-09-13, keeping only the live `find_differences_in_two_set` |
| `helpers/common/processing/data_cleaning_processing.py` | `normalizing/normalizer.py` | one pass per sheet |
| `helpers/common/validation/dataframe_processing.py` | `rules/structure/*.py` (`STRUCT-*`) + `normalizing/` | — |
| `helpers/common/validation/character_processing.py` | — (deleted) | **Done** (ARC-005/ARC-010, Phase 5, 2026-09-13): the module had zero live production importers (only prose mentions of its old method names in `rules/description.py`/`rules/scenario.py`/`rules/temporal_reference.py` docstrings, explaining what each rule replaced) — deleted outright as dead code instead of migrated |
| `helpers/common/validation/description_processing.py` | `rules/description/_codes.py` | — |
| `helpers/common/validation/graph_processing.py` | `rules/composition/_graph.py` | `nx.from_pandas_edgelist` |
| `helpers/common/validation/tree_processing.py` | `rules/composition/_graph.py` | merged with graph |
| `helpers/common/validation/legend_processing.py` | `rules/legend/*.py` | one rule per check; not yet ported (still called from `models/sp_legend.py::data_cleaning`) — Phase 5 (2026-09-13) closed its i18n gap (every message is a `rule.LEG-001…011.*` catalog key, ARC-005) and vectorised its four `.iterrows()` loops (PERF-001); the port to a standalone `rules/legend/*.py` registry is unaffected by this and remains open |
| `helpers/common/validation/proportionality_processing.py` | `rules/proportionality/*.py` | — |
| `helpers/common/validation/value_processing.py` | `rules/values/*.py` | vectorised |
| `helpers/tools/spellchecker/*` | `spell/` | `SpellBackend` |
| `helpers/tools/readme/generate_readme.py` | — (deleted, ADR-0009) | — |
| `models/sp_model_abc.py`, `models/sp_*.py` | itself — the normalizing layer (ADR-0015) | **Done (ARC-007, Phase 5, 2026-09-13 — descoped, not migrated away)**: kept as the normalizing layer by design, not replaced by a separate `normalizing/`/`Normalizer` package; column/dtype definitions are proof-checked against `specs/sheet_specs.py` (ARC-003), structural checks moved to `rules/structure/*.py` (ARC-017), and every message renders through the catalog (ARC-005) — models still own the typed-cleaning pass (`self.cleaned`/`cleaned_column()`) that `rules/*.py` reads from |
| `validators/structure/file_structure_validator.py` | `rules/structure/STRUCT-00x.py` | — |
| `validators/spell/spellchecker_validator.py` | `rules/spelling/SPELL-00x.py` | — |
| `validators/spreadsheets/base/base_validator.py` | `rules/engine.py` | **Done (core, Phase 3a, ADR-0006)**: `RuleContext`/`RuleSpec`/`RuleRegistry`/`Engine` implement prerequisite checks (`requires`/`depends_on`), topological execution, skipped-with-reason (`RuleOutcome.status is SKIPPED`, `SkipReason`), and crash isolation (`FAILED`), 100 % covered by `tests/unit/rules/`; `base_validator.py` itself is untouched, no validator reads from this package yet |
| `validators/spreadsheets/<sheet>/*_validator.py` | `rules/<sheet>/<RULE-ID>.py` | one rule per module; not started — `rules/` has no `<sheet>/` subpackage yet, only the engine core |
| `static/locales/*/messages.json` | `i18n/locales/*.json` | keyed by rule ID |
| `static/report/*`, `static/dictionaries/*`, `static/templates/README.TEMPLATE.md` | `static/report/*`, `static/dictionaries/*`, — | template generator retired |

## Non-goals of the target design

- No plugin loading from arbitrary paths (rules ship with the package; sector-specific rule packs
  are a `future/ideas.md` item).
- No change to the report's visual identity during Phases 1–3 (goldens must stay identical).
- No standalone `normalizing/`/`Normalizer` package (ARC-007, ADR-0015) — `models/sp_*.py`
  fills that role by design; introducing a second, parallel abstraction over the same
  structural-check-plus-typed-cleaning responsibility was considered and rejected.

Last synced with code: 1195fd1
