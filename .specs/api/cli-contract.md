# CLI contract

Entry point: `canoa-data-validate` (`[tool.poetry.scripts]`) → `data_validate.main:main`, also
`python -m data_validate.main`.

## Current contract — implemented (ARC-011/SEC-008/ARC-012, this change)

Defined in `helpers/base/data_args.py::DataArgs._create_parser` with `allow_abbrev=False`.

| Flag | Alias | Deprecated alias | Type / default | Notes |
|---|---|---|---|---|
| `--input_folder PATH` | `-i`, `--input` | `--i` | required | Must be an existing directory (`DataFile._validate_arguments`); required across all three spellings, enforced with `parser.error()` (not `required=True`, since that cannot span aliases); resolved to an absolute, normalized path via `Path.resolve()` (SEC-010) |
| `--output_folder PATH` | `-o`, `--output` | `--o` | default `output_data/` | Any path is accepted, including a basename containing `.` (e.g. `run.2026-08`, `v1.2`); rejected only when the path already exists as a regular file (BUG-009); created if missing; resolved to an absolute, normalized path via `Path.resolve()` (SEC-010); the report file is then written with `pathlib`, guarded to stay inside the resolved output directory (`FileReportGenerator._resolve_report_path`) |
| `--locale`, `-l` | | `--l` | `pt_BR` \| `en_US`, default `pt_BR` | Explicit constructor argument threaded through `GeneralContext` into one shared `LanguageManager`; no persistence (BUG-004, fixed) |
| `--no-spellchecker` | | | flag | Skips `SpellCheckerValidator`; listed as skipped in the report |
| `--no-warning-titles-length` | | | flag | Skips `TITLES_N`; listed as skipped |
| `--no-time` | | | flag | Hides date/time in report and the "Tempo total de execução" stdout line |
| `--no-version` | | | flag | Hides validator version/OS line in report |
| `--debug` | | `--d` | flag | Enables logger, keeps log file, prints per-category dump |
| `--sector TEXT` | | | optional | Shown in report header |
| `--protocol TEXT` | | | optional | Shown in report header |
| `--user TEXT` | | | optional | Shown in report header |
| `--file TEXT` | | | optional | Shown in report header ("Arquivo submetido") |
| `--json PATH` | | | optional, default `None` | After the run, writes the same summary object as the stdout `<{...}>` fragment to `PATH` as pretty JSON (UTF-8) |
| `--fail-on {error,warning,never}` | | | default `error` | Governs the exit code (see below); `never` restores the historical always-0 behaviour |
| `--version` | | | action | Prints `<prog> <METADATA.__version__>` and exits 0; no file I/O, works offline (TOOL-008) |

The deprecated two-dash aliases (`--i`, `--o`, `--l`, `--d`) only ever worked through
`allow_abbrev=True` prefix matching; they are now declared explicitly (so they keep working under
`allow_abbrev=False`) and print one deprecation warning line to stderr naming the replacement each
time they are used (`_make_deprecated_alias_action` in `data_args.py`). Any *other* previously
working abbreviation (e.g. `--input_fol`) is now rejected (`SystemExit(2)`, "unrecognized
arguments") — this is the one user-visible tightening of the CLI's surface in this change.

Outputs:
- `<output_folder>/<input-folder-name>_report.html` and `.pdf` (PDF silently skipped with a
  stderr message if `wkhtmltopdf` is missing).
- stderr: welcome banner, printed once from inside `main()` (ARC-012) — no longer printed at
  `import data_validate` time, and no longer mixed onto stdout.
- stdout: `HTML report created at: …`, `PDF report created at: …`, then a line
  `<{"data_validate": {"version": "0.7.65b732", "report": {"errors": E, "warnings": W, "tests":
  35}}}>` (built with `json.dumps(summary, ensure_ascii=False)`, so it stays valid JSON even when a
  value contains a quote or non-ASCII character — BUG-010, fixed), then `Tempo total de execução: N
  segundos` unless `--no-time`.
- Exit code: see below (SEC-008, fixed — no longer always `0`).

### Exit codes (SEC-008 — implemented)

| Code | Meaning |
|---|---|
| 0 | Validation ran; no issue at or above `--fail-on` severity (or `--fail-on never`) |
| 1 | Validation ran; issues at or above `--fail-on` severity |
| 2 | The tool itself failed: bad/missing arguments (`argparse` `SystemExit(2)`, e.g. a missing
    `--input_folder`), or an unexpected exception anywhere in `DataArgs`/`GeneralContext`/
    `SpreadsheetProcessor` construction — `main()` wraps that single span in one broad
    `except Exception`, prints `Fatal error: <exc>` to stderr, and returns 2. `SpreadsheetProcessor`
    construction calls `FileReportGenerator.build_report` (SEC-004): a failure there is now caught
    (printed to stderr, not raised) only when it is an `OSError` (writing the HTML/PDF to disk) or
    a `jinja2.TemplateError` (rendering the report template) — every other exception (e.g. a
    programming error in a validator) propagates out of `build_report`, out of
    `SpreadsheetProcessor.__init__`, into `main()`'s own broad catch, which reports it as
    `Fatal error: <exc>` and returns 2, same as any other unexpected construction failure. |

Totals are read from `SpreadsheetProcessor.validation_reports.get_total_errors()`/
`get_total_warnings()`; the `tests` count is `len(validation_reports)`.

## Target contract — still pending

The following pieces of `docs/adrs/0005-cli-contract-flags-exit-codes-json.md`'s target contract
remain open (tracked under ARC-011/ARC-012, follow-on phases):

| Flag | Semantics |
|---|---|
| `--format LIST` | Comma list of `html,pdf,json,console`; default `html`; `pdf` requires extra `[pdf]` |
| `--rules LIST` / `--skip-rules LIST` | Run/skip specific rule IDs or categories |
| `--max-file-size BYTES`, `--max-rows N` | Input limits (SEC-003) |
| `--parallel` | Run independent rule groups concurrently |
| `--verbose` / `-v`, `--quiet` / `-q` | Console verbosity; today's stderr progress/log lines are
  unconditional, not gated by a verbosity flag |
| `--list-rules` | Print rule IDs, categories, severities and exit 0 |
| Full stdout quieting | stdout carries the JSON summary today, which already matches the target;
  the remaining gap is that `FileReportGenerator` also prints `HTML report created at: …`/`PDF
  report created at: …` to stdout unconditionally (ARC-012, not moved to logging/stderr in this
  change — see `.specs/quality/backlog/03-architecture.md#ARC-012`) |
| `--input_folder`/`--output_folder` deprecation | Kept as first-class, non-deprecated flags in
  this change (brief decision, see `08-migration-roadmap.md` Phase 1 notes) rather than deprecated
  aliases of `--input`/`--output`; deprecating them is left to a later phase if the platform's
  integration is confirmed migrated to `--input`/`--output` first |

### JSON summary schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/AdaptaBrasil/data_validate/schemas/summary.json",
  "type": "object",
  "required": ["data_validate"],
  "properties": {
    "data_validate": {
      "type": "object",
      "required": ["version", "report"],
      "properties": {
        "version": { "type": "string" },
        "protocol": { "type": "string" },
        "locale": { "type": "string", "enum": ["pt_BR", "en_US"] },
        "exit_code": { "type": "integer", "enum": [0, 1, 2] },
        "report": {
          "type": "object",
          "required": ["errors", "warnings", "tests"],
          "properties": {
            "errors": { "type": "integer", "minimum": 0 },
            "warnings": { "type": "integer", "minimum": 0 },
            "tests": { "type": "integer", "minimum": 0 },
            "skipped": { "type": "integer", "minimum": 0 }
          }
        },
        "outputs": {
          "type": "object",
          "properties": { "html": { "type": "string" }, "pdf": { "type": "string" }, "json": { "type": "string" } }
        }
      }
    }
  }
}
```

Implemented today: `data_validate.version` and `data_validate.report.{errors,warnings,tests}`
(both on stdout and in the `--json PATH` file, which write the identical object). `protocol`,
`locale`, `exit_code`, `skipped`, and `outputs` are not yet populated — still pending.

The full report JSON (with categories and issues) is described in `../architecture/error-model.md`.

### Deprecation policy

| Deprecated | Replacement | Warning from | Status |
|---|---|---|---|
| Two-dash abbreviations `--i`, `--o`, `--l`, `--d` | `-i/--input`, `-o/--output`, `-l/--locale`, `--debug` | Implemented, this change | Warns on stderr every use; removal date not yet set |
| Undeclared prefix abbreviations (e.g. `--input_fol`) | The full flag name | Implemented, this change | Rejected outright (`allow_abbrev=False`), no warning — there was no stable name to warn about |
| `--input_folder`, `--output_folder` | `--input/-i`, `--output/-o` | Not started | Kept as first-class flags in this change (see "Target contract" above) |
| `.config/store.locale` persistence | `--locale` per run | Implemented (BUG-004) | File is no longer read or written anywhere in the package |
| Banner on stdout | Banner on stderr, from `main()` | Implemented, this change (ARC-012) | No longer printed at `import data_validate` time either |
| PDF generated by default | `--format html,pdf` | Not started | `--format` itself is not implemented yet |

Every deprecation is listed in `../future/deprecations.md` and in `CHANGELOG.md`.

Last synced with code: 344fef7 (ARC-011/SEC-008/PERF-004/ARC-012 slice, uncommitted at spec-sync time).
