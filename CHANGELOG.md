# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `.specs/` — the written source of truth for the migration: overview, current/target
  architecture, data flow, error model, module map, CLI/Python API/report-format contracts,
  business rules for all 8 sheets with stable rule IDs, use cases, testing/security/performance/
  code-quality strategy, infrastructure and i18n specs, and future/deprecation notes.
- `.specs/quality/backlog/` — a 90-item, prioritised audit of the current codebase (bugs,
  security, architecture, testing, performance, tooling/CI, docs/i18n) and a 6-phase migration
  roadmap (`08-migration-roadmap.md`).
- `docs/adrs/` — 14 architecture decision records covering the migration strategy, the
  `SheetSpec`/`Issue`/`Rule` model, the CLI contract, report rendering, spell-check backend,
  the tooling baseline, testing policy, and the multi-agent development workflow itself.
- `.claude/` — the multi-agent development harness: standing rules (`model-delegation`,
  `spec-sync`, `coding-standards`, `testing`, `i18n`, `security`, `dataframe-conventions`,
  `architecture-boundaries`, `git-workflow`, `performance`), 12 specialised subagents, 16
  slash commands, and 8 skills (rule authoring, spreadsheet protocol, pytest-mock patterns,
  pandas vectorisation, report rendering, ADR writing, release process, golden harness).
- `CLAUDE.md` and `AGENTS.md` — orchestration guide and tool-agnostic contributor guide.
- `CONTRIBUTING.md` and `SECURITY.md` — contribution workflow and vulnerability-reporting
  policy with a threat-model summary.
- Modern tooling baseline: `mypy` (strict for new/migrated code), `bandit`, `pip-audit`,
  `pytest-xdist`, `hypothesis`, `pytest-benchmark` added to the dev dependency group; `ruff`
  rule set widened (`select = ["E","F","W","I","B","UP","SIM","PD","PL","S","N","RUF","C4",
  "PTH","RET"]`, line length 120); `mypy`/`bandit`/`coverage` configuration in `pyproject.toml`.
- `.github/workflows/ci.yml` (lint, typecheck, security, matrix test on Linux/Windows ×
  3.12/3.13, e2e, build), `release.yml` (trusted-publishing release to PyPI), and `docs.yml`
  (pdoc to GitHub Pages), replacing the six legacy per-OS workflows.
- `.github/dependabot.yml`, `.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md`, and
  `.github/ISSUE_TEMPLATE/{bug_report,feature_request,validation_rule}.yml`.
- New `.pre-commit-config.yaml`: standard hygiene hooks, `ruff-check`/`ruff-format`, `mypy`
  (scoped to `tools/`/`tests/e2e/`), `bandit`, `poetry-check --lock`, `conventional-pre-commit` —
  no hook runs the application pipeline or stages files automatically (see SEC-006 below).
- `tools/harness/`, `tools/i18n_check.py`, `tools/coverage_ratchet.py` — developer scripts for
  running fixtures, profiling the pipeline, checking i18n catalog parity, and enforcing the
  coverage ratchet; legacy `scripts/*.sh/.bat` moved to `tools/legacy/` (kept, unused by any
  `make` target, scheduled for deletion in migration Phase 5).
- New `Makefile` targets: `setup`, `lint`, `format`, `typecheck`, `security`/`security-offline`,
  `test-unit`, `test-e2e`, `test`, `coverage`, `check`, `harness-update`, `bench`, `profile`,
  `run`/`run-all`, `i18n-check`, replacing the previous `black`/`test-fast`/`test-short` set.
- CLI (ARC-011/SEC-008/TOOL-008): `-i/--input` and `-o/--output` as new short/long aliases for
  `--input_folder`/`--output_folder` (kept working unchanged); `--json PATH` writes the same JSON
  summary object as the stdout `<{...}>` fragment to a file; `--fail-on {error,warning,never}`
  (default `error`) governs the exit code; `--version` prints the version and exits 0 offline,
  with no writes. `--i`/`--o`/`--l`/`--d` (the two-dash abbreviations that only ever worked via
  `allow_abbrev=True` prefix matching) are now explicit, deprecated aliases: they still work, but
  print a one-line deprecation warning to stderr naming their replacement.
- `MetadataInfo.PROTOCOL_VERSION`/`__protocol_version__` (DOC-006): a stable constant recording
  which AdaptaBrasil protocol version the validator implements (`"1.16"`); surfaced in the HTML
  report's version line alongside the validator version and OS. See
  `.specs/business-rules/protocol-changelog.md`.

### Changed
- **CLI exit code (SEC-008, breaking for scripts that assumed "always 0")**: `canoa-data-validate`
  now exits `0` when no issue at/above `--fail-on` was found, `1` when one was, and `2` on an
  unexpected runtime failure (bad arguments, unreadable input, a crash inside the pipeline) —
  instead of always exiting `0`. Pass `--fail-on never` to restore the previous always-0 behaviour.
- The startup banner (`main.py`, previously printed at `import data_validate` time) now prints
  once, from inside `main()`, to stderr instead of stdout (ARC-012) — stdout keeps carrying only
  the machine-readable `<{...}>` JSON summary line.
- `argparse` now runs with `allow_abbrev=False`: undeclared prefix abbreviations (e.g.
  `--input_fol`) are rejected; use the explicit `--input_folder`/`-i`/`--input` flags instead.
- `pyproject.toml`: removed `black` and `flake8`/`flake8-html` from the dev dependency group in
  favour of `ruff format`; `[tool.coverage.report]` `fail_under` raised from the historical
  4 %/50 % figures to **54** (ratcheted upward by `tools/coverage_ratchet.py`, never lowered);
  removed `pass`/`continue`/`break` from `exclude_lines`.
- Root documentation (`README.md`, `HOW_IT_WORKS.md`, `TESTING.md`, `CODE_OF_CONDUCT.md`)
  rewritten from scratch to be accurate to the current code, link into `.specs/`, and drop
  hard-coded version numbers in favour of badges. `CODE_OF_CONDUCT.md` now uses the actual
  Contributor Covenant 2.1 text (it previously contained an internal commit-message style
  guide under a misleading filename).
- **Versioning (TOOL-005, breaking for anyone parsing the old `X.Y.Zb<serial>` shape)**:
  `MetadataInfo.__version__` is now read verbatim from `importlib.metadata.version(
  "canoa_data_validate")` (falling back to `"0.0.0+unknown"` when the package is not installed),
  instead of being composed from a hand-maintained `release_level`/`serial`/`dev` triplet
  (`serial: Final = 732`, bumped by `scripts/prepare_metadata.sh` on every commit). A release now
  only needs a `pyproject.toml` version bump — no more `X.Y.Zb<serial>` strings, no shell script to
  run. `MetadataInfo._make_version` was removed; `__status__` is now always `"Production/Stable"`.
  The e2e golden harness already normalised the JSON summary's `version` field to a placeholder
  before this change (it is machine/commit-specific), so no golden re-baseline was needed.

### Removed
- `.github/copilot-instructions.md` (legacy AI-assistant instructions; superseded by
  `CLAUDE.md`/`AGENTS.md`/`.claude/rules/`) and the empty `.github/appmod/` directory.
- The six legacy per-OS CI workflows (`linux-ci-build-*.yml`, `linux-lint-*.yml`,
  `linux-unit-tests-*.yml`, `windows-ci-build-*.yml`, `windows-unit-tests-*.yml`), superseded by
  `ci.yml`.

## [0.7.65] - 2026-02-20

### Added
- New version refactoring and improvements.
- Updated the `pyproject.toml` file to include the `pandas` dependency, ensuring that it is explicitly listed for proper package management.
- Added a new check to validate that all columns in the DataFrame have unique names, preventing potential data processing issues related to duplicate column names.
- Improved the error handling in the `DataImporterFacade.load_all` method to provide more specific and informative error messages for various exceptions, including `FileNotFoundError`, `UnicodeDecodeError`, `ValueError`, `pd.errors.ParserError`, and `IOError`. The order of exception catching was also refined to ensure that more specific exceptions are caught before more general ones.
- Enhanced the `check_vertical_bar` function to provide clearer and more detailed error messages when forbidden characters (specifically the vertical bar `|`) are found in column names. The messages now specify whether the issue is in level 0 or level 1 of a `MultiIndex` column name, or if it is found within data under a column whose level 0 header is "unnamed".
- Corrected the initialization process in the `SpModelABC` class (and functions called within it, specifically `check_unnamed_columns`) to ensure that DataFrames with `MultiIndex` headers are not inadvertently converted to `SingleIndex` headers. The validation functions now inspect column names without altering the DataFrame's structure.
- Ensured that the `check_unnamed_columns` function correctly identifies and processes columns based on their names (e.g., "unnamed") across both `SingleIndex` and `MultiIndex` DataFrames without modifying the original DataFrame's column structure.
- Updated and corrected author information in the `pyproject.toml` file to ensure accurate attribution.
- General improvements to user messages for better clarity and understanding.

### Fixed
- Corrected an issue in the `SpModelABC` initialization (or functions called within it, specifically `check_unnamed_columns`) where DataFrames with `MultiIndex` headers were being converted to `SingleIndex` headers. The validation functions now inspect column names without altering the DataFrame's structure.
- Ensured `check_unnamed_columns` correctly identifies and processes columns based on their names (e.g., "unnamed") across both `SingleIndex` and `MultiIndex` DataFrames without modifying the original DataFrame's column structure.
- Improved the exception handling in `DataImporterFacade.load_all` to provide more specific error messages for different file processing issues, including `FileNotFoundError`, `UnicodeDecodeError`, `ValueError`, `pd.errors.ParserError`, and `IOError`. The order of exception catching was also refined.

### Changed
- Enhanced error messages in `check_vertical_bar`:
    - Messages now specify if a forbidden character (`|`) is found in level 0 or level 1 of a `MultiIndex` column name.
    - A distinct message is now generated if data containing a `|` is found within a column whose level 0 header is "unnamed".
- Updated and corrected author information in `pyproject.toml`.

## [0.5.0] - 2025-05-07

### Added
- New checks related to issues found in the biodiversity sector release.

## [0.4.0] - 2024-12-16

### Added
- Validation that every leaf indicator must have associated data.
- Verification of scenarios in proportionalities.
- Decimal place validation for values.
- New information received from Canoa.

### Changed
- Various improvements to user messages.

## [0.3.0] - 2024-10-08

### Added
- New check for unique indicator titles based on a tree structure. (Merge pull request #230 from MarioCarvalhoBr/main)

## [0.2.0] - 2024-07-02

### Added
- First version with verification of all files.

## [0.1.0] - 2024-04-30

### Added
- First version with the basic structure of the tool.
- Implemented checks for value types, relationships, and patterns in text formats.

[Unreleased]: https://github.com/AdaptaBrasil/data_validate/compare/v0.7.65...HEAD
[0.7.65]: https://github.com/AdaptaBrasil/data_validate/compare/v0.5.0...v0.7.65
[0.5.0]: https://github.com/AdaptaBrasil/data_validate/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/AdaptaBrasil/data_validate/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/AdaptaBrasil/data_validate/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/AdaptaBrasil/data_validate/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/AdaptaBrasil/data_validate/releases/tag/v0.1.0
