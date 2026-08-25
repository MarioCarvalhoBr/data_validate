---
description: Red-green-refactor loop for a feature — write the failing test first, then the minimal implementation
argument-hint: "<feature-description>"
allowed-tools: Bash(poetry run pytest*), Read, Edit, Write, Glob, Grep, Agent
---

Argument: `$ARGUMENTS` — a short description of the feature or fix to build via strict TDD.

1. Delegate to `test-engineer` (`model: sonnet` per `.claude/rules/model-delegation.md`) to write
   one failing test that captures `$ARGUMENTS`, following `.claude/rules/testing.md`. Confirm it
   fails for the right reason (`poetry run pytest <file> -q`) before moving on — red.
2. Delegate to `implementer` (`model: sonnet`, same rule reminder) to write the minimal code that
   makes that test pass — green. Do not let it add anything beyond what the test requires.
3. Run the full test file plus `poetry run ruff check` on touched files; delegate any cleanup
   (naming, duplication, magic numbers) back to `implementer` as a refactor step — refactor, tests
   must stay green throughout.
4. Repeat steps 1–3 for the next behaviour of `$ARGUMENTS` until the feature is complete.
5. Report the final test list and a one-line summary of each red-green-refactor cycle.
