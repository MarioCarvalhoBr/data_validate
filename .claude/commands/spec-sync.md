---
description: Reconcile the current diff against .specs/ and .claude/rules/, updating what drifted
argument-hint: "[ref]"
allowed-tools: Bash(git diff*), Bash(git log*), Read, Edit, Write, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — optional ref/scope for the diff; defaults to the current working-tree
diff against `main`.

1. `git diff $ARGUMENTS` (or default) to see what changed.
2. Delegate to `spec-writer` (`model: sonnet` per `.claude/rules/model-delegation.md` — state the
   rule) with the diff and the instruction to reconcile every behaviour, CLI, layout, or
   convention change against `.specs/**` and, if a new standing convention was introduced in this
   conversation, against `.claude/rules/*` (a new rule file only if none of the ten existing ones
   fit).
3. Have it list any structural decision in the diff that lacks an ADR and flag it (creating the
   ADR itself only if explicitly asked; otherwise recommend `/adr`).
4. Report: specs updated, rules updated (if any), ADRs flagged as missing, and any open questions
   filed to `.specs/future/open-questions.md`.
