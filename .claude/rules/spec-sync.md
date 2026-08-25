# Sync between code, `.specs/` and `.claude/`

Specs and rules are the source of truth for *why* the code looks the way it
does. Code and specs drift apart the moment one changes without the other —
prevent that in every commit, not in a later cleanup pass.

## Rule

Any change that alters behaviour, a business rule, the CLI contract, a file
layout, or a coding/testing convention **must** update the matching file
under `.specs/` or `.claude/rules/` **in the same commit** as the code
change. A PR (or commit) that changes behaviour without a spec update is
incomplete, not "docs later".

Any new rule or convention agreed in conversation becomes either a file in
`.claude/rules/` (a standing convention) or a section in `.specs/` (a
domain fact) before the task is considered done — never left only in chat
history.

Any structural or architectural decision (new interface, new layer, a
reversal of a previous ADR) gets an ADR under `docs/adrs/` referencing the
backlog item and the specs it touches.

`stop-check.sh` alerts (does not block) when `data_validate/**` changed but
nothing under `.specs/` or `.claude/rules/` changed in the same diff — treat
that warning as a checklist item, not noise to dismiss.

## Checklist: change → file to update

| Kind of change | File to update |
|---|---|
| Business rule (new/changed validation) | `.specs/business-rules/<sheet>.md` |
| CLI flag (add/rename/deprecate) | `.specs/api/cli-contract.md` |
| Architecture or public interface | `.specs/architecture/target-architecture.md` + an ADR under `docs/adrs/` |
| Coding/testing/security convention | `.claude/rules/<rule>.md` |
| Tooling or CI/CD change | `.specs/infrastructure/ci-cd.md` |
| Backlog item status change | `.specs/quality/backlog/<file>.md` |
| New rule ID (e.g. `DESC-011`) | `.specs/business-rules/README.md` (the ID map) |

## Never do

- Never merge a behaviour change with the matching spec left stale.
- Never invent a new rule ID without registering it in
  `.specs/business-rules/README.md`.
- Never treat a `stop-check.sh` drift warning as something to silence
  instead of act on.
