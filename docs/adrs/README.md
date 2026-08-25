# Architecture Decision Records

This directory records the architectural decisions behind the `data_validate` (Canoa) migration
using the MADR format defined in `.specs/templates/adr.md`. Every ADR cites `.specs/quality/
backlog/` item IDs as evidence and links to the relevant `.specs/` documents. New ADRs are created
with `/adr "<title>"` (`.claude/commands/adr.md`), which consults the `migration-architect`
subagent; see `.claude/rules/spec-sync.md` for when an ADR is required versus a plain spec update.

Status values: `Proposed` (decided, not yet fully implemented — the target this migration is
building toward), `Accepted` (implemented and in force today), `Rejected`, `Deprecated`, or
`Superseded by ADR-NNNN`.

| # | Title | Status | Date |
|---|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions with ADRs | Accepted | 2026-08-25 |
| [0002](0002-strangler-fig-migration-with-golden-harness.md) | Strangler-fig migration with a golden end-to-end harness as the safety net | Proposed | 2026-08-25 |
| [0003](0003-single-sheetspec-registry.md) | Single `SheetSpec` registry as the source of truth for sheet definitions | Proposed | 2026-08-25 |
| [0004](0004-structured-issue-model-and-message-catalog.md) | Structured `Issue` model and message catalog replace pre-formatted strings | Proposed | 2026-08-25 |
| [0005](0005-cli-contract-flags-exit-codes-json.md) | CLI contract: explicit flags, exit codes, JSON output; deprecate abbreviations and `.config/store.locale` | Proposed | 2026-08-25 |
| [0006](0006-rule-registry-with-prerequisites.md) | Rule registry with declared prerequisites; skipped-with-reason semantics | Proposed | 2026-08-25 |
| [0007](0007-report-rendering-jinja2-autoescape-weasyprint.md) | Report rendering with Jinja2 autoescape; PDF optional via WeasyPrint (drop wkhtmltopdf) | Proposed | 2026-08-25 |
| [0008](0008-spellbackend-protocol-pure-python-fallback.md) | Spell-check behind a `SpellBackend` protocol with a pure-Python fallback | Proposed | 2026-08-25 |
| [0009](0009-readme-hand-written-retire-generator.md) | README maintained by hand; retire the template generator | Proposed | 2026-08-25 |
| [0010](0010-tooling-baseline.md) | Tooling baseline: Poetry, ruff (lint+format), mypy strict-by-default for new code, bandit, pip-audit, pre-commit | Accepted | 2026-08-25 |
| [0011](0011-testing-policy.md) | Testing policy: pytest + pytest-mock only, coverage ratchet, goldens | Accepted | 2026-08-25 |
| [0012](0012-multi-agent-development-workflow.md) | Multi-agent development workflow (orchestrator + specialised subagents) governed by `.claude/rules/` | Accepted | 2026-08-25 |
| [0013](0013-pandas-3-copy-on-write-nullable-dtypes.md) | pandas 3 with Copy-on-Write and nullable/pyarrow dtypes as the DataFrame baseline | Proposed | 2026-08-25 |
| [0014](0014-i18n-json-catalogs-keyed-by-rule-id.md) | i18n via JSON catalogs keyed by rule ID; pt_BR default, en_US required parity | Accepted (partially implemented) | 2026-08-25 |

---
Last synced with code: a4f76c7
