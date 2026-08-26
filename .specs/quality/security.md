# Security

## Threat model

| Asset | Threat | Vector | Impact |
|---|---|---|---|
| Analyst's browser / INPE workstation | Stored XSS | Cell content rendered unescaped in the HTML report (SEC-001) | Session/credential theft, pivot into intranet |
| Validator host | Resource exhaustion | Oversized/zip-bomb `.xlsx`, huge CSV (SEC-003) | DoS of the ingestion server |
| Validator host | Arbitrary file read / SSRF | wkhtmltopdf rendering attacker-controlled HTML (SEC-002) | Data exfiltration |
| Platform decisions | Wrong acceptance | Crashes swallowed, exit code 0 (SEC-004, SEC-008) | Invalid data ingested |
| Supply chain | Malicious/vulnerable dependency, CI tampering | Unpinned actions, lock ignored, no audit (SEC-005) | Compromised releases |
| Repository | Secret / data leak | Hooks staging the whole tree (SEC-006), reports committed (SEC-009) | Exposure of sector data |
| Package dir | Race / corruption | Personal dictionaries written into the package (SEC-007) | Wrong spell results, permission errors |

Trust boundaries: **input bundle is untrusted**; CLI arguments come from the platform (semi-
trusted, still escaped); the package's own `static/` files are trusted.

## Controls

| Control | Where | Status |
|---|---|---|
| Jinja2 `autoescape=True`, template from `PackageLoader`, no HTML built in Python | `reporting/html.py` | target (Phase 4) |
| `markupsafe.escape` for CLI metadata in report header | idem | target |
| Input limits: `max_file_size`, `max_rows`, `max_columns`; reject early with `STRUCT-*` issue | `loading/` | target (Phase 2) |
| PDF optional, WeasyPrint (no browser engine), never with attacker-controlled network access | `reporting/pdf.py` | target (Phase 4) |
| Specific exceptions only; unexpected → exit 2 | everywhere | target (Phase 1) |
| Exit codes 0/1/2; stdout reserved for machine output | `cli.py` | target (Phase 1) |
| No writes outside the output folder; no `os.environ` mutation; temp dirs via `tempfile` | `spell/`, `app/` | target (Phase 5) |
| `bandit -c pyproject.toml -r data_validate tools`, clean | Makefile `security`/`security-offline`, CI `security` job | done |
| `pip-audit --strict`, clean except `pdfkit` (PYSEC-2026-2860/GHSA-9g3x-6x24-vf9f, no fix upstream, tracked SEC-002) | Makefile `security`, CI `security` job | done |
| CodeQL (Python), on push/PR to `main` and weekly schedule | `.github/workflows/codeql.yml` | done |
| Dependabot (pip + actions) | `.github/dependabot.yml` | done |
| Actions pinned by full commit SHA with a version comment | `.github/workflows/*.yml` | done |
| `actions/checkout` with `persist-credentials: false` (a compromised job step can't reuse the checkout's token to push) | every `actions/checkout` step in `ci.yml`/`release.yml`/`docs.yml`/`codeql.yml` | done |
| `poetry.lock` respected (`poetry install --sync`); no `rm poetry.lock` | Makefile, CI | Phase 0 |
| Pre-commit: standard hooks only, never `git add` | `.pre-commit-config.yaml` | Phase 0 |
| Generated reports and docs not committed | `.gitignore`, CI artefacts | Phase 0/5 |
| `defusedxml` if any XML/QML parsing is introduced | `loading/` | policy |
| No `eval`, `exec`, `pickle`, `yaml.load` without `SafeLoader` | code review | policy |
| Bash-tool guard: fail-closed command analysis (blocks `git push`/history rewrites/broad `rm -r`/etc., recurses into `bash -c`/`eval`/`$(...)`/`xargs`) — defence in depth, not a substitute for the controls above (see `.claude/rules/security.md`) | `.claude/hooks/guard-bash.sh`, `.claude/settings.json` | done |

## Review checklist (used by `security-auditor` and `/review`)

1. Does any string from a spreadsheet, filename or CLI argument reach HTML, a shell, a path or
   a format string without escaping/validation?
2. Is every `except` clause specific, and does an unexpected exception change the exit code?
3. Are new inputs bounded (size, rows, columns, recursion depth in graphs)?
4. Does the change write anywhere other than the output folder or a `tempfile` location?
5. Does it add a dependency? Is it maintained, pinned, audited, needed?
6. Are secrets, personal data or generated reports kept out of git?
7. Is there a regression test for the vulnerability class being touched (e.g. XSS golden)?

## Reporting a vulnerability

See `SECURITY.md` at the repository root (private report to the maintainers listed in
`pyproject.toml`; acknowledgement within 5 working days).

Last synced with code: 09279f4
