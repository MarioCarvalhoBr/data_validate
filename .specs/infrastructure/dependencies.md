# Dependency policy

## Principles

1. `poetry.lock` is the truth for every environment (dev, CI, release). `poetry install --sync`;
   never delete the lock to "refresh" (TOOL-004, SEC-005).
2. Runtime dependencies are minimal and pure-Python where possible; native/system-bound features
   live behind extras (`pdf`, `spell`, `fast`).
3. Every runtime dependency has an owner line in this file: why it exists and what would replace
   it.

## Runtime inventory (2026-08-25)

| Package | Version | Why | Alternative / exit plan |
|---|---|---|---|
| pandas | 3.0.1 | DataFrame model | keep; Polars backend is a future idea |
| python-calamine | 0.6.2 | fast `.xlsx` reader | keep |
| chardet | 5.2.0 | encoding detection in `FileSystemUtils` | may be dropped when readers assume UTF-8 with explicit fallback |
| pyenchant | 3.3.0 | hunspell spell-check | extra `spell`; pure-Python fallback (ARC-015) |
| pdfkit | 1.0.0 | PDF via wkhtmltopdf | replace by WeasyPrint under extra `pdf` (SEC-002) |
| jinja2 | 3.1.6 | HTML report | keep (with autoescape) |
| babel | 2.18.0 | locale number formatting | keep |
| networkx | 3.6.1 | composition graph analysis | keep |
| pandas-stubs | 3.0.0 | typing | move to dev |

## Dev inventory (target)

pytest, pytest-cov, pytest-mock, pytest-xdist, pytest-benchmark, hypothesis, coverage, ruff,
mypy (+ `types-*`), bandit, pip-audit, pre-commit, pdoc, genbadge (until badges move to Codecov).
Removed: black, flake8, flake8-html.

## Upgrade cadence

- Dependabot weekly PRs, grouped minor/patch; majors reviewed individually with the changelog
  read and `make check` + `make test-e2e` green.
- pandas/numpy majors: run benchmarks before merging.
- Security advisories (`pip-audit` in CI): fix within one week or document an accepted risk in
  `SECURITY.md`.

## Adding a dependency

1. Justify in the PR (problem, why stdlib/pandas is insufficient, maintenance status, licence
   compatible with MIT).
2. Add to the right group/extra with a caret range; commit the lock.
3. Update this inventory and `packaging.md` if system deps change.

Last synced with code: 09279f4
