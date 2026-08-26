# Environments

| Environment | Where | Python | System deps | How the tool runs |
|---|---|---|---|---|
| Developer (Linux) | Ubuntu 24.04 / Debian; `poetry install`, `make setup` | 3.12 (3.13 tested) | `enchant-2 hunspell-pt-br hunspell-en-us wkhtmltopdf` optional | `poetry run canoa-data-validate …`, `make run FIXTURE=…` |
| Developer (Windows) | Windows 10/11; Poetry; PowerShell | 3.12 | pyenchant wheel (bundled enchant) + dictionaries in `static/dictionaries/hunspell`; wkhtmltopdf installer optional | same commands; `tools/harness/run_fixtures.py` replaces `.bat` |
| Developer (macOS) | Homebrew Python/Poetry | 3.12 | `brew install enchant wkhtmltopdf` optional | same |
| CI | GitHub Actions `ubuntu-24.04`, `windows-2022` | 3.12, 3.13 | installed on Linux only; Windows runs with markers skipping enchant/PDF tests | `make check`, `make test-e2e` |
| Canoa platform server | Linux service that invokes the CLI per upload | 3.12 | enchant + dictionaries; PDF backend per decision (ADR-0007) | `canoa-data-validate --input <upload> --output <reports> --json <summary>` with exit-code handling |
| Library consumer | any | ≥ 3.12 | none for core | `from data_validate import validate` |

## Environment variables

| Variable | Effect | Status |
|---|---|---|
| `ENCHANT_CONFIG_DIR` | Set **by the tool** to `static/dictionaries` today (BUG-022) | to be removed; tool passes paths explicitly |
| `PYTHONUTF8=1` | Recommended on Windows for UTF-8 console/file I/O | documented |
| `DATA_VALIDATE_LOG_LEVEL` (target) | Overrides console log level | Phase 1 |
| `NO_COLOR` (target) | Disables ANSI colours in console renderer | Phase 1 |

## Filesystem expectations

- Read: input folder (recursively **not** — only its root).
- Write: output folder (reports, `logs/` when `--debug`, JSON), temp dir for spell sessions.
- Nothing under the package directory or the user's home is written (target; today `.config/`
  is created — BUG-004).

## Reproducibility

`poetry.lock` + pinned actions + `tools/harness/generate_fixture.py --seed` make CI and
benchmarks reproducible across machines.

Last synced with code: 09279f4
