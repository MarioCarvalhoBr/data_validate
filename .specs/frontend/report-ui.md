# Report UI (HTML / PDF)

The only user interface is the generated report. It must be readable in a browser, printable
to PDF, self-contained (no external assets) and identical across runs for the same input.

## Layout (current template `static/report/report_template.html`)

```
┌─ container ───────────────────────────────────────────────┐
│ card: header                                              │
│   h1 "Canoa — Relatório de Validação de Dados"            │
│   Usuário / Setor estratégico / Protocolo / Data e hora / │
│   Versão do validador – SO / Arquivo submetido            │
│ card: summary                                             │
│   Número de erros · Número de avisos · Testes executados  │
│   Testes não executados (ul, hidden when empty)           │
│ card: errors    (per category: title span + message spans)│
│ card: warnings  (same)                                    │
└───────────────────────────────────────────────────────────┘
```

CSS: inline "Microstrap" (Bootstrap-like minimal framework by Mário Carvalho) with the palette
`.text-primary` (category title), `.text-danger-errors`, `.text-orange-warning`, `.text-gray`;
`preserve-spaces` attribute keeps message whitespace. Page background `#EEEDEA`.

Rendering (migration Phase 4, ADR-0007): the template is loaded from the package's own
`static/report/` directory via `Environment(loader=PackageLoader("data_validate",
"static/report"), autoescape=select_autoescape(["html"]))` — never the user-writable output
folder — and loops over `ReportModel.sections`/`ReportModel.skipped_tests` itself (`{% for %}`);
`FileReportGenerator` no longer builds any HTML string in Python (`_format_messages_as_html`,
`_get_optional_field_text`, the two `f"<strong>..."` blocks in the old
`_build_template_variables` are all deleted). Every value — spreadsheet-derived message text,
`--sector`/`--protocol`/`--user`/`--file` — is escaped by `autoescape=True`; the only markup that
renders unescaped is the markup the template itself authors (the `&ndash;`/`&eacute;`/etc.
entities and the card layout in `report_template.html`).

## Requirements

| # | Requirement | Status |
|---|---|---|
| UI-1 | Self-contained HTML (inline CSS, no JS, no remote fonts) | met |
| UI-2 | Every message shows sheet, row and column when known, in a fixed order | partially (text-embedded); target: rendered from `Issue` fields |
| UI-3 | Category order equals protocol order; empty categories still listed | met |
| UI-4 | Truncation notice after 20 messages per list | met |
| UI-5 | Skipped rules listed with reason | partially (only two flags) → target |
| UI-6 | All labels localised (pt_BR/en_US) via catalog keys `report.label.*` | not met (hard-coded pt-BR) — deliberately deferred past Phase 4 (ADR-0007's "Implementation note"), tracked under ARC-005/DOC-003 |
| UI-7 | Untrusted text escaped; no script execution possible | met (Phase 4, SEC-001 — `autoescape=True`, `PackageLoader`, `ReportModel`) |
| UI-8 | Print stylesheet: Letter/A4, page breaks between cards, no zero-margin clipping | partially (wkhtmltopdf zero margins on the legacy compatibility path) → target: `@page` rules |
| UI-9 | Accessibility: semantic headings, `lang` attribute from locale, colour contrast ≥ 4.5:1, severity not conveyed by colour alone (prefix "Erro:"/"Aviso:" or icon) | not met → Phase 4 follow-up |
| UI-10 | Deterministic output with `--no-time --no-version` | met (goldens rely on it) |

## Target template structure

`static/report/report.html.j2` extended by `_header.j2`, `_summary.j2`, `_category.j2`
(loop over `report.categories`, each with `errors`/`warnings` lists of rendered `Issue`s) and
`_skipped.j2`. Variables come from `ReportModel`; filters `t(key, **params)` (catalog) and
`fmt_number(n, locale)` (babel). Autoescape on; only the CSS block is `|safe`.

Current state (Phase 4): one `report_template.html` (not yet split into partials) already reads
`ReportModel` (`controllers/report/report_model.py`) and loops over `sections`/`skipped_tests`
with autoescape on; the partial-file split (`_header.j2`/`_summary.j2`/`_category.j2`/
`_skipped.j2`) and the `t()`/`fmt_number()` filters remain a later step, not blocking on the
security/architecture fix this phase delivered.

## PDF

Same HTML; renderer adds `@media print` rules. Page size Letter (current) — configurable via
`--pdf-page-size` in target. Fonts: system sans-serif; no downloads. Backend: WeasyPrint (the
`[pdf]` extra) primary, `pdfkit`/`wkhtmltopdf` a compatibility fallback for hosts that already
have it installed, PDF generation skipped (not fatal) when neither is usable (SEC-002).

Last synced with code: 09279f4
