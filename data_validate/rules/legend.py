#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""LEG-012…015: the `legenda` relation/range rules (ARC-017 Phase 3 Port 6, ADR-0006).

Ports `validators/spreadsheets/legend/legend_validator.py::SpLegendValidator`'s two checks
(`validate_relation_indicators_in_legend`, `validate_range_multiple_legend`) onto the `rules`
engine, one `RuleSpec` per `LEG-*` id documented in `.specs/business-rules/legend.md`.
`LEG-001`…`LEG-011` (the per-legend-group structural/cleaning checks: sequential codes, label/color/
min-max/order validation) stay in `models/sp_legend.py::SpLegend.data_cleaning`, delegating to
`helpers/common/validation/legend_processing.py::LegendProcessing` — they run before this module's
rules even see a frame and are out of this port's scope.

One legacy method, several `RuleSpec`s (the same shape `rules/value.py`'s VAL-004/VAL-005 and
`rules/composition.py`'s COMP-005/COMP-006 use): `validate_relation_indicators_in_legend` returned
one combined `(errors, warnings)` pair covering three independent statements (missing/unreferenced
legend codes, level-1-must-not-reference, other-levels-must-reference); `_analyze_relation_indicators`
is the single shared analysis every one of `LEG-012`/`LEG-013`/`LEG-014` calls (uncached, matching
`rules/value.py::_analyze_value_columns`'s own precedent — this analysis is a handful of `groupby`/
mask operations, not a hot loop). The missing-required-column abort is owned by `LEG-012` alone
(registered first, matching the legacy method's own column-check order); `LEG-013`/`LEG-014` stay
silent on a missing column, mirroring `rules/composition.py::check_leaf_indicators_have_proportionality`'s
own "stay silent, the sibling rule already reported it" precedent.

Two conditional-execution quirks preserved exactly (`ctx.options`, not the engine's declarative
`requires`, since neither condition is expressible as "sheet present + column present"):

- `SpLegendValidator.run()` only appends `validate_relation_indicators_in_legend` to its
  validations list `if self.model_sp_legend.is_sanity_check_passed` — a model-level flag (file
  exists, non-empty, read successfully, and `LEG-001`…`LEG-011` produced no error), not a sheet/
  column shape fact. `ctx.options["legend_sanity_ok"]` (set by
  `SpreadsheetProcessor._build_rule_context` from the same `SpLegend.is_sanity_check_passed`
  property) reproduces the gate: `LEG-012`/`LEG-013`/`LEG-014` return `[]` immediately when it is
  `False`, functionally identical to never having been in the legacy validations list (an empty
  issue list either way — see `base_validator.py::set_not_executed`, which is a no-op `pass`).
- `validate_range_multiple_legend` always runs (even when the legend file is absent — the
  protocol's default `[0, 1]` range applies), using `df_legend.groupby(...)` only
  `if self.model_sp_legend.is_sanity_check_passed`, else an always-empty group lookup so every
  column falls back to the default range. `LEG-015` reproduces this the same way, via
  `_legend_sanity_ok(ctx)`.

The outer `if self.model_sp_description.frame.empty: set_not_executed(...); return` gate that
covers *both* legacy checks maps directly onto `requires={_DESCRIPTION_SHEET: ()}` on every
`RuleSpec` below — an empty/absent `descricao` is exactly what the engine's own prerequisite check
already treats as `SKIPPED`.

i18n (ARC-005): `LEG-015`'s message embeds either "de código 'X'" or "padrão" as the legend
descriptor. Rather than build that fragment as a pre-formatted Portuguese/English string and pass
it as one opaque param (which would leak the source locale's words into the other locale's
rendering — forbidden by `.claude/rules/i18n.md`), the two branches are two catalog keys,
`rule.LEG-015.error_default`/`rule.LEG-015.error_coded`, each with its own fully-translated
sentence — the same "one key per branch" shape `rules/value.py` uses for `VAL-004`'s three
sub-cases and `rules/composition.py`'s `unnecessary_column`/`unnecessary_column_level1` split.

PERF-001: `check_value_range_within_legend` (`LEG-015`) replaces the legacy
`for index, value_numeric in df_values_numeric[col].items(): ...` per-cell loop with one boolean
mask per column (`out_of_range_mask`, excluding `DI` and non-numeric cells via `pd.to_numeric(
errors="coerce")`), built once per matching `valores` column — the column-level mapping-building
loop (indicator -> legend -> min/max) stays a Python `for` loop, since it iterates over the (few)
matching columns, not over rows, and already ran that way in the legacy code.

Depends only on `data_validate.rules`/`data_validate.specs`, `pandas`, and the pure
`CollectionsProcessing`/`DataCleaningProcessing`/`DataFrameProcessing.numeric_equals_mask`/
`numeric_not_equals_mask` helpers (the same subset `rules/value.py` already depends on) — never on
`models`, per `.claude/rules/architecture-boundaries.md`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pandas as pd

from data_validate.config import NamesEnum
from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.rules.context import RuleContext
from data_validate.rules.registry import RuleRegistry
from data_validate.specs.issues import Issue, Severity

LEGEND_REGISTRY = RuleRegistry()
"""Every `LEG-*` rule ported from `SpLegendValidator`, in the legacy check order."""

_DESCRIPTION_SHEET = "descricao"
_LEGEND_SHEET = "legenda"
_VALUES_SHEET = "valores"

_ID = "id"
_CODE = "codigo"
_LEVEL = "nivel"
_LEGEND_COLUMN = "legenda"
_LABEL = "label"
_MINIMUM = "minimo"
_MAXIMUM = "maximo"

_MISSING_COLUMN_KEY = "rule.legend.missing_required_column"


def _filename(ctx: RuleContext, sheet: str) -> str:
    """Return `sheet`'s display file name, as delivered (e.g. `"legenda.xlsx"`)."""
    filenames = ctx.options.get("filenames", {})
    if isinstance(filenames, Mapping) and sheet in filenames:
        return str(filenames[sheet])
    return sheet


def _legend_sanity_ok(ctx: RuleContext) -> bool:
    """Return `ctx.options["legend_sanity_ok"]`, defaulting to `False` when absent."""
    return bool(ctx.options.get("legend_sanity_ok", False))


def _legend_read_success(ctx: RuleContext) -> bool:
    """Return `ctx.options["legend_read_success"]`, defaulting to `False` when absent."""
    return bool(ctx.options.get("legend_read_success", False))


def _legend_defaults(ctx: RuleContext) -> tuple[object, object]:
    """Return the configured default `(min, max)` legend range, `(0, 1)` when unset.

    Kept as whatever type `ctx.options` carries (an `int` in production, see
    `SpLegend.CONSTANTS.MIN_LOWER_LEGEND_DEFAULT`/`MAX_UPPER_LEGEND_DEFAULT`) rather than coerced
    to `float`: the rendered message embeds this value verbatim (`"{min_value} a {max_value}"`),
    and the legacy f-string rendered the same `int` default as `"0"`/`"1"`, not `"0.0"`/`"1.0"`.
    """
    return ctx.options.get("min_lower_legend_default", 0), ctx.options.get("max_upper_legend_default", 1)


def _label_data_unavailable(ctx: RuleContext) -> str:
    """Return `ctx.options["label_data_unavailable"]`, defaulting to `"Dado indisponível"`."""
    return str(ctx.options.get("label_data_unavailable", "Dado indisponível"))


def _value_data_unavailable(ctx: RuleContext) -> str:
    """Return `ctx.options["value_data_unavailable"]`, defaulting to `"DI"`."""
    return str(ctx.options.get("value_data_unavailable", "DI"))


def _scenario_symbols(ctx: RuleContext) -> list[str]:
    """Return `ctx.options["scenarios"]` as a `list[str]`, or `[]` when absent/not a list."""
    value = ctx.options.get("scenarios", [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _first_missing_column(frame: pd.DataFrame, columns: Sequence[str]) -> str | None:
    """Return the first name in `columns` absent from `frame`, or `None` if all are present.

    Matches `SpLegendValidator`'s own column-check loop (`for column in required_columns: ...;
    break`), which aborts on the *first* missing column rather than collecting every one.
    """
    for column in columns:
        if column not in frame.columns:
            return column
    return None


def _missing_column_issue(rule_id: str, category: str, filename: str, column: str) -> Issue:
    """Build the "required column is missing" abort `Issue` shared by every rule below.

    Every LEG rule reports this abort as an **error**, matching
    `SpLegendValidator.column_exists`'s callers, which always feed its result into the `errors`
    half of the legacy `(errors, warnings)` tuple.
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
# LEG-012/013/014: relation between descricao.legenda and legenda.codigo (LEG_REL)
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class _RelationFindings:
    """Shared result of `_analyze_relation_indicators`, one field per `LEG-01{2,3,4}` finding.

    `None` means "nothing to report" for that field; `abort` set means every other field is
    `None` (the legacy method returns immediately on a missing required column).
    """

    abort: Issue | None = None
    missing_codes: Issue | None = None
    unreferenced_codes: Issue | None = None
    level_one_with_legend: Issue | None = None
    other_levels_missing_legend: Issue | None = None


def _analyze_relation_indicators(ctx: RuleContext) -> _RelationFindings:
    """Reproduce `validate_relation_indicators_in_legend`'s full analysis, once.

    Returns an all-`None` `_RelationFindings()` when `ctx.options["legend_sanity_ok"]` is falsy —
    the legacy `run()` never even adds this check to its validations list in that case.
    """
    if not _legend_sanity_ok(ctx):
        return _RelationFindings()

    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    legend_frame = ctx.sheet(_LEGEND_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)
    legend_filename = _filename(ctx, _LEGEND_SHEET)

    missing_column = _first_missing_column(description_frame, (_CODE, _LEVEL, _LEGEND_COLUMN))
    if missing_column is not None:
        return _RelationFindings(
            abort=_missing_column_issue("LEG-012", NamesEnum.LEG_REL.value, description_filename, missing_column)
        )

    df_description, _errors = DataCleaningProcessing.clean_dataframe_integers(
        description_frame, description_filename, [_CODE], min_value=1
    )
    df_description[_LEGEND_COLUMN] = pd.to_numeric(df_description[_LEGEND_COLUMN], errors="coerce").astype("Int64")
    df_description = df_description.dropna(subset=[_CODE])
    df_legend = legend_frame.dropna(subset=[_CODE])

    legend_numeric = pd.to_numeric(df_description[_LEGEND_COLUMN], errors="coerce")
    described_legend_ids = (
        df_description[
            DataFrameProcessing.numeric_not_equals_mask(df_description[_LEVEL], 1)
            & df_description[_LEGEND_COLUMN].notna()
            & legend_numeric.notna()
        ][_LEGEND_COLUMN]
        .astype(str)
        .tolist()
    )
    legend_ids_in_legend = df_legend[_CODE].astype(str).unique().tolist()

    missing_in_legend, missing_in_description = CollectionsProcessing.find_differences_in_two_set(
        first_set=set(described_legend_ids), second_set=set(legend_ids_in_legend)
    )
    missing_in_legend = {int(value) for value in missing_in_legend if str(value).isdigit()}
    missing_in_description = {int(value) for value in missing_in_description if str(value).isdigit()}

    missing_codes_issue = None
    if missing_in_legend:
        missing_codes_issue = Issue(
            rule_id="LEG-012",
            severity=Severity.ERROR,
            sheet=description_filename,
            row=None,
            column=_LEGEND_COLUMN,
            message_key="rule.LEG-012.error",
            params={
                "filename": description_filename,
                "legend_filename": legend_filename,
                "missing_codes": str(sorted(missing_in_legend)),
            },
            category=NamesEnum.LEG_REL.value,
        )

    unreferenced_issue = None
    if missing_in_description:
        unreferenced_issue = Issue(
            rule_id="LEG-012",
            severity=Severity.WARNING,
            sheet=legend_filename,
            row=None,
            column=_CODE,
            message_key="rule.LEG-012.warning",
            params={
                "filename": legend_filename,
                "description_filename": description_filename,
                "missing_codes": str(sorted(missing_in_description)),
            },
            category=NamesEnum.LEG_REL.value,
        )

    level_one_mask = DataFrameProcessing.numeric_equals_mask(df_description[_LEVEL], 1)
    codes_level_one = df_description[level_one_mask][_CODE].astype(str).tolist()
    legend_ids_level_one = df_description[level_one_mask & df_description[_LEGEND_COLUMN].notna()][_LEGEND_COLUMN]

    level_one_issue = None
    if not legend_ids_level_one.empty:
        level_one_issue = Issue(
            rule_id="LEG-013",
            severity=Severity.ERROR,
            sheet=description_filename,
            row=None,
            column=_LEGEND_COLUMN,
            message_key="rule.LEG-013.error",
            params={
                "filename": description_filename,
                "legend_filename": legend_filename,
                "codes": str(sorted(codes_level_one)),
            },
            category=NamesEnum.LEG_REL.value,
        )

    other_levels_mask = DataFrameProcessing.numeric_not_equals_mask(
        df_description[_LEVEL], 1
    ) & DataFrameProcessing.numeric_not_equals_mask(df_description[_LEVEL], 2)
    codes_other_levels = set(df_description[other_levels_mask][_CODE].astype(str).tolist())
    codes_other_levels_with_legend = set(
        df_description[other_levels_mask & df_description[_LEGEND_COLUMN].notna()][_CODE].astype(str).tolist()
    )
    missing_other_levels = codes_other_levels - codes_other_levels_with_legend

    other_levels_issue = None
    if missing_other_levels:
        other_levels_issue = Issue(
            rule_id="LEG-014",
            severity=Severity.ERROR,
            sheet=description_filename,
            row=None,
            column=_LEGEND_COLUMN,
            message_key="rule.LEG-014.error",
            params={
                "filename": description_filename,
                "legend_filename": legend_filename,
                "codes": str(sorted(missing_other_levels)),
            },
            category=NamesEnum.LEG_REL.value,
        )

    return _RelationFindings(
        missing_codes=missing_codes_issue,
        unreferenced_codes=unreferenced_issue,
        level_one_with_legend=level_one_issue,
        other_levels_missing_legend=other_levels_issue,
    )


@LEGEND_REGISTRY.rule(rule_id="LEG-012", category=NamesEnum.LEG_REL.value, requires={_DESCRIPTION_SHEET: ()})
def check_relation_missing_and_unreferenced_codes(ctx: RuleContext) -> list[Issue]:
    """LEG-012: every `descricao.legenda` code must exist in `legenda`; the reverse is a warning.

    Owns the shared missing-required-column abort (`descricao.codigo`/`nivel`/`legenda`, in that
    order) for `LEG-012`/`LEG-013`/`LEG-014` — see `_analyze_relation_indicators`.
    """
    findings = _analyze_relation_indicators(ctx)
    if findings.abort is not None:
        return [findings.abort]
    issues: list[Issue] = []
    if findings.missing_codes is not None:
        issues.append(findings.missing_codes)
    if findings.unreferenced_codes is not None:
        issues.append(findings.unreferenced_codes)
    return issues


@LEGEND_REGISTRY.rule(rule_id="LEG-013", category=NamesEnum.LEG_REL.value, requires={_DESCRIPTION_SHEET: ()})
def check_level_one_must_not_reference_legend(ctx: RuleContext) -> list[Issue]:
    """LEG-013: no level-1 `descricao` row may carry a `legenda` reference.

    Silent (no issue) when the shared missing-column abort would have fired — `LEG-012` already
    reports that.
    """
    findings = _analyze_relation_indicators(ctx)
    if findings.abort is not None or findings.level_one_with_legend is None:
        return []
    return [findings.level_one_with_legend]


@LEGEND_REGISTRY.rule(rule_id="LEG-014", category=NamesEnum.LEG_REL.value, requires={_DESCRIPTION_SHEET: ()})
def check_other_levels_must_reference_legend(ctx: RuleContext) -> list[Issue]:
    """LEG-014: every `descricao` row at a level other than 1 or 2 must carry a `legenda` reference.

    Silent (no issue) when the shared missing-column abort would have fired — `LEG-012` already
    reports that.
    """
    findings = _analyze_relation_indicators(ctx)
    if findings.abort is not None or findings.other_levels_missing_legend is None:
        return []
    return [findings.other_levels_missing_legend]


# --------------------------------------------------------------------------------------------
# LEG-015: values must fall inside their legend's range (LEG_RANGE)
# --------------------------------------------------------------------------------------------


def _legend_groups(ctx: RuleContext) -> dict[str, pd.DataFrame]:
    """Return `legenda.codigo -> group` (as `str` keys), or `{}` when legend sanity failed.

    Mirrors `validate_range_multiple_legend`'s own `groups_legends` fallback: when the legend
    model's sanity check did not pass, every column falls back to the default range because no
    group ever matches (`{}` never satisfies a `key in groups`/`.get` lookup).
    """
    if not _legend_sanity_ok(ctx):
        return {}
    legend_frame = ctx.sheet(_LEGEND_SHEET)
    return {str(code): group for code, group in legend_frame.groupby(_CODE)}


def _legend_range_for_column(
    ctx: RuleContext,
    indicator_id: str,
    df_description: pd.DataFrame,
    legend_groups: Mapping[str, pd.DataFrame],
) -> tuple[object | None, object, object]:
    """Resolve `(legend_id, min_value, max_value)` for one `valores` column's indicator.

    Returns the configured defaults (`_legend_defaults`) and `legend_id=None` when the indicator
    has no row in `descricao`, no legend reference, no matching legend group, or the group's
    non-DI slices have no parseable `minimo`/`maximo` — matching `ModelMappingLegend`'s own
    all-defaults starting point and every early-exit branch of the legacy mapping loop.
    """
    min_value, max_value = _legend_defaults(ctx)
    legend_id: object | None = None

    row_description = df_description[df_description[_CODE].astype(str) == indicator_id]
    if row_description.empty:
        return legend_id, min_value, max_value

    key_legend = row_description.iloc[0][_LEGEND_COLUMN]
    group_legend = legend_groups.get(str(key_legend))
    if group_legend is None:
        return legend_id, min_value, max_value

    legend_id = key_legend
    label_unavailable = _label_data_unavailable(ctx)
    group_legend = group_legend[group_legend[_LABEL] != label_unavailable]
    if group_legend.empty:
        return legend_id, min_value, max_value

    minimum = pd.to_numeric(group_legend[_MINIMUM], errors="coerce").min()
    maximum = pd.to_numeric(group_legend[_MAXIMUM], errors="coerce").max()
    if pd.notna(minimum) and pd.notna(maximum):
        min_value, max_value = minimum, maximum
        legend_id = group_legend.iloc[0][_CODE]

    return legend_id, min_value, max_value


def _out_of_range_issue(
    values_filename: str,
    column: str,
    idx: int,
    value: object,
    legend_id: object | None,
    min_value: object,
    max_value: object,
) -> Issue:
    """Build one LEG-015 out-of-range `Issue`; the message key depends on the legend descriptor.

    Two catalog keys, not one key with an embedded fragment (see this module's docstring): the
    "de código 'X'"/"padrão" distinction is a full, per-locale sentence, never a raw string glued
    into a translated one.
    """
    if legend_id is None:
        return Issue(
            rule_id="LEG-015",
            severity=Severity.ERROR,
            sheet=values_filename,
            row=int(idx),
            column=column,
            message_key="rule.LEG-015.error_default",
            params={
                "filename": values_filename,
                "row": int(idx) + 2,
                "value": value,
                "min_value": min_value,
                "max_value": max_value,
                "column": column,
            },
            category=NamesEnum.LEG_RANGE.value,
        )
    return Issue(
        rule_id="LEG-015",
        severity=Severity.ERROR,
        sheet=values_filename,
        row=int(idx),
        column=column,
        message_key="rule.LEG-015.error_coded",
        params={
            "filename": values_filename,
            "row": int(idx) + 2,
            "value": value,
            "legend_id": legend_id,
            "min_value": min_value,
            "max_value": max_value,
            "column": column,
        },
        category=NamesEnum.LEG_RANGE.value,
    )


@LEGEND_REGISTRY.rule(
    rule_id="LEG-015",
    category=NamesEnum.LEG_RANGE.value,
    requires={_DESCRIPTION_SHEET: (), _VALUES_SHEET: ()},
)
def check_value_range_within_legend(ctx: RuleContext) -> list[Issue]:
    """LEG-015: every pattern-matching `valores` cell must fall inside its indicator's legend range.

    Skipped entirely when `descricao` or `valores` is empty (`requires` — the outer legacy gate
    covers both `LEG-012`…`014` and this rule identically, see this module's docstring). Aborts
    with a missing-column issue for the first absent `descricao` column, in `codigo`, `nivel`,
    then `legenda` (only when the legend file was read successfully) order — matching
    `validate_range_multiple_legend`'s own column-check order. Runs even when the legend file is
    absent or failed its own sanity check (`_legend_groups`) — every column then falls back to the
    configured default range.
    """
    description_frame = ctx.sheet(_DESCRIPTION_SHEET)
    values_frame = ctx.sheet(_VALUES_SHEET)
    description_filename = _filename(ctx, _DESCRIPTION_SHEET)
    values_filename = _filename(ctx, _VALUES_SHEET)

    required_columns: list[str] = [_CODE, _LEVEL]
    if _legend_read_success(ctx):
        required_columns.append(_LEGEND_COLUMN)
    missing_column = _first_missing_column(description_frame, required_columns)
    if missing_column is not None:
        return [_missing_column_issue("LEG-015", NamesEnum.LEG_RANGE.value, description_filename, missing_column)]

    value_unavailable = _value_data_unavailable(ctx)
    scenario_symbols = _scenario_symbols(ctx)

    values_frame_no_id = values_frame.drop(columns=[_ID]) if _ID in values_frame.columns else values_frame

    df_description, _errors = DataCleaningProcessing.clean_dataframe_integers(
        description_frame, description_filename, [_CODE], min_value=1
    )
    if _LEGEND_COLUMN in df_description.columns:
        df_description[_LEGEND_COLUMN] = pd.to_numeric(df_description[_LEGEND_COLUMN], errors="coerce").astype("Int64")
    else:
        df_description[_LEGEND_COLUMN] = pd.Series(dtype="Int64")

    level_one_codes = set(
        df_description[DataFrameProcessing.numeric_equals_mask(df_description[_LEVEL], 1)][_CODE].astype(str).tolist()
    )

    valid_columns, _unmatched = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
        items_to_categorize=values_frame_no_id.columns.tolist(),
        allowed_scenario_suffixes=scenario_symbols,
    )

    legend_groups = _legend_groups(ctx)

    issues: list[Issue] = []
    for column in valid_columns:
        indicator_id = column.split("-")[0]
        if indicator_id in level_one_codes:
            continue

        legend_id, min_value, max_value = _legend_range_for_column(ctx, indicator_id, df_description, legend_groups)

        series = values_frame_no_id[column]
        normalized = series.astype(str).str.replace(",", ".", regex=False)
        numeric = pd.to_numeric(normalized, errors="coerce")
        is_unavailable = series == value_unavailable
        out_of_range_mask = (~is_unavailable) & numeric.notna() & ((numeric < min_value) | (numeric > max_value))
        for idx in series.index[out_of_range_mask]:
            issues.append(
                _out_of_range_issue(values_filename, column, idx, series.loc[idx], legend_id, min_value, max_value)
            )

    return issues
