# AGENTS.md

Tool-agnostic contributor guide for `data_validate` (`canoa_data_validate`,
codename *Canoa*) — read by any AI coding assistant (Copilot, Codex, Cursor,
Claude Code), not only Claude. Claude Code also reads `CLAUDE.md`, which
points back here; this file does not repeat that one beyond a pointer.

## Purpose

A multilingual spreadsheet validator for the AdaptaBrasil climate-adaptation
platform (INPE). It reads a bundle of `.csv`/`.xlsx` sheets describing
climate indicators, applies 34 structural and business-rule checks defined
by Protocol v1.13, and produces an HTML/PDF report plus a JSON summary on
stdout that the platform consumes. The codebase is mid-migration to a new,
cleaner architecture (strangler fig) — see `.specs/quality/backlog/` and
`.specs/architecture/target-architecture.md`.

## Build, test, lint

- Package manager: Poetry. Setup: `poetry install --sync` (or `make setup`).
- Run tests: `poetry run pytest` (`make test-unit`, `make test-e2e`).
- Lint/format: `poetry run ruff check .` / `poetry run ruff format .`
  (`make lint`).
- Type check: `poetry run mypy` (`make typecheck`).
- Security: `poetry run bandit -r data_validate` and `poetry run pip-audit`
  (`make security`).
- Everything at once: `make check`.
- Run the validator on a sample bundle:
  `poetry run canoa-data-validate --input_folder data/input/<fixture> --output_folder <out>`.

## Folder structure

```
data_validate/
  config/        configuration, NamesEnum (verification-name keys)
  controllers/   context (DI), SpreadsheetProcessor orchestrator, report
  helpers/       base utils, shared validation/formatting/processing, tools
  middleware/    application bootstrap (locale)
  models/        one Sp* model per sheet (SpModelABC subclasses)
  static/        dictionaries, locale catalogs, Jinja report templates
  validators/    structure/, spell/, spreadsheets/<sheet>/ business rules
  main.py        entry point
tests/           mirrors data_validate/; tests/e2e/ golden harness
.specs/          specifications: architecture, business rules, API, quality
.claude/         agents, commands, rules, skills (see CLAUDE.md)
docs/adrs/       architecture decision records
tools/           dev scripts (harness runner, i18n check, coverage ratchet)
```

## Coding conventions

- Python 3.12+, type hints everywhere, Google-style docstrings in English.
- Line length **120** (project standard going forward — the legacy
  `black` config said 150; that is being retired, not the target).
- No hardcoded user-facing strings — everything through the i18n catalog.
- No global state; dependencies passed through constructors.
- Full detail and rationale: `.claude/rules/coding-standards.md`,
  `dataframe-conventions.md`, `architecture-boundaries.md`.

## Testing conventions

- `pytest` + `pytest-mock` exclusively — `unittest.mock` is forbidden.
- Test tree mirrors `data_validate/`; class `Test<Unit>`, function
  `test_<unit>_<scenario>`.
- **Coverage gate is 50 % today and rises by ratchet** (currently enforced
  at 55.97 % — do not lower it). Any brand-new module needs ≥ 95 % coverage
  before merge. (The old `copilot-instructions.md` claimed "100 % mandatory
  for new files" and a "4 %" gate; both were stale — this section is the
  corrected figure.)
- Full detail: `.claude/rules/testing.md`.

## Anti-patterns (do not do these)

- `.iterrows()` in a validation rule — vectorise instead.
- Work inside `__init__` (I/O, calling `run()`) — construct, then invoke.
- A generic/bare `except Exception` that hides the real error.
- Hardcoded pt-BR/en-US strings in code instead of catalog keys.
- `git push`, `git add .`, or committing without updating the matching spec.

## Adding a validation rule

Follow the `validation-rule-authoring` skill (`.claude/skills/`) end to end:
rule ID registration, message keys in both catalogs, a pure vectorised rule
function, registry/`NamesEnum` wiring, table-driven unit tests, a golden
case, and the business-rule spec update.

## Security policy

Spreadsheet input is untrusted; HTML report output keeps Jinja2 autoescape
on; no `eval`/`exec`/unpickling of file-derived data; input size limits are
enforced; secrets never enter the repo. `bandit`/`pip-audit` run in CI and
must stay clean. Full policy: `.claude/rules/security.md` and
`.specs/quality/security.md`. Report a vulnerability per `SECURITY.md`.

## Pointers

Claude-specific orchestration, standing instructions, and the quick map of
specs/backlog/ADRs live in `CLAUDE.md`. Full specifications live under
`.specs/`, starting at `.specs/README.md`.
