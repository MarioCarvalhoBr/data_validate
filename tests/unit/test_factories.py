#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Table-driven tests for the in-memory bundle factories (TST-010).

Asserts that every factory in `tests.factories` produces columns declared in
`data_validate.specs.SHEET_SPECS`, uses plain-`str` cells (mirroring the loaders' `dtype=str`),
and honours the protocol invariant it claims to (sequential codes, period-terminated
descriptions, continuous legend intervals, weights summing to 1, a coherent `+2`-level
proportionality bundle, ...).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
import pytest

from data_validate.specs import SHEET_SPECS
from tests.factories import (
    DATA_UNAVAILABLE,
    LABEL_DATA_UNAVAILABLE,
    di_at,
    make_bundle,
    make_composition_frame,
    make_description_frame,
    make_legend_frame,
    make_proportionality_frame,
    make_scenario_frame,
    make_temporal_frame,
    make_values_frame,
)


def _assert_all_str_cells(frame: pd.DataFrame) -> None:
    """Assert every cell in `frame` is a plain Python `str` (loaders' `dtype=str`)."""
    for column in frame.columns:
        values = frame[column].tolist()
        assert all(isinstance(value, str) for value in values), f"column {column!r} has a non-str cell"


class TestMakeDescriptionFrame:
    """`make_description_frame` builds a coherent `descricao` sheet."""

    def test_default_columns_are_declared_in_sheet_specs(self) -> None:
        frame = make_description_frame()
        declared = set(SHEET_SPECS["descricao"].column_names)
        assert set(frame.columns) <= declared
        required_names = {column.name for column in SHEET_SPECS["descricao"].required_columns}
        assert required_names <= set(frame.columns)

    def test_default_cells_are_str(self) -> None:
        _assert_all_str_cells(make_description_frame())

    @pytest.mark.parametrize("n_indicators", [1, 2, 5])
    def test_codigo_is_sequential_from_one(self, n_indicators: int) -> None:
        frame = make_description_frame(n_indicators)
        assert frame["codigo"].tolist() == [str(code) for code in range(1, n_indicators + 1)]

    def test_default_levels_are_root_then_children(self) -> None:
        frame = make_description_frame(4)
        assert frame["nivel"].tolist() == ["1", "2", "2", "2"]

    def test_names_are_unique_per_row(self) -> None:
        frame = make_description_frame(5)
        assert frame["nome_simples"].is_unique
        assert frame["nome_completo"].is_unique

    def test_desc_completa_ends_with_a_period_desc_simples_does_not(self) -> None:
        """PROTO-005: the protocol forbids a trailing period on `desc_simples` (DESC-006)."""
        frame = make_description_frame(3)
        assert not frame["desc_simples"].str.endswith(".").any()
        assert frame["desc_completa"].str.endswith(".").all()

    def test_with_scenario_column_adds_cenario(self) -> None:
        frame = make_description_frame(2, with_scenario_column=True)
        assert "cenario" in frame.columns
        assert (frame["cenario"] == "0").all()

    def test_with_legend_column_adds_legenda(self) -> None:
        frame = make_description_frame(2, with_legend_column=True)
        assert "legenda" in frame.columns
        assert (frame["legenda"] == "1").all()

    def test_without_dynamic_flags_omits_dynamic_columns(self) -> None:
        frame = make_description_frame(2)
        assert "cenario" not in frame.columns
        assert "legenda" not in frame.columns

    def test_overrides_replace_generated_column(self) -> None:
        frame = make_description_frame(2, nome_simples=["Custom A", "Custom B"])
        assert frame["nome_simples"].tolist() == ["Custom A", "Custom B"]

    def test_overrides_append_plural_column_not_in_sheet_specs(self) -> None:
        frame = make_description_frame(2, nomes_simples=["Group A", "Group A"])
        assert frame["nomes_simples"].tolist() == ["Group A", "Group A"]

    def test_zero_indicators_raises(self) -> None:
        with pytest.raises(ValueError, match="n_indicators"):
            make_description_frame(0)

    def test_wrong_length_levels_raises(self) -> None:
        with pytest.raises(ValueError, match="levels"):
            make_description_frame(3, levels=[1, 2])

    def test_root_level_not_one_raises(self) -> None:
        with pytest.raises(ValueError, match="nivel 1"):
            make_description_frame(2, levels=[2, 2])

    def test_child_level_below_one_raises(self) -> None:
        with pytest.raises(ValueError, match="nivel must be >= 1"):
            make_description_frame(2, levels=[1, 0])

    def test_override_wrong_length_raises(self) -> None:
        with pytest.raises(ValueError, match="nome_simples"):
            make_description_frame(3, nome_simples=["only one"])


class TestMakeCompositionFrame:
    """`make_composition_frame` builds a coherent `composicao` sheet."""

    def test_columns_match_sheet_specs(self) -> None:
        frame = make_composition_frame()
        assert list(frame.columns) == list(SHEET_SPECS["composicao"].column_names)

    def test_cells_are_str(self) -> None:
        _assert_all_str_cells(make_composition_frame())

    def test_default_edges_attach_every_child_to_root(self) -> None:
        frame = make_composition_frame(n_indicators=4)
        assert frame["codigo_pai"].tolist() == ["1", "1", "1"]
        assert frame["codigo_filho"].tolist() == ["2", "3", "4"]

    def test_explicit_edges_are_honoured(self) -> None:
        frame = make_composition_frame(edges=[(1, 2), (2, 3)])
        assert frame["codigo_pai"].tolist() == ["1", "2"]
        assert frame["codigo_filho"].tolist() == ["2", "3"]

    def test_single_indicator_has_no_edges(self) -> None:
        frame = make_composition_frame(n_indicators=1)
        assert frame.empty
        assert list(frame.columns) == ["codigo_pai", "codigo_filho"]

    def test_zero_indicators_raises(self) -> None:
        with pytest.raises(ValueError, match="n_indicators"):
            make_composition_frame(n_indicators=0)

    @pytest.mark.parametrize("edges", [[(0, 2)], [(1, 0)]])
    def test_edge_below_one_raises(self, edges: list[tuple[int, int]]) -> None:
        with pytest.raises(ValueError, match=">= 1"):
            make_composition_frame(edges=edges)


class TestMakeValuesFrame:
    """`make_values_frame` builds a coherent `valores` sheet."""

    def test_id_column_is_declared_in_sheet_specs(self) -> None:
        frame = make_values_frame()
        assert set(SHEET_SPECS["valores"].column_names) <= set(frame.columns)

    def test_cells_are_str(self) -> None:
        _assert_all_str_cells(make_values_frame())

    def test_id_is_sequential_from_one(self) -> None:
        frame = make_values_frame(n_rows=3)
        assert frame["id"].tolist() == ["1", "2", "3"]

    def test_column_name_without_scenario_matches_code_year_pattern(self) -> None:
        frame = make_values_frame(codes=(7,), years=(2021,))
        assert "7-2021" in frame.columns

    def test_column_name_with_scenario_matches_code_year_scenario_pattern(self) -> None:
        frame = make_values_frame(codes=(7,), years=(2021,), scenarios=("O", "P"))
        assert "7-2021-O" in frame.columns
        assert "7-2021-P" in frame.columns

    def test_values_have_at_most_two_decimals(self) -> None:
        frame = make_values_frame(codes=(2,), years=(2020,), n_rows=2)
        for value in frame["2-2020"]:
            exponent = int(Decimal(value).as_tuple().exponent)
            assert -exponent <= 2

    @pytest.mark.parametrize("kwargs", [{"codes": ()}, {"years": ()}, {"n_rows": 0}])
    def test_empty_dimension_raises(self, kwargs: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            make_values_frame(**kwargs)

    def test_di_at_injects_marker_without_mutating_original(self) -> None:
        frame = make_values_frame(codes=(2,), years=(2020,), n_rows=2)
        column = "2-2020"
        original_value = frame.loc[0, column]

        updated = di_at(frame, 0, column)

        assert updated.loc[0, column] == DATA_UNAVAILABLE
        assert frame.loc[0, column] == original_value

    def test_di_at_unknown_column_raises(self) -> None:
        frame = make_values_frame()
        with pytest.raises(ValueError, match="not in frame"):
            di_at(frame, 0, "does-not-exist")


class TestMakeTemporalFrame:
    """`make_temporal_frame` builds a coherent `referencia_temporal` sheet."""

    def test_columns_match_sheet_specs(self) -> None:
        frame = make_temporal_frame()
        assert list(frame.columns) == list(SHEET_SPECS["referencia_temporal"].column_names)

    def test_cells_are_str(self) -> None:
        _assert_all_str_cells(make_temporal_frame())

    def test_default_has_exactly_one_row(self) -> None:
        frame = make_temporal_frame()
        assert len(frame) == 1

    def test_descricao_ends_with_a_period(self) -> None:
        frame = make_temporal_frame(years=(2020, 2021))
        assert frame["descricao"].str.endswith(".").all()

    def test_simbolo_values_are_unique(self) -> None:
        frame = make_temporal_frame(years=(2020, 2021, 2022))
        assert frame["simbolo"].is_unique

    def test_empty_years_raises(self) -> None:
        with pytest.raises(ValueError, match="years"):
            make_temporal_frame(years=())


class TestMakeScenarioFrame:
    """`make_scenario_frame` builds a coherent `cenarios` sheet."""

    def test_columns_match_sheet_specs(self) -> None:
        frame = make_scenario_frame()
        assert list(frame.columns) == list(SHEET_SPECS["cenarios"].column_names)

    def test_cells_are_str(self) -> None:
        _assert_all_str_cells(make_scenario_frame())

    def test_simbolo_matches_requested_symbols(self) -> None:
        frame = make_scenario_frame(symbols=("O", "P"))
        assert frame["simbolo"].tolist() == ["O", "P"]

    def test_empty_symbols_raises(self) -> None:
        with pytest.raises(ValueError, match="symbols"):
            make_scenario_frame(symbols=())

    def test_duplicate_symbols_raises(self) -> None:
        with pytest.raises(ValueError, match="unique"):
            make_scenario_frame(symbols=("O", "O"))


class TestMakeLegendFrame:
    """`make_legend_frame` builds a coherent `legenda` sheet."""

    def test_columns_match_sheet_specs(self) -> None:
        frame = make_legend_frame()
        assert list(frame.columns) == list(SHEET_SPECS["legenda"].column_names)

    def test_cells_are_str(self) -> None:
        _assert_all_str_cells(make_legend_frame())

    def test_exactly_one_di_row_per_code(self) -> None:
        frame = make_legend_frame(codes=(1, 2))
        for code in ("1", "2"):
            group = frame[frame["codigo"] == code]
            di_rows = group[group["label"] == LABEL_DATA_UNAVAILABLE]
            assert len(di_rows) == 1
            assert (di_rows["minimo"] == "").all()
            assert (di_rows["maximo"] == "").all()

    def test_without_di_row_omits_it(self) -> None:
        frame = make_legend_frame(codes=(1,), with_di_row=False)
        assert (frame["label"] == LABEL_DATA_UNAVAILABLE).sum() == 0

    def test_intervals_are_continuous(self) -> None:
        frame = make_legend_frame(codes=(1,), with_di_row=False)
        maximos = [Decimal(value) for value in frame["maximo"]]
        minimos = [Decimal(value) for value in frame["minimo"]]
        for previous_maximo, next_minimo in zip(maximos[:-1], minimos[1:], strict=True):
            assert next_minimo == previous_maximo + Decimal("0.01")

    def test_ordem_is_sequential_per_code(self) -> None:
        frame = make_legend_frame(codes=(1,))
        assert frame["ordem"].tolist() == ["1", "2", "3"]

    def test_cor_is_a_valid_hex_color(self) -> None:
        frame = make_legend_frame(codes=(1,))
        assert frame["cor"].str.match(r"^#[0-9A-Fa-f]{6}$").all()

    def test_empty_codes_raises(self) -> None:
        with pytest.raises(ValueError, match="codes"):
            make_legend_frame(codes=())


class TestMakeProportionalityFrame:
    """`make_proportionality_frame` reproduces the double-header MultiIndex shape."""

    def test_columns_are_a_two_level_multiindex(self) -> None:
        frame = make_proportionality_frame()
        assert isinstance(frame.columns, pd.MultiIndex)
        assert frame.columns.nlevels == 2

    def test_id_column_pair_is_present(self) -> None:
        frame = make_proportionality_frame()
        assert ("id", "id") in frame.columns

    def test_cells_are_str(self) -> None:
        _assert_all_str_cells(make_proportionality_frame())

    def test_default_has_one_parent_with_two_children(self) -> None:
        frame = make_proportionality_frame()
        parents = frame.columns.get_level_values(0).unique().tolist()
        assert parents == ["id", "2-2020"]

    def test_weights_sum_to_one_per_row(self) -> None:
        frame = make_proportionality_frame(parent_children={"2-2020": ["4-2020", "5-2020", "6-2020"]}, n_rows=3)
        child_columns = [column for column in frame.columns if column[0] == "2-2020"]
        for _, row in frame[child_columns].iterrows():
            row_sum = sum(Decimal(value) for value in row)
            assert row_sum == Decimal("1.000")

    def test_weights_have_at_most_three_decimals(self) -> None:
        frame = make_proportionality_frame(
            parent_children={"2-2020": ["4-2020", "5-2020", "6-2020"]},
        )
        child_columns = [column for column in frame.columns if column[0] == "2-2020"]
        for column in child_columns:
            for value in frame[column]:
                exponent = int(Decimal(value).as_tuple().exponent)
                assert -exponent <= 3

    def test_multiple_parents_are_independent_groups(self) -> None:
        frame = make_proportionality_frame(
            parent_children={"2-2020": ["4-2020", "5-2020"], "3-2020": ["6-2020", "7-2020"]}
        )
        parents = frame.columns.get_level_values(0).unique().tolist()
        assert parents == ["id", "2-2020", "3-2020"]

    def test_empty_parent_children_raises(self) -> None:
        with pytest.raises(ValueError, match="parent_children"):
            make_proportionality_frame(parent_children={})

    def test_parent_without_children_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one child"):
            make_proportionality_frame(parent_children={"2-2020": []})

    def test_zero_rows_raises(self) -> None:
        with pytest.raises(ValueError, match="n_rows"):
            make_proportionality_frame(n_rows=0)


class TestMakeBundle:
    """`make_bundle` builds a mutually consistent minimal bundle."""

    def test_default_bundle_has_the_four_required_sheets(self) -> None:
        bundle = make_bundle()
        assert set(bundle) == {"descricao", "composicao", "valores", "referencia_temporal"}

    def test_description_and_composition_codes_agree(self) -> None:
        bundle = make_bundle(n_indicators=4)
        description_codes = set(bundle["descricao"]["codigo"])
        composition_codes = set(bundle["composicao"]["codigo_pai"]) | set(bundle["composicao"]["codigo_filho"])
        assert composition_codes <= description_codes

    def test_every_indicator_has_a_value_column(self) -> None:
        bundle = make_bundle(n_indicators=4, years=(2020,))
        description_codes = bundle["descricao"]["codigo"].tolist()
        value_columns = set(bundle["valores"].columns) - {"id"}
        for code in description_codes:
            assert f"{code}-2020" in value_columns

    def test_with_legend_adds_legenda_sheet_and_reference(self) -> None:
        bundle = make_bundle(with_legend=True)
        assert "legenda" in bundle
        assert (bundle["descricao"]["legenda"] == "1").all()
        assert set(bundle["descricao"]["legenda"]) <= set(bundle["legenda"]["codigo"])

    def test_with_scenario_symbols_adds_cenarios_sheet_and_suffix(self) -> None:
        bundle = make_bundle(scenario_symbols=("O", "P"), n_indicators=2, years=(2020,))
        assert "cenarios" in bundle
        assert set(bundle["cenarios"]["simbolo"]) == {"O", "P"}
        assert "2-2020-O" in bundle["valores"].columns
        assert "2-2020-P" in bundle["valores"].columns

    def test_with_proportionality_produces_resolvable_parent_and_children(self) -> None:
        bundle = make_bundle(with_proportionality=True, n_indicators=5, years=(2020,))
        proportionality = bundle["proporcionalidades"]
        parents = proportionality.columns.get_level_values(0).unique().tolist()
        assert parents == ["id", "2-2020"]

        children = [column[1] for column in proportionality.columns if column[0] == "2-2020"]
        composition_children = bundle["composicao"][bundle["composicao"]["codigo_pai"] == "2"]["codigo_filho"].tolist()
        assert sorted(child.split("-")[0] for child in children) == sorted(composition_children)

    def test_with_proportionality_below_four_indicators_raises(self) -> None:
        with pytest.raises(ValueError, match="n_indicators"):
            make_bundle(with_proportionality=True, n_indicators=3)
