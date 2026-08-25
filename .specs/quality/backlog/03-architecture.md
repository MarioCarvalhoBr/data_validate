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

### ARC-002 · Global mutable state
- Priority: P0 · Effort: L · Status: open
- Where: class-level Series mutation (BUG-002); module singletons `SHEET`
  (`config/spreadsheet_info.py:53`), `METADATA` (`config/metadata_info.py:152`), `config = Config()`
  + `SingletonMeta` (`data_loader/common/config.py`); locale persisted in `.config/store.locale`
  (BUG-004); `os.environ` mutation (BUG-022); `LanguageManager()` instantiated independently in
  `DataArgs`, `GeneralContext`, `ApplicationConfig`, `FileSystemUtils` (each re-reads the JSON).
- Target: one `AppContext` built in `main()` from CLI args and passed down; frozen dataclasses for
  config; no module-level instances with side effects.

### ARC-003 · Three competing sources of truth for sheet definitions
- Priority: P1 · Effort: M · Status: open
- Where: `config/spreadsheet_info.py` (names, extensions, expected/optional),
  `helpers/tools/data_loader/common/config.py` (required flag, header type, separator, `.qml`),
  `models/sp_*.py::INFO.SP_NAME` + `RequiredColumn/OptionalColumn/DynamicColumn`.
- Target: a single `SheetSpec` registry (`specs/sheets.py`): name, required, header layout, csv
  separator, column specs, business-rule IDs. Everything else derives from it (loader, models,
  file-structure validator, docs).

### ARC-004 · Errors are pre-formatted Portuguese strings
- Priority: P1 · Effort: L · Status: open
- Where: everywhere (`f"{self._filename}, linha {idx + 2}: ..."`) — validators, models, helpers;
  `ValidationReport` stores `List[str]`.
- Problem: no severity/rule/location metadata; cannot sort, deduplicate, translate, export JSON,
  count per column, or link back to the protocol rule. Blocks i18n and any UI beyond HTML.
- Target: `Issue(rule_id, severity, sheet, row, column, message_key, params)` + `MessageCatalog`
  rendering per locale; `ValidationResult` with grouping; renderers for console/JSON/HTML/PDF.

### ARC-005 · i18n is inconsistent (≈95 % of messages hard-coded in pt-BR)
- Priority: P1 · Effort: L · Status: open
- Where: only `FileSystemUtils` and `FileStructureValidator` use `language_manager.text()`; all other
  messages are f-strings (models, validators, `helpers/common/**`, `spellchecker/**`,
  `file_report_generator.py` labels, `spreadsheet_processor.py:98`).
- Target: every message is a catalog key (ARC-004); parity test between locales; report template
  localised.
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
- Priority: P1 · Effort: L · Status: open
- Where: `models/sp_*.py` (structure checks + cleaning + raw mutation), `helpers/common/**` classes
  with only `@staticmethod` and an empty `__init__` (`dataframe_processing.py:22`,
  `character_processing.py:23`, …), overlap between `helpers/common/validation/*` and `validators/*`.
- Target: `SheetModel` = immutable typed frame + spec; cleaning happens once in a `Normalizer`;
  rules live in `rules/<sheet>/<rule_id>.py` as functions; helpers become plain modules.

### ARC-008 · Validator base class carries dead code and triplicated helpers
- Priority: P1 · Effort: S · Status: open
- Where: `validators/spreadsheets/base/base_validator.py:89-96` (`initialize` no-op),
  `:135-205` (`column_exists`, `_column_exists`, `_column_exists_dataframe`), `:238-260`
  (`set_not_executed` placeholder with commented code), `:81` (`get_verify_names()` recomputed per
  validator).
- Target: rules declare `requires = {"descricao": ["codigo", "nivel"]}`; the engine checks
  prerequisites once and marks rules *skipped* with a reason (feature the placeholder wanted).

### ARC-009 · Data loader: property with side effects, mixed result types
- Priority: P1 · Effort: M · Status: open
- Where: `helpers/tools/data_loader/api/facade.py:91-151` (`@property load_all` performs I/O and
  returns a tuple), `DataLoaderModel.header_type` mutated to `"invalid"` by
  `models/sp_proportionality.py:163`, `data["qmls"]` list (BUG-015).
- Target: `SheetLoader.load(folder) -> LoadResult`; readers return `LoadedSheet(frame, meta)`;
  header layout comes from `SheetSpec`.

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
- Priority: P2 · Effort: M · Status: open
- Where: `helpers/base/data_args.py:256-303` (documented flags `--i/--o/--l` exist only through
  `allow_abbrev=True`; `--d` in `scripts/run_main_pipeline.bat`), no `--version`, no `--json`, exit
  code always 0, stdout mixes progress and the `<{...}>` fragment (`main.py:8` prints at import).
- Target: explicit aliases (`-i/--input`, `-o/--output`, `-l/--locale`), `--json PATH`,
  `--format html,pdf,json`, `--fail-on warning|error`, `--version`, `--rules`, `--list-rules`; exit
  codes documented in `.specs/api/cli-contract.md`. Keep old spellings as deprecated aliases for one
  minor release.
- Related: SEC-008, BUG-010

### ARC-012 · `print()` for user output alongside logging
- Priority: P2 · Effort: S · Status: open
- Where: `main.py:8`, `spreadsheet_processor.py:98`, `general_context.py:103`,
  `file_report_generator.py:153,263,335,340,361,368`, `language_manager.py:38,50,61-65`,
  `bootstrap.py:76-81`, `metadata_info.py:74`.
- Target: `rich`/`logging` console handler with levels; stdout reserved for machine output.

### ARC-013 · Naming
- Priority: P2 · Effort: S · Status: open
- Where: `DataModelABC` in `data_args.py:19` (it is an args class), nested `INFO(ConstantBase)` per
  model, `VAR_CONSTS`/`DEFINITIONS` (`sp_model_abc.py:37-63`), `TestReportItem`, `ModelMappingLegend`,
  `SpreadsheetProcessor` vs `Processing` helpers, typos (BUG-024).
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
- Priority: P2 · Effort: M · Status: open
- Where: `controllers/spreadsheet_processor.py:181-215` (hand-ordered constructor calls), each
  validator re-checks emptiness/columns of *other* sheets.
- Target: rule registry with `depends_on` and `requires`; topological execution; optional
  parallel execution of independent rules (process pool) once rules are pure.
- Related: PERF-007
