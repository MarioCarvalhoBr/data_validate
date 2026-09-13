#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""TEMP-001…003: the `referencia_temporal` content rules (ARC-017 Phase 3 Port 4, ADR-0006).

Ports `validators/spreadsheets/temporal_reference/temporal_reference_validator.py::
SpTemporalReferenceValidator`'s three checks (description punctuation, future-only scenario
years, unique `nome`/`simbolo`) onto the `rules` engine, one `RuleSpec` per `TEMP-*` id
documented in `.specs/business-rules/temporal-reference.md`. `CLEAN-005`/`CLEAN-006` (the
`simbolo` integer-cleaning and single-row-without-scenarios checks) stay in
`models/sp_temporal_reference.py::SpTemporalReference.data_cleaning` — out of this port's scope.

i18n (ARC-005): every message this module emits is a catalog key
(`static/locales/<locale>/messages.json`), never an inline string; the shared
"required column is missing" abort reuses one key per rule's severity bucket,
`rule.temporal_reference.missing_required_column`, matching `rules/description.py`'s
`_MISSING_COLUMN_KEY` precedent.

BUG-007 (preserved, not reopened): `check_reference_years_are_future` reads the sheet's raw
`simbolo` column (`ctx.sheet(...)`, the model's own working frame — never a class-level
`RequiredColumn` Series), excludes the first row (the present-time reference), and silently
skips any value that does not parse as a non-negative integer — it is already reported as a
data-cleaning error by `SpTemporalReference.data_cleaning`. "Future" is still `>= current year`
(a symbol equal to the current year passes), and the current year comes from `ctx.clock().year`
rather than `ApplicationConfig.CURRENT_YEAR` directly, so the rule stays pure and testable
(`.claude/rules/coding-standards.md` "no global state").

PERF-001: `check_reference_years_are_future` replaces the legacy per-unique-value
`NumberFormattingProcessing.check_cell_integer`/`parse_numeric` loop with a vectorised
`pd.to_numeric(errors="coerce")` mask over the sheet's distinct `simbolo` values (still only a
handful of rows — `referencia_temporal` has one row per year — never a per-cell loop over the
full sheet); every other rule below was already vectorised in the legacy validator's own helpers
(`CharacterProcessing.check_characters_punctuation_rules`,
`DataFrameProcessing.check_dataframe_unique_values`) and is reproduced with the same shape here,
minus the final string-building step (an `Issue` now, not an f-string).

Depends only on `data_validate.rules`/`data_validate.specs` and `pandas` — never on `models` or
the hardcoded-string-building helpers (`character_processing.py`, `dataframe_processing.py`'s
message-building functions), per `.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

TEMPORAL_REGISTRY = RuleRegistry()
"""Every `TEMP-*` rule ported from `SpTemporalReferenceValidator`, in the legacy check order."""

_SHEET = "referencia_temporal"

_NAME = "nome"
_DESCRIPTION = "descricao"
_SYMBOL = "simbolo"

_MISSING_COLUMN_KEY = "rule.temporal_reference.missing_required_column"


def _excel_row(idx: int) -> int:
    """Convert a 0-based `referencia_temporal` row index into the 1-based Excel row.

    `referencia_temporal` is a single-header sheet (`.claude/rules/dataframe-conventions.md`):
    the spreadsheet row is the data index plus 2 (one for the header row, one because
    spreadsheets are 1-based).
    """
    return int(idx) + 2


def _filename(ctx: RuleContext) -> str:
    """Return the `referencia_temporal` file name as delivered (e.g. `"referencia_temporal.xlsx"`)."""
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


@TEMPORAL_REGISTRY.rule(rule_id="TEMP-001", category=NamesEnum.MAND_PUNC_TEMP.value, requires={_SHEET: ()})
def check_description_ends_with_period(ctx: RuleContext) -> list[Issue]:
    """TEMP-001: `descricao` must end with a period.

    Missing-column and every violation are reported as **warnings**, matching
    `validate_punctuation`'s own severity (it only ever returns `([], warnings)`).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _DESCRIPTION not in frame.columns:
        return [
            _missing_column_issue("TEMP-001", Severity.WARNING, NamesEnum.MAND_PUNC_TEMP.value, filename, _DESCRIPTION)
        ]

    series = frame[_DESCRIPTION]
    mask = series.notna() & (series != "")
    if not mask.any():
        return []

    text = series[mask].astype(str).str.strip()
    not_ends_with_dot = ~text.str.endswith(".")
    return [
        Issue(
            rule_id="TEMP-001",
            severity=Severity.WARNING,
            sheet=filename,
            row=int(idx),
            column=_DESCRIPTION,
            message_key="rule.TEMP-001.warning",
            params={"filename": filename, "row": _excel_row(idx), "column": _DESCRIPTION},
            category=NamesEnum.MAND_PUNC_TEMP.value,
        )
        for idx in text.index[not_ends_with_dot]
    ]


def _future_year_issues(ctx: RuleContext, frame: pd.DataFrame, filename: str) -> list[Issue]:
    """TEMP-002's past-year violations, over the sheet's distinct `simbolo` values.

    Excludes the first row (the present-time reference, matching
    `validate_reference_years`'s `.iloc[1:]`), then keeps only the distinct remaining values, in
    first-occurrence order (matching `Series.unique()`). A value that does not parse as a
    non-negative integer is silently excluded from the violation mask (BUG-007) rather than
    raising or being reported here.
    """
    raw_symbols = frame[_SYMBOL].iloc[1:]
    if raw_symbols.empty:
        return []

    unique_symbols = raw_symbols.drop_duplicates()
    numeric = pd.to_numeric(unique_symbols.astype(str).str.replace(",", ".", regex=False), errors="coerce")
    is_valid_non_negative_integer = numeric.notna() & (numeric % 1 == 0) & (numeric >= 0)
    is_past_year = numeric < ctx.clock().year
    violation_mask = is_valid_non_negative_integer & is_past_year

    return [
        Issue(
            rule_id="TEMP-002",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=_SYMBOL,
            message_key="rule.TEMP-002.error",
            params={"filename": filename, "year": unique_symbols.loc[idx]},
            category=NamesEnum.YEARS_TEMP.value,
        )
        for idx in unique_symbols.index[violation_mask]
    ]


@TEMPORAL_REGISTRY.rule(rule_id="TEMP-002", category=NamesEnum.YEARS_TEMP.value, requires={_SHEET: ()})
def check_reference_years_are_future(ctx: RuleContext) -> list[Issue]:
    """TEMP-002: every distinct `simbolo` (excluding the present-time row) must be a future year.

    "Future" means `>= ctx.clock().year` — a symbol equal to the current year passes (see
    `.specs/business-rules/temporal-reference.md`'s TEMP-002 entry). The missing-column case
    aborts immediately (matches `validate_reference_years`'s early `return errors, []`).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _SYMBOL not in frame.columns:
        return [_missing_column_issue("TEMP-002", Severity.ERROR, NamesEnum.YEARS_TEMP.value, filename, _SYMBOL)]

    return _future_year_issues(ctx, frame, filename)


@TEMPORAL_REGISTRY.rule(rule_id="TEMP-003", category=NamesEnum.UVR_TEMP.value, requires={_SHEET: ()})
def check_name_and_symbol_are_unique(ctx: RuleContext) -> list[Issue]:
    """TEMP-003: `nome` and `simbolo` must each contain no duplicated value.

    Both columns are checked for a missing-column abort first (in `nome`, `simbolo` order),
    then each existing column is checked for uniqueness independently — matches
    `validate_unique_values`'s own two-phase shape (its missing-column loop runs to completion,
    then `DataFrameProcessing.check_dataframe_unique_values` runs over whichever columns exist).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    issues: list[Issue] = [
        _missing_column_issue("TEMP-003", Severity.ERROR, NamesEnum.UVR_TEMP.value, filename, column)
        for column in (_NAME, _SYMBOL)
        if column not in frame.columns
    ]

    for column in (_NAME, _SYMBOL):
        if column not in frame.columns or frame[column].is_unique:
            continue
        issues.append(
            Issue(
                rule_id="TEMP-003",
                severity=Severity.ERROR,
                sheet=filename,
                row=None,
                column=column,
                message_key="rule.TEMP-003.error",
                params={"filename": filename, "column": column},
                category=NamesEnum.UVR_TEMP.value,
            )
        )
    return issues
