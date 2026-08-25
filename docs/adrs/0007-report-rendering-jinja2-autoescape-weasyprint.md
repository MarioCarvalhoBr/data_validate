# ADR-0007: Report rendering with Jinja2 autoescape; PDF optional via WeasyPrint (drop wkhtmltopdf)

- Status: Proposed
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

`FileReportGenerator.__init__` (`controllers/report/file_report_generator.py:47-71`) builds
`self.env = Environment(loader=FileSystemLoader(self.output_folder))` at line 68 with **no
`autoescape`** argument, and the loader points at the *output* directory rather than a fixed
package template directory — a pre-existing file named like the template in that output folder
could itself be loaded as a Jinja template. HTML content is not built by the template engine at
all: `_format_messages_as_html` (lines 265-291, a `@staticmethod`) manually concatenates strings —
`html_parts.append(f"<br><span class='{css_class}' preserve-spaces>{message}</span>")` at line
288 — where `message` is untrusted content taken directly from validation findings, which
themselves quote raw spreadsheet cell values (`nome_simples`, labels, column names). Without
autoescape and without going through the template's `{% for %}` loop, a cell containing
`<img src=x onerror=...>` or `<script>alert(1)</script>` is emitted verbatim into the saved HTML
report and executes when an INPE staff member opens it in a browser (SEC-001). The same pattern
repeats in `_build_template_variables` (lines 173-217): `date_display_html` interpolates
`self.context.config.DATE_NOW` unescaped (line 193), `text_html_version_and_os_info` interpolates
`METADATA.__version__` and `platform.system()` unescaped (line 198), and
`_get_optional_field_text` (lines 219-237) interpolates the CLI's own `--sector`/`--protocol`/
`--user`/`--file` values unescaped (line 237) — so operator-supplied CLI metadata is exposed to the
same injection risk as untrusted spreadsheet content. PDF generation depends on `pdfkit`
(`_save_pdf_file`, lines 342-368, `pdfkit.from_file(html_file_path, pdf_file_path,
options=pdf_options)` at line 358), a wrapper around the native `wkhtmltopdf` binary, archived by
its upstream maintainers since 2023 and built on an unpatched, obsolete QtWebKit engine (SEC-002)
— any HTML injected via SEC-001 is rendered by that same unmaintained engine when producing the
PDF, compounding the risk (potential local-file read/SSRF inside the renderer). `_validate_html_template`
(lines 82-102) validates the template with a hand-rolled regex (`r"\{\{\s*.*?\s*\}\}"`, line 91)
against a fallback template stored as a Python string constant in
`config/application_config.py:62-96` (ARC-016), rather than letting Jinja itself report a missing
variable.

## Decision

Rebuild report rendering per `.specs/architecture/target-architecture.md`'s `reporting/` layer.
`Environment` is constructed with `autoescape=select_autoescape(["html"])` and a
`PackageLoader("data_validate", "static/report")` — templates are loaded only from a fixed location
shipped with the package, never from the user-writable output directory. Message lists render
through the template itself (`{% for issue in errors %}<span class="...">{{ issue.message
}}</span>{% endfor %}`, consuming `ValidationResult`/`Issue` objects from ADR-0004) instead of being
built as HTML strings in Python; `_format_messages_as_html`, `_get_optional_field_text` and the
manual `<strong>...</strong>` string-building are deleted. Anything that must remain
pre-interpolated (e.g. a formatted number) is wrapped with `markupsafe.escape` explicitly, never
assumed safe. A `ReportModel` dataclass replaces the ad hoc `template_vars` dict (ARC-016). PDF
generation becomes optional, gated behind a `--pdf` flag and a `[pdf]` Poetry extra, rendered with
**WeasyPrint** (pure-Python + pango, no native daemon process, actively maintained) directly from
the already-escaped `ReportModel` HTML — `pdfkit`/`wkhtmltopdf` are removed from the default
dependency set entirely (SEC-002, TOOL-008). HTML remains the primary, always-produced artefact.

## Consequences

### Positive
- A cell or CLI argument containing `<script>` renders as literal, inert text
  (`&lt;script&gt;alert(1)&lt;/script&gt;`) instead of executing in the viewer's browser — closes
  SEC-001 for both the spreadsheet-content and CLI-metadata injection points identified above.
- Removing `wkhtmltopdf` drops an archived, unpatched native binary dependency from the install
  matrix (no more Windows-DLL/system-package instructions in the README for PDF support) and
  removes the SSRF/local-file-read surface SEC-002 flags inside that renderer.
- PDF becomes truly optional (`[pdf]` extra) rather than a hard system dependency, aligning with
  TOOL-008's "installed-package experience" goal — a plain `pip install canoa-data-validate` works
  without needing a system PDF toolchain at all.

### Negative
- WeasyPrint's CSS support (no JavaScript, partial modern-CSS coverage) differs from
  wkhtmltopdf/QtWebKit's; the report's CSS (`microstrap`, per the current template) needs a visual
  regression check during Phase 4 to confirm PDF output stays acceptable — tracked as part of the
  Phase 4 gate ("XSS golden test; goldens re-baselined once, reviewed, then stable").
- Moving from Python-built HTML strings to template loops is a rendering-logic rewrite that touches
  every field currently in `_build_template_variables`; mitigated by keeping the golden harness
  (ADR-0002) green throughout Phase 4, re-baselining visual output exactly once with a reviewed
  diff.

## Alternatives considered

### Keep `wkhtmltopdf` but pin its version and sandbox the process
Rejected: pinning does not fix an archived upstream — no future security patches will ever land for
the embedded QtWebKit engine, so "pin and sandbox" caps the risk but never closes it; SEC-002
explicitly calls the binary itself the problem, not a particular version of it.

### Render PDF via headless Chromium (Playwright) in CI/runtime
Rejected: a full browser engine is a much heavier runtime/CI dependency (hundreds of MB, a browser
download step) than WeasyPrint for what is a text-and-table-heavy report with no need for
JavaScript execution or complex modern layout; WeasyPrint is purpose-built for exactly this
document-rendering use case with a much smaller footprint.

### Keep building HTML in Python but manually `html.escape()` every interpolated field
Rejected: SEC-001 is itself evidence this approach fails in practice — the current code already
had ad hoc opportunities to escape and didn't, in `_format_messages_as_html`,
`_get_optional_field_text`, and the two `f"<strong>..."` blocks in `_build_template_variables`.
Manual escaping requires remembering to do it at every single interpolation site forever; Jinja's
`autoescape=True` makes forgetting structurally impossible instead of relying on developer
vigilance at each of dozens of call sites.

## Links

- Backlog: `SEC-001`, `SEC-002` (`02-security.md`); `ARC-016` (`03-architecture.md`);
  `08-migration-roadmap.md` Phase 4 item 1
- Specs: `.specs/architecture/target-architecture.md` (`Renderer` protocol, `reporting/` layer),
  `.specs/frontend/report-ui.md`
- Related ADRs: ADR-0004 (`Issue`/`ValidationResult` feed the renderer), ADR-0005 (`--format`,
  `--pdf` flags)

---
Last synced with code: a4f76c7
