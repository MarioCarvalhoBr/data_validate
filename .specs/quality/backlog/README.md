# Quality Backlog — data_validate (Canoa)

Audit snapshot taken on 2026-08-25 against `main` @ `a4f76c7` (v0.7.65b732), after reading every
`*.py` file under `data_validate/` and `tests/`, the CI workflows, `pyproject.toml`, `Makefile`,
scripts and the legacy `.github/copilot-instructions.md`.

This backlog is the **source of truth for the migration**. Items are picked one at a time
(`/backlog next` or by ID), implemented by a subagent following `.claude/rules/`, verified by tests
under `tests/`, and closed by updating the item status here and the matching spec under `.specs/`.

## Baseline numbers

| Metric | Value |
|---|---|
| Tests | 878 passing in ~3.3 s, **all** under `tests/unit/helpers/` |
| Line coverage | **55.97 %** measured with the legacy coverage exclusions (`pass`/`continue`/`break` excluded); **54.99 %** under the current configuration, which is the ratchet baseline in `tools/coverage_baseline.txt`; the gate is `fail_under = 54` in `pyproject.toml` and `--cov-fail-under=54` in the Makefile |
| Lint | `ruff check .` clean (default rule set only, line length not enforced by ruff) |
| Type checking | none (no mypy/pyright configured) |
| Security tooling | none (no bandit / pip-audit / CodeQL) |
| Python | 3.12.3, Poetry 2.2.1, pandas 3.0.1, pyenchant 3.3.0, pdfkit 1.0.0 (wkhtmltopdf) |
| Locale catalogs | pt_BR 76 keys, en_US 72 keys (4 missing), both contain leftover demo keys |

## Files

| File | Scope |
|---|---|
| [01-bugs.md](01-bugs.md) | Correctness defects found in the current code |
| [02-security.md](02-security.md) | Security and robustness issues |
| [03-architecture.md](03-architecture.md) | Design debt blocking elegance, scalability and maintainability |
| [04-testing.md](04-testing.md) | Test coverage gaps and test infrastructure |
| [05-performance.md](05-performance.md) | Hot spots and scalability limits |
| [06-tooling-ci.md](06-tooling-ci.md) | Build, CI/CD, packaging, pre-commit |
| [07-docs-i18n.md](07-docs-i18n.md) | Documentation and internationalisation |
| [08-migration-roadmap.md](08-migration-roadmap.md) | Phased plan that orders the items above |

## Item format

```
### <ID> · <title>
- Priority: P0 (blocker) | P1 (high) | P2 (medium) | P3 (low)
- Effort: S (< 2 h) | M (half day) | L (1–3 days) | XL (> 3 days)
- Status: open | in-progress | done | wont-fix
- Where: file:line references
- Problem / Evidence / Proposed fix / Tests required / Related
```

IDs are stable; never renumber. New findings are appended at the end of the relevant file.

## Priority summary

| Priority | Count | Done | Highlights |
|---|---|---|---|
| P0 | 7 | 1 | XSS in HTML report (SEC-001), shared mutable class state (BUG-002, ARC-002), work-in-constructors (ARC-001), no tests for validators (TST-001), no e2e safety net (TST-002), shared list mutation (BUG-001) |
| P1 | 28 | 6 | locale global state (BUG-004), string-based error model (ARC-004), i18n incomplete (ARC-005), iterrows hot paths (PERF-001), CI non-blocking lint (TOOL-001), exit-code contract (SEC-008) |
| P2 | 43 | 4 | see files |
| P3 | 12 | 0 | see files |
| **Total** | **90** | **11** | |

Status snapshot: 2026-08-25 — 11 done, 4 in-progress, 75 open
