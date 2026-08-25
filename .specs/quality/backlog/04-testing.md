# 04 · Testing

Rules: pytest + pytest-mock only (no `unittest.mock`), tests mirror the package tree, every new
module ships with ≥ 95 % line coverage, every bug fix ships with a regression test, every business
rule has a unit test *and* a golden fixture case. See `.specs/quality/testing-strategy.md`.

### TST-001 · No tests for models, validators, controllers, CLI
- Priority: P0 · Effort: XL · Status: open
- Where: coverage 0 % `main.py`, 0 % `middleware/bootstrap.py`, 10.3 % `proportionality_validator.py`,
  11.5 % `compostion_graph_validator.py`, 11.7 % `legend_validator.py`, 14.5 % `value_validator.py`,
  16.5 % `composition_tree_validator.py`, 16.9 % `spreadsheet_processor.py`, 18.7 %
  `description_validator.py`, 20 % `file_structure_validator.py`, 23.8 % `file_report_generator.py`,
  25.5 % `spellchecker_validator.py`, 34.4 % `validation_report.py`, models 42–65 %.
- Problem: the 878 existing tests cover only `helpers/`. The business rules (the reason the tool
  exists) have zero automated verification.
- Proposed fix: one test module per rule with table-driven cases (valid, each failure mode, edge:
  empty sheet, missing column, `DI`, scenario/no-scenario); requires ARC-001 to construct validators
  without running them, otherwise test through the pipeline with in-memory frames.
- Related: TST-002

### TST-002 · No end-to-end / golden safety net for the migration
- Priority: P0 · Effort: M · Status: open
- Where: fixtures already exist — `data/input/data_ground_truth_01` (must produce 0 errors) and
  `data/input/data_errors_{01,09,11,13,14,15}`; reports committed under `data/output/**` are de-facto
  goldens but nothing asserts on them.
- Proposed fix: `tests/e2e/test_golden.py` runs the CLI (subprocess) per fixture with
  `--no-time --no-version` and compares a normalised JSON (`{rule_id: {errors: [...], warnings: [...]}}`)
  against `tests/e2e/golden/<fixture>.json`; `make harness-update` regenerates goldens with a diff
  review. This is the first thing to build — every refactor is then measured against it.
- Related: 08-migration-roadmap Phase 0

### TST-003 · Empty `conftest.py`, no shared fixtures, tests touch the real filesystem
- Priority: P1 · Effort: M · Status: open
- Where: `tests/conftest.py`, `LanguageManager` writes `<repo>/.config/store.locale` during tests,
  `LoggerManager` creates `data/output/logs`.
- Proposed fix: fixtures `app_context`, `sheet_bundle` (builder from dict → typed frames),
  `catalog` (fake translator returning keys), `tmp_input_folder`, `freeze_clock`; autouse fixture
  that isolates CWD in `tmp_path`.

### TST-004 · Coverage gate too low and not ratcheted
- Priority: P1 · Effort: S · Status: open
- Where: `pyproject.toml` `--cov-fail-under=50`; TESTING.md says 4 %.
- Proposed fix: ratchet script (`tools/coverage_ratchet.py`) that fails if coverage drops below the
  last committed value; targets 70 % (Phase 1), 85 % (Phase 3), 90 %+ (Phase 5); branch coverage on.

### TST-005 · No property-based, mutation or benchmark tests
- Priority: P1 · Effort: M · Status: open
- Proposed fix: `hypothesis` for `NumberFormattingProcessing`, `CollectionsProcessing` patterns,
  CSV/XLSX readers (round-trip), legend interval logic; `mutmut` on `rules/`; `pytest-benchmark` on a
  synthetic 10k×50 `valores` sheet.
- Related: PERF-009

### TST-006 · Assertions bound to Portuguese message text
- Priority: P2 · Effort: M · Status: open
- Problem: once messages come from a catalog (ARC-004), tests must assert on `Issue.rule_id`,
  `row`, `column`, `params`, not on rendered strings; rendered strings are covered by catalog tests
  and goldens.

### TST-007 · CI runners lack system dependencies for real spell-check / PDF tests
- Priority: P2 · Effort: S · Status: open
- Where: `.github/workflows/*unit-tests*.yml` (no `apt install enchant-2 hunspell-pt-br
  wkhtmltopdf`), Windows job has no enchant.
- Proposed fix: install deps on Linux; mark spell/PDF tests with `@pytest.mark.requires_enchant` /
  `requires_pdf` and skip when absent; pure-Python spell fallback (ARC-015) removes the need.

### TST-008 · Test execution ergonomics
- Priority: P2 · Effort: S · Status: open
- Proposed fix: `pytest-xdist` (`-n auto`), markers `unit/integration/e2e/slow`, `make test-unit`,
  `make test-e2e`, `--durations=10`, `-p no:cacheprovider` in CI.

### TST-009 · Dead test copies in `local_data/`
- Priority: P3 · Effort: S · Status: open
- Where: `local_data/test_legend_processing.py`, `local_data/old_legend_processing.py`
- Proposed fix: delete (gitignored anyway); nothing in `local_data` is a source of truth.

### TST-010 · Test data builders for the protocol
- Priority: P1 · Effort: M · Status: open
- Proposed fix: `tests/factories.py` producing minimal valid bundles (description + composition +
  values + temporal reference, optional scenarios/legend/proportionalities) with helpers to inject a
  single defect; used by rule tests and by fixture generation for benchmarks.
