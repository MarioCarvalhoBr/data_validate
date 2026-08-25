# UC-03 · Validate many bundles in batch / CI

- Primary actors: Canoa platform (server), INPE maintainer (regression checks)
- Goal: validate every folder under a root, collect summaries, fail the job on regressions

## Preconditions
- A root folder with one bundle per sub-folder (e.g. `data/input/*`).

## Main flow
1. Operator runs `python tools/harness/run_fixtures.py --root data/input --output dev-reports/runs`
   (today: `bash scripts/run_main_pipeline.sh`).
2. For each bundle the harness invokes the CLI (`--no-time --no-version --json <out>/summary.json`)
   and records exit code, duration, error/warning counts.
3. The harness prints a table and writes `dev-reports/runs/index.json`.
4. In CI, `make test-e2e` compares each bundle's normalised report with
   `tests/e2e/golden/<bundle>.json`; any difference fails the job with a readable diff.

## Alternative flows
- 2a. One bundle crashes (exit 2) → the harness continues with the others and reports the crash;
  the job fails.
- 4a. A difference is an intended improvement → maintainer runs `make harness-update`, reviews
  the diff, writes the reason in `tests/e2e/golden/CHANGELOG.md`, commits.

## Postconditions
- Reports for all bundles under the output root; CI status reflects regressions.

## Related
- `../quality/testing-strategy.md` (golden harness), `../infrastructure/ci-cd.md`
- Backlog: TST-002, TOOL-009, PERF-007 (parallel bundles)

Last synced with code: 3dcfdb1
