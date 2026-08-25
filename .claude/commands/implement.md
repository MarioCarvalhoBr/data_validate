---
description: "Implement a spec section or backlog ID end to end: brief, implement, test, review, spec-sync"
argument-hint: "<spec-path-or-ID>"
allowed-tools: Bash(poetry run pytest*), Bash(make *), Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — a spec file path (e.g. `.specs/business-rules/legend.md`) or a backlog ID.

1. Read the target spec or backlog entry fully, plus every file it references.
2. Write a task brief: files in scope, acceptance criteria, tests required.
3. Delegate to `implementer` with `model: sonnet` per `.claude/rules/model-delegation.md` (state
   the rule in the brief). Wait for its diff and test results.
4. Check coverage on the touched module(s). If below 95%, delegate to `test-engineer`
   (`model: sonnet`) with the same brief plus the coverage gap.
5. Run `/review` on the resulting diff.
6. Run `/spec-sync` to reconcile `.specs/` and `.claude/rules/` with what actually landed.
7. Report: files changed, tests added, coverage delta, specs updated, and the `/review` verdict.
