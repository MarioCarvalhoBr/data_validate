# Report formats

## HTML (current)

Template: `data_validate/static/report/report_template.html` (inline CSS "Microstrap"). The
generator (`FileReportGenerator`) validates that the template contains every `{{ var }}` present
in the fallback template `ApplicationConfig.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS`; otherwise the
fallback is used.

Template variables built by `_build_template_variables`:

| Variable | Source | Content |
|---|---|---|
| `name` | `METADATA.__project_name__` | "Canoa" |
| `text_display_user` / `_sector` / `_protocol` / `_file` | `--user/--sector/--protocol/--file` | `<strong>Label: <strong class='text-gray'>value</strong></strong><br>` or empty |
| `text_display_date` | `ApplicationConfig.DATE_NOW` unless `--no-time` | "Data e hora do processo: dd/mm/yyyy HH:MM:SS" |
| `text_display_version_and_os_info` | `METADATA.__version__`, `platform.system()` unless `--no-version` | "Versão do validador: 0.7.65b732 – Linux" |
| `error_count`, `warning_count` | totals before truncation, Brazilian number format | e.g. `1.234` |
| `total_tests` | `len(report_list)` | always 35 today |
| `skipped_tests` | `<ul><li>…</li></ul>` of skipped titles | from `--no-spellchecker`, `--no-warning-titles-length` |
| `display_skipped_tests` | `block` / `none` | CSS display for the skipped section |
| `errors`, `warnings` | `_format_messages_as_html` | per category: `<span class='text-primary'>title</span>` then one `<span class='text-danger-errors' preserve-spaces>msg</span>` (or `text-orange-warning`) per message, joined by `<br>` |

Sections in the rendered page (top to bottom): header card (name, metadata lines), summary card
(errors, warnings, tests executed, skipped list), errors card, warnings card.

Security: no autoescape (SEC-001); messages and CLI metadata are inserted verbatim.

## PDF (current)

`pdfkit.from_file(html, pdf, options)` with Letter page, zero margins, UTF-8; requires the
`wkhtmltopdf` binary. Failure is logged to stderr and the run continues.

## stdout JSON (current)

`<{"data_validate": {"version": "…", "report": {"errors": E, "warnings": W, "tests": T}}}>`

## Target

| Format | Renderer | Notes |
|---|---|---|
| HTML | `reporting/html.py` (Jinja2, `autoescape=True`, `PackageLoader`) | Same visual layout and CSS; messages rendered by the template from `ReportModel`, not pre-built HTML; skipped rules with reasons; localised labels via catalog keys `report.label.*` |
| PDF | `reporting/pdf.py` (WeasyPrint, extra `[pdf]`) | Optional; same HTML input |
| JSON | `reporting/json.py` | Schema in `cli-contract.md` + full categories/issues from `../architecture/error-model.md`; `ensure_ascii=False`, UTF-8 file |
| Console | `reporting/console.py` | Human summary on stderr (`--verbose`): counts per category, first N issues |

Compatibility promises during Phases 1–3: HTML byte-identical for the golden fixtures (with
`--no-time --no-version`); stdout JSON line unchanged. Phase 4 re-baselines goldens once (sorted
issues, escaped HTML) with a reviewed diff.

Last synced with code: 3dcfdb1
