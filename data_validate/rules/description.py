#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""DESC-001…010: the `descricao` content rules (ARC-017 Phase 3 Port 2, ADR-0006).

Ports `validators/spreadsheets/description/description_validator.py::SpDescriptionValidator`'s
nine checks (HTML in the simple description, sequential/unique codes, ABNT capitalisation,
indicator levels, punctuation, empty fields, CR/LF characters, simple-description and title
length) onto the `rules` engine, one `RuleSpec` per `DESC-*` id documented in
`.specs/business-rules/description.md`. `DESC-011`/`DESC-012` (the `cenario`/`legenda`
dynamic-column checks) stay in `models/sp_description.py::SpDescription.pre_processing` — they
run before this module's rules even see a frame (they decide whether the columns exist at all)
and are out of this port's scope.

i18n (ARC-005): every message this module emits is a catalog key
(`static/locales/<locale>/messages.json`), never an inline string — a rule builds an `Issue`
carrying `message_key`/`params`; `data_validate.rules.legacy_adapter.extend_report_from_outcomes`
renders it via `ctx.translate`. The "required column is missing" abort — produced today by
`helpers/common/validation/dataframe_processing.py::DataFrameProcessing.column_exists` as a
hardcoded Portuguese string — is reproduced here as its own catalog key,
`rule.description.missing_required_column`, shared by every rule in this module (it is one
message template, not ten): each call site still chooses this rule's own severity so the
message lands in the same errors/warnings list the legacy validator put it in (see
`_missing_column_issue`, and each rule's docstring for which list that is).

PERF-001: `check_html_in_simple_description` and `check_indicator_levels` replace the legacy
`iterrows()` loops with a `.str.contains`/`pd.to_numeric` mask (`.claude/skills/
pandas-vectorization/SKILL.md` patterns 1 and 2); every other rule below was already
vectorised in the legacy validator (or its `character_processing.py`/`dataframe_processing.py`
helpers) and is reproduced with the same shape, minus the final string-building step (an `Issue`
now, not an f-string).

Depends only on `data_validate.rules`/`data_validate.specs`, `pandas`, and
`helpers.common.formatting.text_formatting_processing.TextFormattingProcessing` (a pure text
transform with no message text of its own) — never on `models` or the hardcoded-string-building
helpers (`character_processing.py`, `dataframe_processing.py`'s message-building functions),
per `.claude/rules/architecture-boundaries.md`; those helpers stay in place for the
`cenarios`/`referencia_temporal` validators that still use them and are out of this port's scope.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.helpers.common.formatting.text_formatting_processing import TextFormattingProcessing
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

DESCRIPTION_REGISTRY = RuleRegistry()
"""Every `DESC-*` rule ported from `SpDescriptionValidator`, in the legacy check order."""

_SHEET = "descricao"

_CODE = "codigo"
_LEVEL = "nivel"
_SIMPLE_NAME = "nome_simples"
_COMPLETE_NAME = "nome_completo"
_SIMPLE_DESC = "desc_simples"
_COMPLETE_DESC = "desc_completa"

_NO_PUNCTUATION_COLUMNS: tuple[str, ...] = (_SIMPLE_NAME, _COMPLETE_NAME)
_MUST_END_WITH_DOT_COLUMNS: tuple[str, ...] = (_SIMPLE_DESC, _COMPLETE_DESC)
_PUNCTUATION_CHARS = frozenset(",.;:!?")

_CR = "\x0d"
_LF = "\x0a"

_MISSING_COLUMN_KEY = "rule.description.missing_required_column"


def _excel_row(idx: int) -> int:
    """Convert a 0-based `descricao` row index into the 1-based row a user sees in Excel.

    `descricao` is a single-header sheet (`.claude/rules/dataframe-conventions.md`): the
    spreadsheet row is the data index plus 2 (one for the header row, one because spreadsheets
    are 1-based). A generic, per-sheet-kind `excel_row(idx, sheet_name)` helper is reserved for
    when a second sheet's rules are ported (composition, values, ...); this module only ever
    deals with `descricao`, so a private single-header conversion is enough for now.

    Args:
        idx: 0-based position in the sheet's data rows (excluding the header row).

    Returns:
        int: The 1-based row number as shown in Excel/LibreOffice.
    """
    return int(idx) + 2


def _option_str_tuple(ctx: RuleContext, key: str) -> tuple[str, ...]:
    """Read `ctx.options[key]` as a tuple of `str`, treating a non-iterable value as empty.

    `RuleContext.options` is an untyped `Mapping[str, object]` (`.claude/rules/coding-standards.md`
    forbids inventing a stronger contract this slice does not need yet); this narrows one option
    to the shape `check_no_cr_lf_characters` actually needs, satisfying `mypy --strict` without a
    blanket `# type: ignore`.
    """
    value = ctx.options.get(key, ())
    if isinstance(value, str) or not isinstance(value, Iterable):
        return ()
    return tuple(str(item) for item in value)


def _option_int(ctx: RuleContext, key: str, default: int) -> int:
    """Read `ctx.options[key]` as an `int`, falling back to `default` when absent/invalid."""
    value = ctx.options.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _filename(ctx: RuleContext) -> str:
    """Return the `descricao` file name as delivered (e.g. `"descricao.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and _SHEET in filenames:
        return str(filenames[_SHEET])
    return _SHEET


def _cleaned_column(ctx: RuleContext, column: str) -> pd.Series:
    """Return `ctx.cleaned["descricao"][column]`, or an empty `Series` when absent."""
    sheet_cleaned = ctx.cleaned.get(_SHEET, {})
    return sheet_cleaned.get(column, pd.Series(dtype="object"))


def _missing_column_issue(
    rule_id: str,
    severity: Severity,
    category: str,
    filename: str,
    column: str,
) -> Issue:
    """Build the "required column is missing" abort `Issue` shared by every rule below.

    Reproduces `DataFrameProcessing.column_exists`'s single-header message text (`.claude/rules/
    dataframe-conventions.md`), rendered through the shared `rule.description.missing_
    required_column` catalog key instead of being built as an f-string.

    Args:
        rule_id: The rule reporting the missing column (e.g. `"DESC-001"`).
        severity: The severity the legacy validator used for this rule's abort case — this
            varies per rule (some report it as an error, some as a warning; see each rule's
            docstring), even though the message text is the same for all of them.
        category: The legacy `NamesEnum` report bucket this rule belongs to.
        filename: The `descricao` file name, as delivered.
        column: The missing column's name.

    Returns:
        Issue: A sheet-level (no row) issue carrying the shared missing-column message key.
    """
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


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-001", category=NamesEnum.HTML_DESC.value, requires={_SHEET: ()})
def check_html_in_simple_description(ctx: RuleContext) -> list[Issue]:
    """DESC-001: `desc_simples` must not contain HTML tags.

    The missing-column case is reported as an **error** (matches
    `SpDescriptionValidator.validate_html_in_descriptions`'s `return [msg_error_column], []`),
    even though a found HTML tag itself is a warning.
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _SIMPLE_DESC not in frame.columns:
        return [_missing_column_issue("DESC-001", Severity.ERROR, NamesEnum.HTML_DESC.value, filename, _SIMPLE_DESC)]

    has_html = frame[_SIMPLE_DESC].astype(str).str.contains(r"<.*?>", regex=True, na=False)
    return [
        Issue(
            rule_id="DESC-001",
            severity=Severity.WARNING,
            sheet=filename,
            row=int(idx),
            column=_SIMPLE_DESC,
            message_key="rule.DESC-001.warning",
            params={"filename": filename, "row": _excel_row(idx), "column": _SIMPLE_DESC},
            category=NamesEnum.HTML_DESC.value,
        )
        for idx in frame.index[has_html]
    ]


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-002", category=NamesEnum.SC.value, requires={_SHEET: ()})
def check_sequential_codes(ctx: RuleContext) -> list[Issue]:
    """DESC-002: `codigo` must equal `1, 2, ..., n` after cleaning.

    Reads the model's own cleaned `codigo` (`ctx.cleaned["descricao"]["codigo"]`, populated by
    `SpDescription.data_cleaning`, BUG-002); a size mismatch against the raw column means at
    least one cell was not a valid integer, and aborts with a single error before either of the
    two more specific checks run (matches `validate_sequential_codes`'s early `return`).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _CODE not in frame.columns:
        return [_missing_column_issue("DESC-002", Severity.ERROR, NamesEnum.SC.value, filename, _CODE)]

    cleaned = _cleaned_column(ctx, _CODE)
    if len(cleaned) != len(frame):
        return [
            Issue(
                rule_id="DESC-002",
                severity=Severity.ERROR,
                sheet=filename,
                row=None,
                column=_CODE,
                message_key="rule.DESC-002.non_numeric",
                params={"filename": filename, "column": _CODE},
                category=NamesEnum.SC.value,
            )
        ]

    issues: list[Issue] = []
    if cleaned.iloc[0] != 1:
        issues.append(
            Issue(
                rule_id="DESC-002",
                severity=Severity.ERROR,
                sheet=filename,
                row=None,
                column=_CODE,
                message_key="rule.DESC-002.must_start_at_one",
                params={"filename": filename, "column": _CODE},
                category=NamesEnum.SC.value,
            )
        )

    if list(cleaned) != list(range(1, len(cleaned) + 1)):
        issues.append(
            Issue(
                rule_id="DESC-002",
                severity=Severity.ERROR,
                sheet=filename,
                row=None,
                column=_CODE,
                message_key="rule.DESC-002.must_be_sequential",
                params={"filename": filename, "column": _CODE},
                category=NamesEnum.SC.value,
            )
        )
    return issues


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-003", category=NamesEnum.CO_UN.value, requires={_SHEET: ()})
def check_unique_codes(ctx: RuleContext) -> list[Issue]:
    """DESC-003: `codigo` must contain no duplicated value, after cleaning."""
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _CODE not in frame.columns:
        return [_missing_column_issue("DESC-003", Severity.ERROR, NamesEnum.CO_UN.value, filename, _CODE)]

    cleaned = _cleaned_column(ctx, _CODE)
    duplicated_codes = cleaned[cleaned.duplicated()].tolist()
    if not duplicated_codes:
        return []
    return [
        Issue(
            rule_id="DESC-003",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=_CODE,
            message_key="rule.DESC-003.error",
            params={"filename": filename, "column": _CODE, "duplicated_codes": str(duplicated_codes)},
            category=NamesEnum.CO_UN.value,
        )
    ]


def _capitalization_issues_for_column(ctx: RuleContext, filename: str, column: str) -> list[Issue]:
    """Every DESC-004 mismatch for one name column, in row order."""
    frame = ctx.sheet(_SHEET)
    series = frame[column]

    mask = series.notna() & (series != "")
    if not mask.any():
        return []

    filtered = series[mask].astype(str)
    original_series = (
        filtered.str.replace("  ", " (EXTRA_SPACE)", regex=False)
        .str.replace("\r", "(CR)", regex=False)
        .str.replace("\n", "(LF)", regex=False)
        .str.replace(_CR, "(CR)", regex=False)
        .str.replace(_LF, "(LF)", regex=False)
    )
    expected_series = (
        filtered.str.replace("\r", "", regex=False)
        .str.replace("\n", "", regex=False)
        .str.replace(_CR, "", regex=False)
        .str.replace(_LF, "", regex=False)
        .str.strip()
        .apply(lambda text: TextFormattingProcessing.capitalize_text_keep_acronyms(text.strip()))
    )

    mismatch = original_series != expected_series
    return [
        Issue(
            rule_id="DESC-004",
            severity=Severity.WARNING,
            sheet=filename,
            row=int(idx),
            column=column,
            message_key="rule.DESC-004.warning",
            params={
                "filename": filename,
                "row": _excel_row(idx),
                "column": column,
                "expected_text": expected_series.loc[idx],
                "original_text": original_series.loc[idx],
            },
            category=NamesEnum.INP.value,
        )
        for idx in original_series.index[mismatch]
    ]


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-004", category=NamesEnum.INP.value, requires={_SHEET: ()})
def check_name_capitalization(ctx: RuleContext) -> list[Issue]:
    """DESC-004: `nome_simples`/`nome_completo` follow ABNT capitalisation, no stray whitespace.

    Each column is checked independently, in order: a missing column reports its own
    missing-column warning and does **not** stop the other column from being checked (matches
    `validate_text_capitalization`'s `continue`, not a `return`).
    """
    filename = _filename(ctx)
    frame = ctx.sheet(_SHEET)

    issues: list[Issue] = []
    for column in (_SIMPLE_NAME, _COMPLETE_NAME):
        if column not in frame.columns:
            issues.append(_missing_column_issue("DESC-004", Severity.WARNING, NamesEnum.INP.value, filename, column))
            continue
        issues.extend(_capitalization_issues_for_column(ctx, filename, column))
    return issues


def _numeric_with_comma_decimals(series: pd.Series) -> pd.Series:
    """Coerce `series` to numeric, tolerant of comma decimals (`"1,0"`) like `check_cell_integer`."""
    normalized = series.astype(str).str.strip().str.replace(",", ".", regex=False)
    return pd.to_numeric(normalized, errors="coerce")


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-005", category=NamesEnum.IL.value, requires={_SHEET: ()})
def check_indicator_levels(ctx: RuleContext) -> list[Issue]:
    """DESC-005: `nivel` must parse as an integer >= 1.

    Vectorised (PERF-001) replacement for the legacy per-cell
    `NumberFormattingProcessing.check_cell_integer(level, min_value=1)` loop: a cell is invalid
    exactly when it is not numeric (comma decimals such as `"1,0"` are still accepted, matching
    `check_cell_integer`'s `parse_numeric`), has a fractional part, or is below `1`.
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if _LEVEL not in frame.columns:
        return [_missing_column_issue("DESC-005", Severity.ERROR, NamesEnum.IL.value, filename, _LEVEL)]

    numeric_levels = _numeric_with_comma_decimals(frame[_LEVEL])
    invalid_mask = numeric_levels.isna() | (numeric_levels < 1) | (numeric_levels % 1 != 0)

    return [
        Issue(
            rule_id="DESC-005",
            severity=Severity.ERROR,
            sheet=filename,
            row=int(idx),
            column=_LEVEL,
            message_key="rule.DESC-005.error",
            params={"filename": filename, "row": _excel_row(idx), "column": _LEVEL},
            category=NamesEnum.IL.value,
        )
        for idx in frame.index[invalid_mask]
    ]


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-006", category=NamesEnum.MAND_PUNC_DESC.value, requires={_SHEET: ()})
def check_punctuation(ctx: RuleContext) -> list[Issue]:
    """DESC-006: names never end with punctuation; descriptions end with a period.

    Missing columns are reported first, for all four columns in
    `_NO_PUNCTUATION_COLUMNS + _MUST_END_WITH_DOT_COLUMNS` order, before any violation is
    checked — matches `validate_punctuation`'s own two-phase shape (its missing-column loop
    runs to completion, then `CharacterProcessing.check_characters_punctuation_rules` runs over
    whichever columns exist).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    issues: list[Issue] = []
    for column in _NO_PUNCTUATION_COLUMNS + _MUST_END_WITH_DOT_COLUMNS:
        if column not in frame.columns:
            issues.append(
                _missing_column_issue("DESC-006", Severity.WARNING, NamesEnum.MAND_PUNC_DESC.value, filename, column)
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
                    rule_id="DESC-006",
                    severity=Severity.WARNING,
                    sheet=filename,
                    row=int(idx),
                    column=column,
                    message_key="rule.DESC-006.no_punctuation",
                    params={"filename": filename, "row": _excel_row(idx), "column": column},
                    category=NamesEnum.MAND_PUNC_DESC.value,
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
                    rule_id="DESC-006",
                    severity=Severity.WARNING,
                    sheet=filename,
                    row=int(idx),
                    column=column,
                    message_key="rule.DESC-006.must_end_with_dot",
                    params={"filename": filename, "row": _excel_row(idx), "column": column},
                    category=NamesEnum.MAND_PUNC_DESC.value,
                )
            )

    return issues


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-007", category=NamesEnum.EF.value, requires={_SHEET: ()})
def check_empty_strings(ctx: RuleContext) -> list[Issue]:
    """DESC-007: names and descriptions must never be null or the empty string."""
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    issues: list[Issue] = []
    for column in (_SIMPLE_NAME, _COMPLETE_NAME, _SIMPLE_DESC, _COMPLETE_DESC):
        if column not in frame.columns:
            issues.append(_missing_column_issue("DESC-007", Severity.ERROR, NamesEnum.EF.value, filename, column))
            continue
        series = frame[column]
        empty_mask = series.isna() | (series == "")
        for idx in frame.index[empty_mask]:
            issues.append(
                Issue(
                    rule_id="DESC-007",
                    severity=Severity.ERROR,
                    sheet=filename,
                    row=int(idx),
                    column=column,
                    message_key="rule.DESC-007.error",
                    params={"filename": filename, "row": _excel_row(idx), "column": column},
                    category=NamesEnum.EF.value,
                )
            )
    return issues


def _cr_lf_start_end_issues(filename: str, frame: pd.DataFrame, columns_start_end: tuple[str, ...]) -> list[Issue]:
    """DESC-008's start/end violations, column by column, `end` then `start`, `CR` then `LF`."""
    issues: list[Issue] = []
    for column in columns_start_end:
        if column not in frame.columns:
            continue
        series = frame[column]
        mask = series.notna() & (series != "")
        if not mask.any():
            continue
        text = series[mask].astype(str)

        for char_type, char, slug in (("CR", _CR, "end"), ("LF", _LF, "end")):
            for idx in text.index[text.str.endswith(char)]:
                issues.append(_cr_lf_issue(filename, column, idx, char_type, slug))
        for char_type, char, slug in (("CR", _CR, "start"), ("LF", _LF, "start")):
            for idx in text.index[text.str.startswith(char)]:
                issues.append(_cr_lf_issue(filename, column, idx, char_type, slug))
    return issues


def _cr_lf_issue(filename: str, column: str, idx: int, char_type: str, slug: str) -> Issue:
    """Build one DESC-008 `start`/`end` `Issue`."""
    return Issue(
        rule_id="DESC-008",
        severity=Severity.WARNING,
        sheet=filename,
        row=int(idx),
        column=column,
        message_key=f"rule.DESC-008.{slug}",
        params={"filename": filename, "row": _excel_row(idx), "column": column, "char_type": char_type},
        category=NamesEnum.LB_DESC.value,
    )


def _cr_lf_anywhere_issues(filename: str, frame: pd.DataFrame, columns_anywhere: tuple[str, ...]) -> list[Issue]:
    """DESC-008's "anywhere in the text" violations, column by column, position 1-based."""
    issues: list[Issue] = []
    for column in columns_anywhere:
        if column not in frame.columns:
            continue
        series = frame[column]
        mask = series.notna() & (series != "")
        if not mask.any():
            continue
        text = series[mask].astype(str)
        contains_cr_lf = text.str.contains(r"[\x0d\x0a]", regex=True)
        for idx in text.index[contains_cr_lf]:
            value = text.loc[idx]
            for match in re.finditer(r"[\x0d\x0a]", value):
                char_type = "CR" if match.group() == _CR else "LF"
                issues.append(
                    Issue(
                        rule_id="DESC-008",
                        severity=Severity.WARNING,
                        sheet=filename,
                        row=int(idx),
                        column=column,
                        message_key="rule.DESC-008.anywhere",
                        params={
                            "filename": filename,
                            "row": _excel_row(idx),
                            "column": column,
                            "char_type": char_type,
                            "position": match.start() + 1,
                        },
                        category=NamesEnum.LB_DESC.value,
                    )
                )
    return issues


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-008", category=NamesEnum.LB_DESC.value, requires={_SHEET: ()})
def check_no_cr_lf_characters(ctx: RuleContext) -> list[Issue]:
    """DESC-008: no CR/LF at the start/end of any expected column, nor anywhere in the names.

    `columns_start_end` is `ctx.options["expected_columns"]` — the model's own, per-run
    `SpDescription.EXPECTED_COLUMNS` (dynamic: it may or may not include `cenario`/`legenda`/the
    optional columns), passed in by the caller rather than recomputed here. Missing-column
    warnings are reported first, for the merged, de-duplicated `columns_anywhere +
    columns_start_end` list, before any violation is checked (matches
    `validate_cr_lf_characters`'s own shape).
    """
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)
    columns_start_end = _option_str_tuple(ctx, "expected_columns")
    columns_anywhere = (_SIMPLE_NAME, _COMPLETE_NAME)

    columns_to_check = list(dict.fromkeys((*columns_anywhere, *columns_start_end)))

    issues: list[Issue] = []
    for column in columns_to_check:
        if column not in frame.columns:
            issues.append(
                _missing_column_issue("DESC-008", Severity.WARNING, NamesEnum.LB_DESC.value, filename, column)
            )

    issues.extend(_cr_lf_start_end_issues(filename, frame, columns_start_end))
    issues.extend(_cr_lf_anywhere_issues(filename, frame, columns_anywhere))
    return issues


def _check_text_length(
    ctx: RuleContext,
    *,
    rule_id: str,
    column: str,
    category: str,
    max_length_option: str,
    message_key: str,
) -> list[Issue]:
    """Shared body for DESC-009/DESC-010: both check one column's length the same way."""
    frame = ctx.sheet(_SHEET)
    filename = _filename(ctx)

    if column not in frame.columns:
        return [_missing_column_issue(rule_id, Severity.WARNING, category, filename, column)]

    max_length = _option_int(ctx, max_length_option, default=0)
    series = frame[column]
    non_null = series.notna()
    lengths = series[non_null].astype(str).str.len()
    exceeds_limit = lengths > max_length

    return [
        Issue(
            rule_id=rule_id,
            severity=Severity.WARNING,
            sheet=filename,
            row=int(idx),
            column=column,
            message_key=message_key,
            params={
                "filename": filename,
                "row": _excel_row(idx),
                "column": column,
                "max_length": max_length,
                "actual_length": int(lengths.loc[idx]),
            },
            category=category,
        )
        for idx in lengths.index[exceeds_limit]
    ]


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-009", category=NamesEnum.SIMP_DESC_N.value, requires={_SHEET: ()})
def check_simple_description_length(ctx: RuleContext) -> list[Issue]:
    """DESC-009: `desc_simples` must be at most `ctx.options["simple_desc_max_length"]` characters."""
    return _check_text_length(
        ctx,
        rule_id="DESC-009",
        column=_SIMPLE_DESC,
        category=NamesEnum.SIMP_DESC_N.value,
        max_length_option="simple_desc_max_length",
        message_key="rule.DESC-009.warning",
    )


@DESCRIPTION_REGISTRY.rule(rule_id="DESC-010", category=NamesEnum.TITLES_N.value, requires={_SHEET: ()})
def check_title_length(ctx: RuleContext) -> list[Issue]:
    """DESC-010: `nome_simples` must be at most `ctx.options["title_max_length"]` characters.

    Returns no issues at all when `ctx.options["no_warning_titles_length"]` is set — the
    `--no-warning-titles-length` CLI flag — matching the legacy validator not even registering
    this check in that case; the report still labels the "Titles over N characters" section as
    skipped, independently of this rule, via `FileReportGenerator` (see `.specs/business-rules/
    description.md`'s DESC-010 entry).
    """
    if ctx.options.get("no_warning_titles_length"):
        return []
    return _check_text_length(
        ctx,
        rule_id="DESC-010",
        column=_SIMPLE_NAME,
        category=NamesEnum.TITLES_N.value,
        max_length_option="title_max_length",
        message_key="rule.DESC-010.warning",
    )
