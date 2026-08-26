# UC-03 · Validate many bundles in batch / CI

- Primary actors: Canoa platform (server), INPE maintainer (regression checks)
- Goal: validate every folder under a root, collect summaries, fail the job on regressions

## Preconditions
- A root folder with one bundle per sub-folder (e.g. `data/input/*`).

## Main flow
1. Operator runs `python tools/harness/run_fixtures.py --input data/input --output data/output
   --locale pt_BR [--fixtures NAME ...] [--timeout 600]` (also wired to `make run-all`; replaces
   the legacy `tools/legacy/run_main_pipeline.sh`/`.bat`). `--input`/`--output` default to
   `data/input`/`data/output`; `--fixtures` restricts the run to named subfolders instead of every
   folder under `--input`.
2. For each fixture the harness invokes the CLI once, with `--no-time --no-version --sector
   "Setor A" --protocol "Protocolo B" --user "Usuário C"` and the given `--locale`, capturing
   stdout/stderr and the subprocess exit code. The CLI has no `--json` flag today; instead the
   harness parses the `<{...}>` JSON summary fragment the CLI prints to stdout (errors/warnings/
   tests counts). Today the CLI always exits 0 regardless of validation errors (SEC-008 — no
   exit-code contract yet), so the harness treats a fixture as failed when its exit code is
   non-zero **or** its parsed summary reports a non-zero `errors` count (or the summary could not
   be parsed at all), not on exit code alone.
3. The harness prints a fixed-width summary table to stdout (fixture, exit code, errors, warnings,
   tests, seconds) and returns exit code 1 if any fixture failed by the rule in step 2, or 2 on a
   setup error (e.g. `--input` does not exist). It does not currently write a JSON index file.
4. In CI, `make test-e2e` (`tests/e2e/test_golden.py`) separately compares each bundle's
   normalised report and stdout summary with `tests/e2e/golden/<bundle>.json`; any difference
   fails the job with a readable diff.

### Target (after ARC-011/SEC-008)
Once SEC-008 (non-zero CLI exit code on validation failure) and ARC-011 (structured `--json
<path>` output flag) land, step 2 simplifies to reading the CLI's own exit code directly instead
of parsing a stdout fragment, and step 1 gains a `--json dev-reports/runs/index.json`-style
machine-readable index alongside the printed table.

## Alternative flows
- 2a. One fixture's CLI process crashes (non-zero exit, e.g. an unhandled exception) → the harness
  continues with the remaining fixtures, that fixture is reported as failed in the summary table,
  and the overall run exits 1.
- 1a. `--input` does not exist → the harness exits 2 without running any fixture. If `--input`
  exists but resolves to zero fixture subfolders (and `--fixtures` was not given), it exits 1.
- 4a. A difference is an intended improvement → maintainer runs `make harness-update`, reviews
  the diff, writes the reason in `tests/e2e/golden/CHANGELOG.md`, commits.

## Postconditions
- Reports for all bundles under the output root; CI status reflects regressions.

## Related
- `../quality/testing-strategy.md` (golden harness), `../infrastructure/ci-cd.md`
- Backlog: TST-002, TOOL-009, PERF-007 (parallel bundles)

Last synced with code: 09279f4
