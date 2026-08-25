---
description: Run the golden e2e harness and explain any diffs against tests/e2e/golden
argument-hint: "[fixture]"
allowed-tools: Bash(make test-e2e*), Bash(poetry run pytest*), Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — optional single fixture name under `data/input/`; defaults to all
fixtures.

1. Delegate to `integration-tester` (`model: sonnet` per `.claude/rules/model-delegation.md` —
   state the rule) to run `make test-e2e` (or the single fixture via
   `poetry run pytest tests/e2e -k "$ARGUMENTS" -m e2e`) and classify every diff found.
2. Report each fixture's result and, for any diff, the classification (regression / harness
   artifact / intentional change) with the reasoning.
3. If a regression is found, do not fix it here — report it as a blocker for `/backlog` or
   `/implement` to address.
4. If the user explicitly wants goldens updated for an intentional change, use
   `/harness-update <fixture> "<reason>"` instead of doing it inline.
