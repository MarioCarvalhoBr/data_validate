# Brief · <backlog ID or task title>

## Goal
<One sentence. What "done" looks like.>

## Context to read first
- `.specs/quality/backlog/<file>.md` § `<ID>`
- `<spec paths>`
- `<source files>` (exact paths; note which functions)
- Rules: `.claude/rules/model-delegation.md`, `coding-standards.md`, `testing.md`, `spec-sync.md`
  (+ `dataframe-conventions.md`, `security.md` when relevant)

## Scope
- In: <files/modules to change>
- Out: <explicitly excluded changes>

## Acceptance criteria
1. <observable behaviour / test that must pass>
2. `make check` green; `make test-e2e` green or goldens updated with reason
3. Specs updated: <which files>
4. Commit message: `<type>(<scope>): <ID> <summary>`

## Constraints
- Never `git push`; never `git add .`
- Messages only through the catalog; no `except Exception`; no `iterrows` in rules
- Report back: files changed, tests added, coverage of touched modules, open questions
