# ADR-0011: Testing policy: pytest + pytest-mock only, coverage ratchet, goldens

- Status: Accepted
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

The audit baseline (`.specs/quality/backlog/README.md`) records 878 passing tests, all located
under `tests/unit/helpers/`, running in ~3.3 s at 55.97 % total line coverage — with `main.py` at
0 %, `middleware/bootstrap.py` at 0 %, business-rule validators between 10.3 % and 34.4 %
(`proportionality_validator.py` 10.3 %, `compostion_graph_validator.py` 11.5 %,
`legend_validator.py` 11.7 %, `value_validator.py` 14.5 %, `composition_tree_validator.py` 16.5 %,
`spreadsheet_processor.py` 16.9 %, `description_validator.py` 18.7 %,
`file_structure_validator.py` 20 %, `file_report_generator.py` 23.8 %,
`spellchecker_validator.py` 25.5 %, `validation_report.py` 34.4 %). In other words, the 34
business rules that are the entire reason this tool exists have essentially no automated
verification (TST-001) — every existing test targets `helpers/`, none reach `models/`, `validators/`,
`controllers/`, or the CLI entry point. There is also no end-to-end safety net at all (TST-002):
the only artefacts resembling regression coverage are committed HTML/PDF reports under
`data/output/**`, which nothing asserts against and which are themselves flagged for removal
(SEC-009). `pyproject.toml`'s `[tool.pytest.ini_options] addopts` (line 108) already runs coverage
inline (`--cov=data_validate --cov-fail-under=50 ...`) mixed with test execution flags, with the gate
at 50 % while `TESTING.md` documents a stale "4 %" figure (DOC-001) — a threshold nobody has
revisited as coverage grew. `tests/conftest.py` is effectively empty (TST-003): no shared fixtures,
and components like `LanguageManager` write `<repo>/.config/store.locale` and `LoggerManager`
creates `data/output/logs` directly against the real filesystem during test runs, rather than an
isolated temp directory.

## Decision

Formalise, as of this execution, the testing policy the whole migration is measured against: pytest
+ `pytest-mock` exclusively — `unittest.mock` and `with patch()` context managers are forbidden
project-wide (already the de facto convention; now made a written, enforced rule in
`.claude/rules/testing.md`). Tests mirror the `data_validate/` package tree 1:1. Every **new**
module ships with ≥ 95 % line coverage; every bug fix ships with a regression test that fails
before the fix and passes after (already this backlog's own item format requirement, `.specs/
quality/backlog/README.md`). A golden end-to-end harness (`tests/e2e/test_golden.py`, ADR-0002) is
built as the first deliverable of Phase 0, giving the whole migration a safety net before any
business-rule code is touched. Coverage is **ratcheted**, not fixed: `tools/coverage_ratchet.py`
fails a build if total coverage drops below the last committed value, with roadmap targets of 70 %
(Phase 1 exit gate), 85 % (Phase 3 exit gate), 90 %+ (Phase 5 exit gate) rather than jumping straight
to a number the current 55.97 % baseline cannot support. `tests/conftest.py` gains real fixtures
(`repo_root`, `fixture_folder(name)`, an autouse `tmp_cwd` that `monkeypatch.chdir(tmp_path)`s so no
test writes `.config/` or `data/output/logs` into the repository) with an opt-out marker for any of
the 878 existing tests that turn out to depend on CWD, rather than editing those tests. Test
markers `unit`, `integration`, `e2e`, `slow`, `requires_enchant`, `requires_pdf` are registered so
CI and local runs can select subsets; `hypothesis` is adopted for parser-shaped code (number/date
parsing, CSV/XLSX round-trips); `pytest-benchmark` backs a perf regression threshold (PERF-009).

## Consequences

### Positive
- Every future change to the 34 verification categories gets a real test, closing the single largest
  coverage gap the audit found (TST-001) rather than leaving the tool's core purpose untested
  indefinitely.
- The coverage ratchet makes "coverage never goes down" an enforced fact instead of an aspiration,
  while still being achievable from day one at the actual 55.97 % starting point.
- Isolating tests from the real filesystem (CWD, `.config/`, `data/output/logs`) removes a class of
  flaky/order-dependent test failures and stops test runs from polluting the working tree.

### Negative
- Porting 95 %-coverage discipline to every new module is a real, ongoing cost during Phases 1-5,
  particularly for the business-rule validators currently at 10-25 % coverage; this is treated as
  necessary cost given TST-001's severity (P0), not optional.
- `hypothesis` and `pytest-benchmark` are new dependencies and new test-writing idioms the team
  must learn; scoped narrowly (parsers, one benchmark harness) to keep the learning curve bounded.

## Alternatives considered

### Continue using `unittest`/`unittest.mock`
Rejected: this is already the explicit, standing project convention (`.github/copilot-instructions.md`
§"MANDATORY: Use `pytest`... FORBIDDEN: Never use `unittest.mock`") and the existing 878 tests
already follow it; switching now would be a regression in consistency with no benefit, and
`pytest-mock`'s fixture-based API integrates better with the `conftest.py` fixtures this ADR adds.

### Set a fixed global coverage gate (e.g. 95 %) immediately, project-wide
Rejected: the current baseline is 55.97 % with entire subsystems (`main.py`, `Bootstrap`, most
validators) at 0-35 %; a fixed 95 % gate imposed today would fail every existing commit and provide
no incremental path — a ratchet from the honest starting point, rising through documented
milestones tied to migration phases, is achievable and still strictly monotonic.

### Skip the golden/e2e harness, rely solely on growing unit-test coverage during the rewrite
Rejected: unit tests alone cannot verify that the CLI's externally observed behaviour (HTML report
content, JSON stdout summary, exit code — the platform's actual contract) survives a refactor;
TST-002 is explicitly the first item the roadmap calls for precisely because unit coverage and
end-to-end behavioural equivalence are different guarantees, and the migration needs the latter
before it can safely delete old code (ADR-0002).

## Links

- Backlog: `TST-001` through `TST-010` (`04-testing.md`); `08-migration-roadmap.md` Phase 0
- Specs: `.specs/quality/testing-strategy.md`
- Related ADRs: ADR-0002 (golden harness), ADR-0010 (shared CI gate)

---
Last synced with code: 09279f4
