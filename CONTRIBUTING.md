# Contributing to Data Validate

Thanks for contributing to `canoa-data-validate` (Canoa), the spreadsheet validator for the
AdaptaBrasil platform. This guide covers the practical workflow; conventions and rationale live
under `.specs/` and `.claude/rules/`.

## Development setup

```bash
git clone https://github.com/AdaptaBrasil/data_validate.git
cd data_validate
make setup          # poetry install --sync + pre-commit install
make check           # lint + typecheck + security-offline + unit tests
```

System dependencies (`enchant-2 hunspell-pt-br hunspell-en-us`, `wkhtmltopdf`) are only needed
to exercise spell-check/PDF tests locally — see `README.md` → Installation.

## Branching and commits

- Branch names: `feat|fix|test|chore/<BACKLOG-ID>-<slug>` (e.g. `fix/BUG-006-list-remove`).
  Pick an item from `.specs/quality/backlog/` (`/backlog next` if you use Claude Code).
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/), in
  English, referencing the backlog ID in the body when applicable:
  `fix(rules): BUG-006 avoid list.remove on missing id`.
- **Never push from an automated agent.** Humans review and push; agents commit locally only.
- Never `git add .` blindly — stage the exact paths that belong to the change.

## Pull request checklist

- [ ] Tests added/updated (pytest + pytest-mock only) and passing (`make test-unit`, plus
      `make test-e2e` if behaviour affecting the pipeline changed).
- [ ] Any behaviour/rule/contract/convention change updates the matching file under `.specs/`
      in the same commit (spec-sync — see `.claude/rules/spec-sync.md`).
- [ ] `CHANGELOG.md` has an entry under `## [Unreleased]`.
- [ ] `make check` is green locally.
- [ ] New modules carry ≥ 95 % line coverage; the repo-wide coverage ratchet did not go down.

## Testing

`pytest` + `pytest-mock` exclusively — `unittest.mock` and `with patch(...)` are forbidden. New
modules require ≥ 95 % coverage; the overall gate is a ratchet (currently `fail_under = 54` in
`pyproject.toml`, raised by `tools/coverage_ratchet.py`, never lowered). Every bug fix ships a
named regression test. Details: [`TESTING.md`](TESTING.md) and
[`.claude/rules/testing.md`](.claude/rules/testing.md).

## Code style

- Python 3.12+, `ruff` (line length **120**, `ruff format`), Google-style docstrings, English
  prose and identifiers.
- `mypy --strict` is required for new/migrated modules (legacy `data_validate/**` is exempted
  until migrated — see `pyproject.toml` `[[tool.mypy.overrides]]`).
- No global state, no work inside `__init__` beyond assignment, no bare `except Exception`, no
  hardcoded user-facing strings (everything goes through the i18n catalog).
- Full rationale: [`.claude/rules/coding-standards.md`](.claude/rules/coding-standards.md).

## i18n rule

No user-facing string is ever hardcoded in code. Messages are looked up by key from
`static/locales/<locale>/messages.json`; pt_BR and en_US must stay at parity. See
[`.claude/rules/i18n.md`](.claude/rules/i18n.md).

## Adding a validation rule

Follow the `validation-rule-authoring` skill end to end (rule ID, message keys in both catalogs,
a pure vectorised rule function, registry/`NamesEnum` wiring, table-driven tests, a golden case,
business-rule spec update). With Claude Code: `/rule <RULE-ID>`.

## Multi-agent development workflow

This repository is developed with an AI-orchestrator workflow (see `CLAUDE.md`, `AGENTS.md`
for the tool-agnostic version). Key points for any contributor, human or agent:

- `.claude/rules/` are standing conventions, auto-loaded every session (model delegation,
  spec-sync, testing, i18n, security, DataFrame conventions, architecture boundaries, git
  workflow, performance).
- `.claude/agents/` are specialised subagents (implementer, test-engineer, code-reviewer,
  security-auditor, spec-writer, …); `.claude/commands/` are slash-command workflows
  (`/backlog`, `/implement`, `/review`, `/test`, `/e2e`, `/spec-sync`, `/adr`, `/rule`, `/commit`,
  …); `.claude/skills/` are how-to guides for recurring tasks.
- `.claude/settings.json` is committed and shared; **`.claude/settings.local.json` is personal**
  (gitignored) — use it for your own model/permission preferences, never commit it.
- Picking work: `.specs/quality/backlog/` holds 89 prioritised items (`P0`–`P3`), ordered into
  phases by `.specs/quality/backlog/08-migration-roadmap.md`. Use `/backlog next` or pick an ID
  directly.

## Questions

Open a [discussion or issue](https://github.com/AdaptaBrasil/data_validate/issues) using the
templates under `.github/ISSUE_TEMPLATE/`. For security issues, see
[`SECURITY.md`](SECURITY.md) instead — do not open a public issue.
