# 03 · Architecture & design debt

Goal of the migration: a codebase that is **elegant, scalable, fast and organised** — pure rule
functions over immutable typed data, explicit dependencies, structured issues, one config source,
zero global state. Each item below names the current smell, where it lives, and the target design
(details in `.specs/architecture/target-architecture.md`).

### ARC-001 · Work is done in constructors (models, validators, processor)
- Priority: P0 · Effort: L · Status: done
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
- Done (Phase 3 Port 8 slice, ARC-017 — closes this item): the eighth and last validator is
  ported — `validators/spell/spellchecker_validator.py::SpellCheckerValidator` is deleted; its
  pipeline is now `rules/spell.py`'s `SPELL-001`…`SPELL-005` (`SPELL_REGISTRY`), run by
  `SpreadsheetProcessor._run_rule_registries([SPELL_REGISTRY], ctx)`. With every validator now
  ported, `data_validate/validators/` is deleted **entirely** (see ARC-008's own "Done" note),
  and this slice also fixes every remaining constructor-runs-pipeline case named above: (a)
  `SpModelABC.__init__` no longer calls `self.initialize()` — every concrete model's `run()`
  calls `self.initialize()` as its own first statement instead (only *when* it runs moved, from
  construction to an explicit `run()` call — `initialize()`'s body is unchanged); (b) every
  model's own `__init__` (`SpDescription`, `SpComposition`, `SpValue`, `SpTemporalReference`,
  `SpProportionality`, `SpScenario`, `SpLegend`, `SpDictionary`) no longer calls `self.run()` —
  `SpreadsheetProcessor._configure` calls `model_instance.run()` explicitly right after
  constructing each one; (c) `SpreadsheetProcessor.__init__` (line 94 named above) no longer
  calls `self.run()` — `main.py::main` now does `processor =
  SpreadsheetProcessor(context=general_context); processor.run()`; the welcome-banner log line
  and the total-execution-time print (both previously in `__init__`, around the old `self.run()`
  call) moved into `run()` unchanged, so timing still covers exactly the same work. The one
  remaining, **accepted** exception is `DataArgs.__init__` (`helpers/base/data_args.py:244`,
  named above): its argparse construction is a CLI-boundary object (ADR-0005 territory —
  parsing `sys.argv` *is* what constructing that object means), not a validation/business-logic
  side effect, and stays out of this item's scope; `middleware/bootstrap.py` (also named above)
  no longer exists (deleted by a prior slice, BUG-004). Every test constructing a model or
  `SpreadsheetProcessor` directly and asserting on post-`run()` state now calls `.run()`
  explicitly (`tests/unit/models/test_model_isolation.py`;
  `tests/unit/controllers/test_spreadsheet_processor.py` gained
  `TestConfigureCallsRunExplicitly`, pinning that `_configure` calls `model.run()` on every
  constructed model). **ARC-001 is now done.**

### ARC-002 · Global mutable state
- Priority: P0 · Effort: L · Status: done
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
- Done (closes this item, Phase 5, 2026-09-13): every remaining "Where" item is now resolved or
  judged acceptable. Evidence, grep-verified: (a) `data_loader/common/config.py`'s `Config`/
  `SingletonMeta` singleton — confirmed deleted (the path does not exist; `grep -rn
  "SingletonMeta" data_validate/` returns nothing), already noted under ARC-003's loader-consumer
  slice; (b) `os.environ` mutation (BUG-022) — confirmed already fixed: `dictionary_manager.py`'s
  `_enchant_config_dir_scope` context manager reads the previous `ENCHANT_CONFIG_DIR` value,
  writes a session-scoped temp-dir value, and restores the previous value (or removes the key) in
  a `finally` block — it is scoped and reverted around one call, not a persistent process-wide
  mutation, so it does not count as unresolved global state; (c) the module singletons `SHEET`
  (`config/spreadsheet_info.py:53`) and `METADATA` (`config/metadata_info.py:102`) — both remain,
  by design, and both are read-only after construction: both classes extend `ConstantBase`, whose
  `__setattr__` raises `AttributeError` on any reassignment once `_finalize_initialization()` runs
  (called as the last statement of each `__init__`), and both `__init__` bodies do only attribute
  assignment plus (for `METADATA`) a read-only `importlib.metadata.metadata(...)` lookup wrapped in
  `try/except importlib.metadata.PackageNotFoundError` — no `os.environ` write, no `open(...)`, no
  `print()` at module scope in either file (grep-confirmed for both files and for `os.environ`/
  `open(`/`print(` at module scope across `data_validate/config/**`). (d) `LanguageManager()`
  independently instantiated in `DataArgs`/`GeneralContext`/`ApplicationConfig`/`FileSystemUtils`
  — already fixed in the Phase 1 locale/context slice noted above (one shared instance built by
  `GeneralContext`, injected into the others). **Justification for keeping `SHEET`/`METADATA` as
  module-level instances**: they are immutable constants once constructed (enforced at the
  language level via `ConstantBase`, not by convention alone) with no I/O, environment, or
  filesystem side effects at import time — this satisfies `.claude/rules/coding-standards.md`'s
  "no global/module-level **mutable** state" bar; a plain `SpreadsheetInfo`/`MetadataInfo` class
  attribute exposed as a frozen singleton is architecturally equivalent to a frozen dataclass
  constant module and does not need a further refactor to close this item. **ARC-002 is now done**
  for its full original scope.

### ARC-003 · Three competing sources of truth for sheet definitions
- Priority: P1 · Effort: M · Status: done
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
- Done (closes this item, Phase 5, 2026-09-13 — models' declarations kept as checked duplicates,
  not derived): the remaining consumer this item names, `models/sp_*.py`'s per-model
  `RequiredColumn`/`OptionalColumn`/`DynamicColumn` nested classes, is **not** migrated to derive
  its `pd.Series(dtype=..., name=...)` declarations from `SHEET_SPECS` at import time. Considered
  and rejected: sourcing each `name=` string from `SHEET_SPECS[sheet].column(name)` requires
  either indexing by position (brittle — a spec reorder silently renames the wrong column) or
  already knowing the name to look it up (circular — the point of the declaration is to name the
  column). The single-source-of-truth property this item actually cares about — that a model's
  declared column name/dtype cannot silently drift from the loader's/rules' own expectation — is
  already enforced by proof, not derivation: `tests/unit/specs/test_sheet_specs.py` compares
  every model's `RequiredColumn`/`OptionalColumn`/`DynamicColumn` name/dtype against the matching
  `SHEET_SPECS` entry and fails the moment they diverge (the three pre-existing divergences this
  item's own "Done (step 1)" note already documented — `composicao.codigo_pai`'s `min_value`,
  `referencia_temporal.nome`/`cenarios.nome`'s `dtype`, `descricao.legenda`'s `dtype` — are pinned
  as *known, reviewed* divergences by that same test, not silently tolerated). A model's
  `RequiredColumn` Series today has exactly one real consumer left — `list(RequiredColumn.ALL)`
  fed to `DataFrameProcessing.check_dataframe_column_names` — and every model/validator/rule that
  needs the sheet's authoritative shape (the loader via `FileScanner`/`DataLoaderFacade`, every
  `rules/*.py` registry via `ctx.sheet(...)`/`RuleContext`) already reads `SHEET_SPECS` directly,
  per the "Done (consumers: loader)" note above and ARC-017's rule ports. The three sources this
  item opened against are now: `SHEET_SPECS` (the single source every *new* consumer reads),
  models' declarations (a legacy, test-proven-consistent duplicate, pending deletion once
  ARC-007's `Normalizer` extraction removes the model-level structural check entirely — not a
  second *authority*, since nothing derives its own behaviour from it independently of the proof),
  and `config/spreadsheet_info.py::SpreadsheetInfo` (narrowed, not superseded outright:
  `FileScanner`/`DataLoaderFacade` no longer read its *expected/optional/extensions* logic, per
  the loader-consumer slice above — that structural authority moved to `SHEET_SPECS` — but every
  model still imports its plain `SHEET.SP_NAME_*` string constants, e.g. `SHEET.SP_NAME_DESCRIPTION
  == "descricao"`, purely as a naming convenience with no behaviour of its own to drift from
  `SHEET_SPECS`, the same non-authoritative role `SHEET`/`METADATA` already play under ARC-002).
  **ARC-003 is now done** on this basis: one
  authoritative source (`SHEET_SPECS`), with every remaining duplicate either an inert legacy
  artefact or a test-enforced, intentionally-kept mirror — not three competing, independently
  drifting sources of truth any more.

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
- Done (closes this item, Phase 5, 2026-09-13 — note, not the `data_validate.i18n.catalog.Issue`
  path): every one of the nine rule registries (`STRUCTURE_REGISTRY` … `SPELL_REGISTRY`,
  ARC-017) produces `data_validate.specs.issues.Issue` objects exclusively — no `check_*`
  function anywhere under `rules/` builds or returns a pre-formatted string; every message is a
  `(message_key, params)` pair carried on the `Issue`, rendered only at the boundary
  (`rules/legacy_adapter.py::extend_report_from_outcomes`, via `ctx.translate`/
  `language_manager.text`). This is this item's actual target achieved through the *rule*-facing
  half of the migration (ARC-017), not through wiring in the standalone `specs/issues.py`
  `Issue`/`i18n/catalog.py` `MessageCatalog` pair built in the earlier "Done (model)" note above —
  those two modules remain genuinely unwired into the legacy pipeline (their own tests still
  cover them in isolation), superseded in practice by `RuleContext.translate`/`RuleOutcome`
  carrying the same key+params shape through a different, already-integrated path.
  `ValidationReport`/`ReportModel` (ARC-016) are correctly *render-side* consumers — they store
  and format already-rendered strings for HTML/console output, which is their job, not a
  violation of this item (an "Issue-shaped" report store was never this item's ask; "no
  severity/rule/location metadata, cannot sort/dedupe/translate" was, and every one of those
  properties now exists upstream, at the `Issue`, before rendering). Remaining, explicitly
  out-of-scope-for-this-item hardcoded pt-BR strings (the ARC-005 gap: `models/sp_*.py`'s
  structural/data-cleaning checks, `helpers/common/**`'s message-building helpers, legend's
  in-model LEG-001…011 checks, `file_report_generator.py`'s report labels) are tracked there, not
  here — this item is specifically about the *shape* errors travel in (structured `Issue` vs. a
  pre-formatted string), which is now uniform for every rule the engine runs. **ARC-004 is now
  done.**

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
- Note (Phase 3 Port 5 slice, ARC-017): `SpValueValidator` (`value_validator.py`) and its
  message-building helper `ValueProcessing` (`value_processing.py`) are both deleted; its four
  ported rules (`rules/value.py`'s VAL-002…005) render every message through
  `ctx.translate(message_key, **params)` — 12 new catalog keys added to both
  `static/locales/{pt_BR,en_US}/messages.json` (`rule.value.missing_required_column` shared by
  every rule's "required column is missing" abort case, plus one-or-more
  `rule.VAL-0XX.<slug>` keys per rule — e.g. VAL-004 has four:
  `error`/`aggregate`/`decimal_parse_error`/`silent`), all pt-BR values copied verbatim from the
  legacy f-strings (verified byte-identical by the e2e golden harness run twice). VAL-004's
  `silent` key renders to the empty string, preserving the legacy
  `ValueProcessing.check_numeric_value`'s literal-infinity branch (`return False, "", False`)
  rather than "fixing" it.
- Note (Phase 3 Port 6 slice, ARC-017): `SpLegendValidator`/`ModelMappingLegend`
  (`legend_validator.py`) is deleted; its four ported rules (`rules/legend.py`'s LEG-012…015)
  render every message through `ctx.translate(message_key, **params)` — 7 new catalog keys added
  to both `static/locales/{pt_BR,en_US}/messages.json` (`rule.legend.missing_required_column`
  shared by every rule's "required column is missing" abort case, plus one-or-more
  `rule.LEG-0XX.<slug>` keys per rule), all pt-BR values copied verbatim from the legacy
  f-strings (verified byte-identical by the e2e golden harness run twice). LEG-015 uses two
  distinct keys (`error_default`/`error_coded`) for its "padrão"/"de código 'X'" branch rather
  than one key with a pre-formatted-fragment param, so the en_US locale renders a genuine English
  sentence in both cases instead of an English template around Portuguese connector words.
- Note (Phase 3 Port 7 slice, ARC-017): `SpProportionalityValidator`
  (`proportionality_validator.py`) is deleted; its eight ported rules (`rules/proportionality.py`'s
  PROP-003…010) render every message through `ctx.translate(message_key, **params)` — 15 new
  catalog keys added to both `static/locales/{pt_BR,en_US}/messages.json`
  (`rule.proportionality.missing_required_column`/`_level2` shared by every rule's "required
  column is missing" abort case, plus one-or-more `rule.PROP-0XX.<slug>` keys per rule — e.g.
  PROP-006 has three: `parent_missing`/`child_mismatch`/`child_missing`), all pt-BR values copied
  verbatim from the legacy f-strings (verified byte-identical by the e2e golden harness run
  twice). PROP-007…010 share one `RuleSpec` (a legacy quirk this port's design brief chose to
  keep, since all four already came from one legacy method and share one category, `SUM_PROP`)
  but still tag each `Issue` with its own specific `PROP-0XX` id, so the catalog/spec traceability
  is unaffected by that grouping.
- Note (Phase 3 Port 8 slice, ARC-017 — last validator port): `SpellCheckerValidator`
  (`spellchecker_validator.py`) is deleted; its ported rules (`rules/spell.py`'s
  `SPELL-001`…`SPELL-005`) render every message through `ctx.translate(message_key, **params)` —
  5 new catalog keys added to both `static/locales/{pt_BR,en_US}/messages.json`
  (`rule.spelling.missing_required_column`, `rule.SPELL-001.backend_error`,
  `rule.SPELL-003.warning`, `rule.SPELL-004.warning`, `rule.SPELL-005.error`), the four
  behavioural keys' pt-BR values copied verbatim from the legacy f-strings (verified
  byte-identical by the e2e golden harness run twice — the pt_BR e2e fixtures skip the SPELL
  section entirely when the `pt_BR` enchant dictionary is unavailable, so this port's output is
  compared only when it is). `rule.SPELL-001.backend_error` is a **documented exception** to "one
  key per distinct message, real translations both ways": `DictionaryManager`/`SpellChecker`
  errors are pre-formed, hardcoded-Portuguese strings today regardless of `--locale` (a
  pre-existing gap, not fixed here), so its template is an intentional `{message}`-only
  passthrough, identical in both locales, rather than an invented "translation" of text this port
  has no authority to retranslate. With this port, **every** validator's messages are now catalog
  keys — the only hardcoded pt-BR strings left are (a) ~15 f-strings inside `models/sp_*.py`'s
  structural/data-cleaning checks (`SpModelABC.initialize`, `pre_processing`/`data_cleaning` across
  the eight models) and (b) the report labels/section titles in
  `controllers/report/file_report_generator.py` — both out of this port's scope, so ARC-005
  stays **in-progress**, not done.
- Done (Phase 5 slice, 2026-09-13 — models' own structural/data-cleaning messages, closing (a)
  above): every hardcoded pt-BR literal built directly inside `models/sp_*.py`'s
  `initialize`/`pre_processing`/`expected_structure_columns`/`data_cleaning`, plus the shared
  message-building helpers those methods call — `MessageFormattingProcessing.
  format_text_to_missing_and_expected_columns` (`rule.STRUCT-011.error`/`rule.STRUCT-012.warning`),
  `DataFrameProcessing.check_dataframe_vertical_bar`/`check_dataframe_unnamed_columns`
  (`rule.STRUCT-009.*`/`rule.STRUCT-010.{singular,plural}`), `DataCleaningProcessing.
  clean_column_integer`/`clean_dataframe_integers` (`rule.CLEAN-001…006.error`, keyed by a new
  `rule_id` parameter each model call site now passes), and `NumberFormattingProcessing.
  check_cell_integer`/`validate_integer` (`rule.file_cleaning.value_*`) — now render through a
  `translate: Callable[..., str]` parameter (`self.context.language_manager.text` from every
  model; `rules/*.py`'s own calls into the same shared `DataCleaningProcessing`/
  `NumberFormattingProcessing` methods pass nothing and get a process-wide cached pt-BR default,
  `helpers/common/default_translate.get_default_translate()`, so their discarded return values
  are unaffected). Mechanism chosen (per this item's own brainstorm): an optional `translate`
  parameter defaulting to a cached `LanguageManager(locale="pt_BR")`, not the "helpers return
  structured findings, models render" alternative — the smaller, behaviour-preserving diff for
  helpers with many pre-existing callers/tests, while still meeting "no helper ever writes a
  hardcoded string" (the default is a catalog lookup, not a literal). Naming convention: target
  keys already existed in `.specs/business-rules/*.md` for every one of these
  (`CLEAN-001…006`/`LEG-001…011` reserved under the `FC` category, `STRUCT-008…012` under `FS` —
  see `.specs/business-rules/README.md`'s rule-ID table) from an earlier spec-writing pass, so
  this slice implements exactly the keys already documented there rather than inventing a new
  `clean.`/`struct.` prefix. 31 new catalog keys added to both locales (`rule.STRUCT-008.error`
  … `rule.PROP-002.level2_missing`, full list in the commit diff). Inline model messages also
  moved to the catalog this slice: `DESC-011`/`DESC-012` (`sp_description.py`'s scenario/legend
  dynamic-column errors), `SCEN-001`/`SCEN-002` (`sp_scenario.py`), `VAL-001` (`sp_value.py`,
  three templates), `PROP-001`/`PROP-002` (`sp_proportionality.py`, five templates), `CLEAN-006`
  (`sp_temporal_reference.py`'s "must have exactly one row" check). Regression tests:
  `tests/unit/models/test_i18n_wired_messages.py` (new — 15 tests, one real `LanguageManager`
  per test, no mocks, asserting the exact historical pt-BR string is still produced for every
  wired message: STRUCT-008/009/010, DESC-011/012, CLEAN-001/004/005/006, SCEN-001/002, VAL-001,
  PROP-001), `tests/unit/helpers/common/test_default_translate.py` (new module, 100 % coverage),
  every pre-existing test for the five touched helpers (unchanged, passing against the new
  default-translate fallback). `tests/e2e` golden harness 8/8 twice, byte-identical (none of the
  8 fixtures currently trip these specific messages, so the golden gate proves "nothing else
  broke", not "these specific renders are byte-identical" — that is what the new unit tests
  prove instead, directly, against the real catalog).
  Before/after grep count (`grep -rn '"' data_validate/models data_validate/helpers/common | grep
  -P "[áéíóãçõêâ]"`, a proxy for "pt-BR literal still hardcoded in this tree" — undercounts
  accent-free Portuguese like "duplicados"/"Existem", so treat as a floor, not an exact count):
  **58 → 31**. Explicitly **not done** this round, remaining as ARC-005's open scope:
  `helpers/common/validation/legend_processing.py`'s `LegendProcessing` class (LEG-001…011, ~25
  message sites — only consumer is `models/sp_legend.py`, confirmed by grep, so this is safe,
  contained, well-specced follow-up work per `.specs/business-rules/legend.md`, just not done in
  this slice given its size); `helpers/common/validation/character_processing.py` (grep-checked
  during this slice: it has **no live production importer at all** any more — `rules/
  description.py`/`rules/scenario.py`/`rules/temporal_reference.py` only *mention* its old method
  name, `check_characters_punctuation_rules`, in prose describing what each rule replaced when it
  was ported off the legacy validator; none of the three actually imports the module. Its pt-BR
  literals are unreachable dead code today, same shape as the already-deleted
  `ValueProcessing`/`value_validator.py` — a candidate for outright deletion (ARC-010-shaped
  cleanup) rather than i18n work, left untouched here to keep this slice's diff to genuinely
  live code); `helpers/common/processing/collections_processing.py::
  find_differences_in_two_set_with_message`'s two remaining literals — also grep-checked: this
  specific method has **no caller anywhere** in `data_validate/` (dead code, same as
  `character_processing.py` above; `CollectionsProcessing`'s *other* methods are actively used by
  both models and rules, so the class itself is not dead, only this one method); `DataFrameProcessing.
  check_dataframe_unique_values`/`column_exists`/`check_dataframe_titles_uniques`/
  `check_dataframe_text_length` (not named in this item's original "Where" list, discovered
  during this slice, left untouched to keep the diff scoped to the explicitly-named targets);
  `file_report_generator.py`'s report labels/section titles (unchanged, per (b) above). ARC-005
  **stays in-progress** — real, measured progress, not closed.
- Related: BUG-016, DOC-003

### ARC-006 · Context god-objects and Demeter chains
- Priority: P1 · Effort: M · Status: in-progress
- Where: `controllers/context/general_context.py` (args + config + i18n + fs + logger), usages like
  `self._data_models_context.context.data_args.data_action.no_spellchecker`
  (`spellchecker_validator.py:195`, `description_validator.py:457`), `DataModelContext.get_instance_of`
  linear `isinstance` scan (`data_model_context.py:55-61`).
- Target: small explicit dependencies (`RuleContext(sheets, options, catalog, clock)`), typed
  `SheetBundle["descricao"]` lookup by key.
- Evidence (Phase 5 review, 2026-09-13): the specific Demeter chain named above is gone —
  `spellchecker_validator.py`/`description_validator.py` no longer exist (both deleted by ARC-017's
  Phase 3 ports), and `grep -rn "data_models_context\.context\." data_validate/` returns zero
  hits anywhere in production code. Every one of the nine rule registries now receives the small,
  explicit `RuleContext(sheets, cleaned, options, translate, clock)` this item's target names —
  confirmed by every `tests/unit/rules/test_*.py` module building one directly, with no
  `GeneralContext`/`DataModelContext` involved at all. **Not yet resolved**: `DataModelContext`
  itself is not dead code — `controllers/spreadsheet_processor.py:240-242` still calls
  `self.data_models_context.get_instance_of(models.SpDescription)` (and `SpLegend`,
  `SpDictionary`) to hand specific model instances to the report-building step, i.e. the linear
  `isinstance` scan this item also names is still there and still load-bearing (it is how the
  report step reaches the description/legend/dictionary models directly, outside the rules
  engine). `GeneralContext` itself remains the app-level container by design (args + config + i18n
  + fs + logger in one object is the accepted `AppContext`-shaped role for the legacy pipeline —
  ADR territory, not a defect this item asks to fix). **Stays in-progress**: the rule-facing half
  of this item (the Demeter chain into rule code) is done; the model-lookup half
  (`DataModelContext.get_instance_of`'s linear scan, still used by the report step) is not — a
  typed `SheetBundle`-shaped replacement for that lookup is follow-up work, not folded into any
  slice so far.

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
- Priority: P1 · Effort: S · Status: done
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
- Done (Phase 3 Port 8 slice, ARC-017 — closes this item): with the eighth and last validator
  ported (`rules/spell.py`, replacing the deleted `SpellCheckerValidator`), no validator reads
  from `base_validator.py` any more — `data_validate/validators/` (`base_validator.py` included)
  is deleted **entirely**. Its triplicated `column_exists`/`_column_exists`/
  `_column_exists_dataframe` helpers, the `initialize()` no-op, and the `set_not_executed`
  placeholder are gone with it; every rule now declares its own `RuleSpec.requires` and the
  engine's `Engine._unmet_prerequisite` (Phase 3a) is what actually checks prerequisites and
  records a `SKIPPED` outcome with a reason, for every rule, exactly as this item targeted.
  **ARC-008 is now done.**

### ARC-009 · Data loader: property with side effects, mixed result types
- Priority: P1 · Effort: M · Status: done
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
  Remaining open (as of that slice): `DataLoaderModel` itself keeps its current name/attributes (a
  rename to `LoadedSheet`-shaped value object is ARC-013's naming pass, Phase 5).
- Done (BUG-002/BUG-003 Phase 2c slice): the "`DataLoaderModel.header_type` mutated to
  `\"invalid\"`" half of this item is now fixed — `SpProportionality.post_processing` sets
  `self.header_layout_invalid = True` (a new instance attribute) instead, and
  `DataLoaderModel.header_type` is never written after `DataLoaderFacade.load()` sets it
  (grep-confirmed zero remaining writers). Consumers that used to infer proportionality validity
  from the shared `raw_data`/`header_type` now read `model.frame`/`model.header_layout_invalid`
  instead (see BUG-003's "Done" entry in `01-bugs.md`).
- Done (Phase 5 slice, ARC-013's naming pass — closes this item): `DataLoaderModel` is renamed to
  `LoadedSheet` in `helpers/tools/data_loader/api/facade.py`; every internal consumer (`models/sp_*.py`,
  `sp_model_abc.py`, `helpers/tools/__init__.py`, `helpers/tools/data_loader/__init__.py`, and every
  test that referenced the old name) now imports/uses `LoadedSheet`. `DataLoaderModel = LoadedSheet`
  is kept as a plain class-object alias for one release (grep-confirmed: the alias is the identical
  class, not a subclass or wrapper; regression test:
  `tests/unit/helpers/tools/data_loader/api/test_facade.py::TestDataLoaderModelDeprecatedAlias`).
  **ARC-009 is now done.**

### ARC-010 · Package layout mixes tooling, demos and runtime
- Priority: P2 · Effort: S · Status: done
- Where: `helpers/tools/readme/generate_readme.py` (build script inside the package, prints at
  import), `helpers/tools/spellchecker/main.py` (demo), `data_validate/__init__.py:1-14` ("Adapta
  Parser" placeholder docstring), root scratch (`my_codes.py`, `local_data/`), committed `docs/`,
  `dist/`, `data/output/`.
- Target layout (proposal, see `.specs/architecture/target-architecture.md`):
  `data_validate/{cli,app,config,specs,loading,normalizing,rules,reporting,i18n,spell,util}`;
  tooling under `tools/`; docs generated in CI.
- Done (Phase 5 slice — closes this item): `helpers/tools/readme/` (both `generate_readme.py` and
  its `__init__.py`) and `static/templates/README.TEMPLATE.md` are physically deleted (ADR-0009,
  now "Accepted (implemented)" instead of "partially implemented"), along with the now-empty
  `static/templates/` directory; `pyproject.toml`'s `[tool.coverage.run] omit` no longer lists
  `generate_readme.py` (nothing left to omit) and `tools/check_links.py`'s
  `_DEFAULT_EXCLUDED_FILES` is now an empty `frozenset` (its only entry was that template).
  `helpers/tools/spellchecker/main.py` (the demo script) and its
  `tests/unit/helpers/tools/spellchecker/test_main.py` are deleted — nothing in `data_validate/`
  imported the module. `data_validate/__init__.py`'s "Adapta Parser" placeholder docstring is
  replaced with a 3-line package description naming the real project (`canoa_data_validate`) and
  pointing at `.specs/00-overview.md`; its lazy-`__getattr__` metadata behaviour is unchanged. Root
  scratch `my_codes.py` (already `.gitignore`d, never tracked) is deleted from disk and its
  `.gitignore` line removed (nothing left to ignore). `local_data/`/`dist/` were already untracked
  (0 files under git) and committed `docs/` already contains only `docs/adrs/` — both already
  satisfied this item's intent before this slice, so neither needed a change here.

### ARC-011 · CLI contract
- Priority: P2 · Effort: M · Status: done (remaining rows below are wont-fix, not open)
- Where: `helpers/base/data_args.py` (was `:256-303`; documented flags `--i/--o/--l` existed only
  through `allow_abbrev=True`; `--d` in `scripts/run_main_pipeline.bat`), `main.py`.
- Done (this slice): `allow_abbrev=False`; explicit aliases `-i/--input`/`-o/--output` (kept
  `--input_folder`/`--output_folder` as first-class, not deprecated — see decision note below);
  `--i`/`--o`/`--l`/`--d` declared as explicit, deprecated two-dash aliases (stderr warning naming
  the replacement on use); `--json PATH`; `--fail-on {error,warning,never}`; offline `--version`;
  exit codes standardised (SEC-008, see there). Documented in `.specs/api/cli-contract.md`.
- Done (Phase 5 slice, 2026-09-13): `--list-rules` implemented — `data_validate/rules/__init__.py`
  gains `ALL_REGISTRIES` (every rule registry, in the same fixed order
  `SpreadsheetProcessor._build_pipeline` runs them) and `list_all_rules() -> tuple[RuleSummary, ...]`
  (`RuleSummary(rule_id, category, severity)`, sorted by `rule_id`) — a pure, importable helper
  independent of any `RuleContext`/bundle, per this item's own "an importable helper in
  `rules/__init__.py`" instruction. `helpers/base/data_args.py` gains `_ListRulesAction` (an
  `argparse.Action`, mirroring the existing `action="version"` `--version` flag): `--list-rules`
  prints one `rule_id<TAB>category<TAB>severity` line per registered rule (47 today) to stdout and
  exits 0 during `parser.parse_args()`, before `DataArgs.run()`'s `--input_folder` requirement is
  even checked — no bundle, no `--input_folder`/`--output_folder` needed. `.specs/api/cli-contract.md`
  moved from its "Target contract — still pending" table to "Current contract — implemented".
  Tests: `tests/unit/rules/test_list_all_rules.py` (row count matches total registered, sorted,
  every field populated, no duplicate rule IDs across registries),
  `tests/unit/helpers/base/test_data_args.py::TestDataArgsCliContract::
  test_list_rules_flag_exits_zero_and_prints_every_rule` (real `sys.argv`, real `SystemExit`,
  real stdout capture, mirroring the existing `--version` test).
- Wont-fix (Phase 5 decision, judged out of scope beyond `--list-rules`): `--format
  html,pdf,json,console`, `--rules`/`--skip-rules`, `--max-file-size`/`--max-rows` (SEC-003 already
  enforces fixed limits via config, not a flag), `--parallel` (PERF-007 is its own wont-fix),
  `--verbose`/`--quiet`, a separate `cli.py`/`AppContext` module, and deprecating
  `--input_folder`/`--output_folder` themselves — the PDF-generation-conditional stderr lines
  (ARC-012) and the existing stdout/stderr split already cover the practical need `--verbose`/
  `--quiet` would address, so adding a flag for it is not justified by any concrete gap. Decision:
  `--input_folder`/`--output_folder` were *not* deprecated (unlike `.specs/api/cli-contract.md`'s
  original target table) because the platform's actual invocation of those two flags is still the
  primary integration point and deprecating them belongs with a coordinated platform-side
  migration, not a drive-by change alongside the exit-code fix.
- Related: SEC-008, BUG-010, ARC-012

### ARC-012 · `print()` for user output alongside logging
- Priority: P2 · Effort: S · Status: done
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
  verbatim.
- Done (Phase 5 slice, 2026-09-13 — closes this item): every remaining `print()` this item named
  is moved to stderr, so stdout carries **only** the `<{json}>` summary fragment
  (`FileReportGenerator._print_json_summary`) — nothing else is a `print()` call any more without
  an explicit `file=sys.stderr`. `general_context.py`'s debug-mode `print("\nLog file created
  at:", ...)` gains `file=sys.stderr`. `spreadsheet_processor.py::run`'s "Tempo total de
  execução" print gains `file=sys.stderr`. `file_report_generator.py`'s four `info_message`
  prints that used `file=sys.stdout` (`_save_html_file`'s "HTML report created at: …",
  `_save_pdf_file`'s two "PDF report created at: …" branches — WeasyPrint and `pdfkit` — and the
  `pdfkit`-`ImportError` "skip" message, which was already on stderr) are switched to
  `file=sys.stderr`; the module's other five `print(..., file=sys.stderr)` calls (error paths)
  were already correct and are unchanged. Verified end to end: a real
  `canoa-data-validate --input_folder … --output_folder …` run's stdout now contains *only* the
  `<{...}>` line (blank lines aside); every `HTML report created at:`/`PDF report created
  at:`/`Tempo total de execução:`/banner line is on stderr. `tests/e2e/test_golden.py` (8/8,
  twice) and the full unit suite stay green — the golden harness's `_extract_json_summary` was
  already a regex search over stdout, not a whole-string comparison, so removing the
  now-stderr-only lines from stdout does not change what it extracts.
  **ARC-012 is now done.**

### ARC-013 · Naming
- Priority: P2 · Effort: S · Status: done
- Where: `DataModelABC` in `data_args.py:19` (it is an args class), nested `INFO(ConstantBase)` per
  model, `VAR_CONSTS`/`DEFINITIONS` (`sp_model_abc.py:37-63`), `ModelMappingLegend`,
  `SpreadsheetProcessor` vs `Processing` helpers, typos (BUG-024). `TestReportItem` was renamed to
  `ReportItem` (BUG-020, done).
- Target: naming guide in `.claude/rules/coding-standards.md`; rename during migration with
  deprecation shims.
- Done (Phase 5 slice — closes this item, along with `DataLoaderModel` → `LoadedSheet` under
  ARC-009). Every candidate this item names was individually judged renamed-or-kept by grep count
  (cheap and clearly internal → renamed with no deprecation shim needed; wide-surface → kept, noted
  here instead of churned):

  | Name | Grep count (definitions + call sites) | Decision | Rationale |
  |---|---|---|---|
  | `DataModelABC` → `CliArgsGroup` | 15 (2 files: `data_args.py`, its test) | **Renamed** | It is the ABC for CLI argument-group classes (`DataFile`/`DataAction`/`DataReport`), not a "data model" in the `models/sp_*.py` sense — the old name actively misled. No plain-alias shim: this is a private-to-the-module ABC, `git grep` confirms zero importers outside `data_args.py`/its test. |
  | `SpModelABC.DEFINITIONS`/`VAR_CONSTS` → `SpModelABC.ModelConfigKeys`/`CONFIG_KEYS` | 19 (3 files: `sp_model_abc.py`, `spreadsheet_processor.py`, its test) | **Renamed** | `DEFINITIONS`/`VAR_CONSTS` read as generic placeholders; `ModelConfigKeys`/`CONFIG_KEYS` names what they actually are — the `model_configurations` kwarg keys (`LEGEND_EXISTS_FILE`, `SCENARIO_EXISTS_FILE`, …). |
  | Per-model nested `class INFO(ConstantBase)` (8 models: `sp_legend`/`sp_composition`/`sp_scenario`/`sp_value`/`sp_description`/`sp_dictionary`/`sp_temporal_reference`/`sp_proportionality`) → `class Constants(ConstantBase)` | 8 definitions, 0 external references (each is only ever read as `self.CONSTANTS`/`Model.CONSTANTS`, never by its class name `INFO` from outside its own file) | **Renamed** | `INFO` reads like a logging level, not "this model's constants"; `Constants` matches the `CONSTANTS = Constants()` attribute it backs, and being purely local to each file made the rename free of any external call-site risk. |
  | `ModelMappingLegend` | 2 (both historical docstring/comment mentions in `rules/legend.py`/`tests/unit/rules/test_legend.py`, explaining behaviour parity with a since-deleted class) | **N/A — already gone** | The class itself was deleted in ARC-017 Phase 3 Port 6 (`SpLegendValidator`/`ModelMappingLegend` → `rules/legend.py`); the two remaining mentions are historical-parity prose, not a live identifier, so there is nothing left to rename. |
  | `SpreadsheetProcessor` vs `*Processing` helpers (`MessageFormattingProcessing`, `DataFrameProcessing`, `LegendProcessing`, `TreeProcessing`, and 9 others) | 665 (13 classes across `data_validate/`+`tests/`) | **Kept, noted** | Two distinct, both internally consistent conventions: `*Processing` names a stateless namespace of `@staticmethod` helpers (ARC-007's "procedural namespace" smell is tracked there, not here), `SpreadsheetProcessor` names the one stateful pipeline orchestrator. Renaming either family to remove the surface-level `-or`/`-ing` mismatch would touch 665 call sites for a cosmetic gain — out of proportion to a naming item; deferred to whenever ARC-007 actually restructures the `*Processing` helpers into plain modules (at which point the class names disappear entirely, not just get renamed). |
  | `DataLoaderModel` → `LoadedSheet` | 69 (14 files: production + tests) | **Renamed** (tracked as ARC-009's naming half, done together with this item) | See ARC-009's "Done" entry above — `DataLoaderModel` kept as a plain class alias for one release. |

  Typos (BUG-024's share of this item): see `01-bugs.md::BUG-024` — `legend_processing.py`'s
  `origina_value` → `original_value`, `data_args.py`'s "validaton" → "validation" docstring typo,
  `file_system_utils.py`'s "dempotent" → "Idempotent" docstring typo are all fixed in this slice.
  **ARC-013 is now done.**

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
- Priority: P2 · Effort: M · Status: in-progress
- Where: `helpers/tools/spellchecker/**` (was also `validators/spell/spellchecker_validator.py`,
  deleted by ARC-017 Phase 3 Port 8 — the rule module is `rules/spell.py` now).
- Problem: C extension + system hunspell; env-var configuration; tests need the library installed;
  Windows requires manual DLLs (`hunspell-win/` in .gitignore).
- Target: `SpellBackend` Protocol (`check(word) -> bool`, `suggest`) with `EnchantBackend` and a pure
  Python fallback (`symspellpy`/`pyspellchecker` with the bundled `.dic`); word-level cache.
- Done (Phase 5 slice, 2026-09-13 — Protocol half): `rules/spell.py` already had a private,
  `check_spelling_text_structured`/`errors_dictionary`-shaped `@runtime_checkable Protocol`
  (`_SpellBackend`, used to narrow `ctx.options["spell_backend"]`); this slice makes it public
  (`SpellBackend`, exported from `data_validate.rules`) and adds `clean_files_generated() -> None`
  to its surface — the third method `SpreadsheetProcessor._build_pipeline` calls on the same
  object (`self._spell_backend.clean_files_generated()`), completing the exact three-method shape
  this item's own "Target" line asks for (renamed from the abstract `check(word)`/`suggest` sketch
  to the concrete surface the codebase actually needs: `check_spelling_text_structured`,
  `errors_dictionary`, `clean_files_generated`). `SpreadsheetProcessor.__init__` now types
  `self._spell_backend: SpellBackend | None` instead of leaving it untyped, so every consumer
  (`rules/spell.py`'s `_backend()`, `SpreadsheetProcessor`) is decoupled from the concrete
  `SpellChecker`/`pyenchant` class at the type level. `PERF-006`'s word-level cache lives on
  `SpellCheckerController` (an implementation detail behind the Protocol), unaffected. Tests:
  `tests/unit/rules/test_spell.py::TestSpellBackendProtocol` —
  `FakeSpellBackend` (the existing test double) satisfies the Protocol,
  `SpellChecker` (constructed with its `DictionaryManager`/`SpellCheckerController`/
  `DataFrameProcessor` collaborators mocked, no real `enchant` needed) satisfies it too, and an
  object missing `clean_files_generated` does **not** satisfy it — proving the Protocol is
  checked structurally, not just declared.
- Still open (not this slice's scope, per this item's own instruction — "pure-Python fallback →
  wont-fix"): no `EnchantBackend` wrapper class exists yet (`SpellChecker` itself plays that role
  today, undifferentiated from the Protocol); no pure-Python fallback backend is implemented — a
  Windows/CI host without `pyenchant`/hunspell simply has no working spell-check backend today
  (mitigated by TOOL-008's `[spell]` extra decision: the dependency is optional, and the run
  degrades to "spell-check unavailable" rather than crashing, per SPELL-001's own
  dictionary/backend-error path). Implementing an actual `symspellpy`/`pyspellchecker`-backed
  fallback is real, scoped future work, not done here — **wont-fix for now** per this item's own
  brief, revisit if a host without `pyenchant` needs spell-check to actually run rather than
  degrade gracefully.
- Related: PERF-006, TOOL-008

### ARC-016 · Report generation builds HTML in Python
- Priority: P2 · Effort: M · Status: done
- Where: `controllers/report/file_report_generator.py` (was `:187-217,266-291`),
  `config/application_config.py` (was `:62-96`, fallback template as a class constant), regex-based
  template validation (was `:91-102` — all three now deleted).
- Target: `ReportModel` (dataclass) + Jinja templates with autoescape and i18n filters; PDF renderer
  pluggable.
- Done (migration Phase 4, ADR-0007 — implemented together with SEC-001/SEC-002):
  `controllers/report/report_model.py` declares `ReportSection` (`title`/`errors`/`warnings`,
  frozen, slotted) and `ReportModel` (frozen, slotted — name, formatted error/warning counts,
  total tests, `sections`, `skipped_tests`, date/version display flags and values,
  sector/protocol/user/file). `FileReportGenerator._build_report_model` builds one from a
  `ValidationReport` + the CLI args on `context`, replacing the deleted
  `_build_template_variables`/`_format_messages_as_html`/`_get_optional_field_text`; every field
  is a plain value, never a pre-built HTML fragment. `report_template.html` loops over
  `report.sections`/`report.skipped_tests` itself (`{% for %}`) instead of receiving
  pre-rendered HTML strings; the hand-rolled regex "does the template contain every required
  `{{ var }}`" validator (`_validate_html_template`) and its fallback constant
  (`ApplicationConfig.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS`) are both deleted — Jinja's own
  `TemplateNotFound`/`UndefinedError` (a subclass of `jinja2.TemplateError`) now reports a broken
  template through `build_report`'s existing SEC-004 exception handling instead. PDF renderer is
  pluggable per SEC-002 (WeasyPrint primary, `pdfkit` compatibility fallback, graceful skip).
  i18n filters/catalog-key labels are **not** part of this slice — see ADR-0007's "Implementation
  note" for why report labels stay hardcoded pt-BR HTML in the template for now (tracked under
  ARC-005/DOC-003 as a follow-up, not silently dropped).
- Related: SEC-001, SEC-002

### ARC-017 · Rule execution order and dependencies are implicit
- Priority: P2 · Effort: M · Status: done (PERF-007 parallel execution stays a separate, related item)
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
- Done (validators 5–8, Phase 3 Ports 4–7, not individually logged here at the time — see
  `04-testing.md`'s TST-001 entry and `08-migration-roadmap.md` for the per-port detail): temporal
  reference/scenario (`rules/temporal_reference.py`, `rules/scenario.py`), value
  (`rules/value.py`), legend (`rules/legend.py`), and proportionality (`rules/proportionality.py`)
  are each their own `RuleRegistry`, run through the same `_run_rule_registries`/
  `_build_rule_context` call shape as every port above.
- Done (eighth/last validator port, Phase 3 Port 8 — closes this item): `rules/spell.py` declares
  `SPELL_REGISTRY` (`SPELL-001`…`SPELL-005`, registered in the legacy validator's own check order:
  dictionary/backend errors first — never gated on any prerequisite — then description, then
  temporal reference, then scenario), run through the same `_run_rule_registries`/
  `_build_rule_context` call shape. With this port, every rule executed by
  `SpreadsheetProcessor` (structure, spelling, description, composition, temporal reference,
  proportionality, value, scenario, legend — nine registries in total) goes through
  `Engine(registry).run(ctx)`; `controllers/spreadsheet_processor.py` no longer hand-orders any
  validator construction, only which registries run in which order (still a fixed,
  hand-written sequence in `_build_pipeline`, not a `depends_on`-derived topological one across
  registries — each registry's *internal* rule order is topological via
  `RuleRegistry.topological_order()`, but registry-to-registry order is still explicit). Parallel
  execution (PERF-007) remains unimplemented — a separate, related item. **ARC-017 is now done**
  for its own scope (rule registry + topological execution + skipped-with-reason, replacing every
  hand-ordered validator construction); PERF-007's optional parallel pool is intentionally left
  open as a follow-on, not a blocker for closing this item.
- Related: PERF-007
