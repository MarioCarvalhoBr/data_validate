# Legacy scripts (retired)

These shell scripts (moved here verbatim from the former `scripts/` directory) predate the
Poetry/Makefile/CI tooling introduced by the migration program (see
`.specs/quality/backlog/06-tooling-ci.md`, items TOOL-002, TOOL-005, TOOL-009). They are **kept
only for reference during the migration** and are retired:

- They are not invoked by the `Makefile`, `.pre-commit-config.yaml`, or any
  `.github/workflows/*.yml` — the new tooling never depends on this directory.
- They assume a specific local layout (`source .venv/bin/activate`), hand-increment a version
  `serial` inside the package, and mutate the working tree (`git add .`) — practices tracked as
  SEC-006 / SEC-005 and superseded by `poetry version`, the release workflow, and `pre-commit`.
- `run_main_pipeline.bat` uses the `--d` flag abbreviation of `--debug`, which the CLI contract is
  moving away from (see `.specs/api/cli-contract.md`).

**They will be deleted in Phase 5 of the migration roadmap**
(`.specs/quality/backlog/08-migration-roadmap.md`), once nothing outside this directory
references them. Do not add new functionality here — use `tools/harness/`, `tools/*.py`, and
`Makefile` targets instead.
