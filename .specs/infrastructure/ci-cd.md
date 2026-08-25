# CI/CD

## Workflows (`.github/workflows/`)

### `ci.yml` — on push to `main` and on pull requests

`concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }`. All actions pinned by
commit SHA with a version comment.

| Job | Runner | Steps | Gate |
|---|---|---|---|
| `lint` | ubuntu-24.04 | `poetry install --only dev`, `ruff check .`, `ruff format --check .` | blocking |
| `typecheck` | ubuntu-24.04 | `mypy` | blocking |
| `security` | ubuntu-24.04 | `bandit -r data_validate -c pyproject.toml`, `pip-audit` | blocking (audit may `--ignore-vuln` with justification) |
| `test` | matrix `ubuntu-24.04`, `windows-2022` × Python `3.12`, `3.13` | Poetry cache; Linux `apt-get install enchant-2 hunspell-pt-br hunspell-en-us wkhtmltopdf`; `pytest -n auto --cov --cov-report=xml --junitxml`; Codecov upload (`fail_ci_if_error: false`); junit artefact; coverage ratchet | blocking |
| `e2e` | ubuntu-24.04 | system deps; `make test-e2e` | blocking |
| `build` | ubuntu-24.04 | `poetry build`, `twine check dist/*`, upload artefact | blocking |

### `release.yml` — on tag `v*`

1. Verify tag matches `pyproject.toml` version.
2. `poetry build`; `twine check`.
3. Publish to TestPyPI then PyPI with trusted publishing (`pypa/gh-action-pypi-publish`,
   environment `pypi`, OIDC — no API tokens in secrets).
4. Create a GitHub Release with the CHANGELOG section for the version and the wheel/sdist.

### `docs.yml` — on push to `main`

`pdoc data_validate -o site/` → `actions/upload-pages-artifact` → `actions/deploy-pages`.
Generated HTML is never committed.

### Dependabot (`.github/dependabot.yml`)

Weekly for `pip` (grouped minor/patch) and `github-actions`.

## Branch protection (recommended settings)

`main`: require PR, require `lint`, `typecheck`, `security`, `test`, `e2e`, `build` to pass,
require linear history, no force-push. CODEOWNERS review for `data_validate/rules/**` and
`.specs/business-rules/**`.

## Local parity

`make check` runs the same commands as `lint + typecheck + security + test-unit`; pre-commit
runs ruff/format/mypy/bandit on staged files; the Claude `Stop` hook runs unit tests when Python
files changed.

## Badges

README shows: CI status (`ci.yml`), Codecov coverage, PyPI version, Python versions, license.
The committed SVG badges under `assets/coverage/` are retired (TOOL-006).

Last synced with code: 3dcfdb1
