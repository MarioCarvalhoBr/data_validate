---
name: report-rendering
description: Use when touching the HTML/PDF report renderer or any Jinja2 template that renders spreadsheet-derived (untrusted) content. Covers autoescape, markupsafe.escape, Markup usage, and an XSS regression test sketch — closes SEC-001.
---

# Rendering untrusted spreadsheet content safely

Every string in a validation message can contain attacker-controlled content: a cell value from
`descricao.nome_simples`, a filename, a column name — all copied verbatim into report messages.
The renderer must never let that content execute as HTML/JS in the reader's browser.

## Current state (the bug — SEC-001, P0)

`data_validate/controllers/report/file_report_generator.py` builds its Jinja environment without
autoescape:

```python
# Current — vulnerable: no autoescape, so `{{ message }}` renders any HTML/script in a cell value.
self.env = Environment(loader=FileSystemLoader(self.output_folder))
```

If a spreadsheet's `nome_simples` contains `<script>...</script>`, `validate_html_in_descriptions`
(DESC/`HTML_DESC`) rejects it as a *warning*, but the warning message itself — which repeats the
offending cell value — gets rendered right back into the report unescaped, and a report with only
warnings (not errors) is not blocked from generation.

## The fix

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

self.env = Environment(
    loader=FileSystemLoader(self.output_folder),
    autoescape=select_autoescape(enabled_extensions=("html", "htm", "xml"), default_for_string=True),
)
```

`select_autoescape` turns on escaping for `.html`/`.htm`/`.xml` templates (and for string
templates when `default_for_string=True`) while leaving non-HTML output (plain-text/JSON
renderers) unaffected — those must never carry HTML in the first place, so autoescape doesn't
apply to them at all.

## `markupsafe.escape` for anything built outside a template

Any HTML string assembled in Python (not through `{{ }}` in a `.html` template) — e.g. a
pre-formatted summary string later interpolated into a template as `{{ summary|safe }}` — must be
escaped explicitly before that point:

```python
from markupsafe import escape

safe_cell_value = escape(raw_cell_value)  # escapes <, >, &, ', " — safe to interpolate anywhere
```

Never call `escape()` twice on the same value (double-escaping corrupts legitimate `&amp;` etc.);
escape once, as close to the untrusted source as possible, and let autoescape handle the rest.

## `Markup` — only for HTML the template itself owns

`markupsafe.Markup` marks a string as "already safe, do not escape again." Use it **only** for
HTML fragments the codebase generates and fully controls (e.g. a `<br>` built from a known,
non-user-controlled template snippet) — never wrap raw spreadsheet-derived content in `Markup`,
since that is exactly what disables the protection:

```python
# OK: fragment is a fixed template-owned string, not spreadsheet content.
from markupsafe import Markup
separator = Markup("<hr class=\"section\">")

# NEVER: wrapping untrusted content bypasses autoescape entirely.
# Markup(f"<td>{cell_value}</td>")   # do not do this
```

If a report field must legitimately contain limited formatting (none currently do), sanitize with
an allow-list HTML sanitizer before `Markup`-wrapping it — do not hand-roll tag stripping.

## XSS regression test sketch

```python
"""Regression test for SEC-001: report HTML must escape spreadsheet-derived content."""

import pytest


class TestReportRenderingEscapesUntrustedContent:
    def test_html_report_escapes_script_tag_in_indicator_name(self, tmp_path, mocker) -> None:
        """A <script> tag in a cell value must render as text, never execute."""
        malicious_name = "<script>alert('xss')</script>"
        # Build a minimal report context carrying the malicious value through the normal
        # message-formatting path (not injected directly into the template context) so the
        # test exercises the real pipeline, not just the renderer in isolation.
        report_html = render_report_for_test(
            errors=[f"descricao.csv, linha 2: '{malicious_name}' não pode conter código HTML."]
        )

        assert "<script>" not in report_html
        assert "&lt;script&gt;" in report_html

    def test_html_report_does_not_double_escape_legitimate_ampersand(self, tmp_path) -> None:
        """Escaping must run exactly once — '&' must become '&amp;', not '&amp;amp;'."""
        report_html = render_report_for_test(errors=["fontes: Instituto A & Instituto B."])

        assert "&amp;amp;" not in report_html
        assert "Instituto A &amp; Instituto B" in report_html
```

Add this test under `tests/unit/controllers/report/test_file_report_generator.py` once the
autoescape fix lands (SEC-001), and again as a `tests/e2e` golden case so a future regression is
caught at the pipeline level, not just the unit level.

## PDF rendering

`pdfkit`/`wkhtmltopdf` renders the already-escaped HTML — it inherits the same protection as long
as the HTML step above is correct. Do not re-introduce raw string concatenation when building the
PDF-specific template variant; reuse the same escaped Jinja render path.
