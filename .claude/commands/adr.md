---
description: Create a new architecture decision record from the ADR template
argument-hint: "\"<title>\""
allowed-tools: Read, Write, Glob, Grep, Agent
---

Argument: `$ARGUMENTS` — the ADR title, quoted.

1. Read `docs/adrs/README.md` for the next free ADR number and `.specs/templates/adr.md` for the
   format.
2. Consult `migration-architect` (`model: opus` per `.claude/rules/model-delegation.md` — state the
   rule; this is a structural-decision task, which is the case that justifies the top model) for
   the context, decision, consequences, and alternatives considered.
3. Write `docs/adrs/<NNNN>-<slug>.md` from the template, status `Proposed` unless the decision is
   already implemented in the codebase (then `Accepted`), with links to the backlog IDs and specs
   it affects.
4. Update `docs/adrs/README.md`'s index with the new entry.
5. Report the file path and status chosen.
