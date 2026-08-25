---
description: Cut a release — version bump, changelog, build, local tag (never publishes or pushes)
argument-hint: "<version>"
allowed-tools: Bash(poetry build*), Bash(poetry run twine check*), Bash(git tag*), Bash(make check*), Read, Edit, Grep, Glob, Agent
---

Argument: `$ARGUMENTS` — the target version (semver, e.g. `0.8.0`) or `next` to let the agent infer
it from the changelog.

1. Confirm `make check` is currently green; refuse to proceed otherwise.
2. Delegate to `release-manager` (`model: haiku` per `.claude/rules/model-delegation.md` — state
   the rule; this is mechanical release bookkeeping) with `$ARGUMENTS`, following its documented
   process: changelog finalization, version bump, build, local tag.
3. Report the version chosen, files changed, build artifacts, and the checklist result.
4. Remind the user explicitly: this command never runs `git push` or `poetry publish`/`twine
   upload` — pushing the tag to trigger `release.yml` is a separate, explicit user action.
