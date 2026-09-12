#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Property-based tests for legend_processing.py interval logic (TST-005).

Uses `hypothesis` to generate continuous legend groups (min/max intervals built
with `Decimal` at <= 2 decimal places, `next_min = prev_max + 0.01`) and checks
`LegendProcessing.validate_min_max_values` against continuity and ordering.
"""

from decimal import Decimal
from typing import List, Tuple

import pandas as pd
from hypothesis import given, settings, strategies as st

from data_validate.helpers.common.validation.legend_processing import LegendProcessing

VALUE_DATA_UNAVAILABLE = "Dado indisponível"
MIN_COL = "minimo"
MAX_COL = "maximo"
LABEL_COL = "label"

TWO_PLACE_START = st.decimals(
    min_value=Decimal("-1000"), max_value=Decimal("1000"), places=2, allow_nan=False, allow_infinity=False
)
TWO_PLACE_WIDTH = st.decimals(
    min_value=Decimal("0.01"), max_value=Decimal("100.00"), places=2, allow_nan=False, allow_infinity=False
)


@st.composite
def continuous_legend_group(draw, min_rows: int = 2, max_rows: int = 6) -> Tuple[List[Decimal], List[Decimal]]:
    """Build a continuous legend group: sorted mins/maxs where next_min = prev_max + 0.01."""
    num_rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    widths = draw(st.lists(TWO_PLACE_WIDTH, min_size=num_rows, max_size=num_rows))
    start = draw(TWO_PLACE_START)

    mins: List[Decimal] = []
    maxs: List[Decimal] = []
    current_min = start
    for width in widths:
        current_max = current_min + width
        mins.append(current_min)
        maxs.append(current_max)
        current_min = current_max + Decimal("0.01")
    return mins, maxs


def build_legend_dataframe(mins: List[Decimal], maxs: List[Decimal]) -> pd.DataFrame:
    """Build a single-code legend group DataFrame with string-rendered min/max cells."""
    return pd.DataFrame(
        {
            LABEL_COL: [f"Grupo {i}" for i in range(len(mins))],
            MIN_COL: [str(m) for m in mins],
            MAX_COL: [str(m) for m in maxs],
        }
    )


def legend_processor() -> LegendProcessing:
    """Build a LegendProcessing instance with the standard sentinel/filename."""
    return LegendProcessing(value_data_unavailable=VALUE_DATA_UNAVAILABLE, filename="test_legend.xlsx")


class TestContinuousLegendGroupHasNoErrors:
    """A properly continuous legend group never raises a min/max validation error."""

    @given(group=continuous_legend_group())
    @settings(max_examples=200, deadline=None)
    def test_continuous_group_is_valid(self, group: Tuple[List[Decimal], List[Decimal]]) -> None:
        """No errors are reported for a continuous, correctly ordered legend group."""
        mins, maxs = group
        dataframe = build_legend_dataframe(mins, maxs)

        errors = legend_processor().validate_min_max_values(
            dataframe, code=1, min_col=MIN_COL, max_col=MAX_COL, label_col=LABEL_COL
        )

        assert errors == []


class TestBrokenContinuityYieldsError:
    """Replacing the '+0.01' continuation with any other offset must be reported."""

    @given(
        group=continuous_legend_group(min_rows=3, max_rows=6),
        offset=st.decimals(
            min_value=Decimal("-5.00"), max_value=Decimal("5.00"), places=2, allow_nan=False, allow_infinity=False
        ),
        data=st.data(),
    )
    @settings(max_examples=200, deadline=None)
    def test_offset_other_than_0_01_breaks_continuity(
        self, group: Tuple[List[Decimal], List[Decimal]], offset: Decimal, data: st.DataObject
    ) -> None:
        """Overriding one row's min with prev_max + offset (offset != 0.01) yields >= 1 error."""
        mins, maxs = group
        num_rows = len(mins)
        broken_index = data.draw(st.integers(min_value=1, max_value=num_rows - 1))

        if offset == Decimal("0.01"):
            offset += Decimal("0.02")  # keep the offset different from the valid continuation step

        mins = list(mins)
        maxs = list(maxs)
        width = maxs[broken_index] - mins[broken_index]
        mins[broken_index] = maxs[broken_index - 1] + offset
        maxs[broken_index] = mins[broken_index] + width  # preserve min < max at the broken row

        dataframe = build_legend_dataframe(mins, maxs)

        errors = legend_processor().validate_min_max_values(
            dataframe, code=1, min_col=MIN_COL, max_col=MAX_COL, label_col=LABEL_COL
        )

        assert len(errors) >= 1
        assert any("intervalo não é contínuo" in error for error in errors)


class TestMinGreaterOrEqualMaxYieldsError:
    """A row whose min >= max is always reported, independent of continuity."""

    @given(group=continuous_legend_group(), data=st.data())
    @settings(max_examples=200, deadline=None)
    def test_min_at_least_max_is_reported(
        self, group: Tuple[List[Decimal], List[Decimal]], data: st.DataObject
    ) -> None:
        """Forcing one row's max down to its min triggers a 'mínimo deve ser menor' error."""
        mins, maxs = group
        num_rows = len(mins)
        broken_index = data.draw(st.integers(min_value=0, max_value=num_rows - 1))

        mins = list(mins)
        maxs = list(maxs)
        maxs[broken_index] = mins[broken_index]  # min == max: invalid

        dataframe = build_legend_dataframe(mins, maxs)

        errors = legend_processor().validate_min_max_values(
            dataframe, code=1, min_col=MIN_COL, max_col=MAX_COL, label_col=LABEL_COL
        )

        assert len(errors) >= 1
        assert any("deve ser menor que o valor máximo" in error for error in errors)
