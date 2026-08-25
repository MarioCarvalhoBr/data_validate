# ADR-0006: Rule registry with declared prerequisites; skipped-with-reason semantics

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`BaseValidator` (`validators/spreadsheets/base/base_validator.py`) is the shared ancestor of every
business-rule validator and already carries three symptoms of an implicit, undeclared execution
model (ARC-008). First, `initialize()` (lines 89-96) is a no-op hook every subclass is expected to
override, but nothing declares what a validator *requires* before it can run — each validator
instead re-checks column/sheet existence ad hoc inside its own rule bodies. Second,
`column_exists`/`_column_exists`/`_column_exists_dataframe` (lines 135-205) are three near-identical
wrappers around `DataFrameProcessing.column_exists`, existing only because there is no single place
prerequisites are resolved once and reused. Third, and most tellingly, `set_not_executed` (lines
238-260) is a placeholder whose body is literally `pass`, with the intended implementation left as
a **comment**:
```python
# FUTURE FEATURE: Implement a method to mark validations as not executed in the report list.
for _, report_key in validations:
    self._report_list.set_not_executed(self.validation_titles[report_key])
```
— the project already recognised it needs "skipped, with a reason" semantics and never built them.
Meanwhile `build_reports` (lines 262-295) is the *actual* execution loop: it calls each
`(func, report_key)` pair in a plain Python `for`, and wraps every call in
`except Exception as e:` (line 290), converting **any** unexpected crash — a `KeyError`, a
`TypeError` from bad input — into a user-facing error string
(`f"Exception validation in file during {func.__name__}: {str(e)}"`, line 293) with no distinction
from a genuine business-rule violation (SEC-004). `spreadsheet_processor.py:181-215`
(`_build_pipeline`) hand-orders validator construction (structure → spelling → mandatory →
optional) with no declared dependency graph — the order is correct only because someone remembered
it, and nothing would catch a reordering that silently changes results (ARC-017).

## Decision

Adopt the `Rule` protocol and engine described in `.specs/architecture/target-architecture.md`:
```python
class Rule(Protocol):
    rule_id: str
    category: str
    requires: Mapping[str, tuple[str, ...]]      # {"descricao": ("codigo", "nivel")}
    depends_on: tuple[str, ...]                  # rule IDs that must have produced no error
    def check(self, ctx: RuleContext) -> Iterable[Issue]: ...
```
registered in `rules/registry.py`, one `Rule` per module under `rules/<sheet>/<RULE-ID>.py`
(Phase 3). Before `check()` runs, the engine verifies `requires` (sheet loaded, readable, named
columns present) and `depends_on` (referenced rules produced no error issues); an unmet
prerequisite marks the rule **skipped with reason** — `RuleOutcome(status="skipped", reason=
<catalog key>)` — surfaced in the report exactly where today's dead `set_not_executed` intended to,
replacing the ARC-008 placeholder and the triplicated `column_exists*` helpers with one prerequisite
check performed once per rule. Execution order is topological on `depends_on`, ties keep registry
order (preserving today's structure → description → composition → temporal reference → value →
scenario → legend → proportionality → spell sequence, `08-migration-roadmap.md` Phase 3 item 2); an
unexpected exception inside `check()` is recorded as a distinct `engine.rule_crashed` `Issue`
**and** forces exit code 2 — never silently absorbed as an ordinary validation finding (closing
SEC-004 at the engine level, complementing ADR-0004). Independent rule groups may later run under
`ProcessPoolExecutor` once purity is established (PERF-007), with deterministic output ordering
regardless of execution order.

## Consequences

### Positive
- "Why didn't rule X run?" gets a real, catalog-backed answer (missing column, dependent rule
  failed) instead of the rule silently not appearing or appearing to have passed.
- A crash inside one rule can no longer be mistaken for "the spreadsheet is valid" — it is a
  distinct outcome with its own exit code, closing the specific SEC-004 evidence in
  `base_validator.py:290-295`.
- `--list-rules` becomes possible for free: the registry is the same structure that drives
  execution, so listing "what rules exist, what they require" needs no separate bookkeeping.

### Negative
- Every validator must be rewritten to declare `requires`/`depends_on` explicitly instead of
  checking ad hoc inside the rule body — a one-time cost absorbed per-sheet during Phase 3 as each
  validator is ported (paired with a golden case, per ADR-0002).
- A misdeclared `depends_on` (missing an edge) can silently change execution order versus today's
  hand-ordered pipeline; mitigated by the golden harness catching any resulting output change
  before the corresponding old validator is deleted.

## Alternatives considered

### Keep per-validator ad hoc prerequisite checks, add a shared mixin to reduce duplication
Rejected: a mixin can deduplicate the `column_exists*` helpers but does nothing about the broad
`except Exception` in `build_reports` masking crashes as valid runs (SEC-004), and does not give
`--list-rules` or a declarative dependency graph — it treats the symptom (code duplication) without
addressing the missing semantics (skipped-with-reason, crash isolation) the project itself already
identified as needed.

### Adopt a general-purpose DAG workflow engine (e.g. an Airflow-style scheduler)
Rejected: the rule set is small (~34 checks today, `NamesEnum`), single-process, and re-run from
scratch on every CLI invocation — a workflow engine's persistence, retries, and scheduling machinery
solve problems this batch validator doesn't have, at the cost of a heavy new dependency and
operational surface (a scheduler UI, a metadata database) with no user for it.

### Continue silently skipping unmet prerequisites (status quo)
Rejected: this is precisely the gap `set_not_executed`'s own comment admits — the codebase already
recognises silent skipping without a reason is wrong (SEC-004's "the process exits 0 and the
platform records the run as successful" applies equally to a silently-skipped rule as to a
swallowed exception); the whole point of this ADR is to close that acknowledged gap.

## Links

- Backlog: `ARC-008` (`03-architecture.md`); `ARC-017` (`03-architecture.md`);
  `SEC-004` (`02-security.md`); `08-migration-roadmap.md` Phase 3 item 1
- Specs: `.specs/architecture/target-architecture.md` (`Rule`, `RuleOutcome`, engine semantics)
- Related ADRs: ADR-0002, ADR-0004, ADR-0013 (rule purity depends on immutable typed frames)

---
Last synced with code: a4f76c7
