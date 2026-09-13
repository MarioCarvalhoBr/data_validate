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

| Priority | Count | Status | Highlights |
|---|---|---|---|
| P0 | 7 | 3 done, 4 open | remaining: SEC-001, TST-001, ARC-001, ARC-002 |
| P1 | 28 | 13 done, 5 in-progress, 10 open | |
| P2 | 43 | 17 done, 5 in-progress, 21 open | |
| P3 | 13 | 4 done, 1 wont-fix, 8 open | |
| **Total** | **91** | **37 done, 10 in-progress, 1 wont-fix, 43 open** | |

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
