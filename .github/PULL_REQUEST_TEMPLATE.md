## Summary

<!-- What does this PR change and why? Link the backlog item(s) it closes, e.g. "Closes BUG-006". -->

Backlog ID(s):

## Checklist

- [ ] Tests added or updated for the change (pytest + pytest-mock, table-driven where it fits)
- [ ] `.specs/**` updated in the same PR if this changes behaviour, a business rule, the CLI
      contract, a file layout, or a convention (spec-sync — see `.claude/rules/spec-sync.md`)
- [ ] `CHANGELOG.md` `Unreleased` section updated
- [ ] `make check` passes locally (lint, typecheck, security-offline, unit tests)
- [ ] No production code was touched without a corresponding regression test
- [ ] Commit messages follow Conventional Commits

## Notes for reviewers

<!-- Anything a reviewer should look at closely: risk areas, follow-ups left for later, goldens
     re-baselined and why. -->
