---
description: Full workflow for authoring a new validation rule, using the validation-rule-authoring skill
argument-hint: "<RULE-ID>"
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(poetry run pytest*), Agent
---

Argument: `$ARGUMENTS` — a rule ID, existing (to modify) or new (e.g. `LEG-009`).

1. Load the `validation-rule-authoring` skill and follow its steps.
2. If `$ARGUMENTS` is a new rule, first consult `protocol-expert` (`model: opus` per
   `.claude/rules/model-delegation.md` — state the rule) to confirm what the protocol requires and
   which sheet/severity it belongs to.
3. Write or update the `.specs/business-rules/<sheet>.md` entry for the rule (delegate to
   `spec-writer`, `model: sonnet`, if the spec file needs non-trivial restructuring).
4. Delegate to `implementer` (`model: sonnet`, state the delegation rule) using the skill's
   `templates/rule.py.md` sketch: message keys added to both locale catalogs, a pure vectorised
   rule function, registration in the model/validator.
5. Delegate to `test-engineer` (`model: sonnet`) using `templates/test_rule.py.md`: table-driven
   unit tests plus a proposed golden case.
6. Run `/review`, then `/spec-sync`.
7. Report the rule ID, files touched, and test coverage achieved.
