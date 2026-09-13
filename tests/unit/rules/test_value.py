#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `data_validate.rules.value` (Phase 3 Port 5, VAL-002…005).

Table-driven coverage per rule (happy path, each failure mode, missing-column abort, and the
engine-level empty-sheet skip) built directly against the pure `check_*` functions and a
hand-built `RuleContext` — no engine, no mocks (`.claude/rules/testing.md`).

Rewrites the deleted `value_validator.py::SpValueValidator` (see
`.specs/business-rules/values.md`'s VAL-002…005 entries and ARC-017 Phase 3 Port 5), migrating
the regression tests from
`tests/unit/validators/spreadsheets/value/test_value_validator.py` (deleted):

- BUG-001 (shared-list mutation): every `check_*` function here is a pure `RuleContext ->
  list[Issue]` read with no shared mutable state, so `TestIdempotency` pins that calling any
  rule twice on the same context returns equal results.
- BUG-014 (string `nivel` comparison): `TestCheckRelationIndicatorsInValues::
  test_a_level_one_indicator_stored_as_float_formatted_string_is_still_excluded` reproduces the
  legacy regression (a level 1 indicator stored as `nivel = "1.0"` must not be reported missing
  from `valores`).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from data_validate.config import NamesEnum
from data_validate.rules.context import RuleContext
from data_validate.rules.engine import Engine, RuleStatus
from data_validate.rules.value import (
    VALUE_REGISTRY,
    check_excessive_decimal_places,
    check_id_uniqueness,
    check_relation_indicators_in_values,
    check_unavailable_and_invalid_values,
    check_value_combination_relation,
)
from data_validate.specs.issues import Severity
from tests.factories import make_scenario_frame

_VALORES = "valores.xlsx"
_DESCRICAO = "descricao.xlsx"
_TEMPORAL = "referencia_temporal.xlsx"
_CENARIOS = "cenarios.xlsx"


def _temporal_frame(*years: int) -> pd.DataFrame:
    """Build a minimal `referencia_temporal` sheet whose `simbolo` IS the calendar year.

    `tests.factories.make_temporal_frame` deliberately decouples `simbolo` (a sequential index)
    from `nome`/the calendar year, which does not match `<código>-<ano>` `valores` columns built
    from real years (`.specs/business-rules/temporal-reference.md`: `simbolo` is "used as `<ano>`
    in value columns") — VAL-003 needs `simbolo` to equal the year suffix its `valores` columns
    under test actually use.
    """
    return pd.DataFrame({"simbolo": [str(year) for year in years]})


def _make_context(
    *,
    valores: pd.DataFrame | None = None,
    descricao: pd.DataFrame | None = None,
    referencia_temporal: pd.DataFrame | None = None,
    cenarios: pd.DataFrame | None = None,
    scenarios: list[str] | None = None,
    scenario_exists_file: bool = False,
) -> RuleContext:
    """Build a `RuleContext` wrapping whichever `valores`-domain sheets a test needs."""
    sheets: dict[str, pd.DataFrame] = {}
    filenames: dict[str, str] = {}
    for name, frame, filename in (
        ("valores", valores, _VALORES),
        ("descricao", descricao, _DESCRICAO),
        ("referencia_temporal", referencia_temporal, _TEMPORAL),
        ("cenarios", cenarios, _CENARIOS),
    ):
        if frame is not None:
            sheets[name] = frame
            filenames[name] = filename

    return RuleContext(
        sheets=sheets,
        cleaned={},
        options={
            "filenames": filenames,
            "scenarios": scenarios or [],
            "scenario_exists_file": scenario_exists_file,
        },
        translate=lambda key, **params: key,
        clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )


class TestValueRegistryShape:
    """The registry declares exactly the VAL ids in the legacy validator's run() order."""

    def test_registry_contains_every_ported_val_id_in_legacy_order(self) -> None:
        assert [spec.rule_id for spec in VALUE_REGISTRY] == [
            "VAL-002",
            "VAL-003",
            "VAL-004",
            "VAL-005",
            "VAL-006",
        ]

    def test_every_spec_declares_its_documented_category(self) -> None:
        categories = {spec.rule_id: spec.category for spec in VALUE_REGISTRY}
        assert categories == {
            "VAL-002": NamesEnum.IR.value,
            "VAL-003": NamesEnum.VAL_COMB.value,
            "VAL-004": NamesEnum.UNAV_INV.value,
            "VAL-005": NamesEnum.UNAV_INV.value,
            "VAL-006": NamesEnum.UNIQ_VAL.value,
        }

    def test_empty_values_sheet_skips_every_rule_silently(self) -> None:
        ctx = _make_context(valores=pd.DataFrame())
        result = Engine(VALUE_REGISTRY).run(ctx)
        assert all(outcome.status is RuleStatus.SKIPPED for outcome in result.outcomes)
        assert result.validation_result.issues == ()

    def test_a_non_list_scenarios_option_is_treated_as_no_scenarios(self) -> None:
        """`ctx.options["scenarios"]` is an untyped `Mapping[str, object]` value; a caller that
        passes something other than a `list` must not crash `_scenario_symbols`."""
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        valores = pd.DataFrame({"id": ["1"]})
        ctx = RuleContext(
            sheets={"valores": valores, "descricao": descricao},
            cleaned={},
            options={"filenames": {}, "scenarios": None},
            translate=lambda key, **params: key,
            clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
        )

        assert check_relation_indicators_in_values(ctx) == []


class TestCheckRelationIndicatorsInValues:
    """VAL-002: every `valores` column and every `descricao` code (except level 1) must match."""

    def test_a_coherent_bundle_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2", "3"], "nivel": ["1", "2", "2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"], "3-2020": ["20.00"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        assert check_relation_indicators_in_values(ctx) == []

    @pytest.mark.parametrize("missing_column", ["codigo", "nivel"])
    def test_missing_description_column_reports_an_error(self, missing_column: str) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]}).drop(columns=[missing_column])
        valores = pd.DataFrame({"id": ["1"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        issues = check_relation_indicators_in_values(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.value.missing_required_column"
        assert issues[0].params == {"filename": _DESCRICAO, "column": missing_column}

    def test_both_missing_description_columns_are_reported_in_order(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]}).drop(columns=["codigo", "nivel"])
        valores = pd.DataFrame({"id": ["1"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        issues = check_relation_indicators_in_values(ctx)

        assert [issue.params["column"] for issue in issues] == ["codigo", "nivel"]

    def test_missing_scenario_symbol_column_is_reported_when_scenarios_exist(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        valores = pd.DataFrame({"id": ["1"]})
        ctx = _make_context(valores=valores, descricao=descricao, scenario_exists_file=True)

        issues = check_relation_indicators_in_values(ctx)

        assert len(issues) == 1
        assert issues[0].params == {"filename": "cenarios", "column": "simbolo"}

    def test_invalid_columns_are_reported(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"], "abc": ["1.00"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        issues = check_relation_indicators_in_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-002.invalid_columns"
        assert issues[0].params == {"filename": _VALORES, "invalid_columns": "['abc']"}

    def test_a_column_containing_a_colon_is_not_reported_as_invalid(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        valores = pd.DataFrame({"id": ["1"], "abr/2017:x": ["1.00"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        assert check_relation_indicators_in_values(ctx) == []

    def test_a_description_code_missing_from_values_is_reported(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2", "5"], "nivel": ["1", "2", "2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        issues = check_relation_indicators_in_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-002.missing_codes"
        assert issues[0].params == {"label_from": _DESCRICAO, "label_to": _VALORES, "missing_codes": "[5]"}

    def test_a_values_code_missing_from_description_is_reported(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"], "9-2020": ["5.00"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        issues = check_relation_indicators_in_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-002.missing_codes"
        assert issues[0].params == {"label_from": _VALORES, "label_to": _DESCRICAO, "missing_codes": "[9]"}

    def test_level_one_indicators_are_excluded_from_the_comparison(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        valores = pd.DataFrame({"id": ["1"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        assert check_relation_indicators_in_values(ctx) == []

    def test_a_level_one_indicator_stored_as_float_formatted_string_is_still_excluded(self) -> None:
        """BUG-014: `nivel = "1.0"` must still be recognised as level 1, not compared."""
        descricao = pd.DataFrame({"codigo": ["5008"], "nivel": ["1.0"]})
        valores = pd.DataFrame({"id": ["1"]})
        ctx = _make_context(valores=valores, descricao=descricao)

        assert check_relation_indicators_in_values(ctx) == []

    def test_level_two_with_scenario_zero_is_excluded_when_scenarios_exist(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "5"], "nivel": ["1", "2"], "cenario": ["0", "0"]})
        valores = pd.DataFrame({"id": ["1"]})
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        assert check_relation_indicators_in_values(ctx) == []


class TestCheckValueCombinationRelation:
    """VAL-003: each indicator must have exactly its expected `valores` time/scenario columns."""

    def test_a_coherent_bundle_without_scenarios_reports_nothing(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"]})
        referencia_temporal = _temporal_frame(2020)
        ctx = _make_context(valores=valores, descricao=descricao, referencia_temporal=referencia_temporal)

        assert check_value_combination_relation(ctx) == []

    @pytest.mark.parametrize(
        "missing_from,missing_column",
        [("valores", "id"), ("descricao", "codigo"), ("descricao", "nivel"), ("referencia_temporal", "simbolo")],
    )
    def test_missing_required_column_is_reported(self, missing_from: str, missing_column: str) -> None:
        frames = {
            "valores": pd.DataFrame({"id": ["1"]}),
            "descricao": pd.DataFrame({"codigo": ["1"], "nivel": ["1"]}),
            "referencia_temporal": _temporal_frame(2020),
        }
        frames[missing_from] = frames[missing_from].drop(columns=[missing_column])
        ctx = _make_context(
            valores=frames["valores"], descricao=frames["descricao"], referencia_temporal=frames["referencia_temporal"]
        )

        issues = check_value_combination_relation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.value.missing_required_column"
        filenames = {"valores": _VALORES, "descricao": _DESCRICAO, "referencia_temporal": _TEMPORAL}
        assert issues[0].params == {"filename": filenames[missing_from], "column": missing_column}

    def test_missing_description_cenario_column_is_reported_when_scenarios_exist(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        valores = pd.DataFrame({"id": ["1"]})
        referencia_temporal = _temporal_frame(2020)
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        issues = check_value_combination_relation(ctx)

        assert any(issue.params.get("column") == "cenario" for issue in issues)

    def test_missing_scenario_symbol_column_is_reported_when_scenarios_exist(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"], "cenario": ["0"]})
        valores = pd.DataFrame({"id": ["1"]})
        referencia_temporal = _temporal_frame(2020)
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        issues = check_value_combination_relation(ctx)

        assert any(issue.params == {"filename": "cenarios", "column": "simbolo"} for issue in issues)

    def test_a_missing_required_combination_is_reported(self) -> None:
        # Level 3 (not 2), so a missing base-year column is a real violation, not the
        # level-2/scenario-0 special case silently tolerated below.
        descricao = pd.DataFrame({"codigo": ["1", "2", "5"], "nivel": ["1", "2", "3"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"]})
        referencia_temporal = _temporal_frame(2020)
        ctx = _make_context(valores=valores, descricao=descricao, referencia_temporal=referencia_temporal)

        issues = check_value_combination_relation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-003.required_column"
        assert issues[0].params == {"filename": _VALORES, "combination": "5-2020"}

    def test_an_unnecessary_column_is_reported(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"], "2-2021": ["10.00"]})
        referencia_temporal = _temporal_frame(2020)
        ctx = _make_context(valores=valores, descricao=descricao, referencia_temporal=referencia_temporal)

        issues = check_value_combination_relation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-003.unnecessary_column"
        assert issues[0].params == {"filename": _VALORES, "extra_column": "2-2021"}

    def test_an_unnecessary_column_for_a_level_one_indicator_uses_the_level1_message(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1"], "nivel": ["1"]})
        valores = pd.DataFrame({"id": ["1"], "1-2020": ["10.00"]})
        referencia_temporal = _temporal_frame(2020)
        ctx = _make_context(valores=valores, descricao=descricao, referencia_temporal=referencia_temporal)

        issues = check_value_combination_relation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-003.unnecessary_column_level1"
        assert issues[0].params == {"filename": _VALORES, "extra_column": "1-2020"}

    def test_level_two_scenario_zero_uses_only_the_base_year_column(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"], "cenario": ["0", "0"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"]})
        referencia_temporal = _temporal_frame(2020, 2021)
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        assert check_value_combination_relation(ctx) == []

    def test_level_two_scenario_zero_missing_base_year_column_is_silently_tolerated(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"], "cenario": ["0", "0"]})
        valores = pd.DataFrame({"id": ["1"]})
        referencia_temporal = _temporal_frame(2020)
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        assert check_value_combination_relation(ctx) == []

    def test_level_two_scenario_one_expects_the_full_temporal_scenario_matrix(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"], "cenario": ["0", "1"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"], "2-2021-O": ["10.00"]})
        referencia_temporal = _temporal_frame(2020, 2021)
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        assert check_value_combination_relation(ctx) == []

    def test_a_scenario_value_outside_zero_or_one_expects_no_combination_at_all(self) -> None:
        """Gap G-09: `cenario` values other than 0/1 yield no expected columns."""
        descricao = pd.DataFrame({"codigo": ["1", "5"], "nivel": ["1", "2"], "cenario": ["0", "2"]})
        valores = pd.DataFrame({"id": ["1"], "5-2020": ["10.00"]})
        referencia_temporal = _temporal_frame(2020)
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        issues = check_value_combination_relation(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-003.unnecessary_column"
        assert issues[0].params == {"filename": _VALORES, "extra_column": "5-2020"}


class TestCheckUnavailableAndInvalidValues:
    """VAL-004: every pattern-matching `valores` cell must be `DI` or parse as a number."""

    def test_valid_numbers_and_di_report_nothing(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2"], "2-2020": ["10.50", "DI"]})
        ctx = _make_context(valores=valores)

        assert check_unavailable_and_invalid_values(ctx) == []

    def test_a_single_invalid_cell_is_reported_with_its_value_and_row(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2"], "2-2020": ["10.50", "abc"]})
        ctx = _make_context(valores=valores)

        issues = check_unavailable_and_invalid_values(ctx)

        assert len(issues) == 1
        assert issues[0].rule_id == "VAL-004"
        assert issues[0].severity is Severity.ERROR
        assert issues[0].category == NamesEnum.UNAV_INV.value
        assert issues[0].message_key == "rule.VAL-004.error"
        assert issues[0].params == {"filename": _VALORES, "row": 3, "value": "abc", "column": "2-2020"}

    def test_multiple_invalid_cells_in_one_column_are_aggregated(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2", "3"], "2-2020": ["abc", "10.50", "xyz"]})
        ctx = _make_context(valores=valores)

        issues = check_unavailable_and_invalid_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-004.aggregate"
        assert issues[0].params == {
            "filename": _VALORES,
            "count": 2,
            "column": "2-2020",
            "first_row": 2,
            "last_row": 4,
        }

    def test_the_id_column_is_never_analyzed(self) -> None:
        valores = pd.DataFrame({"id": ["abc", "def"], "2-2020": ["10.50", "20.50"]})
        ctx = _make_context(valores=valores)

        assert check_unavailable_and_invalid_values(ctx) == []

    def test_a_column_not_matching_the_id_year_pattern_is_never_analyzed(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "notes": ["not a number"]})
        ctx = _make_context(valores=valores)

        assert check_unavailable_and_invalid_values(ctx) == []

    def test_a_literal_float_infinity_cell_is_reported_with_the_silent_message(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2"], "2-2020": ["10.50", float("inf")]})
        ctx = _make_context(valores=valores)

        issues = check_unavailable_and_invalid_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-004.silent"
        assert issues[0].params == {}

    def test_a_textual_infinity_cell_is_reported_with_the_decimal_parse_error_message(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2"], "2-2020": ["10.50", "inf"]})
        ctx = _make_context(valores=valores)

        issues = check_unavailable_and_invalid_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-004.decimal_parse_error"
        assert issues[0].params == {"filename": _VALORES, "row": 3, "column": "2-2020"}

    def test_missing_scenario_symbol_column_is_reported_when_scenarios_exist(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.50"]})
        ctx = _make_context(valores=valores, scenario_exists_file=True)

        issues = check_unavailable_and_invalid_values(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.value.missing_required_column"
        assert issues[0].params == {"filename": "cenarios", "column": "simbolo"}


class TestCheckExcessiveDecimalPlaces:
    """VAL-005: numeric `valores` cells with more than two decimal places are counted, once."""

    def test_two_decimal_values_report_nothing(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.50"]})
        ctx = _make_context(valores=valores)

        assert check_excessive_decimal_places(ctx) == []

    def test_a_single_excessive_value_reports_the_singular_message(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.555"]})
        ctx = _make_context(valores=valores)

        issues = check_excessive_decimal_places(ctx)

        assert len(issues) == 1
        assert issues[0].rule_id == "VAL-005"
        assert issues[0].severity is Severity.WARNING
        assert issues[0].category == NamesEnum.UNAV_INV.value
        assert issues[0].message_key == "rule.VAL-005.warning_one"
        assert issues[0].params == {"filename": _VALORES, "count": 1, "first_row": 2, "last_row": 2}

    def test_excessive_values_across_columns_are_summed_with_the_plural_message(self) -> None:
        valores = pd.DataFrame(
            {
                "id": ["1", "2"],
                "2-2020": ["10.555", "20.50"],
                "3-2020": ["30.50", "40.123"],
            }
        )
        ctx = _make_context(valores=valores)

        issues = check_excessive_decimal_places(ctx)

        assert len(issues) == 1
        assert issues[0].message_key == "rule.VAL-005.warning_many"
        assert issues[0].params == {"filename": _VALORES, "count": 2, "first_row": 2, "last_row": 3}

    def test_an_invalid_cell_is_not_also_counted_as_excessive(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["abc"]})
        ctx = _make_context(valores=valores)

        assert check_excessive_decimal_places(ctx) == []

    def test_di_is_not_counted_as_excessive(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["DI"]})
        ctx = _make_context(valores=valores)

        assert check_excessive_decimal_places(ctx) == []

    def test_missing_scenario_symbol_column_reports_nothing(self) -> None:
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.555"]})
        ctx = _make_context(valores=valores, scenario_exists_file=True)

        assert check_excessive_decimal_places(ctx) == []


class TestCheckIdUniqueness:
    """VAL-006 (PROTO-017, gap G-13): `valores.id` must contain no duplicated value."""

    def test_unique_ids_report_nothing(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2", "3"], "2-2020": ["1.00", "2.00", "3.00"]})
        ctx = _make_context(valores=valores)
        assert check_id_uniqueness(ctx) == []

    def test_a_duplicated_id_is_reported(self) -> None:
        valores = pd.DataFrame({"id": ["1", "2", "1"], "2-2020": ["1.00", "2.00", "3.00"]})
        ctx = _make_context(valores=valores)

        issues = check_id_uniqueness(ctx)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.rule_id == "VAL-006"
        assert issue.severity is Severity.ERROR
        assert issue.category == NamesEnum.UNIQ_VAL.value
        assert issue.message_key == "rule.VAL-006.error"
        assert issue.params == {"filename": _VALORES, "column": "id", "duplicated_ids": "['1']"}

    def test_missing_column_reports_an_error(self) -> None:
        valores = pd.DataFrame({"2-2020": ["1.00"]})
        ctx = _make_context(valores=valores)

        issues = check_id_uniqueness(ctx)

        assert len(issues) == 1
        assert issues[0].severity is Severity.ERROR
        assert issues[0].message_key == "rule.value.missing_required_column"
        assert issues[0].params == {"filename": _VALORES, "column": "id"}


class TestIdempotency:
    """BUG-001: no rule here holds shared mutable state — calling one twice must be stable."""

    def test_every_check_is_idempotent_on_the_same_context(self) -> None:
        descricao = pd.DataFrame({"codigo": ["1", "2"], "nivel": ["1", "2"], "cenario": ["0", "1"]})
        valores = pd.DataFrame({"id": ["1"], "2-2020": ["10.00"], "2-2021-O": ["10.555"], "9-2020": ["abc"]})
        referencia_temporal = _temporal_frame(2020, 2021)
        cenarios = make_scenario_frame(symbols=("O",))
        ctx = _make_context(
            valores=valores,
            descricao=descricao,
            referencia_temporal=referencia_temporal,
            cenarios=cenarios,
            scenarios=["O"],
            scenario_exists_file=True,
        )

        assert check_relation_indicators_in_values(ctx) == check_relation_indicators_in_values(ctx)
        assert check_value_combination_relation(ctx) == check_value_combination_relation(ctx)
        assert check_unavailable_and_invalid_values(ctx) == check_unavailable_and_invalid_values(ctx)
        assert check_excessive_decimal_places(ctx) == check_excessive_decimal_places(ctx)
        assert check_id_uniqueness(ctx) == check_id_uniqueness(ctx)
