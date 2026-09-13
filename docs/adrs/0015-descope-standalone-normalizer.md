# ADR-0015: Descope the standalone `Normalizer`/`SheetFrame` layer; models are the normalizing layer

- Status: Accepted (implemented) — closes ARC-007.
- Date: 2026-09-13
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`.specs/architecture/target-architecture.md`'s original sketch (ADR-0013) proposed a dedicated
`normalizing/` package sitting between `loading/` and `rules/`: a `Normalizer` `Protocol`
(`normalize(sheet, ctx) -> (SheetFrame, issues)`) that would run once per sheet and hand every
rule an immutable `SheetFrame` (`raw` + `typed` + a per-column `invalid` mask), replacing the
per-model structural-check-plus-cleaning logic that `models/sp_*.py` has always owned. ARC-007
("models validate, clean and mutate; 'Processing' classes are procedural namespaces") named this
as its target design.

By Phase 5 of the migration, the concerns that originally motivated a *separate* layer are already
resolved through other, already-landed work, without ever building `normalizing/`:

- **Mutation** (BUG-002/BUG-003, Phase 2c): `SpModelABC` owns `self.frame` (an instance-level,
  Copy-on-Write-cheap working frame) and `self.cleaned`/`cleaned_column(name)` (an instance-level
  typed-column store). No model mutates a class-level attribute or the shared `raw_data` any more.
- **Hardcoded messages** (ARC-005, Phase 3 Ports 1-8 and the Phase 5 models/helpers slice): every
  message a model or a `rules/*.py` module produces is a catalog key rendered through
  `translate`/`ctx.translate`, never a pre-formatted Portuguese string.
- **Structural checks split out** (ARC-017): every sheet's structural validation
  (`STRUCT-001`…`STRUCT-015`) already lives in `rules/structure.py` as pure `check_*` functions
  reading `RuleContext`, not inside the model.
- **Rules read typed data without re-parsing it**: every `rules/<sheet>.py` module reads a
  model's cleaned columns (via `RuleContext`, itself built from `model.cleaned_column(...)`-shaped
  data) rather than re-parsing raw strings — the actual behavioural promise a `SheetFrame.typed`
  frame was meant to provide.

What is left inside `models/sp_*.py` today is exactly one responsibility per model: the
structural-check-and-typed-cleaning pass for its one sheet, run once, from an explicit `run()`
call (ARC-001) — not three or four responsibilities entangled together any more. Introducing a
second, parallel `Normalizer` abstraction over that same single responsibility would not remove
any remaining smell this item named; it would only rename the class that already does the job and
require every model's cleaning method to move to a new file for no behavioural gain.

## Decision

Descope the standalone `normalizing/`/`Normalizer`/`SheetFrame` package from the target
architecture. `models/sp_*.py` **is** the normalizing layer, by design: one `SpModelABC` subclass
per sheet, owning both the structural check and the typed-cleaning pass, exposing cleaned columns
through `cleaned_column(name)` for `rules/*.py` to read. `.specs/architecture/target-architecture.md`
is updated accordingly: the mermaid diagram's `normalizing` node is replaced with a `models/`
node annotated "normalizing layer — ADR-0015"; the `SheetFrame`/`Normalizer` dataclass/`Protocol`
sketch is kept as a commented-out historical record, not a pending interface; the "Current module
→ target module" table's `models/sp_model_abc.py, models/sp_*.py` row is marked **Done** (kept, not
migrated away); a "Non-goals" bullet names this decision explicitly so a future reader does not
reopen it as an oversight.

ARC-007 ("models validate, clean and mutate; 'Processing' classes are procedural namespaces") is
closed on this basis: the *specific* smells it named (mutation, procedural-namespace helpers with
hardcoded strings, overlap with `validators/`) are each independently fixed by BUG-002/BUG-003,
ARC-005, and ARC-008/ARC-017 respectively; "models both validate structure and clean data in the
same `run()`" is no longer treated as a defect once a `Normalizer` split is off the table — a model
owning both halves of "check this sheet's shape and produce its typed columns" for one sheet is a
single, cohesive responsibility, not two competing ones, once the *report-facing* structural
checks have already moved to `rules/structure.py`.

## Consequences

### Positive
- No new package/class was written to duplicate `SpModelABC`'s existing typed-cleaning
  responsibility — zero migration risk, zero new surface for `rules/*.py` to depend on, no golden
  harness risk from re-plumbing every model's cleaning call sites through a new intermediary.
- The architecture doc now matches what the code actually does and will keep doing, closing a
  long-open gap between `target-architecture.md`'s sketch and the real Phase 5 shape of the
  codebase (the sketch is now historical/commented, not a misleading "still pending" table row).
- ARC-007 — open since the migration's early phases — is closed, removing one more "someday" item
  from the backlog that had, in practice, already been resolved piecemeal by three other items.

### Negative
- `models/sp_*.py` remains, by name, in the legacy `models/` package rather than a
  clean-architecture-named `normalizing/` one — a naming/location mismatch with the original
  sketch's aesthetic, accepted as cosmetic (ARC-013's naming pass already reviewed `models/`'s
  naming and left it as-is for the same "wide-surface, no behavioural gain" reason).
- If a second consumer of typed, cleaned sheet data ever needs it *without* constructing a full
  model (e.g. a future library-mode caller that only wants `SheetFrame`-shaped data, not a
  validation run), this decision means that consumer still goes through a model instance today —
  revisit if that concrete need materialises, rather than speculatively building the abstraction
  now (`.claude/rules/coding-standards.md`'s "no speculative generality").

## Alternatives considered

### Build `Normalizer`/`SheetFrame` as originally sketched, migrate every model's cleaning into it
Rejected: every concern the sketch was designed to address (mutation, hardcoded messages,
structural-check placement, rules re-parsing raw data) is already fixed independently; building it
now would be a large, purely mechanical migration (moving working, tested cleaning code from eight
`models/sp_*.py` files into eight new `normalizing/<sheet>.py` files) for no additional guarantee
the current design does not already provide.

### Build `Normalizer` as a thin wrapper that just calls into the existing models internally
Rejected: this is a second name for the same object graph with an extra indirection layer and no
new behaviour — it would satisfy the letter of the original sketch's file layout without
satisfying its actual purpose (a genuinely separate, model-independent typed-frame abstraction),
so it does not earn its own added complexity.

### Leave ARC-007 open indefinitely as "someday, Phase 2+ work"
Rejected: the backlog's own discipline (`.claude/rules/spec-sync.md`, `.claude/rules/performance.md`'s
"measure, don't guess" precedent for wont-fix decisions) is to close an item with evidence once its
named smells are resolved, not carry it forward as perpetually-open debt that misdescribes the
current, already-fixed state of the code to any future reader of the backlog.

## Links

- Backlog: `ARC-007` (`03-architecture.md`, closed by this ADR); related closures this decision
  leans on: `BUG-002`/`BUG-003` (`01-bugs.md`), `ARC-005`, `ARC-008`, `ARC-017` (`03-architecture.md`)
- Specs: `.specs/architecture/target-architecture.md` (mermaid diagram, "Core interfaces"
  `normalizing` section, "Current module → target module" table, "Non-goals of the target
  design")
- Related ADRs: ADR-0013 (the pandas 3/CoW/nullable-dtype decision that first sketched
  `Normalizer`/`SheetFrame` — this ADR narrows ADR-0013's scope to the dtype/CoW adoption it also
  covers, without retracting that half; only the standalone-package half is descoped here),
  ADR-0006 (rule registry — the consumer side of "rules read typed data" this decision confirms is
  already satisfied)

---
Last synced with code: 1195fd1
