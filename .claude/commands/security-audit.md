---
description: Full security scan of a path (or the whole codebase) — security-auditor plus bandit and pip-audit
argument-hint: "[path]"
allowed-tools: Bash(poetry run bandit*), Bash(poetry run pip-audit*), Bash(mkdir -p dev-reports/security*), Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — optional path to scope the scan; defaults to `data_validate/`.

1. Run `poetry run bandit -r $ARGUMENTS` (or the default path) and `poetry run pip-audit`.
2. Delegate to `security-auditor` (`model: sonnet`, per `.claude/rules/model-delegation.md` —
   state the rule in the brief) with the bandit/pip-audit raw output plus the path scope, asking
   for a full threat-model pass per `.claude/agents/security-auditor.md`'s process.
3. Ensure `dev-reports/security/` exists and have the report written there as
   `<YYYY-MM-DD>-audit.md` (this path is gitignored).
4. Report the summary (counts by severity) to the user and the report file path; do not fix
   findings automatically — use `/review` or a direct `implementer` brief for that afterward.
