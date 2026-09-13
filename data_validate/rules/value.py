#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""VAL-002…005: the `valores` content rules (ARC-017 Phase 3 Port 5, ADR-0006).

Ports `validators/spreadsheets/value/value_validator.py::SpValueValidator`'s three checks
(indicator-relation comparison, per-indicator column combinations, numeric/DI + decimal-place
validation) onto the `rules` engine, one `RuleSpec` per `VAL-*` id documented in
`.specs/business-rules/values.md`. `VAL-001` (the column-name-pattern structural check) stays in
`models/sp_value.py::SpValue.pre_processing`/`expected_structure_columns` — it runs before this
module's rules even see a frame and is out of this port's scope.

i18n (ARC-005): every message this module emits is a catalog key
(`static/locales/<locale>/messages.json`), never an inline string; the shared "required column is
missing" abort reuses one key per rule's severity bucket, `rule.value.missing_required_column`,
matching `rules/description.py`'s `_MISSING_COLUMN_KEY` precedent.

VAL-004/VAL-005 split one legacy method (`validate_unavailable_codes_values`, which returned both
an errors list and a warnings list from the same per-column pass) into two rule functions sharing
one private analysis (`_analyze_value_columns`), the same "one legacy method, several `RuleSpec`s"
shape `rules/composition.py` uses for COMP-005/COMP-006.

`ValueProcessing` (`helpers/common/validation/value_processing.py`) built its error/warning text as
hardcoded Portuguese f-strings; per `.claude/rules/architecture-boundaries.md` (no
hardcoded-string-building helper) and `rules/description.py`'s own precedent (never reusing
`dataframe_processing.py`'s message-building functions), this port does not reuse it — the module
and its test are deleted, and its logic is reproduced here as `Issue`s. `CombinationsProcessing`
and `CollectionsProcessing` (pure, no message text — both still used elsewhere, e.g. by
`models/sp_value.py`/`sp_proportionality.py`) are reused unchanged.

PERF-001, three hot loops rewritten:

- VAL-002 (`check_relation_indicators_in_values`, IR): unchanged from the legacy shape — it was
  already vectorised (`CollectionsProcessing`'s pattern-matching helpers operate on the column
  list, never on `valores`' rows) and is reproduced with the same shape, minus the final
  string-building step (an `Issue` now, not an f-string).
- VAL-003 (`check_value_combination_relation`, VAL_COMB): replaces the legacy
  `for _, row in df_description.iterrows(): code = str(row[...]); ...` with a `zip()` over three
  plain Python lists (`codigo`/`nivel`/`cenario`, extracted from their columns once via
  `.tolist()`) — no `.iterrows()`, no per-row `Series` construction. The per-code expected-column
  set still requires `CombinationsProcessing.generate_combinations` once per code (its shape is
  genuinely per-indicator, not vectorisable further without changing its output), and the
  membership checks (`combination not in value_columns`, `find_extra_combinations`) are already
  set operations, unchanged from the legacy helper.
- VAL-004/VAL-005 (`_analyze_value_columns`, UNAV_INV): replaces
  `ValueProcessing.process_column_validation`'s per-cell `for index, value in
  dataframe[column].items(): ...` loop with `pd.to_numeric(errors="coerce")` masks over the whole
  column at once (`is_di`, `not_numeric_mask`, the two literal/text-infinity sub-masks); the
  `Decimal` exponent check (no vectorised `Decimal` type exists in pandas) now runs once per
  *unique* candidate value via `Series.map`, not once per cell — `.claude/skills/
  pandas-vectorization/SKILL.md` patterns 1/2, `.claude/rules/dataframe-conventions.md`.

BUG-001 (shared-list mutation) does not apply here: every function below is a pure `RuleContext ->
list[Issue]` read, `RuleContext` itself is frozen (`.claude/rules/dataframe-conventions.md`), and
none of this module's helpers hold any instance/module-level mutable state, so calling any
`check_*` function twice on the same `ctx` is inherently idempotent (see
`tests/unit/rules/test_value.py::TestIdempotency`).

Depends only on `data_validate.rules`/`data_validate.specs`, `pandas`, and the pure
`CollectionsProcessing`/`CombinationsProcessing`/`DataCleaningProcessing`/`NumberFormattingProcessing`/
`DataFrameProcessing.numeric_equals_mask`/`numeric_not_equals_mask` helpers — never on `models`,
never on `ValueProcessing`'s deleted message-building helper, per
`.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing
from data_validate.helpers.common.generation.combinations_processing import CombinationsProcessing
from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

VALUE_REGISTRY = RuleRegistry()
"""Every `VAL-*` rule ported from `SpValueValidator`, in the legacy check order."""

_VALUES_SHEET = "valores"
_DESCRIPTION_SHEET = "descricao"
_TEMPORAL_SHEET = "referencia_temporal"
_SCENARIO_SHEET = "cenarios"

_ID = "id"
_CODE = "codigo"
_LEVEL = "nivel"
_SCENARIO_COLUMN = "cenario"
_SYMBOL = "simbolo"

_DI_MARKER = "DI"
_INFINITE_VALUES = (float("-inf"), float("inf"))

_MISSING_COLUMN_KEY = "rule.value.missing_required_column"


def _filename(ctx: RuleContext, sheet: str) -> str:
    """Return `sheet`'s display file name, as delivered (e.g. `"valores.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and sheet in filenames:
        return str(filenames[sheet])
    return sheet


def _scenario_exists(ctx: RuleContext) -> bool:
    """Return `ctx.options["scenario_exists_file"]`, defaulting to `False` when absent."""
    return bool(ctx.options.get("scenario_exists_file", False))


def _scenario_symbols(ctx: RuleContext) -> list[str]:
    """Return `ctx.options["scenarios"]` as a `list[str]`, or `[]` when absent/not a list."""
    value = ctx.options.get("scenarios", [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _missing_column_issue(rule_id: str, category: str, filename: str, column: str) -> Issue:
    """Build the "required column is missing" abort `Issue` shared by every rule below.

    Every VAL rule reports this abort as an **error**, matching
    `BaseValidator.check_columns_in_models_dataframes`'s callers, which always feed its result
    into the `errors` half of the legacy `(errors, warnings)` tuple.
    """
    return Issue(
        rule_id=rule_id,
        severity=Severity.ERROR,
        sheet=filename,
        row=None,
        column=column,
        message_key=_MISSING_COLUMN_KEY,
        params={"filename": filename, "column": column},
        category=category,
    )


# --------------------------------------------------------------------------------------------
# VAL-002: relation indicators in values (IR)
# --------------------------------------------------------------------------------------------


def _missing_codes_issue(label_from: str, label_to: str, missing_codes: list[int]) -> Issue:
    """Build one VAL-002 "codes missing" `Issue` (one direction of the comparison)."""
    return Issue(
        rule_id="VAL-002",
        severity=Severity.ERROR,
        sheet=label_from,
        row=None,
        column=None,
        message_key="rule.VAL-002.missing_codes",
        params={"label_from": label_from, "label_to": label_to, "missing_codes": str(missing_codes)},
        category=NamesEnum.IR.value,
    )


@VALUE_REGISTRY.rule(
    rule_id="VAL-002",
    category=NamesEnum.IR.value,
    requires={_VALUES_SHEET: (), _DESCRIPTION_SHEET: ()},
)
def check_relation_indicators_in_values(ctx: RuleContext) -> list[Issue]:
    """VAL-002: every `valores` column and every `descricao` code (except level 1) must match.

    Skipped entirely when `valores` or `descricao` is empty (`requires`, matching
    `validate_relation_indicators_in_values`'s own top-level skip). Aborts with one missing-column
    issue per absent column (`descricao.codigo`, `descricao.nivel`, then `cenarios.simbolo` when
    scenarios exist) before comparing any code, exactly matching
    `check_columns_in_models_dataframes`'s own column order.
    """
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    values_frame = ctx.sheet(_VALUES_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)
    exists_scenario = _scenario_exists(ctx)
    scenario_symbols = _scenario_symbols(ctx)

    issues: list[Issue] = [
        _missing_column_issue("VAL-002", NamesEnum.IR.value, description_filename, column)
        for column in (_CODE, _LEVEL)
        if column not in description_frame.columns
    ]
    if exists_scenario:
        scenario_frame = ctx.sheet(_SCENARIO_SHEET)
        if _SYMBOL not in scenario_frame.columns:
            issues.append(
                _missing_column_issue("VAL-002", NamesEnum.IR.value, _filename(ctx, _SCENARIO_SHEET), _SYMBOL)
            )
    if issues:
        return issues

    df_description, _errors = DataCleaningProcessing.clean_dataframe_integers(
        description_frame, description_filename, [_CODE]
    )

    level_one_codes = (
        df_description[DataFrameProcessing.numeric_equals_mask(df_description[_LEVEL], 1)][_CODE].astype(str).tolist()
    )

    columns_to_ignore = [_ID, *level_one_codes]
    valid_value_codes, invalid_columns = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
        values_frame.columns.tolist(), columns_to_ignore, scenario_symbols
    )
    processed_invalid_columns = sorted({column for column in invalid_columns if ":" not in column})

    issues = []
    if processed_invalid_columns:
        issues.append(
            Issue(
                rule_id="VAL-002",
                severity=Severity.ERROR,
                sheet=values_filename,
                row=None,
                column=None,
                message_key="rule.VAL-002.invalid_columns",
                params={"filename": values_filename, "invalid_columns": str(processed_invalid_columns)},
                category=NamesEnum.IR.value,
            )
        )

    filtered_description = df_description[DataFrameProcessing.numeric_not_equals_mask(df_description[_LEVEL], 1)]
    if exists_scenario and _SCENARIO_COLUMN in filtered_description.columns:
        filtered_description = filtered_description[
            ~(
                DataFrameProcessing.numeric_equals_mask(filtered_description[_LEVEL], 2)
                & (filtered_description[_SCENARIO_COLUMN] == "0")
            )
        ]

    valid_description_codes, _invalid = CollectionsProcessing.extract_numeric_integer_ids_from_list(
        id_values_list=list(set(filtered_description[_CODE].astype(str)))
    )

    missing_in_values = sorted(valid_description_codes - valid_value_codes)
    missing_in_description = sorted(valid_value_codes - valid_description_codes)
    if missing_in_values:
        issues.append(_missing_codes_issue(description_filename, values_filename, missing_in_values))
    if missing_in_description:
        issues.append(_missing_codes_issue(values_filename, description_filename, missing_in_description))
    return issues


# --------------------------------------------------------------------------------------------
# VAL-003: value combination relation (VAL_COMB)
# --------------------------------------------------------------------------------------------


@VALUE_REGISTRY.rule(
    rule_id="VAL-003",
    category=NamesEnum.VAL_COMB.value,
    requires={_VALUES_SHEET: (), _DESCRIPTION_SHEET: (), _TEMPORAL_SHEET: ()},
)
def check_value_combination_relation(ctx: RuleContext) -> list[Issue]:
    """VAL-003: each indicator must have exactly its expected `valores` time/scenario columns.

    Skipped entirely when `valores`, `descricao`, or `referencia_temporal` is empty (`requires`,
    matching `validate_value_combination_relation`'s own top-level skip). Aborts with one
    missing-column issue per absent column, in `valores.id`, `descricao.codigo`,
    `descricao.nivel`, `descricao.cenario` (only when scenarios exist),
    `referencia_temporal.simbolo`, `cenarios.simbolo` (only when scenarios exist) order —
    matching `check_columns_in_models_dataframes`'s own required-columns dict order.
    """
    values_frame = ctx.sheet(_VALUES_SHEET)
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    temporal_frame = ctx.sheet(_TEMPORAL_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)
    temporal_filename = _filename(ctx, _TEMPORAL_SHEET)
    exists_scenario = _scenario_exists(ctx)
    scenario_symbols = _scenario_symbols(ctx)

    issues: list[Issue] = []
    if _ID not in values_frame.columns:
        issues.append(_missing_column_issue("VAL-003", NamesEnum.VAL_COMB.value, values_filename, _ID))
    for column in (_CODE, _LEVEL):
        if column not in description_frame.columns:
            issues.append(_missing_column_issue("VAL-003", NamesEnum.VAL_COMB.value, description_filename, column))
    if exists_scenario and _SCENARIO_COLUMN not in description_frame.columns:
        issues.append(
            _missing_column_issue("VAL-003", NamesEnum.VAL_COMB.value, description_filename, _SCENARIO_COLUMN)
        )
    if _SYMBOL not in temporal_frame.columns:
        issues.append(_missing_column_issue("VAL-003", NamesEnum.VAL_COMB.value, temporal_filename, _SYMBOL))
    if exists_scenario:
        scenario_frame = ctx.sheet(_SCENARIO_SHEET)
        if _SYMBOL not in scenario_frame.columns:
            issues.append(
                _missing_column_issue("VAL-003", NamesEnum.VAL_COMB.value, _filename(ctx, _SCENARIO_SHEET), _SYMBOL)
            )
    if issues:
        return issues

    description_columns = [_CODE, _LEVEL, *([_SCENARIO_COLUMN] if exists_scenario else [])]
    df_description, _errors = DataCleaningProcessing.clean_dataframe_integers(
        description_frame, description_filename, description_columns
    )
    df_temporal, _errors = DataCleaningProcessing.clean_dataframe_integers(temporal_frame, temporal_filename, [_SYMBOL])

    temporal_symbols = sorted(df_temporal[_SYMBOL].unique())
    first_year = temporal_symbols[0]
    value_columns = set(values_frame.columns)

    codes = df_description[_CODE].astype(str).tolist()
    levels = df_description[_LEVEL].astype(int).tolist()
    scenarios = df_description[_SCENARIO_COLUMN].astype(int).tolist() if exists_scenario else [0] * len(df_description)

    issues = []
    for code, level, scenario in zip(codes, levels, scenarios):
        expected_combinations: list[str] = []
        if level >= 2:
            if scenario == 0:
                expected_combinations = [f"{code}-{first_year}"]
            elif scenario == 1:
                expected_combinations = CombinationsProcessing.generate_combinations(
                    code, first_year, temporal_symbols, scenario_symbols
                )

        for combination in expected_combinations:
            if combination in value_columns:
                continue
            if level == 2 and scenario == 0:
                continue
            issues.append(
                Issue(
                    rule_id="VAL-003",
                    severity=Severity.ERROR,
                    sheet=values_filename,
                    row=None,
                    column=combination,
                    message_key="rule.VAL-003.required_column",
                    params={"filename": values_filename, "combination": combination},
                    category=NamesEnum.VAL_COMB.value,
                )
            )

        actual_combinations = [column for column in value_columns if column.startswith(f"{code}-")]
        has_extra, extra_columns = CombinationsProcessing.find_extra_combinations(
            expected_combinations, actual_combinations
        )
        if not has_extra:
            continue
        for extra_column in extra_columns:
            message_key = "rule.VAL-003.unnecessary_column_level1" if level == 1 else "rule.VAL-003.unnecessary_column"
            issues.append(
                Issue(
                    rule_id="VAL-003",
                    severity=Severity.ERROR,
                    sheet=values_filename,
                    row=None,
                    column=extra_column,
                    message_key=message_key,
                    params={"filename": values_filename, "extra_column": extra_column},
                    category=NamesEnum.VAL_COMB.value,
                )
            )
    return issues


# --------------------------------------------------------------------------------------------
# VAL-004/VAL-005: unavailable and invalid values, excessive decimal places (UNAV_INV)
# --------------------------------------------------------------------------------------------


def _excessive_decimal_rows(series: pd.Series, mask: pd.Series) -> set[int]:
    """Row numbers (1-based Excel, `idx + 2`) of `series[mask]` cells with > 2 decimal places.

    `NumberFormattingProcessing.check_two_decimals_places` runs once per *unique* candidate
    value (`Series.map`), not once per cell, since no vectorised `Decimal` type exists in pandas
    (PERF-001).
    """
    candidates = series[mask]
    if candidates.empty:
        return set()
    flags = {value: NumberFormattingProcessing.check_two_decimals_places(value) for value in candidates.unique()}
    excessive = candidates.map(flags)
    return {int(idx) + 2 for idx in candidates.index[excessive]}


def _invalid_value_issue(filename: str, column: str, idx: int, value: object) -> Issue:
    """VAL-004: the single-invalid-cell message (a genuinely non-numeric, non-`DI` cell)."""
    return Issue(
        rule_id="VAL-004",
        severity=Severity.ERROR,
        sheet=filename,
        row=int(idx),
        column=column,
        message_key="rule.VAL-004.error",
        params={"filename": filename, "row": int(idx) + 2, "value": value, "column": column},
        category=NamesEnum.UNAV_INV.value,
    )


def _decimal_parse_error_issue(filename: str, column: str, idx: int) -> Issue:
    """VAL-004: the single-invalid-cell message for a value whose decimal-exponent check raised.

    Reproduces `ValueProcessing.check_numeric_value`'s `except (ValueError, TypeError)` branch:
    reachable when a cell parses as a numeric *text* form of infinity (e.g. `"inf"`, `"Infinity"`)
    — `pd.to_numeric` accepts it as a finite-looking, non-`NaN` float, but
    `Decimal(str(value)).as_tuple().exponent` is the special string `'F'`, so comparing it against
    an int raises `TypeError`.
    """
    return Issue(
        rule_id="VAL-004",
        severity=Severity.ERROR,
        sheet=filename,
        row=int(idx),
        column=column,
        message_key="rule.VAL-004.decimal_parse_error",
        params={"filename": filename, "row": int(idx) + 2, "column": column},
        category=NamesEnum.UNAV_INV.value,
    )


def _silent_invalid_value_issue(filename: str, column: str, idx: int) -> Issue:
    """VAL-004: the single-invalid-cell case for a literal Python `float('inf')`/`-inf` cell.

    Reproduces `ValueProcessing.check_numeric_value`'s `if value in [-inf, inf]: return False, "",
    False` branch: the cell IS counted as invalid, but the legacy error message text is the empty
    string — preserved here (`rule.VAL-004.silent` renders to `""`) rather than "fixed", since this
    port must stay byte-identical to the legacy report (see this module's docstring).
    """
    return Issue(
        rule_id="VAL-004",
        severity=Severity.ERROR,
        sheet=filename,
        row=int(idx),
        column=column,
        message_key="rule.VAL-004.silent",
        params={},
        category=NamesEnum.UNAV_INV.value,
    )


def _invalid_values_aggregate_issue(filename: str, column: str, count: int, first_row: int, last_row: int) -> Issue:
    """VAL-004: the aggregated message for a column with more than one invalid cell."""
    return Issue(
        rule_id="VAL-004",
        severity=Severity.ERROR,
        sheet=filename,
        row=None,
        column=column,
        message_key="rule.VAL-004.aggregate",
        params={"filename": filename, "count": count, "column": column, "first_row": first_row, "last_row": last_row},
        category=NamesEnum.UNAV_INV.value,
    )


def _column_invalid_value_issues(
    series: pd.Series,
    filename: str,
    column: str,
    invalid_index: pd.Index,
    not_numeric_mask: pd.Series,
    decimal_parse_error_mask: pd.Series,
) -> list[Issue]:
    """VAL-004's per-column errors: one message when a column has exactly one invalid cell, one
    aggregated message otherwise — the per-cell reason (not-numeric, decimal-parse-error, or the
    silent literal-infinity case) only matters in the single-cell case, matching
    `ValueProcessing.process_column_validation`'s own `len(invalid_values) == 1` branch.
    """
    count = len(invalid_index)
    if count == 0:
        return []
    if count == 1:
        idx = invalid_index[0]
        if bool(not_numeric_mask.loc[idx]):
            return [_invalid_value_issue(filename, column, idx, series.loc[idx])]
        if bool(decimal_parse_error_mask.loc[idx]):
            return [_decimal_parse_error_issue(filename, column, idx)]
        return [_silent_invalid_value_issue(filename, column, idx)]
    first_row = int(invalid_index.min()) + 2
    last_row = int(invalid_index.max()) + 2
    return [_invalid_values_aggregate_issue(filename, column, count, first_row, last_row)]


def _analyze_value_column(series: pd.Series, column: str, filename: str) -> tuple[list[Issue], set[int]]:
    """Analyze one `valores` column: invalid-cell issues plus its excessive-decimal row numbers.

    Vectorised replacement for `ValueProcessing.check_numeric_value`'s per-cell loop
    (PERF-001, `.claude/rules/dataframe-conventions.md`): every mask below is computed once over
    the whole column.
    """
    is_di = series == _DI_MARKER
    normalized = series.astype(str).str.replace(",", ".", regex=False)
    numeric_value = pd.to_numeric(normalized, errors="coerce")
    raw_is_na = series.isna()

    not_numeric_mask = (~is_di) & (raw_is_na | numeric_value.isna())
    is_numeric_infinite = (~is_di) & (~not_numeric_mask) & numeric_value.abs().eq(float("inf"))
    is_literal_float_infinite = series.isin(_INFINITE_VALUES)
    silent_infinite_mask = is_numeric_infinite & is_literal_float_infinite
    decimal_parse_error_mask = is_numeric_infinite & ~is_literal_float_infinite

    invalid_mask = not_numeric_mask | silent_infinite_mask | decimal_parse_error_mask
    invalid_index = series.index[invalid_mask]

    errors = _column_invalid_value_issues(
        series, filename, column, invalid_index, not_numeric_mask, decimal_parse_error_mask
    )

    decimal_candidate_mask = (~is_di) & (~invalid_mask)
    excessive_rows = _excessive_decimal_rows(series, decimal_candidate_mask)
    return errors, excessive_rows


def _decimal_warning_issue(filename: str, count: int, first_row: int, last_row: int) -> Issue:
    """VAL-005: the single, cross-column decimal-places warning, singular or plural by `count`."""
    message_key = "rule.VAL-005.warning_one" if count == 1 else "rule.VAL-005.warning_many"
    return Issue(
        rule_id="VAL-005",
        severity=Severity.WARNING,
        sheet=filename,
        row=None,
        column=None,
        message_key=message_key,
        params={"filename": filename, "count": count, "first_row": first_row, "last_row": last_row},
        category=NamesEnum.UNAV_INV.value,
    )


def _analyze_value_columns(ctx: RuleContext) -> tuple[list[Issue], list[Issue]]:
    """Shared VAL-004/VAL-005 analysis: every pattern-matching `valores` column, once.

    Returns:
        tuple[list[Issue], list[Issue]]: `(errors, warnings)` — VAL-004 returns the first,
            VAL-005 the second; `count_excessive_decimal_rows` sums each column's own excessive
            count (may double-count a row number that is excessive in more than one column),
            while `first_row`/`last_row` come from the row numbers deduplicated *across* every
            column, matching `ValueProcessing.validate_data_values_in_columns` exactly.
    """
    values_frame = ctx.sheet(_VALUES_SHEET)
    filename = _filename(ctx, _VALUES_SHEET)
    scenario_symbols = _scenario_symbols(ctx)

    candidate_frame = values_frame.drop(columns=[_ID]) if _ID in values_frame.columns else values_frame
    valid_columns, _unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
        candidate_frame.columns.tolist(), scenario_symbols
    )

    errors: list[Issue] = []
    all_excessive_rows: set[int] = set()
    total_excessive_count = 0

    for column in valid_columns:
        column_errors, column_excessive_rows = _analyze_value_column(candidate_frame[column], column, filename)
        errors.extend(column_errors)
        total_excessive_count += len(column_excessive_rows)
        all_excessive_rows.update(column_excessive_rows)

    warnings: list[Issue] = []
    if all_excessive_rows:
        warnings.append(
            _decimal_warning_issue(filename, total_excessive_count, min(all_excessive_rows), max(all_excessive_rows))
        )
    return errors, warnings


@VALUE_REGISTRY.rule(rule_id="VAL-004", category=NamesEnum.UNAV_INV.value, requires={_VALUES_SHEET: ()})
def check_unavailable_and_invalid_values(ctx: RuleContext) -> list[Issue]:
    """VAL-004: every pattern-matching `valores` cell must be `DI` or parse as a number.

    Aborts with a missing-column issue when scenarios exist and `cenarios.simbolo` is absent
    (matches `validate_unavailable_codes_values`'s own column check, which only ever guards the
    scenario symbol column). Owns the abort for both VAL-004 and VAL-005 (one legacy method, one
    column check) — VAL-005 stays silent on a missing column.
    """
    if _scenario_exists(ctx):
        scenario_frame = ctx.sheet(_SCENARIO_SHEET)
        if _SYMBOL not in scenario_frame.columns:
            return [
                _missing_column_issue("VAL-004", NamesEnum.UNAV_INV.value, _filename(ctx, _SCENARIO_SHEET), _SYMBOL)
            ]

    errors, _warnings = _analyze_value_columns(ctx)
    return errors


@VALUE_REGISTRY.rule(
    rule_id="VAL-005",
    category=NamesEnum.UNAV_INV.value,
    requires={_VALUES_SHEET: ()},
    severity_default=Severity.WARNING,
)
def check_excessive_decimal_places(ctx: RuleContext) -> list[Issue]:
    """VAL-005: numeric `valores` cells with more than two decimal places are counted, once.

    Silent (returns `[]`, no warning) when the scenario-column abort VAL-004 owns would have
    fired — see `check_unavailable_and_invalid_values`'s docstring; the legacy method returns no
    warnings at all in that case either.
    """
    if _scenario_exists(ctx):
        scenario_frame = ctx.sheet(_SCENARIO_SHEET)
        if _SYMBOL not in scenario_frame.columns:
            return []

    _errors, warnings = _analyze_value_columns(ctx)
    return warnings


# --------------------------------------------------------------------------------------------
# VAL-006: id uniqueness (UNIQ_VAL)
# --------------------------------------------------------------------------------------------


@VALUE_REGISTRY.rule(rule_id="VAL-006", category=NamesEnum.UNIQ_VAL.value, requires={_VALUES_SHEET: ()})
def check_id_uniqueness(ctx: RuleContext) -> list[Issue]:
    """VAL-006 (PROTO-017, gap G-13): `valores.id` must contain no duplicated value.

    Protocol §2.6 p.11 ("identificador único"). No registry (`spd_data.json`, PROTO-013/TERR-002)
    is needed for this half of the gap -- uniqueness is a property of `valores` alone.
    """
    frame = ctx.sheet(_VALUES_SHEET)
    filename = _filename(ctx, _VALUES_SHEET)

    if _ID not in frame.columns:
        return [_missing_column_issue("VAL-006", NamesEnum.UNIQ_VAL.value, filename, _ID)]

    duplicated_ids = frame[_ID][frame[_ID].duplicated()].tolist()
    if not duplicated_ids:
        return []
    return [
        Issue(
            rule_id="VAL-006",
            severity=Severity.ERROR,
            sheet=filename,
            row=None,
            column=_ID,
            message_key="rule.VAL-006.error",
            params={"filename": filename, "column": _ID, "duplicated_ids": str(duplicated_ids)},
            category=NamesEnum.UNIQ_VAL.value,
        )
    ]
