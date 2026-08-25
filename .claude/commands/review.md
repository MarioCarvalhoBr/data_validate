---
description: Run code-reviewer and security-auditor in parallel over a diff and consolidate findings
argument-hint: "[ref]"
allowed-tools: Bash(git diff*), Bash(git log*), Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — optional ref/PR/branch; defaults to the current working-tree diff against
the branch's merge base with `main`.

1. Resolve the diff scope from `$ARGUMENTS` (or default) with `git diff`/`git log`.
2. Launch `code-reviewer` and `security-auditor` in parallel, both `model: sonnet`, both given the
   same diff scope and reminded of `.claude/rules/model-delegation.md`.
3. Consolidate both findings lists into one, ordered blocker → major → minor → nit, deduplicating
   overlapping findings and noting when both agents flagged the same line.
4. If there are blocker or major findings, delegate the fixes to `implementer` (`model: sonnet`)
   with the specific findings as the brief, then re-run this diff scope through both reviewers
   once more.
5. Report the final consolidated findings list and verdict (approve / approve with nits / changes
   required). Do not commit.
