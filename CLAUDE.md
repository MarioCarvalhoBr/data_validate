# CLAUDE.md

**Data Validate** (`canoa_data_validate`, codename *Canoa*) validates AdaptaBrasil
climate-indicator spreadsheets against Protocol v1.13, and is being migrated to a
new, elegant/scalable/fast/organised source tree while keeping the CLI/report/JSON
contract with the platform green at every step. Read `.specs/00-overview.md` first.

## Standing instructions

- Orchestrate, don't hand-code: follow `.claude/rules/model-delegation.md` for every
  coding task — delegate to `sonnet`/`haiku` subagents, review before calling it done.
- Every behaviour/rule/contract/convention change updates its spec in the same
  commit — `.claude/rules/spec-sync.md`.
- TDD with `pytest` + `pytest-mock` only (never `unittest.mock`).
- Never `git push`. Never `git add .`. Conventional Commits, in English.
- All generated prose is English; Portuguese is only for message catalogs and the
  end-user report.

## Quick map

| What | Where |
|---|---|
| Specs (architecture, business rules, API, quality) | `.specs/` — start at `.specs/README.md` |
| Migration backlog (89 items, prioritised) | `.specs/quality/backlog/` |
| Architecture decisions | `docs/adrs/` |
| Standing conventions (auto-loaded) | `.claude/rules/` |
| Specialised subagents | `.claude/agents/` |
| Slash-command workflows | `.claude/commands/` |
| How-to guides for recurring tasks | `.claude/skills/` |
| Tool-agnostic contributor guide | `AGENTS.md` |

## Essential commands

```
make setup                              # poetry install --sync + pre-commit install
make check                              # lint + typecheck + security + test-unit
make lint / make typecheck / make security
make test-unit / make test-e2e
make harness-update                     # regenerate e2e goldens (review the diff!)
make bench                              # performance benchmarks
make run FIXTURE=data_ground_truth_01   # run the CLI against one data/input/ fixture
make run-all / make docs / make build
poetry run canoa-data-validate --help
```

## Architecture in 10 lines

Current: `main.py` → `Bootstrap` (locale) → `GeneralContext` (args, config, i18n, fs,
logger) → `SpreadsheetProcessor` (`DataLoaderFacade` → 8 `Sp*` models with structural
checks + cleaning → `FileStructureValidator`, `SpellCheckerValidator`, per-sheet
business validators) → `ValidationReport` → `FileReportGenerator` (Jinja2 + pdfkit).
Target (strangler fig, see `.specs/architecture/target-architecture.md`): `cli` →
`app` (`AppContext`) → `loading`/`normalizing` → `rules` (registry, `Rule` protocol,
`Issue` model) → `reporting`/`i18n`, all reading a single `SheetSpec` registry. See
`.specs/architecture/current-architecture.md` and `module-map.md` for the full map.

## Critical conventions

- User-facing messages only via the i18n catalog (`context.lm.text(...)`) — never an
  f-string or hardcoded sentence. See `.claude/rules/i18n.md`.
- Every validation check has a `NamesEnum` value today and a stable rule ID
  (`DESC-001`, …) in `.specs/business-rules/README.md` for new/migrated rules.
- Never read spreadsheet files outside `DataLoaderFacade`/the loading layer.
- Never use a generic/bare `except Exception` — catch specific types.
- DataFrames are treated as immutable; no `.iterrows()` in rules — see
  `.claude/rules/dataframe-conventions.md`.
- Line length 120 (`ruff`), not the legacy 150.

## Backlog item workflow (5 steps)

1. `/backlog <ID|next>` — pick an item from `.specs/quality/backlog/`, branch
   `feat/<ID>-slug` or `fix/<ID>-slug`.
2. Orchestrator writes a task brief (context, files, acceptance, tests) and delegates
   per `.claude/rules/model-delegation.md`.
3. Subagent implements with TDD; `make check` green locally.
4. `/review` (code-reviewer + security-auditor) → fix findings → `/spec-sync`.
5. Commit (Conventional Commits, reference the ID) → mark the item `done` in
   `.specs/quality/backlog/`. Full detail: `.specs/quality/backlog/08-migration-roadmap.md`.

## Commands, agents

Commands (`.claude/commands/`): `/backlog`, `/implement`, `/review`,
`/security-audit`, `/test`, `/tdd`, `/e2e`, `/harness-update`, `/spec-sync`, `/adr`,
`/rule`, `/i18n-check`, `/perf`, `/migrate`, `/release`, `/commit`.

Agents (`.claude/agents/`): implementer, test-engineer, code-reviewer,
security-auditor, integration-tester, performance-engineer, spec-writer,
i18n-guardian, docs-writer, protocol-expert, migration-architect, release-manager.

@AGENTS.md
@.specs/00-overview.md
