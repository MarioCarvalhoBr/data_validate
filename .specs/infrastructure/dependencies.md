# Dependency policy

## Principles

1. `poetry.lock` is the truth for every environment (dev, CI, release). `poetry install --sync`;
   never delete the lock to "refresh" (TOOL-004, SEC-005).
2. Runtime dependencies are minimal and pure-Python where possible; native/system-bound features
   live behind extras (`pdf`, `spell`, `fast`).
3. Every runtime dependency has an owner line in this file: why it exists and what would replace
   it.

## Runtime inventory (updated 2026-09-13 against `pyproject.toml`'s current `[project].dependencies`
and `[project.optional-dependencies]`; TOOL-008/SEC-002/ARC-016/TOOL-003 already changed several
rows below since the 2026-08-25 baseline — see each row's note)

| Package | Version | Why | Alternative / exit plan |
|---|---|---|---|
| pandas | 3.0.1 | DataFrame model | keep; Polars backend is a future idea |
| python-calamine | 0.6.2 | fast `.xlsx` reader | keep |
| chardet | 5.2.0 | encoding detection in `FileSystemUtils` | may be dropped when readers assume UTF-8 with explicit fallback |
| pyenchant | 3.3.0 | hunspell spell-check | **main dependency, not an extra** (TOOL-008 decision, 2026-09-13): its import is already lazy and already fails gracefully into a `SPELL-001` business-rule error when unusable, so moving it behind a `[spell]` extra would only change default-install footprint, not runtime robustness — deferred as a narrower, non-blocking follow-up; pure-Python fallback remains the longer-term exit plan (ARC-015) |
| jinja2 | 3.1.6 | HTML report | keep (with autoescape) |
| babel | 2.18.0 | locale number formatting | keep |
| networkx | 3.6.1 | composition graph analysis | keep |

`pdfkit` is **no longer a declared dependency** (main or extra) as of Phase 4/ADR-0007 (SEC-002):
`weasyprint (>=70,<80)` under the `pdf` extra is the supported PDF renderer;
`pdfkit`/`wkhtmltopdf` survives only as an opportunistic compatibility fallback used when already
present on the host (`FileReportGenerator._save_pdf_file`'s lazy import), never installed by
`pip install canoa_data_validate[pdf]`. `pandas-stubs` already moved to the dev group (TOOL-003;
`^3.0.0.260204` under `[tool.poetry.group.dev.dependencies]`), not a runtime dependency — removed
from this table.

## Dev inventory (target)

pytest, pytest-cov, pytest-mock, pytest-xdist, pytest-benchmark, hypothesis, coverage, ruff,
mypy (+ `types-*`), bandit, pip-audit, pre-commit, pdoc.
Removed: black, flake8, flake8-html, genbadge (SEC-009/TOOL-006: badges are Codecov/CI now, no
local SVG generation).

## Upgrade cadence (TOOL-010)

- **Routine (weekly)**: Dependabot opens grouped minor/patch PRs against `pyproject.toml` +
  `poetry.lock`; grouped so `make check` + `make test-e2e` run once per group, not once per
  package. A green CI run is the only merge gate — no extra manual review beyond that for a
  minor/patch bump within the declared caret range.
- **Majors**: reviewed individually, never auto-merged — read the changelog, bump by hand with
  `poetry update <package>`, run `make check` + `make test-e2e` locally before opening the PR.
  `pandas`/`numpy` majors additionally require `make bench` before/after (a major can change
  copy-on-write semantics or dtype defaults that shift the PERF-009 budget numbers) — pin the new
  major only once the benchmark stays inside the < 10 s / < 1 GB budget.
- **Security advisories**: `pip-audit` runs in CI (`make security`) on every push. A finding is
  fixed within one week via `poetry update <affected-package>` targeting the patched version (not
  a blanket `poetry update` of the whole lock, which would also pull in unreviewed majors); if no
  patched version exists yet, document the accepted risk and a revisit date in `SECURITY.md` rather
  than leaving the finding unexplained in CI logs.
- **Lock discipline**: `poetry.lock` is regenerated only via `poetry install --sync` /
  `poetry update <package>` — never hand-edited, never deleted to "refresh" (TOOL-004, SEC-005).
  Every dependency bump commits `pyproject.toml` and `poetry.lock` together.

## Caret-range rationale

Every dependency in the inventory above is declared with a caret range (`^`/`(>=x,<y)` in Poetry's
`project.dependencies` syntax) rather than pinned to an exact version:
- A caret range lets Dependabot's weekly patch/minor PRs land without a manual `pyproject.toml`
  edit for every release upstream makes, while `poetry.lock` still pins the exact resolved version
  actually installed — so builds stay reproducible (the lock, not the range, is what CI/release
  installs from) while the *allowed* range stays wide enough for routine automation to work.
  Exact pins would turn every patch release into a manual `pyproject.toml` diff for no safety
  benefit the lock file doesn't already provide.
- The range's upper bound is the next major version (semver's contract: breaking changes only at
  a major bump) — this is what makes "majors reviewed individually, minors/patches automatic" a
  safe default rather than a hope; a library that breaks its own semver contract is a reason to
  tighten that specific package's range, not to abandon caret ranges generally.

## Adding a dependency

1. Justify in the PR (problem, why stdlib/pandas is insufficient, maintenance status, licence
   compatible with MIT).
2. Add to the right group/extra with a caret range; commit the lock.
3. Update this inventory and `packaging.md` if system deps change.

Last synced with code: 1325b48
