#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.proportionality` (Phase 3 Port 7, PROP-003…010).

Table-driven coverage per rule (happy path, each failure mode, the shared missing-column abort,
and the engine-level empty-sheet skip) built directly against the pure `check_*` functions and a
hand-built `RuleContext` — no engine beyond `TestProportionalityRegistryShape`, no mocks
(`.claude/rules/testing.md`). Proportionality frames are built by `_prop_frame` (below) rather than
`tests/factories.py::make_proportionality_frame`: that factory pairs the `id` column's level-0
placeholder as `("id", "id")`, which several ported rules would (correctly, per the legacy code)
treat as a genuine parent/indicator-code column — `_prop_frame` instead reproduces the real
`DataLoaderFacade` double-header shape, `("Unnamed: 0_level_0", "id")`.

Rewrites the untested legacy `proportionality_validator.py::SpProportionalityValidator` (deleted,
see `.specs/business-rules/proportionality.md`'s PROP-003…010 entries and ARC-017 Phase 3 Port 7),
migrating `tests/unit/validators/spreadsheets/proportionality/test_proportionality_validator.py`'s
BUG-006 (missing `id` no longer crashes past the column guard) and BUG-014 (`nivel = "1.0"` string
vs. numeric comparisons) regressions onto the new rule functions.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.rules.proportionality import (
    PROPORTIONALITY_REGISTRY,
    check_columns_repeated_indicators,
    check_parent_child_relationships,
    check_relation_indicators_in_proportionality,
    check_relation_indicators_in_value_and_proportionality,
    check_sum_properties_in_influencing_factors,
)
from data_validate.specs.issues import Severity
from tests.factories import DATA_UNAVAILABLE, make_composition_frame, make_values_frame

_PROPORCIONALIDADES = "proporcionalidades.xlsx"
_DESCRICAO = "descricao.xlsx"
_VALORES = "valores.xlsx"
_COMPOSICAO = "composicao.xlsx"


def _prop_frame(
    column_specs: list[tuple[str, str, list[str]]],
    *,
    id_values: list[str] | None = None,
    id_level1_name: str = "id",
) -> pd.DataFrame:
    """Build a `proporcionalidades`-shaped frame with an explicit, ordered column list.

    Args:
        column_specs: `(parent_column, child_column, values)` triples, in header order; the
            same `parent_column` may repeat (to test PROP-004's repeated-indicator detection).
        id_values: The `id` column's values; defaults to `"1"`, `"2"`, ... matching the first
            spec's row count.
        id_level1_name: Level-1 name of the id column; pass something other than `"id"` to
            simulate the column being absent (BUG-006 regressions).

    Returns:
        pd.DataFrame: A double-header (`MultiIndex`) frame, the id column's level 0 always
            `"Unnamed: 0_level_0"` (matching the real double-header loader's output).
    """
    if id_values is None:
        n_rows = len(column_specs[0][2]) if column_specs else 1
        id_values = [str(row) for row in range(1, n_rows + 1)]

    columns = [("Unnamed: 0_level_0", id_level1_name)]
    data: list[list[str]] = [id_values]
    for level0, level1, values in column_specs:
        columns.append((level0, level1))
        data.append(values)

    return pd.DataFrame(list(zip(*data, strict=True)), columns=pd.MultiIndex.from_tuples(columns))


def _make_context(
    *,
    proporcionalidades: pd.DataFrame | None = None,
    descricao: pd.DataFrame | None = None,
    valores: pd.DataFrame | None = None,
    composicao: pd.DataFrame | None = None,
    scenarios: list[str] | None = None,
    value_data_unavailable: str = DATA_UNAVAILABLE,
    precision_decimal_place_truncate: int = 3,
    current_language: str = "pt_BR",
) -> RuleContext:
    """Build a `RuleContext` over a proportionality-relevant bundle, every PROP option set."""
    sheets: dict[str, pd.DataFrame] = {}
    filenames: dict[str, str] = {}

    if proporcionalidades is not None:
        sheets["proporcionalidades"] = proporcionalidades
        filenames["proporcionalidades"] = _PROPORCIONALIDADES
    if descricao is not None:
        sheets["descricao"] = descricao
        filenames["descricao"] = _DESCRICAO
    if valores is not None:
        sheets["valores"] = valores
        filenames["valores"] = _VALORES
    if composicao is not None:
        sheets["composicao"] = composicao
        filenames["composicao"] = _COMPOSICAO

    return RuleContext(
        sheets=sheets,
        cleaned={},
        options={
            "filenames": filenames,
            "scenarios": scenarios or [],
            "value_data_unavailable": value_data_unavailable,
            "precision_decimal_place_truncate": precision_decimal_place_truncate,
            "current_language": current_language,
        },
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestProportionalityRegistryShape:
    """The registry declares exactly the PROP ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_prop_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in PROPORTIONALITY_REGISTRY] == [
            "PROP-003",
            "PROP-004",
            "PROP-005",
            "PROP-006",
            "PROP-007",
        ]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in PROPORTIONALITY_REGISTRY}
        assert categories == {
            "PROP-003": NamesEnum.IR.value,
            "PROP-004": NamesEnum.REP_IND_PROP.value,
            "PROP-005": NamesEnum.IND_VAL_PROP.value,
            "PROP-006": NamesEnum.IR_PROP.value,
            "PROP-007": NamesEnum.SUM_PROP.value,
        }

    def test_empty_proportionality_skips_every_rule_silently(self) -> None:
        ctx = _make_context(
            proporcionalidades=pd.DataFrame(),
            descricao=pd.DataFrame({"codigo": ["1"], "nivel": ["1"]}),
            valores=make_values_frame(),
            composicao=make_composition_frame(),
        )
        result = Engine(PROPORTIONALITY_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()


class TestCheckRelationIndicatorsInProportionality:
    """PROP-003: every non-level-1 `descricao` code must have a match in `proporcionalidades`."""

    def test_a_coherent_bundle_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2", "3"], "nivel": ["1", "2", "2"]})
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, descricao=descricao)

        assert check_relation_indicators_in_proportionality(ctx) == []

    def test_a_description_code_missing_from_proportionality_is_an_error(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2", "3", "4"], "nivel": ["1", "2", "2", "2"]})
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, descricao=descricao)

        issues = check_relation_indicators_in_proportionality(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-003"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.IR.value
        assert issue.message_key == "rule.PROP-003.missing_codes"
        assert issue.params == {"label_from": _DESCRICAO, "label_to": _PROPORCIONALIDADES, "missing_codes": "[4]"}

    def test_a_proportionality_code_missing_from_description_is_an_error(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"]})
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, descricao=descricao)

        issues = check_relation_indicators_in_proportionality(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.PROP-003.missing_codes"
        assert issue.params == {"label_from": _PROPORCIONALIDADES, "label_to": _DESCRICAO, "missing_codes": "[3]"}

    def test_a_level_one_code_stored_as_float_formatted_string_is_still_excluded(self) -> None:
        """BUG-014: `nivel = "1.0"` must still be stripped from the codes compared."""
        descricao = pd.DataFrame({"codigo": ["2", "3"], "nivel": ["1.0", "2"]})
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, descricao=descricao)

        assert check_relation_indicators_in_proportionality(ctx) == []

    @pytest.mark.parametrize("missing_column", ["codigo", "nivel"])
    def test_missing_description_column_reports_the_abort(self, missing_column: str) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]}).drop(columns=[missing_column])
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, descricao=descricao)

        issues = check_relation_indicators_in_proportionality(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column"
        assert issues[0].params == {"filename": _DESCRICAO, "column": missing_column}

    def test_missing_proportionality_id_reports_the_level2_abort(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])], id_level1_name="territorio")
        ctx = _make_context(proporcionalidades=proporcionalidades, descricao=descricao)

        issues = check_relation_indicators_in_proportionality(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column_level2"
        assert issues[0].params == {"filename": _PROPORCIONALIDADES, "column": "id"}


class TestCheckColumnsRepeatedIndicators:
    """PROP-004: a parent indicator must not appear twice (non-consecutively) on header row 1."""

    def test_distinct_parents_report_nothing(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"]), ("4-2020", "5-2020", ["1", "1"])])
        ctx = _make_context(proporcionalidades=proporcionalidades)
        assert check_columns_repeated_indicators(ctx) == []

    def test_a_consecutive_repeat_is_not_reported(self) -> None:
        """Two child columns of the same parent (consecutive) are one group, not a repeat."""
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"]), ("2-2020", "4-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades)
        assert check_columns_repeated_indicators(ctx) == []

    def test_a_non_consecutive_repeat_is_an_error(self) -> None:
        proporcionalidades = _prop_frame(
            [
                ("2-2020", "3-2020", ["0.5", "0.5"]),
                ("4-2020", "5-2020", ["1", "1"]),
                ("2-2020", "6-2020", ["0.3", "0.3"]),
            ]
        )
        ctx = _make_context(proporcionalidades=proporcionalidades)

        issues = check_columns_repeated_indicators(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-004"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.REP_IND_PROP.value
        assert issue.message_key == "rule.PROP-004.error"
        assert issue.params == {"filename": _PROPORCIONALIDADES, "parent": "2-2020"}

    def test_missing_id_reports_the_level2_abort(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5"])], id_level1_name="territorio")
        ctx = _make_context(proporcionalidades=proporcionalidades)

        issues = check_columns_repeated_indicators(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column_level2"
        assert issues[0].params == {"filename": _PROPORCIONALIDADES, "column": "id"}


class TestCheckRelationIndicatorsInValueAndProportionality:
    """PROP-005: `proporcionalidades` and `valores` column names must match."""

    def test_a_coherent_bundle_reports_nothing(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        valores = make_values_frame(codes=(2, 3))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        assert check_relation_indicators_in_value_and_proportionality(ctx) == []

    def test_a_proportionality_column_missing_from_values_is_an_error(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"]), ("6-2020", "7-2020", ["1", "1"])])
        valores = make_values_frame(codes=(2, 3))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_relation_indicators_in_value_and_proportionality(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-005"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.IND_VAL_PROP.value
        assert issue.message_key == "rule.PROP-005.missing_codes"
        assert issue.params == {
            "label_from": _PROPORCIONALIDADES,
            "label_to": _VALORES,
            "missing_codes": "['6-2020', '7-2020']",
        }

    def test_a_values_column_missing_from_proportionality_is_an_error(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        valores = make_values_frame(codes=(2, 3, 9))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_relation_indicators_in_value_and_proportionality(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.PROP-005.missing_codes"
        assert issue.params == {
            "label_from": _VALORES,
            "label_to": _PROPORCIONALIDADES,
            "missing_codes": "['9-2020']",
        }

    def test_missing_proportionality_id_reports_the_level2_abort(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])], id_level1_name="territorio")
        valores = make_values_frame(codes=(2, 3))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_relation_indicators_in_value_and_proportionality(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column_level2"
        assert issues[0].params == {"filename": _PROPORCIONALIDADES, "column": "id"}

    def test_missing_values_id_reports_the_abort(self) -> None:
        """BUG-006: a `valores` frame without `id` must not raise past the column guard."""
        proporcionalidades = _prop_frame([("2-2020", "3-2020", ["0.5", "0.5"])])
        valores = pd.DataFrame({"3-2020": ["0.50"]})
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_relation_indicators_in_value_and_proportionality(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column"
        assert issues[0].params == {"filename": _VALORES, "column": "id"}


class TestCheckParentChildRelationships:
    """PROP-006: `proporcionalidades` parent/child pairs must agree with `composicao`."""

    def test_a_coherent_bundle_reports_nothing(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 4), (2, 5)])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0.5", "0.5"]), ("2-2020", "5-2020", ["0.5", "0.5"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        assert check_parent_child_relationships(ctx) == []

    def test_a_parent_missing_from_composition_is_an_error(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 4)])
        proporcionalidades = _prop_frame([("9-2020", "8-2020", ["1", "1"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        issues = check_parent_child_relationships(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-006"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.IR_PROP.value
        assert issue.message_key == "rule.PROP-006.parent_missing"
        assert issue.params == {
            "filename": _PROPORCIONALIDADES,
            "parent": "9",
            "parent_col": "9-2020",
            "composicao_filename": _COMPOSICAO,
        }

    def test_a_child_not_in_composition_is_a_mismatch_error(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 4)])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["1", "1"]), ("2-2020", "6-2020", ["1", "1"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        issues = check_parent_child_relationships(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.PROP-006.child_mismatch"
        assert issue.params == {
            "filename": _PROPORCIONALIDADES,
            "child": "6",
            "child_col": "6-2020",
            "parent": "2",
            "parent_col": "2-2020",
            "composicao_filename": _COMPOSICAO,
        }

    def test_a_composition_child_missing_from_proportionality_is_an_error(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 4), (2, 5)])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["1", "1"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        issues = check_parent_child_relationships(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.PROP-006.child_missing"
        assert issue.params == {
            "filename": _PROPORCIONALIDADES,
            "child": "5",
            "parent": "2",
            "parent_col": "2-2020",
            "composicao_filename": _COMPOSICAO,
        }

    def test_findings_are_bucketed_child_missing_then_mismatch_then_parent_missing(self) -> None:
        """Reproduces the legacy `sorted(set(errors))` step's final order without ever
        rendering the Portuguese sentences it used to sort (see this module's docstring)."""
        composicao = make_composition_frame(edges=[(1, 2), (2, 4), (2, 5), (2, 6)])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["1", "1"]), ("2-2020", "7-2020", ["1", "1"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        issues = check_parent_child_relationships(ctx)

        message_keys = [issue.message_key for issue in issues]
        assert message_keys == [
            "rule.PROP-006.child_missing",
            "rule.PROP-006.child_missing",
            "rule.PROP-006.child_mismatch",
        ]
        assert [issue.params["child"] for issue in issues[:2]] == ["5", "6"]

    def test_missing_proportionality_id_reports_the_level2_abort(self) -> None:
        composicao = make_composition_frame(edges=[(1, 2), (2, 4)])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["1", "1"])], id_level1_name="territorio")
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        issues = check_parent_child_relationships(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column_level2"
        assert issues[0].params == {"filename": _PROPORCIONALIDADES, "column": "id"}

    @pytest.mark.parametrize("missing_column", ["codigo_pai", "codigo_filho"])
    def test_missing_composition_column_reports_the_abort(self, missing_column: str) -> None:
        composicao = make_composition_frame(edges=[(1, 2)]).drop(columns=[missing_column])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["1", "1"])])
        ctx = _make_context(proporcionalidades=proporcionalidades, composicao=composicao)

        issues = check_parent_child_relationships(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column"
        assert issues[0].params == {"filename": _COMPOSICAO, "column": missing_column}


class TestCheckSumPropertiesInInfluencingFactors:
    """PROP-007…010: factors must be numeric/DI and sum to 1 per parent/row."""

    def test_a_coherent_bundle_reports_nothing(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0.5", "0.5"]), ("2-2020", "5-2020", ["0.5", "0.5"])])
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        assert check_sum_properties_in_influencing_factors(ctx) == []

    def test_a_single_non_numeric_cell_is_a_prop_007_error(self) -> None:
        """A single invalid cell alongside two children that already sum to 1 (once the
        invalid cell is replaced by DI/0) isolates PROP-007 from PROP-010: the row's sum is
        unaffected by the invalid cell's replacement, so no tolerance issue is also raised."""
        proporcionalidades = _prop_frame(
            [
                ("2-2020", "4-2020", ["0.5"]),
                ("2-2020", "5-2020", ["0.5"]),
                ("2-2020", "6-2020", ["abc"]),
            ]
        )
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-007"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.SUM_PROP.value
        assert issue.message_key == "rule.PROP-007.error_single"
        assert issue.params == {
            "filename": _PROPORCIONALIDADES,
            "row": 3,
            "value_di": DATA_UNAVAILABLE,
            "parent": "2-2020",
        }

    def test_multiple_non_numeric_cells_are_aggregated(self) -> None:
        """Two invalid cells, in different rows; the row a cell was invalidated in still sums
        to 1 (its other cell alone equals 1), isolating PROP-007 from PROP-009/PROP-010."""
        proporcionalidades = _prop_frame(
            [
                ("2-2020", "4-2020", ["abc", "0.5", "1"]),
                ("2-2020", "5-2020", ["1", "0.5", "xyz"]),
            ]
        )
        valores = make_values_frame(codes=(9,), n_rows=3)
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.PROP-007.error_aggregate"
        assert issue.params == {
            "filename": _PROPORCIONALIDADES,
            "count": 2,
            "value_di": DATA_UNAVAILABLE,
            "parent": "2-2020",
            "first_row": 3,
            "last_row": 5,
        }

    def test_a_single_excessive_decimal_cell_is_a_prop_008_warning(self) -> None:
        """The excess-decimal cell truncates to a value that still lets the row sum to 1
        exactly, isolating PROP-008 from PROP-010."""
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0.1234"]), ("2-2020", "5-2020", ["0.877"])])
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-008"
        assert issue.severity is Severity.WARNING
        assert issue.message_key == "rule.PROP-008.warning_one"
        assert issue.params == {"filename": _PROPORCIONALIDADES, "count": 1, "first_line": 3}

    def test_multiple_excessive_decimal_cells_use_the_plural_key(self) -> None:
        proporcionalidades = _prop_frame(
            [
                ("2-2020", "4-2020", ["0.1234"]),
                ("2-2020", "5-2020", ["0.3456"]),
                ("2-2020", "6-2020", ["0.532"]),
            ]
        )
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.message_key == "rule.PROP-008.warning_many"
        assert issue.params == {"filename": _PROPORCIONALIDADES, "count": 2, "first_line": 3}

    def test_a_zero_sum_row_with_a_non_zero_value_is_a_prop_009_error(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0"])], id_values=["1"])
        valores = pd.DataFrame({"id": ["1"], "4-2020": ["5"]})
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-009"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.PROP-009.error"
        assert issue.params == {
            "filename": _PROPORCIONALIDADES,
            "id": "1",
            "col": "4-2020",
            "values_filename": _VALORES,
        }

    def test_a_zero_sum_row_with_a_zero_value_reports_nothing(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0"])], id_values=["1"])
        valores = pd.DataFrame({"id": ["1"], "4-2020": ["0"]})
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        assert check_sum_properties_in_influencing_factors(ctx) == []

    def test_a_sum_outside_tolerance_is_a_prop_010_error(self) -> None:
        proporcionalidades = _prop_frame(
            [("2-2020", "4-2020", ["0.30"]), ("2-2020", "5-2020", ["0.30"])], id_values=["1"]
        )
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-010"
        assert issue.severity is Severity.ERROR
        assert issue.message_key == "rule.PROP-010.error"
        assert issue.params == {"filename": _PROPORCIONALIDADES, "row": 3, "parent": "2-2020", "sum": "0,6"}

    def test_a_sum_within_tolerance_but_not_one_is_a_prop_010_warning(self) -> None:
        proporcionalidades = _prop_frame(
            [("2-2020", "4-2020", ["0.500"]), ("2-2020", "5-2020", ["0.495"])], id_values=["1"]
        )
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "PROP-010"
        assert issue.severity is Severity.WARNING
        assert issue.message_key == "rule.PROP-010.warning"
        assert issue.params == {"filename": _PROPORCIONALIDADES, "row": 3, "parent": "2-2020", "sum": "0,995"}

    def test_sum_is_formatted_per_current_language(self) -> None:
        proporcionalidades = _prop_frame(
            [("2-2020", "4-2020", ["0.30"]), ("2-2020", "5-2020", ["0.30"])], id_values=["1"]
        )
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores, current_language="en_US")

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert issues[0].params["sum"] == "0.6"

    def test_missing_proportionality_id_reports_the_level2_abort(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0.5"])], id_level1_name="territorio")
        valores = make_values_frame(codes=(9,))
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column_level2"
        assert issues[0].params == {"filename": _PROPORCIONALIDADES, "column": "id"}

    def test_missing_values_id_reports_the_abort(self) -> None:
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0.5"])])
        valores = pd.DataFrame({"4-2020": ["0.50"]})
        ctx = _make_context(proporcionalidades=proporcionalidades, valores=valores)

        issues = check_sum_properties_in_influencing_factors(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.proportionality.missing_required_column"
        assert issues[0].params == {"filename": _VALORES, "column": "id"}


class TestIdempotency:
    """BUG-001: no rule here holds shared mutable state — calling one twice must be stable."""

    def test_every_check_is_idempotent_on_the_same_context(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2", "3"], "nivel": ["1", "2", "2"]})
        composicao = make_composition_frame(edges=[(1, 2), (2, 4), (2, 5)])
        proporcionalidades = _prop_frame([("2-2020", "4-2020", ["0.5", "0.5"]), ("2-2020", "5-2020", ["0.5", "0.5"])])
        valores = make_values_frame(codes=(4, 5))
        ctx = _make_context(
            proporcionalidades=proporcionalidades, descricao=descricao, valores=valores, composicao=composicao
        )

        assert check_relation_indicators_in_proportionality(ctx) == check_relation_indicators_in_proportionality(ctx)
        assert check_columns_repeated_indicators(ctx) == check_columns_repeated_indicators(ctx)
        assert check_relation_indicators_in_value_and_proportionality(
            ctx
        ) == check_relation_indicators_in_value_and_proportionality(ctx)
        assert check_parent_child_relationships(ctx) == check_parent_child_relationships(ctx)
        assert check_sum_properties_in_influencing_factors(ctx) == check_sum_properties_in_influencing_factors(ctx)
