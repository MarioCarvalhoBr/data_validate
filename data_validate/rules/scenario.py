#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""SCEN-003…004: the `cenarios` content rules (ARC-017 Phase 3 Port 4, ADR-0006).

Ports `validators/spreadsheets/scenario/scenario_validator.py::SpScenarioValidator`'s two checks
(name/description punctuation, unique `nome`/`simbolo`) onto the `rules` engine, one `RuleSpec`
per `SCEN-*` id documented in `.specs/business-rules/scenarios.md`. `SCEN-001`/`SCEN-002` (the
"a delivered file must define at least one symbol" and "symbols must not repeat" structural
checks) stay in `models/sp_scenario.py::SpScenario.pre_processing` — they run before this
module's rules even see a frame and are out of this port's scope.

i18n (ARC-005): every message this module emits is a catalog key
(`static/locales/<locale>/messages.json`), never an inline string; the shared "required column
is missing" abort reuses one key per rule's severity bucket,
`rule.scenario.missing_required_column`, matching `rules/description.py`'s `_MISSING_COLUMN_KEY`
precedent.

Every check below was already vectorised in the legacy validator's own helpers
(`CharacterProcessing.check_characters_punctuation_rules`,
`DataFrameProcessing.check_dataframe_unique_values`) and is reproduced with the same shape here,
minus the final string-building step (an `Issue` now, not an f-string) — mirrors
`rules/description.py::check_punctuation`'s two-phase shape (columns that must not end with
punctuation, columns that must end with a period) for a two-column sheet instead of a
four-column one.

Depends only on `data_validate.rules`/`data_validate.specs` and `pandas` — never on `models` or
the hardcoded-string-building helpers (`character_processing.py`, `dataframe_processing.py`'s
message-building functions), per `.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

SCENARIO_REGISTRY = RuleRegistry()
"""Every `SCEN-*` rule ported from `SpScenarioValidator`, in the legacy check order."""

_SHEET = "cenarios"

_NAME = "nome"
_DESCRIPTION = "descricao"
_SYMBOL = "simbolo"

_NO_PUNCTUATION_COLUMNS: tuple[str, ...] = (_NAME,)
_MUST_END_WITH_DOT_COLUMNS: tuple[str, ...] = (_DESCRIPTION,)
_PUNCTUATION_CHARS = frozenset(",.;:!?")

_MISSING_COLUMN_KEY = "rule.scenario.missing_required_column"


def _excel_row(idx: int) -> int:
    """Convert a 0-based `cenarios` row index into the 1-based Excel row.

    `cenarios` is a single-header sheet (`.claude/rules/dataframe-conventions.md`): the
    spreadsheet row is the data index plus 2 (one for the header row, one because spreadsheets
    are 1-based).
    """
    return int(idx) + 2


def _filename(ctx: RuleContext) -> str:
    """Return the `cenarios` file name as delivered (e.g. `"cenarios.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and _SHEET in filenames:
        return str(filenames[_SHEET])
    return _SHEET


def _missing_column_issue(rule_id: str, severity: Severity, category: str, filename: str, column: str) -> Issue:
    """Build the "required column is missing" abort `Issue` shared by every rule below."""
    return Issue(
        rule_id=rule_id,
        severity=severity,
        sheet=filename,
        row=None,
        column=column,
        message_key=_MISSING_COLUMN_KEY,
        params={"filename": filename, "column": column},
        category=category,
    )


@SCENARIO_REGISTRY.rule(rule_id="SCEN-003", category=NamesEnum.MAND_PUNC_SCEN.value, requires={_SHEET: ()})
def check_punctuation(ctx: RuleContext) -> list[Issue]:
    """SCEN-003: `nome` never ends with punctuation; `descricao` must end with a period.

    Missing columns are reported first, for `nome` then `descricao`, before any violation is
    checked — matches `validate_punctuation`'s own two-phase shape (its missing-column loop runs
    to completion, then `CharacterProcessing.check_characters_punctuation_rules` runs over
    whichever columns exist). Every issue is a **warning**, matching the legacy validator's own
    severity (it only ever returns `([], warnings)`).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    issues: list[Issue] = []
    for column in _NO_PUNCTUATION_COLUMNS + _MUST_END_WITH_DOT_COLUMNS:
        if column not in frame.columns:
            issues.append(
                _missing_column_issue("SCEN-003", Severity.WARNING, NamesEnum.MAND_PUNC_SCEN.value, filename, column)
            )

    for column in _NO_PUNCTUATION_COLUMNS:
        if column not in frame.columns:
            continue
        series = frame[column]
        mask = series.notna() & (series != "")
        if not mask.any():
            continue
        text = series[mask].astype(str).str.strip()
        ends_with_punctuation = text.str[-1].isin(_PUNCTUATION_CHARS)
        for idx in text.index[ends_with_punctuation]:
            issues.append(
                Issue(
                    rule_id="SCEN-003",
                    severity=Severity.WARNING,
                    sheet=filename,
                    row=int(idx),
                    column=column,
                    message_key="rule.SCEN-003.no_punctuation",
                    params={"filename": filename, "row": _excel_row(idx), "column": column},
                    category=NamesEnum.MAND_PUNC_SCEN.value,
                )
            )

    for column in _MUST_END_WITH_DOT_COLUMNS:
        if column not in frame.columns:
            continue
        series = frame[column]
        mask = series.notna() & (series != "")
        if not mask.any():
            continue
        text = series[mask].astype(str).str.strip()
        not_ends_with_dot = ~text.str.endswith(".")
        for idx in text.index[not_ends_with_dot]:
            issues.append(
                Issue(
                    rule_id="SCEN-003",
                    severity=Severity.WARNING,
                    sheet=filename,
                    row=int(idx),
                    column=column,
                    message_key="rule.SCEN-003.must_end_with_dot",
                    params={"filename": filename, "row": _excel_row(idx), "column": column},
                    category=NamesEnum.MAND_PUNC_SCEN.value,
                )
            )

    return issues


@SCENARIO_REGISTRY.rule(rule_id="SCEN-004", category=NamesEnum.UVR_SCEN.value, requires={_SHEET: ()})
def check_name_and_symbol_are_unique(ctx: RuleContext) -> list[Issue]:
    """SCEN-004: `nome` and `simbolo` must each contain no duplicated value.

    Both columns are checked for a missing-column abort first (in `nome`, `simbolo` order),
    then each existing column is checked for uniqueness independently — matches
    `validate_unique_values`'s own two-phase shape (its missing-column loop runs to completion,
    then `DataFrameProcessing.check_dataframe_unique_values` runs over whichever columns exist).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    issues: list[Issue] = [
        _missing_column_issue("SCEN-004", Severity.ERROR, NamesEnum.UVR_SCEN.value, filename, column)
        for column in (_NAME, _SYMBOL)
        if column not in frame.columns
    ]

    for column in (_NAME, _SYMBOL):
        if column not in frame.columns or frame[column].is_unique:
            continue
        issues.append(
            Issue(
                rule_id="SCEN-004",
                severity=Severity.ERROR,
                sheet=filename,
                row=None,
                column=column,
                message_key="rule.SCEN-004.error",
                params={"filename": filename, "column": column},
                category=NamesEnum.UVR_SCEN.value,
            )
        )
    return issues


_SYMBOL_CHARSET_PATTERN = re.compile(r"^[A-Za-z0-9]$")
"""PROTO-006 (protocol §2.1 p.4, v1.16): "Um único caractere ... apenas letras e números" --
exactly one ASCII letter or digit; an accented letter, punctuation, space, or a multi-character
value all fail this pattern."""


@SCENARIO_REGISTRY.rule(rule_id="SCEN-005", category=NamesEnum.SYMB_SCEN.value, requires={_SHEET: ()})
def check_symbol_charset(ctx: RuleContext) -> list[Issue]:
    """SCEN-005 (PROTO-006, gap G-17): `simbolo` must be exactly one ASCII letter or digit.

    Protocol §2.1 p.4 (v1.16, clarifying v1.10's G-17): "Um único caractere ... apenas letras e
    números, não podendo ter espaço, pontuação ou qualquer outro caracter especial." An accented
    letter (e.g. `"é"`) is not ASCII and therefore also rejected -- the protocol's "apenas letras"
    means the unaccented Latin alphabet the value-column pattern (`CÓDIGO-ANO[-CENÁRIO]`) can
    actually match.
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _SYMBOL not in frame.columns:
        return [_missing_column_issue("SCEN-005", Severity.ERROR, NamesEnum.SYMB_SCEN.value, filename, _SYMBOL)]

    series = frame[_SYMBOL].astype(str)
    invalid_mask = ~series.str.match(_SYMBOL_CHARSET_PATTERN)
    return [
        Issue(
            rule_id="SCEN-005",
            severity=Severity.ERROR,
            sheet=filename,
            row=int(idx),
            column=_SYMBOL,
            message_key="rule.SCEN-005.error",
            params={"filename": filename, "row": _excel_row(idx), "column": _SYMBOL, "value": series.loc[idx]},
            category=NamesEnum.SYMB_SCEN.value,
        )
        for idx in series.index[invalid_mask]
    ]
