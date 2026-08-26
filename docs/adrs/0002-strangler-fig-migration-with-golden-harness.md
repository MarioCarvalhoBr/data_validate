# ADR-0002: Strangler-fig migration with a golden end-to-end harness as the safety net

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

The current pipeline is a straight-line call chain: `main.py` builds `DataArgs`, runs `Bootstrap`,
builds `GeneralContext`, then `SpreadsheetProcessor.__init__` (`controllers/
spreadsheet_processor.py:94`, `self.run()`) executes `_prepare_statement → _read_data → _configure
→ _build_pipeline → _report` synchronously inside the constructor (ARC-001: "work is done in
constructors"). Every model (`models/sp_*.py`) and validator
(`validators/spreadsheets/*_validator.py`) does the same — `self._prepare_statement(); self.run()`
in `__init__` (see `validators/spreadsheets/base/base_validator.py:87`, `self.initialize()` called
from `__init__`). This means the object graph cannot be constructed and inspected without running
the whole pipeline, and it means the 878 existing tests (all under `tests/unit/helpers/` per the
backlog baseline) test none of `main.py` (0 % coverage), `middleware/bootstrap.py` (0 %), or the
business-rule validators (10–35 %) — TST-001. There is **no** automated check today that the CLI's
externally-visible behaviour (HTML report content, JSON stdout summary, exit code) is preserved
across a change; the only safety net is manual inspection of `data/output/**` reports that happen
to be committed to git (TST-002, SEC-009). AdaptaBrasil's platform depends on that exact stdout
`<{...}>` JSON fragment (`controllers/report/file_report_generator.py:239-263`) and on the HTML
report structure — any regression there breaks the platform silently, since the process exits 0
even on crashes (SEC-008).

## Decision

Migrate with a **strangler-fig** strategy: build the new layered core
(`.specs/architecture/target-architecture.md` — `cli/app/specs/loading/normalizing/rules/
reporting/i18n/spell/util`) next to the current tree, and route the pipeline through it one rule
or one sheet at a time, per the five phases in `08-migration-roadmap.md` (Phase 0 safety net,
Phase 1 foundations, Phase 2 loading/normalisation, Phase 3 rules engine, Phase 4 reporting/i18n,
Phase 5 spell/perf/release). Old code for a slice is deleted only after the golden harness proves
the new path produces the same externally-observable result. The harness
(`tests/e2e/test_golden.py`, `tests/e2e/golden/<fixture>.json`, `tests/e2e/golden/CHANGELOG.md`,
built in this same execution per `08-migration-roadmap.md` Phase 0 item 1) runs
`poetry run python -m data_validate.main` as a subprocess against every folder in `data/input/*`
(including `data_ground_truth_01`, which must yield zero errors, and the `data_errors_*` fixtures),
parses the generated HTML report into a normalised `{rule_id: {errors: [...], warnings: [...]}}`
structure (via `html.parser`, not brittle regex) plus the stdout JSON summary, and diffs it against
the committed golden. `make harness-update` regenerates goldens only with a reviewed diff and a
recorded reason (`tests/e2e/golden/CHANGELOG.md`); spelling-dependent output is normalised out
(`"spell_skipped": true`) when `enchant` is unavailable in CI. Each phase's exit gate
(`08-migration-roadmap.md`) requires the goldens to stay byte-stable across 3 consecutive runs
before the corresponding old module is deleted.

## Consequences

### Positive
- The platform's contract (exit code, HTML content, JSON summary) is protected by an automated,
  repeatable check from day one, instead of relying on manual review of committed report files.
- Each migration phase is independently shippable and revertible: a slice that breaks the harness
  is caught before merge, not discovered by the platform team in production.
- Coverage grows incrementally and honestly (55.97 % → 70 % → 85 % → 90 %+ per TST-004) because the
  harness forces every ported rule to be exercised end-to-end, not just unit-mocked.

### Negative
- Running the full pipeline as a subprocess per fixture is slower than pure unit tests (mitigated
  by marking it `@pytest.mark.e2e`, run separately from `make test-unit`, and by keeping the
  fixture set small and curated).
- Two implementations of overlapping logic (old validators + new rules) coexist during each phase,
  temporarily increasing the codebase's total size and requiring discipline to delete the old side
  promptly once a slice's gate is green.
- Golden fixtures can mask a genuine improvement as a "regression" if the diff isn't reviewed
  carefully; mitigated by requiring a written reason in `tests/e2e/golden/CHANGELOG.md` for every
  `make harness-update`.

## Alternatives considered

### Big-bang rewrite
Rejected: the validator is a dependency of a live platform (AdaptaBrasil) with no feature-flagging
or staged rollout mechanism on the CLI side; a full rewrite merged in one step has no rollback path
if a subtle business-rule regression (e.g. in the 34 verification categories) reaches production, and the
current 55.97 % coverage / 0 % on core validators gives no confidence a rewrite would be
behaviourally equivalent without an explicit comparison mechanism.

### Branch-by-abstraction with a runtime feature flag choosing old vs. new code path
Rejected: feature flags are valuable when both code paths serve live traffic simultaneously and
need a fast kill-switch; `data_validate` is a batch CLI invoked per run with no shared runtime
state between invocations, so a flag adds indirection (`if use_new_pipeline: ... else: ...`
scattered through `SpreadsheetProcessor`) without the operational benefit a web service would get.
The golden harness gives the same confidence at merge time instead.

### Shadow/parallel-run diffing in production (run old and new pipelines on live input, compare)
Rejected: there is no "production" execution environment this tool runs inside — it is invoked
per-bundle on a shared server per the CLI contract, not a long-running service. Shadow-running
would mean executing every real spreadsheet bundle twice against real (frequently sensitive) sector
data outside of CI, which the golden-harness-on-checked-in-fixtures approach avoids entirely.

## Links

- Backlog: `TST-001`, `TST-002` (`04-testing.md`); `ARC-001` (`03-architecture.md`);
  `08-migration-roadmap.md` (all phases)
- Specs: `.specs/architecture/target-architecture.md`, `.specs/quality/testing-strategy.md`
- Related ADRs: ADR-0001, ADR-0011 (testing policy), ADR-0004, ADR-0006

---
Last synced with code: 09279f4
