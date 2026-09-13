#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""PROP-003…010: the `proporcionalidades` content rules (ARC-017 Phase 3 Port 7, ADR-0006).

Ports `validators/spreadsheets/proportionality/proportionality_validator.py::
SpProportionalityValidator`'s five checks onto the `rules` engine, one `RuleSpec` per
`validate_*` method documented in `.specs/business-rules/proportionality.md`
(`PROP-001`/`PROP-002` are the header/structural checks that stay in
`models/sp_proportionality.py`, out of this port's scope):

- `validate_relation_indicators_in_proportionality` → PROP-003 (IR).
- `validate_columns_repeated_indicators` → PROP-004 (REP_IND_PROP).
- `validate_relation_indicators_in_value_and_proportionality` → PROP-005 (IND_VAL_PROP).
- `validate_parent_child_relationships` → PROP-006 (IR_PROP).
- `validate_sum_properties_in_influencing_factors`/`_check_sum_equals_one` → PROP-007…010
  (SUM_PROP: numeric format, excessive decimals, zero-sum rows, sum tolerance).

One legacy method, one `RuleSpec`, several rule IDs on its `Issue`s: PROP-007…010 all share
`NamesEnum.SUM_PROP` (the legacy `_check_sum_equals_one` orchestration already emits every one of
these four statements from a single pass over each parent's subdataset — there is no natural place
to split it into four independent prerequisite-checked entries the way `rules/value.py`'s
VAL-004/VAL-005 or `rules/legend.py`'s LEG-012/013/014 do for a *shared category*), so
`check_sum_properties_in_influencing_factors` is registered once, under `rule_id="PROP-007"`, and
tags each individual finding with its own specific `PROP-0XX` id for spec traceability.

The outer `if self._dataframe.empty: set_not_executed(...)` gate every legacy check shared (the
proportionality sheet is empty or its header layout was structurally invalid,
`models/sp_proportionality.py::SpProportionality.post_processing`) maps onto
`requires={_PROPORTIONALITY_SHEET: ()}` on every `RuleSpec` below, plus each rule's own additional
sheet requirement (`descricao`/`valores`/`composicao`) — an engine `SKIPPED` outcome is exactly what
the legacy `set_not_executed` no-op already meant (see `base_validator.py::set_not_executed`).

PROP-006 (`check_parent_child_relationships`) reproduces `validate_parent_child_relationships`'s
final `errors = sorted(set(errors))` step without ever rendering the Portuguese sentences it used
to sort: the three message shapes it can produce ("Deve existir…" / "O indicador '…" / "O indicador
pai '…") never share a common prefix beyond the sheet name, so their *relative* order is fixed
(`'D' < "'" < 'p'` — child-missing, then child-mismatch, then parent-missing, regardless of any
interpolated value) and is reproduced here as three fixed-order buckets, each internally sorted by
the exact tuple of fields that appear, in order, inside its own message template — this reproduces
`sorted(set(errors))`'s final string order using only structured data, never building message text
in rule code (`.claude/rules/i18n.md`).

PERF-001: `validate_parent_child_relationships`'s `for __, row in df_composition.iterrows(): ...`
(building a `codigo_pai -> [codigo_filho, …]` dict) is replaced by
`df_composition.groupby(_PARENT, sort=False)[_CHILD].apply(list)` — no `.iterrows()`
(`.claude/rules/dataframe-conventions.md`). `ProportionalityProcessing` (`helpers/common/
validation/proportionality_processing.py`) keeps every pure, frame-level helper
(`build_subdatasets`, decimal truncation/summation) but no longer builds message text itself — see
its own module docstring.

i18n (ARC-005): every message this module emits is a catalog key, never an inline string; the
shared "required column is missing" abort reuses `rule.proportionality.missing_required_column`/
`_level2`, matching `rules/composition.py`'s precedent for a `MultiIndex` sheet's own column.
PROP-006's three message shapes get one key each (`parent_missing`/`child_mismatch`/
`child_missing`); PROP-007's single-vs-aggregate and PROP-008's singular-vs-plural cases each get
their own key, matching `rules/value.py`'s VAL-004/VAL-005 precedent.

Depends only on `data_validate.rules`/`data_validate.specs`, `pandas`, and the pure
`CollectionsProcessing`/`DataCleaningProcessing`/`DataFrameProcessing`/`DescriptionProcessing`/
`NumberFormattingProcessing`/`ProportionalityProcessing` helpers — never on `models`, per
`.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing
from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.common.validation.description_processing import DescriptionProcessing
from data_validate.helpers.common.validation.proportionality_processing import ProportionalityProcessing
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

PROPORTIONALITY_REGISTRY = RuleRegistry()
"""Every `PROP-*` rule ported from `SpProportionalityValidator`, in the legacy check order."""

_PROPORTIONALITY_SHEET = "proporcionalidades"
_DESCRIPTION_SHEET = "descricao"
_VALUES_SHEET = "valores"
_COMPOSITION_SHEET = "composicao"

_ID = "id"
_CODE = "codigo"
_LEVEL = "nivel"
_SCENARIO_COLUMN = "cenario"
_PARENT = "codigo_pai"
_CHILD = "codigo_filho"

_MISSING_COLUMN_KEY = "rule.proportionality.missing_required_column"
_MISSING_COLUMN_LEVEL2_KEY = "rule.proportionality.missing_required_column_level2"


def _filename(ctx: RuleContext, sheet: str) -> str:
    """Return `sheet`'s display file name, as delivered (e.g. `"proporcionalidades.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and sheet in filenames:
        return str(filenames[sheet])
    return sheet


def _scenario_symbols(ctx: RuleContext) -> list[str]:
    """Return `ctx.options["scenarios"]` as a `list[str]`, or `[]` when absent/not a list."""
    value = ctx.options.get("scenarios", [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _value_data_unavailable(ctx: RuleContext) -> str:
    """Return `ctx.options["value_data_unavailable"]`, defaulting to `"DI"`."""
    return str(ctx.options.get("value_data_unavailable", "DI"))


def _precision(ctx: RuleContext) -> int:
    """Return `ctx.options["precision_decimal_place_truncate"]`, defaulting to `3`."""
    value = ctx.options.get("precision_decimal_place_truncate", 3)
    if isinstance(value, int):
        return value
    return 3


def _current_language(ctx: RuleContext) -> str:
    """Return `ctx.options["current_language"]`, defaulting to `"pt_BR"`."""
    return str(ctx.options.get("current_language", "pt_BR"))


def _proportionality_missing_id(frame: pd.DataFrame) -> bool:
    """Return whether `frame` (the `proporcionalidades` sheet) lacks an `id` column.

    Checks level 1 of a `MultiIndex` (the real, double-header shape every model-level frame
    has), falling back to a flat column check so a rule-level test can pass a plain frame too.
    """
    if isinstance(frame.columns, pd.MultiIndex):
        return _ID not in frame.columns.get_level_values(1)
    return _ID not in frame.columns


def _missing_column_issue(rule_id: str, category: str, filename: str, column: str, *, level2: bool = False) -> Issue:
    """Build the shared "required column is missing" abort `Issue`.

    Every PROP rule reports this abort as an **error**, matching
    `BaseValidator.check_columns_in_models_dataframes`'s callers. `level2=True` renders
    `rule.proportionality.missing_required_column_level2` (the `proporcionalidades` sheet's own
    `id` column, on header row 2), matching `DataFrameProcessing.column_exists`'s `MultiIndex`
    branch text.
    """
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=filename,
        row=None,
        column=column,
        message_key=_MISSING_COLUMN_LEVEL2_KEY if level2 else _MISSING_COLUMN_KEY,
        params={"filename": filename, "column": column},
        category=category,
    )


def _missing_codes_issue(
    rule_id: str, category: str, label_from: str, label_to: str, missing_codes: Iterable[Any]
) -> Issue:
    """Build one "codes missing" `Issue` (one direction of a set comparison), shared by PROP-003
    and PROP-005 — the same shape `rules/value.py`'s VAL-002/`rules/composition.py`'s COMP-001 use.
    """
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=label_from,
        row=None,
        column=None,
        message_key=f"rule.{rule_id}.missing_codes",
        params={"label_from": label_from, "label_to": label_to, "missing_codes": str(sorted(missing_codes))},
        category=category,
    )


# --------------------------------------------------------------------------------------------
# PROP-003: relation indicators in proportionality (IR)
# --------------------------------------------------------------------------------------------


@PROPORTIONALITY_REGISTRY.rule(
    rule_id="PROP-003",
    category=NamesEnum.IR.value,
    requires={_PROPORTIONALITY_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_relation_indicators_in_proportionality(ctx: RuleContext) -> list[Issue]:
    """PROP-003: every `descricao` code (except level 1) must have a match in `proporcionalidades`.

    Skipped entirely when `proporcionalidades` or `descricao` is empty (`requires`, matching
    `validate_relation_indicators_in_proportionality`'s own top-level and inner skips). Aborts
    with one issue per missing column, in `proporcionalidades.id` (level 2), then
    `descricao.codigo`, `descricao.nivel` order, matching
    `check_columns_in_models_dataframes`'s own required-columns dict order.
    """
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    proportionality_frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)
    proportionality_filename = _filename(ctx, _PROPORTIONALITY_SHEET)

    issues: list[Issue] = []
    if _proportionality_missing_id(proportionality_frame):
        issues.append(_missing_column_issue("PROP-003", NamesEnum.IR.value, proportionality_filename, _ID, level2=True))
    issues.extend(
        _missing_column_issue("PROP-003", NamesEnum.IR.value, description_filename, column)
        for column in (_CODE, _LEVEL)
        if column not in description_frame.columns
    )
    if issues:
        return issues

    df_description, _errors = DataCleaningProcessing.clean_dataframe_integers(
        description_frame, description_filename, [_CODE]
    )
    codes_level_one = set(
        df_description[DataFrameProcessing.numeric_equals_mask(df_description[_LEVEL], 1)][_CODE].astype(str).tolist()
    )
    valid_description_codes = DescriptionProcessing.get_valids_codes_from_description(
        description_frame, _LEVEL, _CODE, _SCENARIO_COLUMN
    )

    scenario_symbols = _scenario_symbols(ctx)
    valid_proportionality_codes: set[str] = set()
    for level_values in (
        proportionality_frame.columns.get_level_values(0).unique().tolist(),
        proportionality_frame.columns.get_level_values(1).unique().tolist(),
    ):
        candidates = [column for column in level_values if not column.startswith("Unnamed")]
        matched, _unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
            candidates, scenario_symbols
        )
        cleaned_codes = {str(code).split("-")[0] for code in matched} - codes_level_one
        valid_proportionality_codes |= cleaned_codes

    description_codes = {int(code) for code in valid_description_codes}
    proportionality_codes = {int(code) for code in valid_proportionality_codes}

    missing_in_proportionality, missing_in_description = CollectionsProcessing.find_differences_in_two_set(
        first_set=description_codes, second_set=proportionality_codes
    )

    issues = []
    if missing_in_proportionality:
        issues.append(
            _missing_codes_issue(
                "PROP-003",
                NamesEnum.IR.value,
                description_filename,
                proportionality_filename,
                missing_in_proportionality,
            )
        )
    if missing_in_description:
        issues.append(
            _missing_codes_issue(
                "PROP-003", NamesEnum.IR.value, proportionality_filename, description_filename, missing_in_description
            )
        )
    return issues


# --------------------------------------------------------------------------------------------
# PROP-004: repeated parent indicators (REP_IND_PROP)
# --------------------------------------------------------------------------------------------


def _proportionality_parent_names(frame: pd.DataFrame) -> list[str]:
    """Every level-0 (parent) column name of `frame`, `Unnamed*` placeholders excluded.

    Kept as the raw, non-unique `.tolist()` (not `.unique()`): consecutive repeats of the same
    name are exactly what `CollectionsProcessing.generate_group_from_list` groups, matching
    `validate_columns_repeated_indicators`'s own list.
    """
    return [
        str(column)
        for column in frame.columns.get_level_values(0).tolist()
        if not str(column).lower().startswith("unnamed")
    ]


@PROPORTIONALITY_REGISTRY.rule(
    rule_id="PROP-004", category=NamesEnum.REP_IND_PROP.value, requires={_PROPORTIONALITY_SHEET: ()}
)
def check_columns_repeated_indicators(ctx: RuleContext) -> list[Issue]:
    """PROP-004: a parent indicator must not appear twice (non-consecutively) on header row 1.

    Skipped entirely when `proporcionalidades` is empty (`requires`). Aborts with a missing-`id`
    issue (level 2) when the sheet's own `id` column is absent, matching
    `validate_columns_repeated_indicators`'s own column check.
    """
    frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    filename = _filename(ctx, _PROPORTIONALITY_SHEET)

    if _proportionality_missing_id(frame):
        return [_missing_column_issue("PROP-004", NamesEnum.REP_IND_PROP.value, filename, _ID, level2=True)]

    parent_names = _proportionality_parent_names(frame)
    if not parent_names:
        return []

    grouped_columns = CollectionsProcessing.generate_group_from_list(parent_names)
    seen: set[str] = set()
    repeated: set[str] = set()
    for group in grouped_columns:
        first_element = group[0]
        if first_element in seen:
            repeated.add(first_element)
        else:
            seen.add(first_element)

    return [
        Issue(
            rule_id="PROP-004",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=None,
            message_key="rule.PROP-004.error",
            params={"filename": filename, "parent": parent},
            category=NamesEnum.REP_IND_PROP.value,
        )
        for parent in sorted(repeated)
    ]


# --------------------------------------------------------------------------------------------
# PROP-005: indicator columns must match between proporcionalidades and valores (IND_VAL_PROP)
# --------------------------------------------------------------------------------------------


@PROPORTIONALITY_REGISTRY.rule(
    rule_id="PROP-005",
    category=NamesEnum.IND_VAL_PROP.value,
    requires={_PROPORTIONALITY_SHEET: (), _VALUES_SHEET: ()},
)
def check_relation_indicators_in_value_and_proportionality(ctx: RuleContext) -> list[Issue]:
    """PROP-005: every `proporcionalidades` column name must have a match in `valores`.

    Skipped entirely when `proporcionalidades` or `valores` is empty (`requires`, matching
    `validate_relation_indicators_in_value_and_proportionality`'s own top-level skip). Aborts
    with one issue per missing column, in `proporcionalidades.id` (level 2), then `valores.id`
    order (BUG-006: both sides are guarded here, before any `list`/set manipulation runs).
    """
    proportionality_frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    values_frame = ctx.sheet(_VALUES_SHEET)
    proportionality_filename = _filename(ctx, _PROPORTIONALITY_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)

    issues: list[Issue] = []
    if _proportionality_missing_id(proportionality_frame):
        issues.append(
            _missing_column_issue("PROP-005", NamesEnum.IND_VAL_PROP.value, proportionality_filename, _ID, level2=True)
        )
    if _ID not in values_frame.columns:
        issues.append(_missing_column_issue("PROP-005", NamesEnum.IND_VAL_PROP.value, values_filename, _ID))
    if issues:
        return issues

    level_one = [
        column
        for column in proportionality_frame.columns.get_level_values(0).unique().tolist()
        if not column.lower().startswith("unnamed: 0_level_0")
    ]
    level_two = [
        column for column in proportionality_frame.columns.get_level_values(1).unique().tolist() if column != _ID
    ]
    columns_proportionality = set(level_one) | set(level_two)

    columns_values = {column for column in values_frame.columns.unique().tolist() if column != _ID}

    missing_in_values, missing_in_proportionality = CollectionsProcessing.find_differences_in_two_set(
        first_set=columns_proportionality, second_set=columns_values
    )

    issues = []
    if missing_in_values:
        issues.append(
            _missing_codes_issue(
                "PROP-005",
                NamesEnum.IND_VAL_PROP.value,
                proportionality_filename,
                values_filename,
                missing_in_values,
            )
        )
    if missing_in_proportionality:
        issues.append(
            _missing_codes_issue(
                "PROP-005",
                NamesEnum.IND_VAL_PROP.value,
                values_filename,
                proportionality_filename,
                missing_in_proportionality,
            )
        )
    return issues


# --------------------------------------------------------------------------------------------
# PROP-006: parent/child pairs must agree with composicao (IR_PROP)
# --------------------------------------------------------------------------------------------


def _composition_missing_columns(frame: pd.DataFrame) -> list[str]:
    """Every one of `codigo_pai`/`codigo_filho` missing from `frame`, in that order."""
    return [column for column in (_PARENT, _CHILD) if column not in frame.columns]


@PROPORTIONALITY_REGISTRY.rule(
    rule_id="PROP-006",
    category=NamesEnum.IR_PROP.value,
    requires={_PROPORTIONALITY_SHEET: (), _COMPOSITION_SHEET: ()},
)
def check_parent_child_relationships(ctx: RuleContext) -> list[Issue]:
    """PROP-006: every `proporcionalidades` parent/child pair must agree with `composicao`.

    Skipped entirely when `proporcionalidades` or `composicao` is empty (`requires`, matching
    `validate_parent_child_relationships`'s own top-level skip). Aborts with one issue per
    missing column, in `proporcionalidades.id` (level 2), then `composicao.codigo_pai`,
    `composicao.codigo_filho` order. See this module's docstring for how the three message
    shapes' fixed bucket order reproduces the legacy `sorted(set(errors))` step.
    """
    proportionality_frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    composition_frame = ctx.sheet(_COMPOSITION_SHEET)
    proportionality_filename = _filename(ctx, _PROPORTIONALITY_SHEET)
    composition_filename = _filename(ctx, _COMPOSITION_SHEET)

    issues: list[Issue] = []
    if _proportionality_missing_id(proportionality_frame):
        issues.append(
            _missing_column_issue("PROP-006", NamesEnum.IR_PROP.value, proportionality_filename, _ID, level2=True)
        )
    issues.extend(
        _missing_column_issue("PROP-006", NamesEnum.IR_PROP.value, composition_filename, column)
        for column in _composition_missing_columns(composition_frame)
    )
    if issues:
        return issues

    subdatasets = ProportionalityProcessing.build_subdatasets(proportionality_frame, _ID)
    filtered_composition = composition_frame[DataFrameProcessing.numeric_not_equals_mask(composition_frame[_PARENT], 1)]
    children_by_parent: dict[Any, list[Any]] = {
        parent: group[_CHILD].tolist() for parent, group in filtered_composition.groupby(_PARENT, sort=False)
    }

    parent_missing: set[tuple[str, str]] = set()
    child_mismatch: set[tuple[str, str, str, str]] = set()
    child_missing: set[tuple[str, str, str]] = set()

    for parent_id, subdataset in subdatasets.items():
        cleaned_parent_id = parent_id.split("-")[0]
        if cleaned_parent_id not in children_by_parent:
            if ":" not in parent_id:
                parent_missing.add((cleaned_parent_id, parent_id))
            continue

        children_columns = [
            str(column) for column in subdataset.columns.tolist() if not str(column).lower().startswith(_ID)
        ]
        children_codes = [child.split("-")[0] for child in children_columns]

        for child_code, child_column in zip(children_codes, children_columns):
            if child_code not in children_by_parent[cleaned_parent_id]:
                child_mismatch.add((child_code, child_column, cleaned_parent_id, parent_id))

        for child in children_by_parent[cleaned_parent_id]:
            if child not in children_codes:
                child_missing.add((str(child), cleaned_parent_id, parent_id))

    issues = []
    issues.extend(
        Issue(
            rule_id="PROP-006",
            severity=Severity.ERROR,
            sheet=proportionality_filename,
            row=None,
            column=None,
            message_key="rule.PROP-006.child_missing",
            params={
                "filename": proportionality_filename,
                "child": child,
                "parent": parent,
                "parent_col": parent_col,
                "composicao_filename": composition_filename,
            },
            category=NamesEnum.IR_PROP.value,
        )
        for child, parent, parent_col in sorted(child_missing)
    )
    issues.extend(
        Issue(
            rule_id="PROP-006",
            severity=Severity.ERROR,
            sheet=proportionality_filename,
            row=None,
            column=None,
            message_key="rule.PROP-006.child_mismatch",
            params={
                "filename": proportionality_filename,
                "child": child,
                "child_col": child_col,
                "parent": parent,
                "parent_col": parent_col,
                "composicao_filename": composition_filename,
            },
            category=NamesEnum.IR_PROP.value,
        )
        for child, child_col, parent, parent_col in sorted(child_mismatch)
    )
    issues.extend(
        Issue(
            rule_id="PROP-006",
            severity=Severity.ERROR,
            sheet=proportionality_filename,
            row=None,
            column=None,
            message_key="rule.PROP-006.parent_missing",
            params={
                "filename": proportionality_filename,
                "parent": parent,
                "parent_col": parent_col,
                "composicao_filename": composition_filename,
            },
            category=NamesEnum.IR_PROP.value,
        )
        for parent, parent_col in sorted(parent_missing)
    )
    return issues


# --------------------------------------------------------------------------------------------
# PROP-007…010: sum properties in influencing factors (SUM_PROP)
# --------------------------------------------------------------------------------------------


def _numeric_format_issues(invalid_mask: pd.DataFrame, filename: str, parent_id: str, value_di: str) -> list[Issue]:
    """PROP-007: one issue per parent, single-cell or aggregated, from an invalid-cell mask."""
    if not bool(invalid_mask.to_numpy().any()):
        return []

    rows_with_errors = invalid_mask.any(axis=1)
    error_indices = rows_with_errors[rows_with_errors].index
    count_errors = int(invalid_mask.to_numpy().sum())

    if count_errors == 1:
        row_idx = error_indices[0]
        return [
            Issue(
                rule_id="PROP-007",
                severity=Severity.ERROR,
                sheet=filename,
                row=int(row_idx),
                column=None,
                message_key="rule.PROP-007.error_single",
                params={"filename": filename, "row": int(row_idx) + 3, "value_di": value_di, "parent": parent_id},
                category=NamesEnum.SUM_PROP.value,
            )
        ]

    excel_indices = error_indices + 3
    return [
        Issue(
            rule_id="PROP-007",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=None,
            message_key="rule.PROP-007.error_aggregate",
            params={
                "filename": filename,
                "count": count_errors,
                "value_di": value_di,
                "parent": parent_id,
                "first_row": int(excel_indices.min()),
                "last_row": int(excel_indices.max()),
            },
            category=NamesEnum.SUM_PROP.value,
        )
    ]


def _zero_sum_issue(proportionality_filename: str, values_filename: str, row_id: Any, child_column: str) -> Issue:
    """PROP-009: one issue per `(id, child_column)` zero-sum violation."""
    return Issue(
        rule_id="PROP-009",
        severity=Severity.ERROR,
        sheet=proportionality_filename,
        row=None,
        column=child_column,
        message_key="rule.PROP-009.error",
        params={
            "filename": proportionality_filename,
            "id": row_id,
            "col": child_column,
            "values_filename": values_filename,
        },
        category=NamesEnum.SUM_PROP.value,
    )


def _tolerance_issue(
    severity: Severity,
    message_key: str,
    filename: str,
    idx: int,
    parent_id: str,
    value_sum: Decimal,
    current_language: str,
) -> Issue:
    """PROP-010: one error/warning issue for a row whose sum falls outside/inside the tolerance."""
    formatted_sum = NumberFormattingProcessing.format_number_brazilian(value_sum, current_language)
    return Issue(
        rule_id="PROP-010",
        severity=severity,
        sheet=filename,
        row=int(idx),
        column=None,
        message_key=message_key,
        params={"filename": filename, "row": int(idx) + 3, "parent": parent_id, "sum": formatted_sum},
        category=NamesEnum.SUM_PROP.value,
    )


@PROPORTIONALITY_REGISTRY.rule(
    rule_id="PROP-007",
    category=NamesEnum.SUM_PROP.value,
    requires={_PROPORTIONALITY_SHEET: (), _VALUES_SHEET: ()},
)
def check_sum_properties_in_influencing_factors(ctx: RuleContext) -> list[Issue]:
    """PROP-007…010: `proporcionalidades` factors must be numeric/DI and sum to 1 per parent/row.

    Skipped entirely when `proporcionalidades` or `valores` is empty (`requires`, matching
    `validate_sum_properties_in_influencing_factors`'s own top-level skip). Owns the shared
    missing-column abort for the whole `SUM_PROP` category (one legacy method,
    `_check_sum_equals_one`, one `RuleSpec` — see this module's docstring); every `Issue` it
    emits still carries its own specific `PROP-0XX` id (007 numeric-format error, 008 excessive-
    decimals warning aggregated across every parent, 009 zero-sum-row error, 010 sum-tolerance
    error/warning) for traceability with `.specs/business-rules/proportionality.md`.
    """
    proportionality_frame = ctx.sheet(_PROPORTIONALITY_SHEET)
    values_frame = ctx.sheet(_VALUES_SHEET)
    proportionality_filename = _filename(ctx, _PROPORTIONALITY_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)

    issues: list[Issue] = []
    if _proportionality_missing_id(proportionality_frame):
        issues.append(
            _missing_column_issue("PROP-007", NamesEnum.SUM_PROP.value, proportionality_filename, _ID, level2=True)
        )
    if _ID not in values_frame.columns:
        issues.append(_missing_column_issue("PROP-007", NamesEnum.SUM_PROP.value, values_filename, _ID))
    if issues:
        return issues

    value_di = _value_data_unavailable(ctx)
    precision = _precision(ctx)
    current_language = _current_language(ctx)

    subdatasets = ProportionalityProcessing.build_subdatasets(proportionality_frame, _ID)

    issues = []
    excessive_total = 0
    excessive_first_line: int | None = None

    for parent_id, subdataset in subdatasets.items():
        ids = subdataset.iloc[:, 0]
        raw_data = subdataset.iloc[:, 1:]

        is_di = raw_data == value_di
        cleaned_data, invalid_mask = ProportionalityProcessing.find_invalid_numeric_cells(raw_data, is_di, value_di)
        issues.extend(_numeric_format_issues(invalid_mask, proportionality_filename, parent_id, value_di))

        excessive_mask = ProportionalityProcessing.find_excessive_decimal_mask(cleaned_data, value_di, precision)
        count_excess = int(excessive_mask.to_numpy().sum())
        if count_excess:
            excessive_total += count_excess
            if excessive_first_line is None:
                first_row_idx = excessive_mask.any(axis=1).idxmax()
                excessive_first_line = int(first_row_idx) + 3

        row_sums = ProportionalityProcessing.convert_to_decimal_and_sum(cleaned_data, value_di, precision)

        for row_id, child_column in ProportionalityProcessing.find_zero_sum_violations(
            row_sums, ids, cleaned_data, values_frame, _ID, value_di
        ):
            issues.append(_zero_sum_issue(proportionality_filename, values_filename, row_id, child_column))

        error_index, warning_index = ProportionalityProcessing.sum_tolerance_indices(row_sums)
        for idx in error_index:
            issues.append(
                _tolerance_issue(
                    Severity.ERROR,
                    "rule.PROP-010.error",
                    proportionality_filename,
                    idx,
                    parent_id,
                    row_sums.loc[idx],
                    current_language,
                )
            )
        for idx in warning_index:
            issues.append(
                _tolerance_issue(
                    Severity.WARNING,
                    "rule.PROP-010.warning",
                    proportionality_filename,
                    idx,
                    parent_id,
                    row_sums.loc[idx],
                    current_language,
                )
            )

    if excessive_total:
        message_key = "rule.PROP-008.warning_one" if excessive_total == 1 else "rule.PROP-008.warning_many"
        issues.append(
            Issue(
                rule_id="PROP-008",
                severity=Severity.WARNING,
                sheet=proportionality_filename,
                row=None,
                column=None,
                message_key=message_key,
                params={
                    "filename": proportionality_filename,
                    "count": excessive_total,
                    "first_line": excessive_first_line,
                },
                category=NamesEnum.SUM_PROP.value,
            )
        )
    return issues
