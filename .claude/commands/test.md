---
description: Create or expand tests for a module until it reaches the coverage target
argument-hint: "<module>"
allowed-tools: Bash(poetry run pytest*), Read, Edit, Write, Glob, Grep, Agent
---

Argument: `$ARGUMENTS` — a module path (e.g. `data_validate/helpers/common/validation/legend_processing.py`).

1. Run `poetry run pytest --cov=$ARGUMENTS --cov-report=term-missing -q` to get the current
   coverage and the uncovered line ranges for the module.
2. Delegate to `test-engineer` (`model: sonnet` per `.claude/rules/model-delegation.md` — state the
   rule) with the module path, current coverage, and uncovered lines, targeting ≥ 95% (new code)
   or the current ratchet floor (legacy code, see `.claude/rules/testing.md`).
3. Re-run the coverage command to confirm the target was met.
4. Report the before/after coverage numbers and the test files touched.
