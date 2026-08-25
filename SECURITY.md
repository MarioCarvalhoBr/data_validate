# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.7.x (current) | Yes — receives security fixes |
| < 0.7 | No |

There is no long-term-support branch yet; security fixes land on `main` and are released as the
next `0.7.x` patch. This will be revisited once `1.0.0` ships (see
`.specs/quality/backlog/08-migration-roadmap.md`).

## Reporting a vulnerability

Please **do not** open a public GitHub issue for a security report. Instead, use one of:

1. **GitHub private security advisory** — open one at
   <https://github.com/AdaptaBrasil/data_validate/security/advisories/new> (preferred: it lets
   maintainers collaborate on a fix before disclosure).
2. **Email** — mariodearaujocarvalho@gmail.com. Include a description of the issue, steps to
   reproduce (a minimal spreadsheet bundle if the bug is data-triggered), the affected version,
   and your assessment of impact.

### Response targets

- **Acknowledgement**: within 5 working days.
- **Triage / severity assessment**: within 10 working days of acknowledgement.
- **Fix or mitigation**: timeline communicated after triage, based on severity; P0 issues are
  prioritised over feature work.

We credit reporters in the advisory and the `CHANGELOG.md` entry unless anonymity is requested.

## Threat model summary

Full model and control matrix: [`.specs/quality/security.md`](.specs/quality/security.md).

| Asset | Threat | Vector |
|---|---|---|
| Analyst's browser | Stored XSS | Spreadsheet cell content rendered unescaped into the HTML report |
| Validator host | Resource exhaustion | Oversized/malformed `.xlsx`/`.csv` input |
| Validator host | Arbitrary file read / SSRF | `wkhtmltopdf` rendering attacker-controlled HTML |
| Platform ingestion | Wrong acceptance decision | Exceptions swallowed, exit code always `0` today |
| Supply chain | Malicious/vulnerable dependency | Unpinned CI actions, unaudited dependencies |

Trust boundaries: the **input spreadsheet bundle is untrusted**; the **HTML report is opened in
a browser** by an analyst and must not execute attacker-supplied script; the **JSON summary on
stdout is parsed by the AdaptaBrasil platform** and must stay well-formed even on validator
failure.

## Known open items

| ID | Issue | Scheduled |
|---|---|---|
| SEC-001 | Report HTML rendered without Jinja2 autoescape (stored XSS via cell content) | Migration Phase 4 — `ReportModel` + autoescaped templates (ADR-0007) |
| SEC-002 | PDF generation via `wkhtmltopdf` (unmaintained, historically vulnerable to SSRF/file-read) | Migration Phase 4 — replace with WeasyPrint behind an optional `[pdf]` extra (ADR-0007) |
| SEC-003 | No input size/row/column limits before parsing | Migration Phase 2 |
| SEC-007 | Spell-check writes personal dictionaries inside the installed package directory | Migration Phase 5 |
| SEC-008 | Exit code is always `0`, regardless of validation result or crash | Migration Phase 1 — explicit exit codes (ADR-0005) |

The full, prioritised list (with `bandit`/`pip-audit` findings and CVSS-like severity) lives in
[`.specs/quality/backlog/02-security.md`](.specs/quality/backlog/02-security.md). `bandit` and
`pip-audit` run in CI (`make security`) and are expected to stay clean for new code.
