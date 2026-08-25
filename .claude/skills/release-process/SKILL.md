---
name: release-process
description: Use when cutting a release of canoa-data-validate — the checklist behind /release and release-manager, from changelog to tag, and what CI does after the tag is pushed.
---

# Release process

Local steps (done by `/release` via `release-manager`, never push/publish from here):

1. **Changelog**: `CHANGELOG.md`'s `Unreleased` section must be non-empty and accurate against
   `git log` since the last tag (Keep a Changelog format, sections Added/Changed/Fixed/Removed).
2. **Version**: semver bump inferred from the changelog entries — any `Removed`/breaking entry →
   major; any `Added` → minor; `Fixed`-only → patch. Update `pyproject.toml` `[project].version`
   (and any other place it is duplicated — check `main.py`/CLI `--version` output).
3. **Move the changelog section**: `Unreleased` entries move under `## [<version>] - <YYYY-MM-DD>`;
   a fresh empty `Unreleased` heading stays at the top for the next cycle.
4. **Build**: `poetry build`, then `poetry run twine check dist/*` to catch metadata problems
   before they reach PyPI.
5. **Tag locally**: `git tag -a v<version> -m "<version>"` — do not push it in this step.
6. **Checklist verification**: `make check` green, changelog and version consistent, build
   artifacts present in `dist/`, tag created.

## What happens after (not part of this skill's scope, requires an explicit human push)

Pushing the tag (`git push origin v<version>`, a deliberate separate action, never automated by
an agent) triggers `release.yml`: build → publish to TestPyPI then PyPI via trusted publishing
(`pypa/gh-action-pypi-publish`, no long-lived API token) → create the GitHub Release with notes
pulled from the changelog section just written.

## Pre-release checks worth running manually before tagging

- `make test-e2e` — goldens must be stable; a release must never ship a silent report-format
  regression.
- `poetry run pip-audit` — no new known vulnerabilities in the dependency set being shipped.
- Confirm optional extras (`[pdf]` for wkhtmltopdf/WeasyPrint, `[spell]` for pyenchant) still
  install cleanly if `pyproject.toml` extras changed since the last release.

## Never

- Never push the tag or publish from an agent — that is `release-manager`'s hard boundary.
- Never bump the version without changelog entries justifying the bump level.
- Never release with `make check` red or e2e goldens unstable.
