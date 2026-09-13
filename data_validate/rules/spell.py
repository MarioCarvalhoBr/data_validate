#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""SPELL-001…005: the spell-check rules (ARC-017 Phase 3 Port 8, ADR-0006).

Ports `validators/spell/spellchecker_validator.py::SpellCheckerValidator`'s pipeline onto the
`rules` engine, one `RuleSpec` per checked model plus one for the dictionary/backend errors, all
tagged `NamesEnum.SPELL` (`.specs/business-rules/spelling.md`):

- `_prepare_statement` (dictionary/backend initialisation errors, BUG-027) → `SPELL-001`,
  `check_dictionary_backend`. Registered first and **never** gated on `--no-spellchecker`
  (`ctx.options["no_spellchecker"]`), matching the legacy validator's own
  `self._prepare_statement()` call, which ran before `run()` checked that flag — a broken
  dictionary is reported even when spell-checking itself is skipped.
- `validate_spellchecker(SpDescription)` → `SPELL-002`, `check_spelling_description`.
- `validate_spellchecker(SpTemporalReference)` → `SPELL-003`, `check_spelling_temporal_reference`.
- `validate_spellchecker(SpScenario)` (only when scenarios exist) → `SPELL-004`,
  `check_spelling_scenario`.

One `RuleSpec` per checked model (not per spelling.md behaviour) because each model's own sheet
gates its own `requires` (an empty `descricao`/`referencia_temporal`/`cenarios` sheet must skip
independently, matching `validate_spellchecker`'s own `if self._dataframe.empty: return` guard).
Every one of these three model rules can still emit an `Issue` tagged with *any* of `SPELL-002`
(missing column), `SPELL-003` (two or more consecutive spaces), `SPELL-004` (misspelled words), or
`SPELL-005` (processing failure) — the RuleSpec id names which model's sheet gates the rule, not
which specific finding it may report, exactly mirroring `rules/proportionality.py`'s `PROP-007`
precedent (one legacy method, one `RuleSpec`, several `Issue`-level rule ids).

`--no-spellchecker` (`ctx.options["no_spellchecker"]`) makes `SPELL-002`/`003`/`004` return no
issues at all, without even checking for a missing column — matching the legacy `run()`'s
`validations` list simply never gaining that model's entry. `SPELL-004`'s scenario gate additionally
checks `ctx.options["scenarios"]` (matching `if self._data_model.scenarios:`, evaluated against the
processor's global scenario-symbol list, not `SpScenario`'s own `scenarios` attribute — see
`SpreadsheetProcessor._build_rule_context`, which passes the same list to every model's
constructor kwarg and to `RuleContext.options["scenarios"]`).

Sort order (BUG-006-adjacent, i18n-safe): the legacy `validate_spellchecker` sorted the two
per-model warning lists (`errors.extend(sorted(errors_spellchecker))`,
`warnings.extend(sorted(warnings_spellchecker))`) as already-rendered Portuguese strings, which
reorders same-day multi-digit line numbers lexicographically (`"linha 10"` sorts before
`"linha 2"`). `_sort_by_rendered_text` reproduces this **without building message text in rule
code**: it calls `ctx.translate(issue.message_key, **issue.params)` — the same call
`extend_report_from_outcomes` makes later to render for real — purely to derive a sort key, then
returns the original `Issue` objects (never the rendered strings) in that order; `sorted()` is
stable, so ties keep their original (row-then-signal) order, matching Python's `sorted()` on the
legacy string list exactly.

BUG-027 (dictionary-error passthrough): `DictionaryManager`/`SpellChecker.errors_dictionary`
strings arrive pre-formed (hardcoded Portuguese, independent of `--locale` — a pre-existing legacy
gap this port does not fix, tracked in `.specs/business-rules/spelling.md`). Wrapping each one in
a full sentence-shaped catalog key/template pair would either duplicate the exact same Portuguese
text as a "translation" or invent an English rendering for a string this port has no authority to
retranslate (the strings themselves live in `dictionary_manager.py`, out of this port's scope).
`rule.SPELL-001.backend_error` is therefore a documented, intentional passthrough: a `{message}`-
only template (identical in both locales) that renders exactly the string
`DictionaryManager`/`SpellChecker` produced — legacy-compat, not a model for new catalog keys.

Depends only on `data_validate.rules`/`data_validate.specs` and the `SpellChecker`/`SpellingFinding`
backend contract (`helpers/tools/spellchecker/spellchecker.py`) — never on `models`, per
`.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol, runtime_checkable

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

SPELL_REGISTRY = RuleRegistry()
"""Every `SPELL-*` rule ported from `SpellCheckerValidator`, in the legacy check order."""


class _SpellingFinding(Protocol):
    """Structural shape of one backend finding (matches `SpellChecker.SpellingFinding`)."""

    row_index: int
    column: str
    kind: str
    words: Sequence[str]


@runtime_checkable
class _SpellBackend(Protocol):
    """Structural shape this module needs from `ctx.options["spell_backend"]`.

    A `Protocol` (not the concrete `SpellChecker` class) so a test double
    (`tests/unit/rules/test_spell.py::FakeSpellBackend`) satisfies `isinstance` too, per
    `.claude/rules/architecture-boundaries.md`'s "rules never depend on models" combined with
    `rules/composition.py::_facts`'s `isinstance`-narrowing precedent for a `ctx.options` value
    typed as `object`.
    """

    errors_dictionary: Sequence[str]

    def check_spelling_text_structured(
        self, df: pd.DataFrame, columns_sheets: list[str]
    ) -> tuple[tuple[_SpellingFinding, ...], str | None]: ...


def _backend(ctx: RuleContext) -> _SpellBackend | None:
    """Return `ctx.options["spell_backend"]` narrowed to `_SpellBackend`, or `None`."""
    backend = ctx.options.get("spell_backend")
    if isinstance(backend, _SpellBackend):
        return backend
    return None


_DESCRIPTION_SHEET = "descricao"
_TEMPORAL_SHEET = "referencia_temporal"
_SCENARIO_SHEET = "cenarios"

_DESCRIPTION_COLUMNS: tuple[str, ...] = ("nome_simples", "nome_completo", "desc_simples", "desc_completa")
_TEMPORAL_COLUMNS: tuple[str, ...] = ("descricao",)
_SCENARIO_COLUMNS: tuple[str, ...] = ("nome", "descricao")

_MISSING_COLUMN_KEY = "rule.spelling.missing_required_column"


def _filename(ctx: RuleContext, sheet: str) -> str:
    """Return `sheet`'s display file name, as delivered (e.g. `"descricao.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and sheet in filenames:
        return str(filenames[sheet])
    return sheet


def _excel_row(idx: int) -> int:
    """Convert a 0-based row index into the 1-based Excel row for a single-header sheet.

    `descricao`/`referencia_temporal`/`cenarios` are all single-header sheets
    (`.claude/rules/dataframe-conventions.md`): the spreadsheet row is the data index plus 2.
    """
    return int(idx) + 2


def _missing_column_issue(filename: str, column: str) -> Issue:
    """Build the shared "required column is missing" abort `Issue` (SPELL-002, a warning).

    Matches `BaseValidator.column_exists`'s plain-`Index` branch text (every spell-checked sheet
    is single-header, never a `MultiIndex`) and `validate_spellchecker`'s own severity (it always
    appends this to `warnings`, never `errors`).
    """
    return Issue(
        rule_id="SPELL-002",
        severity=Severity.WARNING,
        sheet=filename,
        row=None,
        column=column,
        message_key=_MISSING_COLUMN_KEY,
        params={"filename": filename, "column": column},
        category=NamesEnum.SPELL.value,
    )


def _processing_error_issue(filename: str, error: str) -> Issue:
    """Build the "processing failed" `Issue` (SPELL-005), matching `check_spelling_text`'s
    own broad-catch wrapper text `f"Erro ao processar o arquivo {file_name}: {e}"`."""
    return Issue(
        rule_id="SPELL-005",
        severity=Severity.ERROR,
        sheet=filename,
        row=None,
        column=None,
        message_key="rule.SPELL-005.error",
        params={"filename": filename, "message": error},
        category=NamesEnum.SPELL.value,
    )


def _finding_to_issue(finding: _SpellingFinding, filename: str) -> Issue:
    """Build one `Issue` from a `SpellingFinding` (SPELL-003 or SPELL-004, both warnings)."""
    if finding.kind == "multiple_spaces":
        return Issue(
            rule_id="SPELL-003",
            severity=Severity.WARNING,
            sheet=filename,
            row=finding.row_index,
            column=finding.column,
            message_key="rule.SPELL-003.warning",
            params={"filename": filename, "row": _excel_row(finding.row_index), "column": finding.column},
            category=NamesEnum.SPELL.value,
        )
    return Issue(
        rule_id="SPELL-004",
        severity=Severity.WARNING,
        sheet=filename,
        row=finding.row_index,
        column=finding.column,
        message_key="rule.SPELL-004.warning",
        params={
            "filename": filename,
            "row": _excel_row(finding.row_index),
            "column": finding.column,
            "words": str(list(finding.words)),
        },
        category=NamesEnum.SPELL.value,
    )


def _sort_by_rendered_text(ctx: RuleContext, issues: list[Issue]) -> list[Issue]:
    """Reproduce `sorted(warnings_spellchecker)` over already-rendered text (see module docstring).

    Sorts by each `Issue`'s own rendered text (`ctx.translate`), a stable sort so ties (identical
    rendered text) keep their original relative order; the `Issue` objects themselves — never
    the rendered strings — are what gets returned and later rendered again for real.
    """
    return sorted(issues, key=lambda issue: ctx.translate(issue.message_key, **issue.params))


def _spelling_issues_for_model(ctx: RuleContext, *, sheet: str, columns: tuple[str, ...]) -> list[Issue]:
    """Shared body of `SPELL-002`/`003`/`004`: one checked model's column/quality checks.

    Mirrors `SpellCheckerValidator.validate_spellchecker`: `--no-spellchecker` skips everything
    (including the missing-column check) for this model; otherwise every missing column is
    reported first (in `columns` order), then the remaining columns are checked through the
    backend, a processing failure aborts with `SPELL-005`, and quality findings are rendered and
    sorted to match the legacy `sorted(warnings_spellchecker)` step.
    """
    if ctx.options.get("no_spellchecker"):
        return []

    frame = ctx.sheet(sheet)
    filename = _filename(ctx, sheet)
    backend = _backend(ctx)

    issues: list[Issue] = [_missing_column_issue(filename, column) for column in columns if column not in frame.columns]
    valid_columns = [column for column in columns if column in frame.columns]
    if not valid_columns or backend is None:
        return issues

    findings, error = backend.check_spelling_text_structured(frame, valid_columns)
    if error is not None:
        issues.append(_processing_error_issue(filename, error))
        return issues

    finding_issues = [_finding_to_issue(finding, filename) for finding in findings]
    issues.extend(_sort_by_rendered_text(ctx, finding_issues))
    return issues


@SPELL_REGISTRY.rule(rule_id="SPELL-001", category=NamesEnum.SPELL.value)
def check_dictionary_backend(ctx: RuleContext) -> list[Issue]:
    """SPELL-001: the language dictionary/backend must initialise without error (BUG-027).

    Reads `ctx.options["spell_backend"].errors_dictionary` (already collected by
    `SpellChecker._prepare_statement` at construction time, in
    `SpreadsheetProcessor._build_rule_context`) — never gated on `--no-spellchecker` or any
    `requires` sheet, matching the legacy validator's own unconditional `_prepare_statement()`
    call. Every error string is a `SPELL-001` issue, in `errors_dictionary`'s own order.
    """
    backend = _backend(ctx)
    if backend is None:
        return []

    return [
        Issue(
            rule_id="SPELL-001",
            severity=Severity.ERROR,
            sheet="dicionario",
            row=None,
            column=None,
            message_key="rule.SPELL-001.backend_error",
            params={"message": message},
            category=NamesEnum.SPELL.value,
        )
        for message in backend.errors_dictionary
    ]


@SPELL_REGISTRY.rule(rule_id="SPELL-002", category=NamesEnum.SPELL.value, requires={_DESCRIPTION_SHEET: ()})
def check_spelling_description(ctx: RuleContext) -> list[Issue]:
    """SPELL-002…005 (description): spell-check `nome_simples`/`nome_completo`/`desc_simples`/
    `desc_completa`. Skipped entirely when `descricao` is empty (`requires`, matching
    `validate_spellchecker`'s own `if self._dataframe.empty: return` guard)."""
    return _spelling_issues_for_model(ctx, sheet=_DESCRIPTION_SHEET, columns=_DESCRIPTION_COLUMNS)


@SPELL_REGISTRY.rule(rule_id="SPELL-003", category=NamesEnum.SPELL.value, requires={_TEMPORAL_SHEET: ()})
def check_spelling_temporal_reference(ctx: RuleContext) -> list[Issue]:
    """SPELL-002…005 (referencia_temporal): spell-check `descricao`. Skipped entirely when
    `referencia_temporal` is empty (`requires`)."""
    return _spelling_issues_for_model(ctx, sheet=_TEMPORAL_SHEET, columns=_TEMPORAL_COLUMNS)


@SPELL_REGISTRY.rule(rule_id="SPELL-004", category=NamesEnum.SPELL.value, requires={_SCENARIO_SHEET: ()})
def check_spelling_scenario(ctx: RuleContext) -> list[Issue]:
    """SPELL-002…005 (cenarios): spell-check `nome`/`descricao`, only when scenarios exist.

    Skipped entirely when `cenarios` is empty (`requires`) or when `ctx.options["scenarios"]` is
    empty (matching `if self._data_model.scenarios:`, evaluated against the processor's global
    scenario-symbol list — see this module's docstring).
    """
    if not ctx.options.get("scenarios"):
        return []
    return _spelling_issues_for_model(ctx, sheet=_SCENARIO_SHEET, columns=_SCENARIO_COLUMNS)
