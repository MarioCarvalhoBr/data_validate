# UC-05 · Add a new validation rule

- Primary actor: INPE maintainer (with the `implementer`/`test-engineer` agents)
- Goal: a new protocol requirement becomes a traceable, tested, localised rule

## Preconditions
- The requirement is written (protocol section or issue) and has a target sheet.

## Main flow
1. Maintainer runs `/rule <SHEET-NNN>` (skill `validation-rule-authoring`).
2. Spec: add the rule row to `.specs/business-rules/<sheet>.md` (ID, severity, description,
   protocol section, message text pt-BR + en-US).
3. Catalog: add `rule.<ID>.error|warning` to both locale files; `tools/i18n_check.py` passes.
4. Code: create `rules/<sheet>/<ID>.py` with a pure `check(ctx)` (vectorised), declare
   `requires`/`depends_on`, register it. Today: add a `validate_*` method in the sheet validator,
   append `(method, NamesEnum.X.value)` to `run()`, and add the key to `NamesEnum` + both
   catalogs if it is a new category.
5. Tests: table-driven unit tests (`tests/unit/rules/<sheet>/test_<ID>.py`) covering pass, each
   failure, missing column, empty sheet; add/adjust a golden fixture case under `data/input/`.
6. `make check` and `make test-e2e` green; `/review`; `/spec-sync`; commit with the rule ID.

## Alternative flows
- 4a. The rule needs a new normalised column → extend `ColumnSpec` in `specs/sheets.py` and the
  normaliser first (own commit).
- 5a. Goldens change for existing fixtures → expected only if the new rule fires on them; update
  via `make harness-update` with the reason.

## Postconditions
- `--list-rules` shows the rule; report renders it under its category; spec, code, tests and
  catalogs reference the same ID.

## Related
- `../business-rules/README.md`, `.claude/skills/validation-rule-authoring/SKILL.md`
- Backlog: DOC-002, ARC-017

Last synced with code: 3dcfdb1
