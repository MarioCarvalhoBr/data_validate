---
name: adr-writing
description: Use when a structural decision needs to be recorded — a new interface, a dropped dependency, a changed CLI contract, or any choice future contributors would otherwise have to reverse-engineer. Format, timing, and how to link back to specs/backlog.
---

# Writing an ADR

Architecture Decision Records live in `docs/adrs/NNNN-<slug>.md`, format MADR
(`.specs/templates/adr.md`): Title, Status, Context, Decision, Consequences, Alternatives
considered, Links.

## When to write one

Write an ADR when a decision:
- Changes a structural contract other code depends on (an interface signature, a CLI flag's
  meaning, a file layout, a dependency swap like wkhtmltopdf → WeasyPrint).
- Would cost real effort to reverse later, or someone could reasonably ask "why not X instead?"
- Is being proposed during `/migrate` planning (`migration-architect` always writes one for a
  phase-level structural choice).

Do **not** write one for: a bug fix, a routine refactor with no external contract change, a test
addition, or a documentation update — those go through the normal implement → review flow.

## Status lifecycle

- `Proposed` — decided in principle, not yet (fully) implemented in the codebase.
- `Accepted` — implemented and in effect; only mark this once the code actually reflects it.
- `Superseded by NNNN` — a later ADR replaced this decision; keep the old file, add the pointer.
- Never `Rejected` silently — if a considered alternative was rejected, it belongs in
  "Alternatives considered" on the ADR that won, not as its own record.

## Numbering and index

Numbers are sequential and never reused. Check `docs/adrs/README.md` for the next free number
before writing, and update that index in the same change — a new ADR without an index entry is
incomplete.

## Linking back

Every ADR must link: the backlog ID(s) it closes or relates to, and the `.specs/` file(s) its
decision affects (so `spec-writer` can find it during `/spec-sync`). A decision without a
traceable spec or backlog link is a signal the ADR is either premature or the backlog is missing
an item — fix the gap, don't skip the link.

## Writing style

English, present tense for "Decision" ("We use X" not "We will use X"), past tense for "Context"
where it describes the prior state. State consequences honestly, including negative ones — an ADR
that only lists benefits didn't do the trade-off analysis.
