# 08 · Migration roadmap

The migration produces a **new source tree** that is elegant, scalable, fast and organised while the
current CLI keeps working for the Canoa platform at every step. The strategy is *strangler fig*:
build the new core next to the old one, route the pipeline through it rule by rule, verify with the
golden harness, delete the old code when a slice is fully migrated.

Every phase has an exit gate. A phase is not done until the gate is green in CI and the specs under
`.specs/` are updated (`.claude/rules/spec-sync.md`).

## Phase 0 — Safety net (no behaviour change)
Closes: TST-002, TST-003, TST-004, TST-008, TOOL-001, TOOL-002, TOOL-003, TOOL-004, TOOL-007,
SEC-005, SEC-006, DOC-001, DOC-005
1. Golden e2e harness over `data/input/*` (`tests/e2e/`), `make harness-update`.
2. CI gates: ruff, ruff-format, mypy (non-strict on legacy), bandit, pip-audit, unit + e2e, coverage
   ratchet from 54.99 % (measured 55.97 % with legacy exclusions; baseline in `tools/coverage_baseline.txt`; gate `fail_under = 54` in `pyproject.toml` and Makefile).
3. Standard pre-commit; delete pipeline-running hooks.
4. `conftest.py` fixtures + CWD isolation; `pytest-xdist`.
5. Rewrite root docs; delete `copilot-instructions.md`; `.claude/`, `.specs/`, `docs/adrs/` in place.
Gate: `make check` green on Linux and Windows; goldens byte-stable across 3 runs.
Status (2026-08-25): Done — TST-002, TST-004, TST-008, TOOL-001, TOOL-002, TOOL-003, TOOL-004, TOOL-007, SEC-006, DOC-001, DOC-005 (11 items). In-progress — TST-003, TOOL-006, SEC-005 (3 items). Remaining — run `pre-commit install`, TOOL-006 artefacts, SEC-005 dependency upgrades, TST-003 autouse isolation.

## Phase 1 — Foundations: context, config, issues, CLI
Closes: BUG-001, BUG-004, BUG-005, BUG-008, BUG-009, BUG-010, BUG-011, BUG-017, BUG-021, BUG-023,
ARC-002, ARC-003, ARC-004 (model only), ARC-006, ARC-011, ARC-012, SEC-008, PERF-004, TOOL-005,
TOOL-008
1. `SheetSpec` registry (single source of truth) — ADR-0003.
2. `Issue`/`Severity`/`ValidationResult` + `MessageCatalog`; adapter that renders the *same strings
   as today* so goldens stay green — ADR-0004.
3. `AppContext` (locale, options, clock, catalog, logger) built once in `main()`; delete
   `Bootstrap`, `.config/store.locale`, module singletons.
4. New CLI (`data_validate/cli.py`, argparse or Typer) with explicit aliases, exit codes, `--json`;
   old spellings kept as deprecated aliases — ADR-0005.
Gate: goldens unchanged; `mypy --strict` on new modules; coverage ≥ 70 %.

## Phase 2 — Loading & normalisation
Closes: BUG-002, BUG-003, BUG-013, BUG-014, BUG-015, BUG-018, ARC-007 (models), ARC-009, PERF-002,
PERF-003, PERF-005, SEC-003
1. `SheetLoader` returning `LoadResult`; readers driven by `SheetSpec`; size limits.
2. `Normalizer` producing an immutable typed `SheetFrame` per sheet (nullable dtypes, invalid masks)
   in **one pass**; models become thin wrappers (or disappear).
3. Structural checks (columns, unnamed, `|`) become rules `STRUCT-*`.
Gate: goldens unchanged; benchmark baseline recorded (PERF-009).

## Phase 3 — Rules engine
Closes: ARC-001, ARC-005, ARC-008, ARC-017, BUG-006, BUG-007, BUG-019, BUG-025, BUG-026, PERF-001,
PERF-007, TST-001, TST-006, TST-010, DOC-002, DOC-003
1. `Rule` protocol + registry with `rule_id`, `requires`, `depends_on`, `severity`; engine handles
   prerequisites and *skipped-with-reason* — ADR-0006.
2. Port validators one sheet at a time (order: structure → description → composition → temporal
   reference → value → scenario → legend → proportionality → spell), vectorising as they move; each
   rule gets unit tests + a golden case; messages move to the catalog (pt_BR and en_US).
3. Delete `validators/`, `helpers/common/validation/` once empty.
Gate: goldens unchanged (message text identical); all 34 `NamesEnum` rules mapped to rule IDs in
`.specs/business-rules/`; coverage ≥ 85 %.

## Phase 4 — Reporting & i18n completion
Closes: SEC-001, SEC-002, ARC-016, BUG-016, BUG-020, DOC-004, DOC-006
1. `ReportModel` + Jinja templates with autoescape; HTML, JSON, console renderers; PDF via WeasyPrint
   behind `[pdf]` extra — ADR-0007.
2. Localised report template; catalog parity test; `PROTOCOL_VERSION` in report.
Gate: XSS golden test; goldens re-baselined once (reviewed diff), then stable.

## Phase 5 — Spell-check, performance, release
Closes: ARC-015, BUG-022, SEC-007, PERF-006, PERF-008, PERF-009, TST-005, TST-007, TOOL-006,
TOOL-009, TOOL-010, ARC-010, ARC-013, ARC-014, BUG-024, DOC-007
1. `SpellBackend` protocol; enchant + pure-Python fallback; word cache.
2. Benchmarks in CI with thresholds; optional parallel rule execution.
3. Release automation (tag → PyPI), docs to Pages, remove committed artefacts.
4. Final layout cleanup and renames; `mypy --strict` project-wide; coverage ≥ 90 %.
Gate: 1.0.0 release candidate.

## Working agreement per item
1. Pick an item → `/backlog <ID>` (creates a branch `feat/<ID>-slug` or `fix/<ID>-slug`).
2. Orchestrator writes the task brief (context, files, acceptance, tests) and delegates to a
   subagent per `.claude/rules/model-delegation.md`.
3. Subagent implements with TDD; `make check` locally.
4. `/review` (code-reviewer + security-auditor) → fix → `/spec-sync` → commit (Conventional Commits,
   reference the ID) → mark item `done` here.
