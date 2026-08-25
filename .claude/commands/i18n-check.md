---
description: Check pt_BR/en_US catalog parity and scan for hard-coded user-facing strings
allowed-tools: Bash(poetry run python tools/i18n_check.py*), Read, Grep, Glob, Agent
---

1. Delegate to `i18n-guardian` (`model: haiku` per `.claude/rules/model-delegation.md` — state the
   rule; this is mechanical/trivial work) to run `tools/i18n_check.py` and scan for hard-coded
   strings per its documented process.
2. Report the findings as returned: missing keys per catalog, unused keys, and hard-coded string
   hits with `file:line`.
3. This command only reports; use `/implement` or a direct `implementer` brief to fix catalog gaps.
