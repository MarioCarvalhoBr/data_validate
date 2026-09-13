#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `ProportionalityProcessing` (ARC-017 Phase 3 Port 7).

Every method here is pure and message-free (see the module's own docstring); these tests exercise
the structured data each one returns directly, independent of `rules/proportionality.py`'s own
`Issue`-building tests (`tests/unit/rules/test_proportionality.py`).
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from data_validate.helpers.common.validation.proportionality_processing import ProportionalityProcessing

_DI = "DI"


class TestBuildSubdatasets:
    """`build_subdatasets`: unchanged pure frame-slicing helper."""

    def test_builds_one_subdataset_per_parent(self) -> None:
        columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "id"), ("2-2020", "4-2020"), ("2-2020", "5-2020")])
        frame = pd.DataFrame([["1", "0.5", "0.5"]], columns=columns)

        subdatasets = ProportionalityProcessing.build_subdatasets(frame, "id")

        assert list(subdatasets.keys()) == ["2-2020"]
        assert subdatasets["2-2020"].columns.tolist() == ["id", "4-2020", "5-2020"]

    def test_returns_empty_when_id_column_is_absent(self) -> None:
        columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "territorio"), ("2-2020", "4-2020")])
        frame = pd.DataFrame([["1", "1.0"]], columns=columns)

        assert ProportionalityProcessing.build_subdatasets(frame, "id") == {}


class TestFindInvalidNumericCells:
    """`find_invalid_numeric_cells`: DI-aware numeric-format mask, no message text."""

    def test_a_valid_numeric_cell_is_not_flagged(self) -> None:
        df_data = pd.DataFrame({"4-2020": ["0.5"]})
        is_di = df_data == _DI

        cleaned, invalid_mask = ProportionalityProcessing.find_invalid_numeric_cells(df_data, is_di, _DI)

        assert not invalid_mask.to_numpy().any()
        assert cleaned.loc[0, "4-2020"] == "0.5"

    def test_a_di_cell_is_not_flagged(self) -> None:
        df_data = pd.DataFrame({"4-2020": [_DI]})
        is_di = df_data == _DI

        _cleaned, invalid_mask = ProportionalityProcessing.find_invalid_numeric_cells(df_data, is_di, _DI)

        assert not invalid_mask.to_numpy().any()

    def test_a_non_numeric_non_di_cell_is_flagged_and_replaced(self) -> None:
        df_data = pd.DataFrame({"4-2020": ["abc"]})
        is_di = df_data == _DI

        cleaned, invalid_mask = ProportionalityProcessing.find_invalid_numeric_cells(df_data, is_di, _DI)

        assert bool(invalid_mask.loc[0, "4-2020"])
        assert cleaned.loc[0, "4-2020"] == _DI

    def test_does_not_mutate_the_input_frame(self) -> None:
        df_data = pd.DataFrame({"4-2020": ["abc"]})
        is_di = df_data == _DI

        ProportionalityProcessing.find_invalid_numeric_cells(df_data, is_di, _DI)

        assert df_data.loc[0, "4-2020"] == "abc"


class TestFindExcessiveDecimalMask:
    """`find_excessive_decimal_mask`: flags cells with more than `precision` decimal places."""

    def test_a_cell_within_precision_is_not_flagged(self) -> None:
        df_data = pd.DataFrame({"4-2020": ["0.123"]})
        mask = ProportionalityProcessing.find_excessive_decimal_mask(df_data, _DI, 3)
        assert not bool(mask.loc[0, "4-2020"])

    def test_a_cell_beyond_precision_is_flagged(self) -> None:
        df_data = pd.DataFrame({"4-2020": ["0.1234"]})
        mask = ProportionalityProcessing.find_excessive_decimal_mask(df_data, _DI, 3)
        assert bool(mask.loc[0, "4-2020"])

    def test_a_di_cell_is_never_flagged(self) -> None:
        df_data = pd.DataFrame({"4-2020": [_DI]})
        mask = ProportionalityProcessing.find_excessive_decimal_mask(df_data, _DI, 3)
        assert not bool(mask.loc[0, "4-2020"])


class TestConvertToDecimalAndSum:
    """`convert_to_decimal_and_sum`: truncated `Decimal` row sums."""

    def test_sums_two_columns_truncating_excess_decimals(self) -> None:
        df_data = pd.DataFrame({"4-2020": ["0.5001"], "5-2020": ["0.5"]})
        row_sums = ProportionalityProcessing.convert_to_decimal_and_sum(df_data, _DI, 3)
        assert row_sums.iloc[0] == Decimal("1.000")

    def test_di_cells_contribute_zero(self) -> None:
        df_data = pd.DataFrame({"4-2020": [_DI], "5-2020": ["1"]})
        row_sums = ProportionalityProcessing.convert_to_decimal_and_sum(df_data, _DI, 3)
        assert row_sums.iloc[0] == Decimal("1")


class TestFindZeroSumViolations:
    """`find_zero_sum_violations`: zero-sum proportionality rows vs. non-zero `valores`."""

    def test_a_zero_sum_row_with_a_zero_value_is_not_a_violation(self) -> None:
        row_sums = pd.Series([Decimal("0")])
        ids = pd.Series(["1"])
        df_data = pd.DataFrame({"4-2020": ["0"]})
        sp_df_values = pd.DataFrame({"id": ["1"], "4-2020": ["0"]})

        violations = ProportionalityProcessing.find_zero_sum_violations(row_sums, ids, df_data, sp_df_values, "id", _DI)

        assert violations == []

    def test_a_zero_sum_row_with_a_di_value_is_not_a_violation(self) -> None:
        row_sums = pd.Series([Decimal("0")])
        ids = pd.Series(["1"])
        df_data = pd.DataFrame({"4-2020": ["0"]})
        sp_df_values = pd.DataFrame({"id": ["1"], "4-2020": [_DI]})

        violations = ProportionalityProcessing.find_zero_sum_violations(row_sums, ids, df_data, sp_df_values, "id", _DI)

        assert violations == []

    def test_a_zero_sum_row_with_a_non_zero_value_is_a_violation(self) -> None:
        row_sums = pd.Series([Decimal("0")])
        ids = pd.Series(["1"])
        df_data = pd.DataFrame({"4-2020": ["0"]})
        sp_df_values = pd.DataFrame({"id": ["1"], "4-2020": ["5"]})

        violations = ProportionalityProcessing.find_zero_sum_violations(row_sums, ids, df_data, sp_df_values, "id", _DI)

        assert violations == [("1", "4-2020")]

    def test_a_non_zero_sum_row_is_never_checked(self) -> None:
        row_sums = pd.Series([Decimal("1")])
        ids = pd.Series(["1"])
        df_data = pd.DataFrame({"4-2020": ["1"]})
        sp_df_values = pd.DataFrame({"id": ["1"], "4-2020": ["5"]})

        violations = ProportionalityProcessing.find_zero_sum_violations(row_sums, ids, df_data, sp_df_values, "id", _DI)

        assert violations == []

    def test_an_id_absent_from_values_is_skipped_without_raising(self) -> None:
        row_sums = pd.Series([Decimal("0")])
        ids = pd.Series(["99"])
        df_data = pd.DataFrame({"4-2020": ["0"]})
        sp_df_values = pd.DataFrame({"id": ["1"], "4-2020": ["5"]})

        violations = ProportionalityProcessing.find_zero_sum_violations(row_sums, ids, df_data, sp_df_values, "id", _DI)

        assert violations == []

    def test_an_unparseable_value_is_skipped_without_raising(self) -> None:
        row_sums = pd.Series([Decimal("0")])
        ids = pd.Series(["1"])
        df_data = pd.DataFrame({"4-2020": ["0"]})
        sp_df_values = pd.DataFrame({"id": ["1"], "4-2020": ["not-a-number"]})

        violations = ProportionalityProcessing.find_zero_sum_violations(row_sums, ids, df_data, sp_df_values, "id", _DI)

        assert violations == []


class TestSumToleranceIndices:
    """`sum_tolerance_indices`: the [0.99, 1.01] tolerance band around a sum of 1."""

    @pytest.mark.parametrize(
        ("value", "expected_error", "expected_warning"),
        [
            (Decimal("1"), False, False),
            (Decimal("0"), False, False),
            (Decimal("0.995"), False, True),
            (Decimal("1.005"), False, True),
            (Decimal("0.5"), True, False),
            (Decimal("1.5"), True, False),
        ],
    )
    def test_classifies_a_single_row_sum(self, value: Decimal, expected_error: bool, expected_warning: bool) -> None:
        row_sums = pd.Series([value])

        error_index, warning_index = ProportionalityProcessing.sum_tolerance_indices(row_sums)

        assert (len(error_index) == 1) is expected_error
        assert (len(warning_index) == 1) is expected_warning
