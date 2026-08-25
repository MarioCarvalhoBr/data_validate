---
name: validation-rule-authoring
description: Use when adding a new validation rule (or changing an existing one) for any spreadsheet — descricao, composicao, valores, referencia_temporal, cenarios, legenda, proporcionalidades, dicionario. Covers ID assignment, message catalog keys, a pure vectorised rule function, registry wiring, and table-driven tests.
---

# Authoring a validation rule

A rule checks one business constraint on one sheet and reports it as an error (blocks a clean
report) or a warning (does not). Every rule has a stable ID, one message key per language, a pure
function, a registration point, and tests. Follow these steps in order.

## 1. Assign the rule ID

Pick the prefix from `.specs/business-rules/README.md` matching the sheet: `STRUCT-` (file/column
structure, any sheet), `DESC-` (descricao), `COMP-` (composicao), `VAL-` (valores), `TEMP-`
(referencia_temporal), `SCEN-` (cenarios), `LEG-` (legenda), `PROP-` (proporcionalidades),
`SPELL-` (spell check, any text column). Use the next free number for that prefix. If the rule
already exists under a `NamesEnum` member (see `data_validate/config/names_enum.py`), reuse that
mapping rather than inventing a parallel ID — record the `NamesEnum` ↔ rule-ID mapping in
`.specs/business-rules/README.md`.

Before assigning an ID for genuinely new behaviour (not already in `NamesEnum`), consult the
`protocol-expert` agent (or the `spreadsheet-protocol` skill) to confirm the protocol requires it
and to classify its severity.

## 2. Write the spec entry

Add or update the rule's row in `.specs/business-rules/<sheet>.md`: rule ID, `NamesEnum` key (if
any), severity, current message text (pt-BR), the future catalog key, protocol section/page, the
`file:function` that implements it today (or "not yet implemented"), and the covering test path
(or "none — TST-00N").

## 3. Add message catalog keys

Add the same key to **both** `data_validate/static/locales/pt_BR/messages.json` and
`.../en_US/messages.json`, with a `message` field using named placeholders (`{filename}`, `{row}`,
`{column}`, ...) — never positional `{}`/`%s`. Keep the pt-BR text matching what the current
f-string produces if you are formalizing an existing message (goldens depend on exact wording).

## 4. Write the rule function

Follow `templates/rule.py.md`: a pure, vectorised function — no `iterrows` (see the
`pandas-vectorization` skill), takes the already-cleaned DataFrame/Series and context it needs as
explicit parameters, returns `(errors: list[str], warnings: list[str])` matching the existing
`BaseValidator` convention (`Tuple[List[str], List[str]]`), or a `list[Issue]` if the module has
already migrated to the target `Issue` model (see `.specs/architecture/error-model.md`).

## 5. Register the rule

Add `(self.validate_<name>, NamesEnum.<KEY>.value)` to the validator's `run()` validations list
(see `data_validate/validators/spreadsheets/description/description_validator.py` for the
pattern), or to the target rule registry once the module has migrated (Phase 3).

## 6. Write tests

Follow `templates/test_rule.py.md`: table-driven with `pytest.mark.parametrize`, pytest-mock only,
covering the happy path, the violation, boundary values, missing column, and empty DataFrame.

## 7. Propose a golden case

If the rule changes observable report output, tell `integration-tester` so it can add or update a
`data/input/` fixture and run `make harness-update` with a written reason — do not update goldens
yourself from this skill.

See `templates/rule.py.md` and `templates/test_rule.py.md` for ready-to-adapt sketches.
