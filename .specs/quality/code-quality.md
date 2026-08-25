# Code quality

## Tooling baseline (ADR-0010)

| Tool | Config | Scope | Gate |
|---|---|---|---|
| `ruff check` | `[tool.ruff]` line-length 120, target py312, rules `E,F,W,I,B,UP,SIM,PD,PL,S,N,RUF,C4,PTH,RET` | whole repo | CI `lint`, pre-commit |
| `ruff format` | double quotes | whole repo | CI `lint --check`, PostToolUse hook |
| `mypy` | `strict = true`; `ignore_errors` overrides for the explicit list of legacy modules (shrinks every phase) | `data_validate`, `tests/e2e`, `tools` | CI `typecheck` |
| `bandit` | `[tool.bandit]` exclude `tests`, `tools/legacy` | `data_validate` | CI `security` |
| `pip-audit` | lock file | dependencies | CI `security` |
| `pytest` + coverage ratchet | see `testing-strategy.md` | tests | CI `test` |

### Why these ruff rule families

| Family | Reason |
|---|---|
| `E,W,F` | pycodestyle/pyflakes basics |
| `I` | deterministic imports |
| `B` | bugbear: mutable defaults, unused loop vars, `except Exception` without re-raise patterns |
| `UP` | modern syntax (`list[str]`, `X \| None`) |
| `SIM` | simplifications, early returns |
| `PD` | pandas anti-patterns (`iterrows`, `.values`, chained indexing) — core of the performance goal |
| `PL` | pylint: too many args/branches/returns, magic numbers (`PLR2004`) |
| `S` | bandit-in-ruff: `assert`, `eval`, subprocess, temp files |
| `N` | naming |
| `RUF` | ruff-specific (mutable class defaults, unused `noqa`) |
| `C4` | comprehensions |
| `PTH` | `pathlib` over `os.path` |
| `RET` | consistent returns |

Legacy files keep a **listed** `per-file-ignores` block; removing an entry is part of migrating
that module.

## Definition of done (per backlog item / PR)

1. Scope matches the backlog item; no drive-by changes outside it (Boy Scout only inside touched
   functions).
2. `make check` green locally: lint, format, typecheck, security, unit tests.
3. New/changed behaviour covered by tests (≥ 95 % for new modules; regression test for bugs).
4. `make test-e2e` green, or goldens updated with a written reason.
5. Messages only through the catalog, both locales.
6. Specs updated in the same commit (`.claude/rules/spec-sync.md`); ADR if a structural
   decision was taken.
7. Conventional Commit referencing the ID; CHANGELOG `Unreleased` entry when user-visible.
8. `/review` findings addressed (code-reviewer + security-auditor).

## Style essentials (full text in `.claude/rules/coding-standards.md`)

- Google-style docstrings in English on public symbols; none that restate the code.
- No work in `__init__`; no module-level side effects; no global mutable state.
- Frozen dataclasses for value objects; `Protocol` for seams; builtins generics.
- Exceptions for failures, `Issue`s for findings; never `(bool, str)` tuples.
- Functions ≤ ~40 lines, ≤ 5 parameters (else a dataclass), early returns.

Last synced with code: 3dcfdb1
