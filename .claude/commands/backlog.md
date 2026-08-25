---
description: Pick the next backlog item (or a specific ID), create its branch, and start the implementation flow
argument-hint: "[ID|next]"
allowed-tools: Bash(git status*), Bash(git branch*), Bash(git switch*), Bash(git checkout -b*), Read, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — a backlog ID (e.g. `BUG-006`) or the literal `next` (default when empty).

1. Read `.specs/quality/backlog/08-migration-roadmap.md` and `.specs/quality/backlog/README.md`.
2. **Selecting "next"**: find the lowest-numbered phase in the roadmap that is not yet fully
   closed (its "Closes:" list still has items whose status in `01-bugs.md`…`07-docs-i18n.md` is
   not `done`/`wont-fix`). Within that phase's closable items, pick by priority P0 > P1 > P2 > P3;
   within the same priority, pick the lowest ID (e.g. `BUG-001` before `BUG-006`). Selecting a
   specific `$ARGUMENTS` ID skips this search — go straight to step 3 with that ID.
3. Read the chosen item's full entry (Problem/Evidence/Proposed fix/Tests required/Related) in its
   backlog file, and read every file under "Where:".
4. Set its status to `in-progress` in the backlog file.
5. Create the branch: `feat/<ID>-<slug>` for new capability, `fix/<ID>-<slug>` for a bug, using a
   short kebab-case slug from the title (e.g. `fix/BUG-006-avoid-list-remove-on-missing-id`).
   `git checkout -b <branch>`.
6. Write a task brief (context, files, acceptance criteria, tests required) and delegate to the
   `implementer` agent with `model: sonnet`, per `.claude/rules/model-delegation.md` — remind it
   of that rule explicitly in the brief.
7. After `implementer` reports back, run `/review` on the diff.
8. On approval, set the item's status to `done` in its backlog file and report the branch name and
   summary to the user; do not commit or push — that is a separate explicit step (`/commit`).
