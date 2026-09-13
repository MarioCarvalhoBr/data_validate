# Quality Backlog — data_validate (Canoa)

Audit snapshot taken on 2026-08-25 against `main` @ `a4f76c7` (v0.7.65b732), after reading every
`*.py` file under `data_validate/` and `tests/`, the CI workflows, `pyproject.toml`, `Makefile`,
scripts and the legacy `.github/copilot-instructions.md`.

This backlog is the **source of truth for the migration**. Items are picked one at a time
(`/backlog next` or by ID), implemented by a subagent following `.claude/rules/`, verified by tests
under `tests/`, and closed by updating the item status here and the matching spec under `.specs/`.

## Baseline numbers

| Metric | Value |
|---|---|
| Tests | 878 passing in ~3.3 s, **all** under `tests/unit/helpers/` |
| Line coverage | **55.97 %** measured with the legacy coverage exclusions (`pass`/`continue`/`break` excluded); **54.99 %** under the current configuration, which is the ratchet baseline in `tools/coverage_baseline.txt`; the gate is `fail_under = 54` in `pyproject.toml` and `--cov-fail-under=54` in the Makefile |
| Lint | `ruff check .` clean (default rule set only, line length not enforced by ruff) |
| Type checking | none (no mypy/pyright configured) |
| Security tooling | none (no bandit / pip-audit / CodeQL) |
| Python | 3.12.3, Poetry 2.2.1, pandas 3.0.1, pyenchant 3.3.0, pdfkit 1.0.0 (wkhtmltopdf) |
| Locale catalogs | pt_BR 76 keys, en_US 72 keys (4 missing), both contain leftover demo keys |

## Files

| File | Scope |
|---|---|
| [01-bugs.md](01-bugs.md) | Correctness defects found in the current code |
| [02-security.md](02-security.md) | Security and robustness issues |
| [03-architecture.md](03-architecture.md) | Design debt blocking elegance, scalability and maintainability |
| [04-testing.md](04-testing.md) | Test coverage gaps and test infrastructure |
| [05-performance.md](05-performance.md) | Hot spots and scalability limits |
| [06-tooling-ci.md](06-tooling-ci.md) | Build, CI/CD, packaging, pre-commit |
| [07-docs-i18n.md](07-docs-i18n.md) | Documentation and internationalisation |
| [08-migration-roadmap.md](08-migration-roadmap.md) | Phased plan that orders the items above |
| [09-protocol-v116.md](09-protocol-v116.md) | Protocol v1.16 alignment (PROTO-001…017, incl. the optional `spd_data.json` territory registry) |

## Item format

```
### <ID> · <title>
- Priority: P0 (blocker) | P1 (high) | P2 (medium) | P3 (low)
- Effort: S (< 2 h) | M (half day) | L (1–3 days) | XL (> 3 days)
- Status: open | in-progress | done | wont-fix
- Where: file:line references
- Problem / Evidence / Proposed fix / Tests required / Related
```

IDs are stable; never renumber. New findings are appended at the end of the relevant file.

## Priority summary

Recomputed 2026-09-13 (Phase 5 round L2) from a fresh `grep -n "^- Priority:"` of every item in
files 01–07 (93 unique items — see the note below on a duplicate `BUG-003` heading found in
`01-bugs.md`, counted once here). This recompute supersedes the previous one (also dated
2026-09-13): several items closed by earlier same-day slices (ARC-010/011/012/013/016/017 among
others) had already flipped their own header's `Status:` line without the table below being
recomputed afterward — this pass re-derives every count directly from the current per-item
headers, not from the previous table's numbers. `09-protocol-v116.md`'s 18 `PROTO-*`/`TERR-*`
items are tracked separately as **Phase 6 scheduled** (all `open` by design — Phase 6 runs only
after files 01–07 are done/wont-fix, per `08-migration-roadmap.md`) and are not part of this
table.

| Priority | Count | Status | Highlights |
|---|---|---|---|
| P0 | 7 | 7 done | fully closed — SEC-001, TST-001/002, ARC-001/002, BUG-001/002 |
| P1 | 29 | 26 done, 2 in-progress, 1 wont-fix | in-progress: ARC-004, ARC-006; wont-fix: PERF-003 |
| P2 | 43 | 39 done, 1 in-progress, 1 open, 2 wont-fix | open: ARC-014; in-progress: ARC-015; wont-fix: PERF-005/007 |
| P3 | 14 | 13 done, 1 wont-fix | wont-fix: BUG-012 |
| **Total** | **93** | **85 done, 3 in-progress, 1 open, 4 wont-fix** | +18 Phase 6 `PROTO-*`/`TERR-*` items (all open, scheduled) |

Note: `01-bugs.md` contains two `### BUG-003` headings (one with a full "Done" write-up, one a
stale duplicate with `Status: open` and no "Done" note, immediately preceding `BUG-004`). Counted
once (as done, matching the substantive entry) in the table above. `01-bugs.md` is owned by a
parallel work-stream in this phase and was not edited here — flagged for that owner to dedupe.

Status snapshot: 2026-09-12 — 35 done, 7 in-progress, 1 wont-fix, 48 open (of 91 items incl.
TOOL-011). This slice moved SEC-008 and PERF-004 to done, and ARC-011/ARC-012/TOOL-008 to
in-progress (see `03-architecture.md`, `02-security.md`, `05-performance.md`,
`06-tooling-ci.md`, `08-migration-roadmap.md`).

Status snapshot: 2026-09-12 (Phase 2c models slice) — 37 done, 9 in-progress, 1 wont-fix, 44
open. This slice moved BUG-002 and BUG-003 to done, and ARC-007 and PERF-003 to in-progress
(see `01-bugs.md`, `03-architecture.md`, `05-performance.md`, `08-migration-roadmap.md`).
BUG-014 was reviewed but left open (finding recorded in `01-bugs.md`).

Status snapshot: 2026-09-12 (Phase 3a rule-engine core slice) — 37 done, 10 in-progress, 1
wont-fix, 43 open. This slice moved ARC-017 to in-progress: `data_validate/rules/` (`context.py`,
`registry.py`, `engine.py`) implements the `RuleContext`/`RuleSpec`/`RuleRegistry`/`Engine`
core from ADR-0006, 100% covered by `tests/unit/rules/`; ARC-001 and ARC-008 gained a note each
(the `Rule.check`/skipped-with-reason shapes those items target now exist and are exercised, but
no validator or model constructor was touched) (see `03-architecture.md`,
`docs/adrs/0006-rule-registry-with-prerequisites.md`).

Status snapshot: 2026-09-13 (Phase 3 Port 8 slice — the migration's last validator port). Not a
recomputed aggregate (the intervening Phase 3b/Port 2–7 slices did not update the counts/snapshot
above either — see each backlog file's own item statuses for the authoritative per-item state).
This slice: `rules/spell.py` (`SPELL_REGISTRY`, `SPELL-001`…`SPELL-005`) replaces the deleted
`validators/spell/spellchecker_validator.py::SpellCheckerValidator` — the eighth and last
validator ported — so `data_validate/validators/` (and its mirrored `tests/unit/validators/`) is
deleted **entirely**, moving **ARC-008 → done**. The same slice fixes every remaining
constructor-runs-pipeline case (`SpModelABC`/every `Sp*` model/`SpreadsheetProcessor`), moving
**ARC-001 → done** (the one accepted exception, `DataArgs`'s argparse-in-`__init__`, is a
CLI-boundary object, out of scope). **ARC-017 → done** (every validator now runs through a
`RuleRegistry`/`Engine`, replacing every hand-ordered validator construction; PERF-007's parallel
execution is a separate, still-open follow-on). **TST-001 → done** (`04-testing.md`: every rule
ID now has a dedicated, table-driven unit test module; models/controllers/CLI are exercised via
`tests/unit/models/test_model_isolation.py`, `tests/unit/controllers/test_spreadsheet_processor.py`,
`tests/unit/test_main.py`). ARC-005 stays in-progress (spelling's messages are now catalog keys;
~15 hardcoded pt-BR f-strings remain in `models/sp_*.py`'s structural/cleaning checks and in
`controllers/report/file_report_generator.py`'s report labels). See `03-architecture.md`,
`04-testing.md`, `.specs/business-rules/spelling.md`.

Status snapshot: 2026-09-13 (Phase 4 report-rendering slice, ADR-0007). Moves **SEC-001 → done**
(the P0 stored-XSS item), **SEC-002 → done**, and **ARC-016 → done**. `FileReportGenerator` is
rebuilt on `Environment(loader=PackageLoader("data_validate", "static/report"),
autoescape=select_autoescape(["html"]))`; `report_template.html` loops over
`ReportModel.sections`/`skipped_tests` (`controllers/report/report_model.py`, new, ARC-016)
instead of receiving Python-built HTML strings; `_format_messages_as_html`/
`_get_optional_field_text`/the regex template validator and its fallback constant are all
deleted. PDF generation is now optional and pluggable (WeasyPrint primary via the `[pdf]` extra,
`pdfkit`/`wkhtmltopdf` a compatibility fallback, graceful skip when neither is usable) — `pdfkit`
is removed from `[project].dependencies`, closing `pip-audit`'s last `--ignore-vuln`'d finding
(`make security` runs a plain `pip-audit`, no escape hatch). e2e: 7/8 golden fixtures stayed
byte-identical; `data_errors_01` gained one reviewed line change (escaping now preserves content
a previous non-escaping render let the harness's naive HTML extractor mangle); one new fixture,
`data_errors_xss`, added additively with its own golden. See `02-security.md`, `03-architecture.md`,
`docs/adrs/0007-report-rendering-jinja2-autoescape-weasyprint.md`,
`tests/e2e/golden/CHANGELOG.md`.

Status snapshot: 2026-09-13 (Phase 5 documentation-closure slice). Moves **TOOL-010 → done**
(dependency upgrade-cadence/caret-range policy written in `.specs/infrastructure/dependencies.md`),
**DOC-003 → done** (`rule.<RULE-ID>.<kind>` convention confirmed live for all 77 `rule.*` keys per
locale, out of 137 total; remaining legacy prefixes documented as by-design in
`.specs/i18n/catalog.md`), **ARC-002 → done** (module singletons `SHEET`/`METADATA` confirmed
immutable-after-init and side-effect-free at import; the `data_loader` `Config`/`SingletonMeta`
singleton and the `os.environ` mutation (BUG-022) were already resolved by earlier slices),
**TST-006 → done** (every `tests/unit/rules/test_*.py` module asserts on `Issue.rule_id`/
`message_key`/`params` against an identity `translate` stub, never a rendered pt-BR string),
**PERF-002 → done (with note)** and **PERF-003 → wont-fix (residual)** (both measured
budget-immaterial against the PERF-009 numbers — 3.05s/184MB vs. the 10s/1GB budget), **PERF-005 →
wont-fix** (same budget margin; revisit trigger is a budget breach or ~10x data growth, matching
PERF-007's precedent), and **TOOL-008 → done (with note)** (`pyenchant` stays a main dependency,
not moved to a `[spell]` extra — its already-lazy import is wrapped in a `try/except Exception`
that would surface a missing package the same way a broken system hunspell install is surfaced
today, as a `SPELL-001` business-rule error, not a crash). **ARC-006 stays in-progress**: the
Demeter chain into rule code is gone (`data_models_context.context.` is a zero-hit grep in
production code), but `DataModelContext.get_instance_of`'s linear `isinstance` scan is still used
by the report-building step in `spreadsheet_processor.py`. This slice also recomputed the priority
summary table above from a fresh `grep` of every `Status:` line (93 unique items across files
01-07, one duplicate `BUG-003` heading found and noted, not fixed — owned by a parallel
work-stream). See `03-architecture.md`, `04-testing.md`, `05-performance.md`, `06-tooling-ci.md`,
`07-docs-i18n.md`, `08-migration-roadmap.md`, `.specs/infrastructure/dependencies.md`,
`.specs/i18n/catalog.md`.

Status snapshot: 2026-09-13 (Phase 5 round L2 — legend i18n/vectorisation, dead-code cleanup,
SEC-004 narrowing, ARC-007 closure). Moves **ARC-005 → done** (the last open gap,
`legend_processing.py`'s LEG-001…011, is now catalog-keyed via a `translate` parameter threaded
from `models/sp_legend.py`; the only remaining pt-BR literals anywhere in `models/`/
`helpers/common/` are 3 hits in `dataframe_processing.py`'s dead
`check_dataframe_unique_values`/`column_exists`, unreachable in production, tracked as residual
debt rather than reopening this item), **PERF-001 → done** (the same four `.iterrows()` loops in
`legend_processing.py` are vectorised — masks, `Series.apply`, `Series.shift(1)` — leaving zero
executable `.iterrows()` calls anywhere in `data_validate/`), **SEC-004 → done** (the two sites
this item's own prior note flagged for follow-up are both fixed: `dictionary_manager.py`'s three
enchant-boundary broad catches narrowed to `(enchant.errors.Error, OSError, ImportError)`;
`spellchecker.py::check_spelling_text`, dead in production, deleted along with its broad catch),
and **ARC-007 → done** (a descope decision, not a migration: the standalone `Normalizer`/
`SheetFrame` layer the target architecture sketched is retired — `models/sp_*.py` already is the
normalizing layer by design, every concern this item named is independently resolved by
BUG-002/BUG-003/ARC-005/ARC-008/ARC-017, see **ADR-0015** and the updated
`.specs/architecture/target-architecture.md`). Two dead-code symbols this round's dead-code sweep
flagged are deleted: `helpers/common/validation/character_processing.py` (whole module, zero
production callers) and `helpers/common/processing/collections_processing.py::
find_differences_in_two_set_with_message` (zero callers); the deleted module's test file
(`test_dataframe_character_processing.py`) also covered the *live* `DataFrameProcessing` class
sharing that file, so its `DataFrameProcessing`-only tests were preserved, not deleted, under a
new name (`test_dataframe_processing.py`) rather than lost. Full unit suite: 1672 passed (up from
1605 mid-slice, before that test-file split was corrected), 4 skipped, 95.07 % coverage;
`tests/e2e` 8/8 twice, byte-identical; `ruff`/`mypy --strict`/`bandit` clean. This slice also fully
recomputed the priority summary table above (see its own methodology note) — several items closed
by other same-day slices had not been reflected in the table before this recompute. See
`02-security.md`, `03-architecture.md`, `05-performance.md`, `.specs/business-rules/legend.md`,
`.specs/architecture/target-architecture.md`, `docs/adrs/0015-descope-standalone-normalizer.md`.
