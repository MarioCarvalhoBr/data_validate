# 03 · Architecture & design debt

Goal of the migration: a codebase that is **elegant, scalable, fast and organised** — pure rule
functions over immutable typed data, explicit dependencies, structured issues, one config source,
zero global state. Each item below names the current smell, where it lives, and the target design
(details in `.specs/architecture/target-architecture.md`).

### ARC-001 · Work is done in constructors (models, validators, processor)
- Priority: P0 · Effort: L · Status: open
- Where: `controllers/spreadsheet_processor.py:94` (`self.run()` in `__init__`), every model
  (`models/sp_*.py` → `self.run()`), every validator (`validators/**` → `self._prepare_statement();
  self.run()` in `__init__`), `helpers/base/data_args.py:244` (argparse in `__init__`),
  `middleware/bootstrap.py:46`.
- Problem: objects cannot be constructed without executing I/O and the whole pipeline; impossible to
  unit-test, reuse as a library, or run rules selectively/in parallel.
- Target: constructors only store dependencies; `Pipeline.run(bundle) -> ValidationResult`;
  `Rule.check(ctx) -> list[Issue]`.
- Note (Phase 3a slice, ARC-017): the `Rule.check(ctx) -> list[Issue]` execution shape now exists
  and is exercised end to end (`data_validate/rules/engine.py::Engine.run`) — a `check` function
  receives an immutable `RuleContext` and returns issues, no constructor work involved. Still
  open: no `models/sp_*.py`/`validators/**` constructor was touched by this slice; every model and
  validator still runs its pipeline from `__init__` exactly as described above. Porting a
  validator to a `Rule` module (closing this item for that validator) is the next slice.
- Note (Phase 3b slice, ARC-017): the first validator is ported —
  `validators/structure/file_structure_validator.py::FileStructureValidator` is deleted; its four
  checks are now `rules/structure.py`'s six pure `check_*` functions (`STRUCT-001`…`STRUCT-006`),
  run by `SpreadsheetProcessor._run_structure_rules` via `Engine(STRUCTURE_REGISTRY).run(ctx)`. No
  constructor work at all for this validator any more — `_run_structure_rules` only builds a
  `RuleContext` and calls `Engine.run`/`extend_report_from_outcomes`. Still open: every other
  validator (spelling, description, composition, temporal reference, proportionality, value,
  scenario, legend) still runs its pipeline from `__init__` unchanged; each is its own future
  slice.
- Note (Phase 3 Port 2 slice, ARC-017): the second validator is ported —
  `validators/spreadsheets/description/description_validator.py::SpDescriptionValidator` is
  deleted; its nine checks are now `rules/description.py`'s ten pure `check_*` functions
  (`DESC-001`…`DESC-010`). `_run_structure_rules` was generalised into
  `SpreadsheetProcessor._run_rule_registries(registries, ctx)` + `_build_rule_context()`, so both
  `STRUCTURE_REGISTRY` and `DESCRIPTION_REGISTRY` run through the same
  `Engine(...).run(ctx)`/`extend_report_from_outcomes(...)` call shape, against one shared
  `RuleContext` built once per pipeline run. No constructor work at all for this validator any
  more. Still open: spelling, composition, temporal reference, proportionality, value, scenario,
  legend.
- Note (Phase 3 Port 3 slice, ARC-017): the third/fourth validators are ported — both
  `SpCompositionGraphValidator`/`compostion_graph_validator.py` and
  `SpCompositionTreeValidator`/`composition_tree_validator.py` are deleted (BUG-024: the
  `compostion_` filename typo is gone); their nine checks are now `rules/composition.py`'s nine
  pure `check_*` functions (`COMP-001`…`COMP-009`), registered in `COMPOSITION_REGISTRY` and run
  through the same `_run_rule_registries`/`_build_rule_context` call shape. No constructor work
  at all for either validator any more. Still open: spelling, temporal reference,
  proportionality, value, scenario, legend.

### ARC-002 · Global mutable state
- Priority: P0 · Effort: L · Status: open
- Where: class-level Series mutation (BUG-002, fixed — see the "Done" note below); module singletons `SHEET`
  (`config/spreadsheet_info.py:53`), `METADATA` (`config/metadata_info.py:152`), `config = Config()`
  + `SingletonMeta` (`data_loader/common/config.py`); locale persisted in `.config/store.locale`
  (BUG-004); `os.environ` mutation (BUG-022); `LanguageManager()` instantiated independently in
  `DataArgs`, `GeneralContext`, `ApplicationConfig`, `FileSystemUtils` (each re-reads the JSON).
- Target: one `AppContext` built in `main()` from CLI args and passed down; frozen dataclasses for
  config; no module-level instances with side effects.
- Done (partial — Phase 1 locale/context slice, BUG-004/BUG-021/BUG-023): locale persisted in
  `.config/store.locale` is gone (`Bootstrap` and the whole `middleware` package are deleted;
  `LanguageManager` takes an explicit `locale` constructor argument and performs no file I/O to
  resolve it). `LanguageManager()` is no longer instantiated independently in `DataArgs`,
  `GeneralContext`, `ApplicationConfig`, and `FileSystemUtils` (each re-reading the JSON catalog on
  its own) — `GeneralContext` now builds **one** `LanguageManager` from `data_args.data_file.locale`
  and injects that same instance into `ApplicationConfig(language_manager=...)` and
  `FileSystemUtils(language_manager=...)` (both gained an optional constructor parameter; each still
  defaults to building its own when not given, for any remaining standalone caller). `DataArgs` no
  longer builds an unused `LanguageManager` of its own. Still open / not touched by this slice:
  the `SHEET` (`config/spreadsheet_info.py`), `METADATA` (`config/metadata_info.py`), and
  `Config`/`SingletonMeta` (`data_loader/common/config.py`) module singletons, and `os.environ`
  mutation (BUG-022) — all remain global mutable state for a future slice of this item.
- Done (Phase 2c slice, BUG-002): class-level `RequiredColumn`/`OptionalColumn`/`DynamicColumn`
  Series mutation is fixed — see BUG-002's "Done" entry in `01-bugs.md` for the full detail
  (`SpModelABC.cleaned`/`cleaned_column()` replace `setattr` on the class).

### ARC-003 · Three competing sources of truth for sheet definitions
- Priority: P1 · Effort: M · Status: in-progress
- Where: `config/spreadsheet_info.py` (names, extensions, expected/optional),
  `helpers/tools/data_loader/common/config.py` (required flag, header type, separator, `.qml`),
  `models/sp_*.py::INFO.SP_NAME` + `RequiredColumn/OptionalColumn/DynamicColumn`.
- Target: a single `SheetSpec` registry (`specs/sheets.py`): name, required, header layout, csv
  separator, column specs, business-rule IDs. Everything else derives from it (loader, models,
  file-structure validator, docs).
- Done (step 1): `data_validate/specs/sheet_specs.py` now declares `SHEET_SPECS` (`ColumnSpec`,
  `SheetSpec`, `ColumnKind`, `HeaderLayout`), proven consistent with all three legacy sources by
  `tests/unit/specs/test_sheet_specs.py` (100 % coverage of the new module). Divergences found
  between the legacy sources during this proof (documented in `sheet_specs.py`'s module
  docstring, not yet fixed): `composicao.codigo_pai` is cleaned with `min_value=1` by the model
  but with `min_value=0` by both composition tree/graph validators; `referencia_temporal.nome`
  and `cenarios.nome` are declared `dtype="int64"` for a name column (BUG-013); `descricao`'s
  dynamic `legenda` column is declared `dtype="str"` but cleaned as an integer. No consumer
  (loader, models, `FileStructureValidator`) has been migrated to read from `SHEET_SPECS` yet —
  that is Phases 2-3 of the migration roadmap; `SpreadsheetInfo`, `Config.file_specs`, and each
  model's `RequiredColumn`/`OptionalColumn`/`DynamicColumn` remain the sources those consumers
  actually read from today.
- Done (consumers: loader): the data-loader consumer is migrated (BUG-015/BUG-018/ARC-009). Both
  `FileScanner` (expected stems, allowed extensions) and `DataLoaderFacade.load()` (header layout,
  CSV separator, required flag for backfilling missing sheets) now read exclusively from
  `SHEET_SPECS`/`ALLOWED_EXTENSIONS`; `helpers/tools/data_loader/common/config.py`'s `Config`/
  `SingletonMeta` singleton is deleted, closing the second of the three sources this item names.
  `models/sp_*.py`'s `RequiredColumn`/`OptionalColumn`/`DynamicColumn` (the third source) and
  `config/spreadsheet_info.py::SpreadsheetInfo` (the first) are unchanged — still open for a later
  slice (Phase 3). `tests/unit/specs/test_sheet_specs.py`'s `TestSheetSpecsMatchDataLoaderConfig`
  class (which proved `SHEET_SPECS` against the now-deleted `Config`) is replaced by
  `TestSheetSpecsPinnedLoaderFacts`, pinning the same header-layout/separator/required values as
  fixed expectations instead of comparing against a second source.

### ARC-004 · Errors are pre-formatted Portuguese strings
- Priority: P1 · Effort: L · Status: in-progress
- Where: everywhere (`f"{self._filename}, linha {idx + 2}: ..."`) — validators, models, helpers;
  `ValidationReport` stores `List[str]`.
- Problem: no severity/rule/location metadata; cannot sort, deduplicate, translate, export JSON,
  count per column, or link back to the protocol rule. Blocks i18n and any UI beyond HTML.
- Target: `Issue(rule_id, severity, sheet, row, column, message_key, params)` + `MessageCatalog`
  rendering per locale; `ValidationResult` with grouping; renderers for console/JSON/HTML/PDF.
- Done (model): `data_validate/specs/issues.py` declares `Severity` (`StrEnum`), the frozen/slotted
  `Issue` dataclass (`rule_id` validated against
  `^(STRUCT|DESC|COMP|VAL|TEMP|SCEN|LEG|PROP|SPELL|CLEAN)-\d{3}$`, `params` frozen into a
  `MappingProxyType`, plus a `category` field for the legacy `NamesEnum` adapter), and
  `ValidationResult` (`errors`/`warnings`/`error_count`/`warning_count`, `by_category()`,
  `truncated(limit)` mirroring `ValidationReport.flatten`'s per-category/per-severity limit
  without emitting the omitted-count message itself, and `omitted_counts(limit)` for the
  renderer to do that). `data_validate/i18n/catalog.py` declares `MessageCatalog` (locale +
  explicit `catalog_dir`, no `store.locale` side effects), `default_catalog_dir()`, and
  `CatalogNotFoundError`/`CatalogInvalidError`; `text()` copies `LanguageManager.text`'s exact
  fallback strings so behaviour is unchanged, and `render(issue)` renders an `Issue` directly.
  100 % coverage on both new modules
  (`tests/unit/specs/test_issues.py`, `tests/unit/i18n/test_message_catalog.py`); mypy strict via
  a new `data_validate.i18n.*` override in `pyproject.toml` (alongside the existing
  `data_validate.specs.*` one). Neither module is wired into the legacy pipeline yet — no
  validator/model/`ValidationReport` call site was touched — that is Phase 3 (see ADR-0004's
  "Phase 1 render identical strings" note and `08-migration-roadmap.md`).

### ARC-005 · i18n is inconsistent (≈95 % of messages hard-coded in pt-BR)
- Priority: P1 · Effort: L · Status: open
- Where: only `FileSystemUtils` and (until ARC-017 Phase 3b) `FileStructureValidator` used
  `language_manager.text()`; all other messages are f-strings (models, validators,
  `helpers/common/**`, `spellchecker/**`, `file_report_generator.py` labels,
  `spreadsheet_processor.py:98`).
- Target: every message is a catalog key (ARC-004); parity test between locales; report template
  localised.
- Note (Phase 3b slice, ARC-017): `FileStructureValidator` is deleted; its six ported rules
  (`rules/structure.py`) render every message through a single `ctx.translate(message_key,
  **params)` call — the `validator_structure_error_*` keys are unchanged (both locales already
  carried every one; the "missing from `en_US`" BUG-016 notes on STRUCT-002/003/005/006 were
  stale, corrected in `.specs/business-rules/file-structure.md`), and the legacy
  `.text(key).format(**kwargs)` double-call for STRUCT-003/004 collapsed into the single-call
  form with no output change (verified byte-identical by the e2e golden harness).
- Note (Phase 3 Port 2 slice, ARC-017): `SpDescriptionValidator` (description_validator.py) is
  deleted; its ten ported rules (`rules/description.py`, DESC-001…010) render every message
  through `ctx.translate(message_key, **params)` — 16 new catalog keys added to both
  `static/locales/{pt_BR,en_US}/messages.json` (one `rule.description.missing_required_column`
  shared by every rule's "required column is missing" abort case, plus one-or-more
  `rule.DESC-0XX.<slug>` keys per rule for its distinct message templates — e.g. DESC-002 has
  three: `non_numeric`/`must_start_at_one`/`must_be_sequential`), all pt-BR values copied
  verbatim from the legacy f-strings (verified byte-identical by the e2e golden harness run
  twice).
- Note (Phase 3 Port 3 slice, ARC-017): both composition validators
  (`compostion_graph_validator.py`/`composition_tree_validator.py`) are deleted; their nine
  ported rules (`rules/composition.py`, COMP-001…009) render every message through
  `ctx.translate(message_key, **params)` — 14 new catalog keys added to both
  `static/locales/{pt_BR,en_US}/messages.json` (`rule.composition.missing_required_column`/
  `_level2` shared by every rule's "required column is missing" abort case,
  `rule.composition.leaf_without_data` shared by COMP-005/COMP-006, plus one-or-more
  `rule.COMP-0XX.<slug>` keys per rule — e.g. COMP-009 has three:
  `parent_missing`/`child_missing`/`level_mismatch`), all pt-BR values copied verbatim from the
  legacy f-strings (verified byte-identical by the e2e golden harness run twice). COMP-004's
  duplicate-title warning uses two distinct keys (`warning.simple_name`/`warning.complete_name`)
  rather than one key with a Portuguese-noun param, so the en_US locale renders a genuine English
  sentence instead of an English template around a Portuguese word.
- Note (Phase 3 Port 4 slice, ARC-017): both `SpTemporalReferenceValidator`
  (`temporal_reference_validator.py`) and `SpScenarioValidator` (`scenario_validator.py`) are
  deleted; their five ported rules (`rules/temporal_reference.py`'s TEMP-001…003,
  `rules/scenario.py`'s SCEN-003…004) render every message through `ctx.translate(message_key,
  **params)` — 9 new catalog keys added to both `static/locales/{pt_BR,en_US}/messages.json`
  (`rule.temporal_reference.missing_required_column`/`rule.scenario.missing_required_column`
  shared by every rule's "required column is missing" abort case, plus one-or-more
  `rule.TEMP-0XX.<slug>`/`rule.SCEN-0XX.<slug>` keys per rule), all pt-BR values copied verbatim
  from the legacy f-strings (verified byte-identical by the e2e golden harness run twice).
  TEMP-002's current-year comparison now reads `ctx.clock().year` instead of
  `ApplicationConfig.CURRENT_YEAR` directly, keeping the rule pure.
- Related: BUG-016, DOC-003

### ARC-006 · Context god-objects and Demeter chains
- Priority: P1 · Effort: M · Status: open
- Where: `controllers/context/general_context.py` (args + config + i18n + fs + logger), usages like
  `self._data_models_context.context.data_args.data_action.no_spellchecker`
  (`spellchecker_validator.py:195`, `description_validator.py:457`), `DataModelContext.get_instance_of`
  linear `isinstance` scan (`data_model_context.py:55-61`).
- Target: small explicit dependencies (`RuleContext(sheets, options, catalog, clock)`), typed
  `SheetBundle["descricao"]` lookup by key.

### ARC-007 · Models validate, clean and mutate; "Processing" classes are procedural namespaces
- Priority: P1 · Effort: L · Status: in-progress
- Where: `models/sp_*.py` (structure checks + cleaning + raw mutation), `helpers/common/**` classes
  with only `@staticmethod` and an empty `__init__` (`dataframe_processing.py:22`,
  `character_processing.py:23`, …), overlap between `helpers/common/validation/*` and `validators/*`.
- Target: `SheetModel` = immutable typed frame + spec; cleaning happens once in a `Normalizer`;
  rules live in `rules/<sheet>/<rule_id>.py` as functions; helpers become plain modules.
- Done (partial — Phase 2c, BUG-002/BUG-003): models no longer mutate class-level column
  declarations or the shared `DataLoaderModel.raw_data`. `SpModelABC` now owns `self.frame`
  (per-instance working frame) and `self.cleaned` (per-instance cleaned-column store,
  `cleaned_column(name)`); `SpDescription`/`SpProportionality` reassign `self.frame` via
  non-mutating ops (`.drop()`, `.assign()`) instead of writing into `raw_data`;
  `SpDescription`/`SpComposition`/`SpTemporalReference` store cleaned columns in `self.cleaned`
  instead of `setattr`-ing a class attribute. Still open (this slice did not touch): models still
  both validate structure *and* clean data in the same `run()` (no `Normalizer` extraction yet);
  `helpers/common/**` "Processing" classes are still `@staticmethod`-only namespaces; no rule
  lives under `rules/<sheet>/<rule_id>.py` yet — that extraction is Phase 3+ of the migration
  roadmap.

### ARC-008 · Validator base class carries dead code and triplicated helpers
- Priority: P1 · Effort: S · Status: open
- Where: `validators/spreadsheets/base/base_validator.py:89-96` (`initialize` no-op),
  `:135-205` (`column_exists`, `_column_exists`, `_column_exists_dataframe`), `:238-260`
  (`set_not_executed` placeholder with commented code), `:81` (`get_verify_names()` recomputed per
  validator).
- Target: rules declare `requires = {"descricao": ["codigo", "nivel"]}`; the engine checks
  prerequisites once and marks rules *skipped* with a reason (feature the placeholder wanted).
- Note (Phase 3a slice, ARC-017): `data_validate/rules/engine.py::Engine` now implements exactly
  this — `RuleSpec.requires`/`depends_on` are checked once per rule and an unmet prerequisite
  produces a `RuleOutcome(status=SKIPPED, skip_reason=...)` naming the reason (missing sheet,
  missing column, or a `SKIPPED`/`FAILED` dependency), replacing the placeholder's intended
  behaviour. `base_validator.py` itself (the triplicated `column_exists*` helpers, the
  `set_not_executed` no-op) is untouched — no validator has been ported to a `Rule` module yet,
  so the old code path still runs unchanged in the legacy pipeline.

### ARC-009 · Data loader: property with side effects, mixed result types
- Priority: P1 · Effort: M · Status: in-progress
- Where: `helpers/tools/data_loader/api/facade.py:91-151` (`@property load_all` performs I/O and
  returns a tuple), `DataLoaderModel.header_type` mutated to `"invalid"` by
  `models/sp_proportionality.py:163`, `data["qmls"]` list (BUG-015).
- Target: `SheetLoader.load(folder) -> LoadResult`; readers return `LoadedSheet(frame, meta)`;
  header layout comes from `SheetSpec`.
- Done: `DataLoaderFacade.load() -> LoadResult` is a real method (no I/O in a property);
  `LoadResult` (`models: dict[str, DataLoaderModel]`, `errors: list[str]`) lives in
  `helpers/tools/data_loader/api/facade.py`. `load_all` is kept for one release as a thin
  `@property` that emits `DeprecationWarning` (`stacklevel=2`) and returns
  `(result.models, result.errors)` for existing callers; `SpreadsheetProcessor._read_data` was
  migrated to call `load()` directly and read `.models`/`.errors` off the `LoadResult`. The `"qmls"`
  key is gone (BUG-015 — nothing in `data_validate/` consumed it). Header layout and CSV separator
  now come from `SHEET_SPECS` (`HeaderLayout`, `SheetSpec.csv_separator`) instead of the deleted
  `Config` singleton, closing the "mixed result types"/"guessed separator" half of this item.
  Remaining open: `DataLoaderModel` itself keeps its current name/attributes (a rename to
  `LoadedSheet`-shaped value object is ARC-013's naming pass, Phase 5).
- Done (BUG-002/BUG-003 Phase 2c slice): the "`DataLoaderModel.header_type` mutated to
  `\"invalid\"`" half of this item is now fixed — `SpProportionality.post_processing` sets
  `self.header_layout_invalid = True` (a new instance attribute) instead, and
  `DataLoaderModel.header_type` is never written after `DataLoaderFacade.load()` sets it
  (grep-confirmed zero remaining writers). Consumers that used to infer proportionality validity
  from the shared `raw_data`/`header_type` now read `model.frame`/`model.header_layout_invalid`
  instead (see BUG-003's "Done" entry in `01-bugs.md`).

### ARC-010 · Package layout mixes tooling, demos and runtime
- Priority: P2 · Effort: S · Status: open
- Where: `helpers/tools/readme/generate_readme.py` (build script inside the package, prints at
  import), `helpers/tools/spellchecker/main.py` (demo), `data_validate/__init__.py:1-14` ("Adapta
  Parser" placeholder docstring), root scratch (`my_codes.py`, `local_data/`), committed `docs/`,
  `dist/`, `data/output/`.
- Target layout (proposal, see `.specs/architecture/target-architecture.md`):
  `data_validate/{cli,app,config,specs,loading,normalizing,rules,reporting,i18n,spell,util}`;
  tooling under `tools/`; docs generated in CI.

### ARC-011 · CLI contract
- Priority: P2 · Effort: M · Status: in-progress
- Where: `helpers/base/data_args.py` (was `:256-303`; documented flags `--i/--o/--l` existed only
  through `allow_abbrev=True`; `--d` in `scripts/run_main_pipeline.bat`), `main.py`.
- Done (this slice): `allow_abbrev=False`; explicit aliases `-i/--input`/`-o/--output` (kept
  `--input_folder`/`--output_folder` as first-class, not deprecated — see decision note below);
  `--i`/`--o`/`--l`/`--d` declared as explicit, deprecated two-dash aliases (stderr warning naming
  the replacement on use); `--json PATH`; `--fail-on {error,warning,never}`; offline `--version`;
  exit codes standardised (SEC-008, see there). Documented in `.specs/api/cli-contract.md`.
- Still open (left to a later phase, judged out of this slice's scope): `--format
  html,pdf,json,console`, `--rules`/`--skip-rules`, `--max-file-size`/`--max-rows`, `--parallel`,
  `--verbose`/`--quiet`, `--list-rules`, a separate `cli.py`/`AppContext` module, and deprecating
  `--input_folder`/`--output_folder` themselves. Decision: `--input_folder`/`--output_folder` were
  *not* deprecated in this slice (unlike `.specs/api/cli-contract.md`'s original target table)
  because the platform's actual invocation of those two flags is still the primary integration
  point and deprecating them belongs with a coordinated platform-side migration, not a
  drive-by change alongside the exit-code fix — tracked as the "still open" row above.
- Related: SEC-008, BUG-010, ARC-012

### ARC-012 · `print()` for user output alongside logging
- Priority: P2 · Effort: S · Status: in-progress
- Where: `main.py:8` (was; now `main.py`'s `main()`), `spreadsheet_processor.py:98`,
  `general_context.py:103`, `file_report_generator.py:153,263,335,340,361,368`,
  `language_manager.py:38,50,61-65`, `bootstrap.py:76-81`, `metadata_info.py:74`.
- Target: `rich`/`logging` console handler with levels; stdout reserved for machine output.
- Done (this slice): the welcome banner (`main.py:8`) no longer prints at `import data_validate`
  time; it prints once from inside `main()`, to stderr instead of stdout (ARC-011/SEC-008).
- Partial (BUG-004 side effect, prior slice): `bootstrap.py` no longer exists (the whole
  `middleware` package was deleted), so its `print()`s are gone with it — not converted, moot.
  `language_manager.py`'s internal `print()`s (`_load_translations`, `set_language`) are replaced
  with `logging.getLogger(__name__).warning(...)`/`.error(...)` calls, message text preserved
  verbatim. `general_context.py:103`'s debug-mode `print("\nLog file created at:", ...)`,
  `spreadsheet_processor.py:98`'s "Tempo total de execução" print, and every `print()` in
  `file_report_generator.py` are intentionally kept as `print()` for now (still open, tracked
  here) — only the banner was in scope for this slice.

### ARC-013 · Naming
- Priority: P2 · Effort: S · Status: open
- Where: `DataModelABC` in `data_args.py:19` (it is an args class), nested `INFO(ConstantBase)` per
  model, `VAR_CONSTS`/`DEFINITIONS` (`sp_model_abc.py:37-63`), `ModelMappingLegend`,
  `SpreadsheetProcessor` vs `Processing` helpers, typos (BUG-024). `TestReportItem` was renamed to
  `ReportItem` (BUG-020, done).
- Target: naming guide in `.claude/rules/coding-standards.md`; rename during migration with
  deprecation shims.

### ARC-014 · Typing discipline
- Priority: P2 · Effort: M · Status: open
- Where: `**kwargs: Dict[str, Any]` everywhere, `context: GeneralContext = None` (implicit
  Optional), `Tuple[bool, str]` / `Tuple[bool, List[str]]` return codes (`file_system_utils.py`,
  `dataframe_processing.py`) contradicting the project's own Clean-Code rule #6, `typing.List/Dict`
  instead of builtins.
- Target: `mypy --strict` on new modules, `from __future__ import annotations`, `TypedDict`/dataclasses
  for kwargs, exceptions for failures.
- Related: TOOL-003

### ARC-015 · Spellchecker tightly coupled to pyenchant
- Priority: P2 · Effort: M · Status: open
- Where: `helpers/tools/spellchecker/**`, `validators/spell/spellchecker_validator.py`
- Problem: C extension + system hunspell; env-var configuration; tests need the library installed;
  Windows requires manual DLLs (`hunspell-win/` in .gitignore).
- Target: `SpellBackend` Protocol (`check(word) -> bool`, `suggest`) with `EnchantBackend` and a pure
  Python fallback (`symspellpy`/`pyspellchecker` with the bundled `.dic`); word-level cache.
- Related: PERF-006

### ARC-016 · Report generation builds HTML in Python
- Priority: P2 · Effort: M · Status: open
- Where: `controllers/report/file_report_generator.py:187-217,266-291`, `config/application_config.py:62-96`
  (fallback template as a class constant), regex-based template validation (`:91-102`).
- Target: `ReportModel` (dataclass) + Jinja templates with autoescape and i18n filters; PDF renderer
  pluggable.
- Related: SEC-001, SEC-002

### ARC-017 · Rule execution order and dependencies are implicit
- Priority: P2 · Effort: M · Status: in-progress
- Where: `controllers/spreadsheet_processor.py:181-215` (hand-ordered constructor calls), each
  validator re-checks emptiness/columns of *other* sheets.
- Target: rule registry with `depends_on` and `requires`; topological execution; optional
  parallel execution of independent rules (process pool) once rules are pure.
- Done (engine core, Phase 3a, ADR-0006): `data_validate/rules/` is a new package —
  `context.py` (`RuleContext`, immutable, `has_sheet`/`sheet` helpers), `registry.py`
  (`RuleSpec`, `RuleRegistry.register`/`get`/`topological_order` with a stable Kahn's algorithm
  that ties-break on registration order, `RegistryCycleError`, the `@registry.rule(...)`
  decorator), `engine.py` (`Engine.run(ctx, only=...)`, `RuleOutcome`, `RuleStatus`
  `PASSED`/`ISSUES`/`SKIPPED`/`FAILED`, `SkipReason`, `EngineResult.validation_result`
  flattening). 100% line coverage (`tests/unit/rules/`, 67 tests), mypy-strict clean
  (`data_validate.rules.*` override in `pyproject.toml`). Still open: no rule module exists
  under `rules/<sheet>/<RULE-ID>.py` yet, `controllers/spreadsheet_processor.py` still
  hand-orders the legacy validators unchanged, and parallel execution (PERF-007) is not
  implemented — the per-rule execution loop is shaped for a future pool but runs sequentially.
- Done (first validator port, Phase 3b): `rules/structure.py` declares `STRUCTURE_REGISTRY`
  (`STRUCT-001`…`STRUCT-006`, one `check_*` function per id, registered in the legacy check
  order — no `depends_on` needed since the one order-sensitive case, STRUCT-002's zipped-subfolder
  short-circuit, is handled inside STRUCT-003/STRUCT-004's own bodies via a shared
  `_is_zipped_with_extra_folder` gate, not via engine skip semantics). `rules/legacy_adapter.py::
  extend_report_from_outcomes` renders `Engine.run(...)`'s outcomes into the legacy
  `ValidationReport` and is written to be reused by every later validator port.
  `SpreadsheetProcessor._build_pipeline` no longer constructs `FileStructureValidator` — it calls
  `SpreadsheetProcessor._run_structure_rules` (new, independently unit-tested), and
  `validators/structure/file_structure_validator.py` is deleted. 100% line coverage on both new
  modules (`tests/unit/rules/test_structure.py`, `test_legacy_adapter.py`), mypy-strict clean,
  e2e golden harness 7/7 twice, byte-identical. `legacy_adapter.py` imports `ValidationReport`
  under `TYPE_CHECKING` only — a runtime import would cycle back through
  `controllers/__init__.py` → `spreadsheet_processor.py` → `rules`.
- Done (third/fourth validator port, Phase 3 Port 3): `rules/composition.py` declares
  `COMPOSITION_REGISTRY` (`COMP-001`…`COMP-009`, registered in the two legacy validators'
  combined check order), run through the same `_run_rule_registries`/`_build_rule_context` call
  shape as description. Each `RuleSpec.requires` now names both sheets a rule needs
  (`{"composicao": (), "descricao": ()}` for COMP-001/COMP-004/COMP-007/COMP-008/COMP-009,
  `{"composicao": (), "valores": ()}` for COMP-005/COMP-006) so the engine's `SKIPPED` status
  replaces the legacy `set_not_executed` no-op for an empty sheet (ARC-008 closed for this
  validator). `data_validate.rules.composition.compute_composition_facts` closes BUG-019
  (computes the graph/tree/relation facts once, injected via
  `ctx.options["composition_facts"]` by `_build_rule_context`, read — never recomputed — by
  every `COMP-*` rule). `validators/spreadsheets/composition/` (both
  `compostion_graph_validator.py` and `composition_tree_validator.py`) is deleted. 96.72 % line
  coverage on the new module (`tests/unit/rules/test_composition.py`), mypy-strict clean, e2e
  golden harness 7/7 twice, byte-identical. Still open: spelling, temporal reference,
  proportionality, value, scenario, legend.
- Related: PERF-007
