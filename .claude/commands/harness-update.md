---
description: Regenerate golden e2e fixtures with a reviewed diff and a recorded reason
argument-hint: "<fixture> \"<reason>\""
allowed-tools: Bash(make harness-update*), Bash(git diff*), Read, Edit, Grep, Glob, Agent
---

Arguments: `$ARGUMENTS` — a fixture name and a quoted reason string, e.g.
`data_ground_truth_01 "legend message now includes the offending code per LEG-003"`.

1. Refuse to proceed if no reason string is given — a golden update always needs one.
2. Delegate to `integration-tester` (`model: sonnet` per `.claude/rules/model-delegation.md` —
   state the rule) to run `make harness-update FIXTURE=<fixture>` and produce a diff of the golden
   file before/after.
3. Review that diff yourself line by line — every changed message must trace to a reviewed,
   intentional code change, not noise (timestamps, ordering, whitespace).
4. Append an entry to `tests/e2e/golden/CHANGELOG.md`: date, fixture, reason (verbatim from
   `$ARGUMENTS`), and the commit/PR this belongs to if known.
5. Report the diff summary and the changelog entry written. Do not commit.
