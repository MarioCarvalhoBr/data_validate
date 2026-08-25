# CLI contract

Entry point: `canoa-data-validate` (`[tool.poetry.scripts]`) → `data_validate.main:main`, also
`python -m data_validate.main`.

## Current contract (v0.7.65) — must keep working until the deprecation dates below

Defined in `helpers/base/data_args.py::DataArgs._create_parser` with `allow_abbrev=True`.

| Flag | Type / default | Notes |
|---|---|---|
| `--input_folder PATH` | required | Must be an existing directory (`DataFile._validate_arguments`) |
| `--output_folder PATH` | default `output_data/` | Basename must not contain `.` (BUG-009); created if missing |
| `--locale`, `-l` | `pt_BR` \| `en_US`, default `pt_BR` | Persisted to `.config/store.locale` by `Bootstrap` (BUG-004) |
| `--no-spellchecker` | flag | Skips `SpellCheckerValidator`; listed as skipped in the report |
| `--no-warning-titles-length` | flag | Skips `TITLES_N`; listed as skipped |
| `--no-time` | flag | Hides date/time in report and the "Tempo total de execução" stdout line |
| `--no-version` | flag | Hides validator version/OS line in report |
| `--debug` | flag | Enables logger, keeps log file, prints per-category dump |
| `--sector TEXT` | optional | Shown in report header |
| `--protocol TEXT` | optional | Shown in report header |
| `--user TEXT` | optional | Shown in report header |
| `--file TEXT` | optional | Shown in report header ("Arquivo submetido") |

Abbreviations in use by scripts and docs (`--i`, `--o`, `--l`, `--d`) work **only** because of
argparse prefix matching; they are not declared aliases.

Outputs:
- `<output_folder>/<input-folder-name>_report.html` and `.pdf` (PDF silently skipped with a
  stderr message if `wkhtmltopdf` is missing).
- stdout: welcome banner (printed at import), `HTML report created at: …`, `PDF report created
  at: …`, then a line `<{"data_validate": {"version": "0.7.65b732", "report": {"errors": E,
  "warnings": W, "tests": 35}}}>` (built with `str(dict).replace("'", '"')` — BUG-010), then
  `Tempo total de execução: N segundos` unless `--no-time`.
- Exit code: always `0` (SEC-008).

## Target contract

| Flag | Alias | Type / default | Semantics |
|---|---|---|---|
| `--input PATH` | `-i`, `--input_folder` (deprecated) | required | Bundle folder |
| `--output PATH` | `-o`, `--output_folder` (deprecated) | default `./output` | Created with parents; may contain dots |
| `--locale {pt_BR,en_US}` | `-l` | default `pt_BR` | Used for messages, report and spell dictionary; **not persisted** |
| `--format LIST` | | default `html` | Comma list of `html,pdf,json,console`; `pdf` requires extra `[pdf]` |
| `--json PATH` | | optional | Write the JSON summary/report to a file (`-` = stdout) |
| `--fail-on {error,warning,never}` | | default `error` | Governs exit code 1 |
| `--rules LIST` / `--skip-rules LIST` | | optional | Run/skip specific rule IDs or categories |
| `--no-spellchecker` | | flag | Kept; equivalent to `--skip-rules SPELL-*` |
| `--no-warning-titles-length` | | flag | Kept; equivalent to `--skip-rules DESC-010` |
| `--no-time`, `--no-version` | | flags | Kept (report header) |
| `--sector`, `--protocol`, `--user`, `--file` | | optional | Kept (report header, HTML-escaped) |
| `--max-file-size BYTES`, `--max-rows N` | | defaults from `specs/limits.py` | Input limits (SEC-003) |
| `--parallel` | | flag | Run independent rule groups concurrently |
| `--verbose` / `-v`, `--quiet` / `-q` | | flags | Console verbosity; default prints only the summary |
| `--debug` | | flag | Keep log file, log at DEBUG |
| `--list-rules` | | action | Print rule IDs, categories, severities and exit 0 |
| `--version` | | action | `canoa-data-validate 0.8.0 (protocol 1.13)` |

### Exit codes

| Code | Meaning |
|---|---|
| 0 | Validation ran; no issue at or above `--fail-on` severity |
| 1 | Validation ran; issues at or above `--fail-on` severity |
| 2 | The tool itself failed (bad arguments, unreadable folder, rule crash, renderer failure) |

### stdout / stderr

- stdout carries **only** machine output: the one-line JSON summary (always, for platform
  compatibility) plus whatever `--json -` or `--format console` requests.
- Progress, warnings about optional features (no PDF backend, no spell dictionary) and errors go
  to stderr via logging.
- No banner at import time.

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

The full report JSON (with categories and issues) is described in `../architecture/error-model.md`.

### Deprecation policy

| Deprecated | Replacement | Warning from | Removed in |
|---|---|---|---|
| `--input_folder`, `--output_folder` | `--input/-i`, `--output/-o` | 0.8.0 (stderr warning) | 1.0.0 |
| Prefix abbreviations `--i`, `--o`, `--l`, `--d` | explicit aliases | 0.8.0 (`allow_abbrev=False`; `--i/--o/--l` kept as hidden aliases) | 1.0.0 |
| `.config/store.locale` persistence | `--locale` per run | 0.8.0 (file ignored) | 0.8.0 |
| Banner and "Tempo total" on stdout | `--verbose` on stderr | 0.8.0 | 0.8.0 |
| PDF generated by default | `--format html,pdf` | 0.9.0 | 1.0.0 |

Every deprecation is listed in `../future/deprecations.md` and in the CHANGELOG.

Last synced with code: 3dcfdb1
