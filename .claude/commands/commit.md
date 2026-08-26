---
description: Review the diff, group by scope, and create Conventional Commits (never git add ., never push)
argument-hint: "[scope-hint]"
allowed-tools: Bash(git status*), Bash(git diff*), Bash(git log*), Bash(git add -- *), Bash(git commit*)
---

Argument: `$ARGUMENTS` — optional hint about which changes to focus on if the working tree has
unrelated changes mixed together.

1. `git status` and `git diff` to see everything changed; `git log -5 --oneline` to match this
   repo's commit message style.
2. Group the changes by logical scope (one commit per coherent unit — e.g. don't mix a rule fix
   with an unrelated doc update). Use `$ARGUMENTS` to prioritize if given.
3. For each group, stage the **explicit file paths** with `git add -- <paths>` (never `git add .`,
   `git add -A`, or a bare `git add *`) and create a commit with a Conventional Commits message in
   English, including the scope and backlog ID when one applies (e.g.
   `fix(rules): BUG-006 avoid list.remove on missing id`).
4. **Legacy hook caveat**: while `.pre-commit-config.yaml` still runs the old pipeline-executing
   hooks (before Phase D replaces it — see `.claude/rules/git-workflow.md`), commit with
   `--no-verify`. Once the new pre-commit config is in place, drop `--no-verify` and let the
   standard hooks run.
5. Never run `git push`. Report the commit(s) created (hash + message) and confirm nothing in
   `local_data/`, `my_codes.py`, `.idea/`, `dist/`, or `dev-reports/` was staged.
