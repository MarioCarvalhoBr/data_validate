---
description: Plan and execute one migration-roadmap slice for a module — architect, implement, verify, sync
argument-hint: "<module>"
allowed-tools: Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — a module or slice name matching a step in
`.specs/quality/backlog/08-migration-roadmap.md` (e.g. `SheetSpec registry`, `Issue model`).

1. Delegate to `migration-architect` (`model: opus` per `.claude/rules/model-delegation.md` —
   state the rule; structural planning justifies the top model) to plan `$ARGUMENTS`: interface
   definitions, old→new mapping, ordered increments, and any ADR needed.
2. For each increment in the plan, run `/implement <increment>` (which itself delegates to
   `implementer`/`test-engineer` at `sonnet` and runs `/review`).
3. After all increments land, run `/e2e` to confirm the golden harness is unchanged (or
   re-baselined only with an explicit, reviewed reason via `/harness-update`).
4. Run `/spec-sync` to update `.specs/architecture/target-architecture.md`'s module map and mark
   the roadmap phase's progress.
5. Report the increments completed, the ADR(s) written, and the e2e result.
