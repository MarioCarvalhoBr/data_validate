---
description: Profile a fixture, benchmark, and suggest vectorisation fixes for hot paths
argument-hint: "[fixture]"
allowed-tools: Bash(poetry run python tools/harness/profile_pipeline.py*), Bash(make bench*), Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — optional fixture name under `data/input/`; defaults to the largest
available fixture (synthesize one with `tools/harness/generate_fixture.py` if none is large enough
to expose hot paths).

1. Delegate to `performance-engineer` (`model: sonnet` per `.claude/rules/model-delegation.md` —
   state the rule) to profile `$ARGUMENTS` (or default), identify the top bottleneck(s), and
   propose vectorisation fixes per the `pandas-vectorization` skill.
2. If the user asked for fixes (not just a profile), have it apply the fix, re-profile, and add a
   `pytest-benchmark` regression test; otherwise stop at the proposal.
3. Report the profile summary, bottleneck(s) found, before/after numbers if a fix was applied, and
   confirm `tests/e2e` goldens are unchanged.
