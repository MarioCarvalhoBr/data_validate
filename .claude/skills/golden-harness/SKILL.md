---
name: golden-harness
description: Use when running, debugging, or updating the golden end-to-end harness in tests/e2e/ — how it normalizes report output, what a diff means, and the process for updating a golden with a reviewed reason.
---

# The golden e2e harness

`tests/e2e/test_golden.py` is the safety net for the whole migration: it runs the real CLI end to
end over every fixture folder in `data/input/*` and asserts the output matches a stored golden,
so any behaviour change — intentional or not — is visible in the diff.

## How it works

1. For each subfolder of `data/input/`, run the pipeline exactly as the platform does:
   `poetry run python -m data_validate.main --input_folder data/input/<fixture> --output_folder
   <tmp> --locale pt_BR --no-time --no-version --sector "Setor A" --protocol "Protocolo B" --user
   "Usuário C"` via `subprocess`, inside an isolated `tmp_path` (never the repo's `data/output/`).
2. Parse the generated HTML report with `html.parser` (never a fragile regex) to extract a
   normalized, ordered list of `(verification_name, severity, message)` tuples, and parse the
   stdout JSON summary.
3. First run for a fixture: no golden exists yet — running with `--update-golden` (or
   `make harness-update FIXTURE=<fixture>`) creates `tests/e2e/golden/<fixture>.json`.
4. Every subsequent run: compare the freshly generated, normalized output against the stored
   golden; any difference fails the test with a readable diff (which messages appeared, vanished,
   or changed text).
5. Tests are marked `@pytest.mark.e2e` (excluded from the fast `test-unit` target, included in
   `test-e2e`/`test`).

## Spell-check skip

If `pyenchant`/hunspell dictionaries are not available in the environment, the harness skips the
spelling section rather than failing or silently passing: it strips that section from both the
freshly generated output and the comparison, and records `"spell_skipped": true` in the golden so
a reviewer knows that run didn't exercise `SPELL-*` rules.

## Reading a diff

- **Message text changed, count same** → likely a deliberate wording/i18n change; needs a written
  reason (see below) before updating the golden.
- **Message count changed (new/missing findings)** → almost always a behaviour change in a
  validator; treat as a regression unless the task explicitly intended it (e.g. a new rule from
  `/rule`).
- **Ordering changed only** → check the normalization step first; sort order should be stable
  (verification name, then row) — an ordering diff usually means the harness's normalization
  regressed, not the report.
- **JSON summary changed shape** (new/missing key) → a CLI/report contract change; must be
  reflected in `.specs/api/report-format.md` in the same change (`spec-sync`).

## Updating a golden

Never run `make harness-update` casually. Use `/harness-update <fixture> "<reason>"`
(`integration-tester`), which: regenerates the golden, produces a line-by-line diff for you to
review, and appends an entry to `tests/e2e/golden/CHANGELOG.md` (date, fixture, reason, commit/PR
if known) in the same change as the code causing the diff. A golden update with no accompanying
code change in the same commit is almost always a mistake.

## Stability requirement

Run the suite three times in a row before trusting a golden is stable — any nondeterminism
(dict/set ordering, floating-point formatting, file-system iteration order) must be fixed in the
pipeline or the harness's normalization, never worked around by loosening the comparison.
