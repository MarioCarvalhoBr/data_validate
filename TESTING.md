# Testing

Framework: **pytest + pytest-mock only** (`unittest.mock` is forbidden). Tests mirror the
`data_validate/` package tree under `tests/unit/`; end-to-end goldens live under `tests/e2e/`.

## Commands

```bash
make test-unit        # unit tests, parallel (pytest-xdist), marker "not e2e"
make test-e2e          # golden end-to-end harness against data/input/* fixtures
make test               # test-unit + test-e2e
make coverage           # unit tests + term/html/xml coverage + ratchet check
make harness-update     # regenerate e2e goldens (review the diff before committing!)
make bench               # pytest-benchmark performance suite
make check               # lint + typecheck + security-offline + test-unit (fast local gate)
```

## Markers

`unit` (default, every commit), `integration`, `e2e` (`make test-e2e`), `slow` (`make bench`),
`requires_enchant` (real hunspell backend), `requires_pdf` (wkhtmltopdf). Tests requiring an
absent optional dependency skip with a clear reason instead of failing.

## Golden policy

`tests/e2e/test_golden.py` runs the real CLI against every fixture under `data/input/` and
compares normalised output (parsed HTML + stdout JSON) against `tests/e2e/golden/*.json`.
Goldens are regenerated **only** via `make harness-update`, with the diff reviewed and the
reason recorded in `tests/e2e/golden/CHANGELOG.md`. Three consecutive runs must produce
identical goldens.

## Coverage

The repo-wide gate is a **ratchet**, currently `fail_under = 54` in `pyproject.toml`
(measured 54.99–55.97 % on 2026-08-25), raised over time by `tools/coverage_ratchet.py` and
never lowered — this replaces the outdated "4 %" figure that appeared in earlier docs. Any
brand-new module needs **≥ 95 %** line coverage before merge, and every bug fix ships a
regression test.

Full strategy, fixtures and the test pyramid: [`.specs/quality/testing-strategy.md`](.specs/quality/testing-strategy.md).
