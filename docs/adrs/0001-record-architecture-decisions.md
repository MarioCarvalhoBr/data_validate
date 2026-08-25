# ADR-0001: Record architecture decisions with ADRs

- Status: Accepted
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`data_validate` (Canoa) is entering a multi-phase migration (`.specs/quality/backlog/
08-migration-roadmap.md`, Phases 0-5) that will replace most of the current pipeline — `main.py`
→ `Bootstrap` → `GeneralContext` → `SpreadsheetProcessor` → `ValidationReport` →
`FileReportGenerator` — with a new layered design (`.specs/architecture/target-architecture.md`)
while keeping the CLI/report/JSON contract green for the AdaptaBrasil platform at every step.
Before this audit (`.specs/quality/backlog/`, 89 items across bugs, security, architecture,
testing, performance, tooling and docs), no architectural decision in this codebase was ever
written down: choices such as the three competing sheet-definition sources (`config/
spreadsheet_info.py`, `helpers/tools/data_loader/common/config.py`, `models/sp_*.py::INFO`; see
ARC-003) or the dual locale-file bug (`middleware/bootstrap.py` vs `helpers/tools/locale/
language_manager.py`; see BUG-004) accumulated silently and were only recoverable by reading code.
A strangler-fig migration run by an orchestrator and specialised subagents
(`.claude/rules/model-delegation.md`) makes this worse without a durable record: different
subagents, in different sessions, need the same rationale to avoid re-litigating or contradicting
prior decisions.

## Decision

Adopt Architecture Decision Records in MADR format (Markdown Architecture Decision Records),
stored under `docs/adrs/NNNN-<slug>.md`, numbered sequentially and never renumbered. Every ADR
follows `.specs/templates/adr.md`: `Status`, `Date`, `Deciders`, `Context` (grounded in
`file:line` evidence), `Decision` (concrete interfaces/names/locations), `Consequences`
(positive/negative), `Alternatives considered` (≥ 2, with rejection reasons), `Links` (backlog IDs,
specs, related ADRs). `docs/adrs/README.md` is the index: number, title, status, date. The
`/adr "<title>"` command (`.claude/commands/adr.md`) creates new ADRs from the template and
consults the `migration-architect` subagent (opus) for structural decisions; any subagent
proposing a structural change during implementation must either point to an existing ADR or ask
the orchestrator to write one before proceeding (`.claude/rules/spec-sync.md`). ADR status starts
`Proposed` for anything not yet implemented and moves to `Accepted` only when the corresponding
migration-phase gate is green; a superseding decision gets a new ADR that marks the old one
`Superseded by ADR-NNNN` rather than editing history.

## Consequences

### Positive
- Every non-trivial design choice has a citable rationale, reviewable in the same PR as the code
  that implements it, instead of living only in chat history or a subagent's working memory.
- New contributors (human or AI) can answer "why is it built this way?" from `docs/adrs/` instead
  of archaeology across `git blame`.
- `code-reviewer` and `spec-writer` subagents can check a diff against an ADR for consistency
  (`.claude/rules/spec-sync.md`), catching accidental architecture drift.

### Negative
- Adds ceremony: a structural change now requires an ADR before or alongside the code, which slows
  down small experiments (mitigated by scoping ADRs to structural/cross-cutting decisions only,
  not every function signature).
- ADRs can go stale if `spec-sync` discipline lapses; mitigated by the `stop-check.sh` hook
  alerting when `data_validate/` changes without a `.specs/`/`docs/adrs/` touch in the same commit.

## Alternatives considered

### No decision record — rely on commit messages and code comments
Rejected: commit messages explain *what* changed, not the rejected alternatives or forces behind
*why*; this project's own history shows the cost — SEC-006 documents a 2026-08-25 incident where
undocumented pre-commit behaviour silently rewrote 22 files in what was meant to be a docs-only
commit, precisely the kind of surprise a recorded decision (or its absence) would have flagged.

### Lightweight decision log (single running `DECISIONS.md` file, Y-statement style)
Rejected: a single growing file does not scale to 14+ decisions with alternatives and
consequences, is hard to link to from specs/backlog items by stable ID, and loses per-decision
status tracking (`Proposed` → `Accepted` → `Superseded`) that this migration explicitly needs
across five phases.

### Decisions recorded only in `.specs/architecture/target-architecture.md`
Rejected: that document (owned by `spec-writer`) describes the target *state*, not the *decision
history* — it would have to be rewritten on every reversal, destroying the audit trail. ADRs and
target-architecture.md are complementary: the ADR captures the choice and why, the spec describes
the resulting shape.

## Links

- Backlog: `.specs/quality/backlog/08-migration-roadmap.md` (phased plan every ADR below supports)
- Specs: `.specs/templates/adr.md`, `.specs/architecture/target-architecture.md`
- Related ADRs: all of ADR-0002 through ADR-0014 depend on this process being in place

---
Last synced with code: a4f76c7
