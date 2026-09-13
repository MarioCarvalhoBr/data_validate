# Report formats

## HTML (current, Phase 4 — SEC-001/ARC-016/ADR-0007 shipped)

Template: `data_validate/static/report/report_template.html` (inline CSS "Microstrap"), loaded
from the package via `Environment(loader=PackageLoader("data_validate", "static/report"),
autoescape=select_autoescape(["html"]))` — never from the output folder. The hand-rolled
"does the template contain every required `{{ var }}`" regex validator and its fallback
constant (`ApplicationConfig.REPORT_TEMPLATE_DEFAULT_BASIC_NO_CSS`) are both deleted; a
missing/broken template now raises `jinja2.TemplateNotFound`/`TemplateError`, caught by
`build_report`'s existing `except (OSError, TemplateError)` (SEC-004).

`ReportModel`/`ReportSection` (`data_validate/controllers/report/report_model.py`, frozen
dataclasses, ARC-016) replace the old `_build_template_variables` dict — every field is a plain
Python value, never pre-built HTML:

| `ReportModel` field | Source | Content |
|---|---|---|
| `name` | `METADATA.__project_name__` | "Canoa" |
| `user` / `sector` / `protocol` / `file` | `--user/--sector/--protocol/--file` | raw string or `None` |
| `show_date` / `date_now` | `not --no-time` / `ApplicationConfig.DATE_NOW` | bool / "dd/mm/yyyy HH:MM:SS" |
| `show_version` / `version` / `os_name` / `protocol_version` | `not --no-version` / `METADATA.__version__` / `platform.system()` / `METADATA.__protocol_version__` | bool / plain strings |
| `error_count`, `warning_count` | totals before truncation, Brazilian number format | e.g. `"1.234"` |
| `total_tests` | `len(report_list)` | always 34 today |
| `skipped_tests` | tuple of localized titles | from `--no-spellchecker`, `--no-warning-titles-length`, any `was_executed=False` report |
| `sections` | one `ReportSection(title, errors, warnings)` per report, in iteration order | raw, untrusted message text |

`report_template.html` renders these with `{{ }}`/`{% for %}` itself — `{% for section in
report.sections %}<span class="text-primary">{{ section.title }}</span>{% for message in
section.errors %}<span class="text-danger-errors" preserve-spaces>{{ message }}</span>{% endfor
%}{% endfor %}` (and the equivalent loop over `section.warnings` in the "Avisos" card) — instead
of the deleted `_format_messages_as_html` building that same markup as a Python string.
`--user`/`--sector`/`--protocol`/`--file`/`date_now`/version line are each an `{% if %}`-guarded
`{{ report.<field> }}` in the info card. Every one of these is escaped by `autoescape=True`;
report **labels** ("Usuário", "Setor estratégico", "Data e hora do processo", …) stay hardcoded
pt-BR HTML *inside the template itself* (not moved to catalog keys this phase — see ADR-0007's
"Implementation note" for the reasoning; tracked under ARC-005/DOC-003).

Sections in the rendered page (top to bottom): header card (name, metadata lines), summary card
(errors, warnings, tests executed, skipped list), errors card, warnings card — layout unchanged
from before Phase 4.

Security: `autoescape=True` (SEC-001) — a message or CLI value containing `<script>` renders as
`&lt;script&gt;`, never a raw tag; see `tests/unit/controllers/report/
test_file_report_generator.py::TestXssEscaping`.

## PDF (current, Phase 4 — SEC-002 shipped)

`FileReportGenerator._save_pdf_file` tries WeasyPrint first (`weasyprint.HTML(filename=...)
.write_pdf(...)`, pure Python + pango, the `[pdf]` Poetry extra); falls back to
`pdfkit.from_file(html, pdf, options)` (Letter page, zero margins, UTF-8) only as a compatibility
path for hosts that already have `wkhtmltopdf` installed (neither is a declared dependency any
more); if neither backend is usable, PDF generation is skipped with a stderr message
(`"PDF generation skipped: install canoa-data-validate[pdf] for PDF output."`) and the run
continues — HTML remains the primary, always-produced artefact, exit code unaffected. A genuine
conversion failure (not an availability problem) from either backend is still logged to stderr.

## stdout JSON (current)

`<{"data_validate": {"version": "…", "report": {"errors": E, "warnings": W, "tests": T}}}>`
(unchanged by Phase 4).

## Target

| Format | Renderer | Notes |
|---|---|---|
| HTML | `reporting/html.py` (Jinja2, `autoescape=True`, `PackageLoader`) | Phase 4 delivered the autoescape/`PackageLoader`/`ReportModel` core in `controllers/report/`, not yet in a dedicated `reporting/` package; localised labels via catalog keys `report.label.*` remain a follow-up (ARC-005/DOC-003) |
| PDF | `reporting/pdf.py` (WeasyPrint, extra `[pdf]`) | Phase 4 delivered the WeasyPrint-primary/`pdfkit`-fallback/graceful-skip behaviour in `controllers/report/file_report_generator.py`; moving it into a dedicated `reporting/pdf.py` module is a later layering step |
| JSON | `reporting/json.py` | Schema in `cli-contract.md` + full categories/issues from `../architecture/error-model.md`; `ensure_ascii=False`, UTF-8 file |
| Console | `reporting/console.py` | Human summary on stderr (`--verbose`): counts per category, first N issues |

Compatibility promises during Phases 1–3: HTML byte-identical for the golden fixtures (with
`--no-time --no-version`); stdout JSON line unchanged. Phase 4 re-baselined goldens once: 7/8
fixtures stayed byte-identical, one (`data_errors_01`) gained a single reviewed line change
because escaping now *preserves* content a previous, non-escaping render had let the golden
harness's naive HTML extractor mangle (see `tests/e2e/golden/CHANGELOG.md`'s 2026-09-13 entry);
one new fixture (`data_errors_xss`) was added additively.

Last synced with code: 09279f4
