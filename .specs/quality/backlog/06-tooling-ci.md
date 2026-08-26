# 06 · Tooling, CI/CD, packaging

### TOOL-001 · CI does not gate quality
- Priority: P1 · Effort: M · Status: done
- Where: `.github/workflows/workflow.yml` (only prints the Python version),
  `linux-lint-ubuntu-24-04.yml:29,33` (`poetry add ruff`, `continue-on-error: true`),
  `linux-unit-tests-ubuntu-24-04.yml` (no cache, no coverage upload, no system deps), Windows jobs
  (no enchant/wkhtmltopdf), no type-check, security, build or release job, no `concurrency`, actions
  not pinned.
- Proposed fix: single `ci.yml` with jobs `lint` (ruff check + ruff format --check),
  `typecheck` (mypy), `security` (bandit, pip-audit), `test` (matrix ubuntu/windows × 3.12/3.13,
  coverage → Codecov, junit summary), `e2e` (golden harness), `build` (poetry build + twine check);
  `release.yml` on tag (build, publish to TestPyPI/PyPI via trusted publishing, GitHub release with
  changelog); `docs.yml` (pdoc → GitHub Pages).
- Done: ci.yml/release.yml/docs.yml (d1ae7c1)
- Related: SEC-005

### TOOL-002 · Pre-commit runs the whole pipeline and stages everything
- Priority: P1 · Effort: S · Status: done
- Where: `.pre-commit-config.yaml`, `scripts/generate_logs_coverage_badge.sh`, `scripts/prepare_*.sh`
- Proposed fix: standard hook set (ruff, ruff-format, mypy, bandit, check-yaml, check-toml,
  end-of-file-fixer, trailing-whitespace, detect-private-key, `poetry check --lock`,
  conventional-pre-commit for messages). Keep the old scripts under `tools/legacy/` until removed.
- Done: standard pre-commit (d1ae7c1); note `pre-commit install` still to be run by the maintainer
- Related: SEC-006

### TOOL-003 · `pyproject.toml` hygiene
- Priority: P1 · Effort: S · Status: done
- Where: `pandas-stubs` in runtime deps; `requires-python = ">=3.12, !=3.14.1, <4.0"`; no
  `[tool.ruff]` (line-length 150 only for black → ruff's E501 not selected); no `[tool.mypy]`,
  `[tool.bandit]`; `black` *and* `ruff` (use `ruff format`); coverage `exclude_lines` includes
  `pass`, `continue`, `break` (hides real gaps); `classifiers` minimal.
- Proposed fix: move stubs to dev group; `[tool.ruff] line-length = 120, select = ["E","F","I","B",
  "UP","SIM","PD","PL","S","N","RUF"]`; `[tool.mypy] strict = true` with per-module overrides for
  legacy; drop black; `[tool.pytest.ini_options] addopts` without coverage (coverage via `make`),
  markers registered.
- Done: (d1ae7c1); ruff/mypy/bandit config; legacy per-file-ignores baseline to shrink

### TOOL-004 · Makefile
- Priority: P2 · Effort: S · Status: done
- Where: `Makefile:16-23` (`rm -rf poetry.lock` on install/update), `clean` deletes `docs/`,
  `exec` uses `python3` outside Poetry, no `check`, `typecheck`, `security`, `harness` targets.
- Proposed fix: `make setup`, `make check` (lint+type+security+unit), `make test-unit`,
  `make test-e2e`, `make harness-update`, `make bench`, `make docs`, `make build`.
- Done: Makefile rewritten. Note: `make release-dry-run` is not implemented; `make build` is the
  real target that exists today.

### TOOL-005 · Versioning by shell scripts and a hand-incremented `serial`
- Priority: P2 · Effort: S · Status: open
- Where: `scripts/prepare_metadata.sh`, `scripts/prepare_pyproject.sh`, `config/metadata_info.py:44`
  (`serial = 732`), README badge `0.7.65b732`.
- Proposed fix: single version in `pyproject.toml`; `importlib.metadata.version("canoa_data_validate")`;
  bumps via `poetry version` in the release workflow (or `poetry-dynamic-versioning` from git tags);
  `CHANGELOG.md` maintained by `release-please` or `towncrier` fragments.
- Related: BUG-017

### TOOL-006 · Generated artefacts committed
- Priority: P2 · Effort: S · Status: in-progress
- Where: `docs/**` (pdoc HTML), `data/output/**` (reports), `assets/coverage/*.svg`, `dev-reports/`
  (ignored but present), `dist/` (ignored but present).
- Proposed fix: `docs.yml` publishes to Pages; goldens replace reports; Codecov badge; `make clean`.
- Done: pdoc HTML removed; `data/output/**` reports and `assets/coverage/*.svg` still tracked; replace by goldens/Codecov
- Related: SEC-009

### TOOL-007 · Repository scaffolding
- Priority: P2 · Effort: S · Status: done
- Proposed fix: `.editorconfig`, `CODEOWNERS`, `.github/ISSUE_TEMPLATE/{bug,feature,rule}.yml`,
  `.github/PULL_REQUEST_TEMPLATE.md`, `dependabot.yml` (pip + actions), `SECURITY.md`,
  `CONTRIBUTING.md`, remove empty `.github/appmod/appcat`, delete `.github/copilot-instructions.md`
  (replaced by `AGENTS.md` + `CLAUDE.md`).
- Done: (d1ae7c1)

### TOOL-008 · Installed-package experience
- Priority: P2 · Effort: M · Status: open
- Where: `main.py:8` prints at import; `.config` lookups (BUG-004); enchant temp files inside the
  package (BUG-022); `wkhtmltopdf` hard requirement (SEC-002); `static/` must be shipped (OK today).
- Proposed fix: `canoa-data-validate --version` works offline; no writes inside the package; optional
  extras `[pdf]`, `[spell]`.

### TOOL-009 · Scripts
- Priority: P3 · Effort: S · Status: open
- Where: `scripts/run_main_pipeline.bat` uses `--d` (abbreviation of `--debug`),
  `scripts/*.sh` `source .venv/bin/activate` (assumes venv location), Portuguese echo messages.
- Proposed fix: replace with `tools/harness/run_fixtures.py` (cross-platform, Python) and Make
  targets.

### TOOL-010 · Dependency policy
- Priority: P3 · Effort: S · Status: open
- Where: `pyproject.toml` caret ranges on everything, `pandas>=3.0.1` (very new; verify calamine and
  pandas-stubs compatibility), `poetry.lock` 157 kB.
- Proposed fix: document upgrade cadence in `.specs/infrastructure/dependencies.md`; Dependabot
  weekly; `pip-audit` in CI.
