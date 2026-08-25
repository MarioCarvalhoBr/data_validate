# ADR-0010: Tooling baseline: Poetry, ruff (lint+format), mypy strict-by-default for new code, bandit, pip-audit, pre-commit

- Status: Accepted
- Date: 2026-08-25
- Deciders: Mário de Araújo Carvalho (INPE) with the AI orchestrator

## Context

Before this execution, `pyproject.toml`'s dev dependency group (lines 52-63) was:
`pytest`, `coverage`, `pytest-cov`, `flake8`, `black`, `pre-commit`, `pdoc`, `flake8-html`,
`genbadge`, `pytest-mock`, `ruff` — two formatters/linters doing overlapping jobs (`black` for
formatting, `flake8`/`flake8-html` and `ruff` both for linting), with **no `[tool.ruff]` section at
all** (TOOL-003), so `ruff check .` ran with default rules only and no configured line length,
while `[tool.black]` (lines 118-138) set `line-length = 150` — non-standard and disconnected from
any `ruff`-enforced `E501`. There was no `[tool.mypy]`, no static type checking configured anywhere
in the project (the backlog baseline records "Type checking: none"). There was no `[tool.bandit]`
and no `pip-audit` invocation anywhere in `Makefile` or CI (SEC-005: "no bandit, no pip-audit, no
CodeQL, no dependabot.yml"). The `Makefile`'s own lint targets (`black`, `ruff`, `lint`, lines
90-96) only ran formatting/linting, never type-checking or security scanning. `.pre-commit-config.yaml`
(referenced by SEC-006/TOOL-002, not itself owned by this ADR's file but read as part of this
audit) ran the *entire application pipeline* on commit — regenerating README/docs/PDF reports/
badges and running `git add .` inside the hook — rather than static-analysis-only checks, and
caused a documented incident on 2026-08-25 where a 9-file docs commit came out as 22 files.
`[tool.coverage.report] exclude_lines` (`pyproject.toml:83-98`) included `"pass"`, `"continue"`,
`"break"` — lines that can legitimately hide real, untested branches, not just boilerplate.

## Decision

Establish, as of this execution, the tooling baseline every subsequent phase builds on: Poetry
remains the package/dependency manager. `black`, `flake8`, and `flake8-html` are removed from
`[tool.poetry.group.dev.dependencies]`; `ruff` (already present) becomes the single lint **and**
format tool (`ruff format` replacing `black`, `ruff check` replacing `flake8`), configured with
`[tool.ruff] line-length = 120, target-version = "py312"`, `select = ["E","F","W","I","B","UP",
"SIM","PD","PL","S","N","RUF","C4","PTH","RET"]` (adding pandas-specific `PD`, security `S`,
pylint-equivalent `PL`, and `naming`/`RUF` rules the previous default-only configuration never
enabled), with any `ignore`/`per-file-ignores` justified in a comment and scoped to explicitly
listed legacy files for the coverage ratchet to shrink over time. `mypy` is added with `strict =
true` as the **default for new modules**, with `[[tool.mypy.overrides]] ignore_errors = true`
listing legacy `data_validate.*` modules explicitly (never a blanket exemption), and `strict` kept
on for `tests/e2e/` and `tools/`. `bandit` (`exclude_dirs = ["tests", "tools/legacy"]`) and
`pip-audit` are added as dedicated `make security`/CI jobs. `.pre-commit-config.yaml` is replaced
with the standard hook set — `pre-commit-hooks` (trailing-whitespace, end-of-file-fixer, check-yaml,
check-toml, check-json, check-added-large-files 1 MB, detect-private-key, no-commit-to-branch main),
`ruff-pre-commit` (lint + format), `mirrors-mypy`, `bandit`, `poetry-check --lock`,
`conventional-pre-commit` — with **no hook that runs the application pipeline or calls `git add`**.
`[tool.coverage.report] exclude_lines` drops `"pass"`, `"continue"`, `"break"`.

## Consequences

### Positive
- One Rust-native tool (`ruff`) replaces two Python-native ones (`black` + `flake8`) for lint and
  format, running measurably faster and eliminating any chance of the two disagreeing on style.
- Type errors, security issues (bandit) and known-vulnerable dependencies (pip-audit) are now
  caught before merge instead of never being checked at all — closing the "Type checking: none" /
  "Security tooling: none" gaps recorded in the backlog baseline.
- Commit hooks can no longer surprise-modify 22 files from a 9-file change (SEC-006's documented
  incident) — pre-commit is limited to static, read-only-except-the-file-being-committed checks.

### Negative
- `mypy --strict` on new modules is a stricter bar than the codebase has ever enforced; contributors
  porting legacy code into a "new" module will hit type errors that previously went unchecked,
  which is the intended ratchet effect but adds friction during Phase 1-3 rule porting.
- The explicit per-module `ignore_errors` override list must be actively maintained (shrunk as
  modules migrate) — an unmaintained, growing exemption list would silently defeat the strict
  default; this is a process risk the `spec-sync` rule and `code-reviewer` subagent are expected to
  catch.

## Alternatives considered

### Keep `black` + `flake8`/`flake8-html` alongside `ruff`
Rejected: three overlapping tools for two jobs (format, lint) with no configured `[tool.ruff]`
section meant `ruff` was effectively dead weight already; consolidating onto one actively-developed,
much faster tool removes redundant CI time and eliminates any risk of the tools disagreeing.

### Adopt `pylint` instead of `ruff` for linting
Rejected: `pylint` is materially slower on a codebase this size and requires separate configuration
for the pandas- and security-aware checks (`PD`, `S`, `PL`-equivalent rule families) that `ruff`
now provides natively in one binary with one config block; there is no capability `pylint` offers
here that `ruff`'s selected rule set does not already cover for this project's needs.

### Enable `mypy --strict` project-wide immediately, with no legacy overrides
Rejected: the current codebase's typing discipline (ARC-014: `**kwargs: Dict[str, Any]` everywhere,
implicit-Optional defaults like `context: GeneralContext = None`, `Tuple[bool, str]` return codes)
would fail strict mypy in hundreds of places on day one, turning the type checker into permanently-
ignored CI noise rather than a useful gate; a strict-by-default-for-new-code policy with an explicit,
shrinking legacy allowlist gives the same eventual destination without an unusable interim state.

## Links

- Backlog: `TOOL-003` (`06-tooling-ci.md`); `SEC-005`, `SEC-006` (`02-security.md`);
  `TOOL-002` (`06-tooling-ci.md`); `ARC-014` (`03-architecture.md`);
  `08-migration-roadmap.md` Phase 0 item 2-3
- Specs: `.specs/quality/code-quality.md`
- Related ADRs: ADR-0011 (testing policy shares the same CI gate), ADR-0012 (workflow this tooling
  supports)

---
Last synced with code: a4f76c7
