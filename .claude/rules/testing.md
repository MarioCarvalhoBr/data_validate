---
paths: ["tests/**", "data_validate/**"]
---

# Testing

## Framework

- `pytest` + `pytest-mock` only. `unittest.mock` and `with patch(...)`
  context managers are forbidden — use the `mocker` fixture
  (`mocker.patch(...)`, `mocker.MagicMock()`) as a direct assignment.
- Test tree mirrors the package tree: `data_validate/foo/bar.py` →
  `tests/unit/foo/test_bar.py`.
- Test function names: `test_<unit>_<scenario>` (e.g.
  `test_validate_temperature_below_minimum`). Test classes: `Test<Unit>`.
- Use `@pytest.mark.parametrize` for table-driven cases instead of copies of
  near-identical test bodies.
- Shared fixtures live in `tests/conftest.py` (or a nearer `conftest.py`);
  do not redefine the same fixture in multiple test files.

## Coverage

- Repo-wide gate is a ratchet starting at 54.99 % measured with the current configuration (55.97 % measured with the legacy coverage exclusions `pass`/`continue`/`break` excluded); baseline in `tools/coverage_baseline.txt`; gate `fail_under = 54` in `pyproject.toml` and `--cov-fail-under=54` in the Makefile. The ratchet only ever goes up, never down. Do not lower it to make a change pass.
- Any new module (created, not merely touched) needs ≥ 95 % line coverage
  before the PR is done.
- Every bug fix ships with a regression test that fails on the pre-fix code
  and passes after.

## Golden / e2e harness

- `tests/e2e/test_golden.py` runs the real CLI against `data/input/*` and
  compares normalised output against `tests/e2e/golden/*.json`.
- Only regenerate goldens via `make harness-update`, only with the diff
  reviewed by a human or `integration-tester`, and only with the reason
  recorded in `tests/e2e/golden/CHANGELOG.md`. Never regenerate to silently
  make a failing test pass.

## Property-based testing

- Use `hypothesis` for parsers and format-detection code (CSV separators,
  encodings, code patterns like `CÓDIGO-ANO[-CENÁRIO]`) where the input
  space is large and edge cases are easy to miss by hand.

## Markers

Register and use: `unit`, `integration`, `e2e`, `slow`, `requires_enchant`,
`requires_pdf`. Skip (don't fail) a test when its optional system
dependency (enchant/hunspell, wkhtmltopdf) is unavailable, with a clear
skip reason.

## Never do

- Never use `unittest.mock` or `with patch()`.
- Never write a test that depends on the current working directory without
  using the `tmp_cwd` fixture.
- Never regenerate a golden to make a test pass without review.
