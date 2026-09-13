#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing proportionality data cleaning and validation utilities.

This module defines the `ProportionalityProcessing` class: pure, frame-level helpers that build
per-parent subdatasets, flag non-numeric/excessive-decimal cells, sum truncated `Decimal` values,
find zero-sum rows that disagree with `valores`, and find rows whose sum falls outside the [0.99,
1.01] tolerance band.

ARC-017 Phase 3 Port 7 (`rules/proportionality.py`, PROP-007…010): every method here used to build
and return pre-formatted Portuguese error/warning strings directly (`errors.append(f"...")`), which
both duplicated message text outside the i18n catalog and coupled this otherwise-pure helper to one
specific validator's wording (`.claude/rules/architecture-boundaries.md`, `.claude/rules/i18n.md`).
Every method below now returns structured data (masks, indices, `(id, column)` pairs) instead;
`rules/proportionality.py` is the only place that turns that data into `Issue`s, matching
`rules/value.py`'s decision to not reuse `ValueProcessing`'s (deleted) message-building helper.
"""

from decimal import Decimal
from typing import Any, List, Tuple

import pandas as pd
from pandas import DataFrame

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing

_TOLERANCE_LOWER_BOUND = Decimal("0.99")
_TOLERANCE_UPPER_BOUND = Decimal("1.01")


class ProportionalityProcessing:
    """
    Utility class for processing proportionality data.

    Provides static methods to build hierarchical sub-datasets, flag non-numeric/excessive-decimal
    cells, sum truncated `Decimal` values, and locate rows that violate the zero-sum or tolerance
    statements — every method is pure (no message text, no I/O) and frame/row-index level (no
    `.iterrows()`).
    """

    def __init__(self) -> None:
        """Initialize the ProportionalityProcessing class."""
        pass

    @staticmethod
    def build_subdatasets(df_proportionalities: DataFrame, column_name_id: str):
        """
        Construct subdatasets mapping parent indicators to their children data.

        Iterates through the DataFrame columns to identify parent-child groups
        based on the multi-level column structure.

        Args:
            df_proportionalities: The main DataFrame containing proportionality data
            column_name_id: The specific column name identifying the ID

        Returns:
            Dictionary mapping parent IDs to DataFrames of their children
        """
        df_proportionalities = df_proportionalities.copy()

        # Create columns information
        columns_multi_index_prop = df_proportionalities.columns
        columns_level_one_prop = df_proportionalities.columns.get_level_values(0).unique().tolist()
        columns_level_one_prop_cleaned = [
            col for col in columns_level_one_prop if not col.lower().startswith("unnamed")
        ]

        # Create subdatasets and others variables
        subdatasets = {}
        has_found_col_id = False
        found_col_level_0 = None

        # Find the column with the ID
        for column in columns_multi_index_prop:
            col_level_0, col_level_1 = column
            if col_level_1 == column_name_id:
                has_found_col_id = True
                found_col_level_0 = col_level_0
                break

        if not has_found_col_id:
            return subdatasets

        sub_dataset_id = df_proportionalities[found_col_level_0]

        for parent_id in columns_level_one_prop_cleaned:
            subdatasets[parent_id] = pd.concat([sub_dataset_id, df_proportionalities[parent_id]], axis=1)

        return subdatasets

    @staticmethod
    def find_invalid_numeric_cells(
        df_data: DataFrame,
        is_di: DataFrame,
        value_di: Any,
    ) -> Tuple[DataFrame, DataFrame]:
        """
        Replace non-numeric, non-DI cells with `value_di` and report which cells were invalid.

        A cell is invalid when it is not `DI`, is not empty, and does not parse as a number
        (comma accepted as the decimal separator).

        Args:
            df_data: DataFrame with data to validate.
            is_di: Boolean DataFrame mask indicating which cells already equal `value_di`.
            value_di: Value representing "Data Unavailable".

        Returns:
            Tuple of (cleaned DataFrame with invalid cells replaced by `value_di`, boolean
            DataFrame of the same shape marking every invalid cell).
        """
        df_numeric = df_data.replace(",", ".", regex=True).apply(pd.to_numeric, errors="coerce")
        invalid_mask = df_numeric.isna() & (~is_di) & (df_data.notna())

        cleaned = df_data.copy()
        cleaned[invalid_mask] = value_di
        return cleaned, invalid_mask

    @staticmethod
    def find_excessive_decimal_mask(
        df_data: DataFrame,
        value_di: Any,
        precision: int,
    ) -> DataFrame:
        """
        Flag cells whose decimal precision exceeds `precision`.

        Args:
            df_data: DataFrame to check.
            value_di: Value to ignore (DI).
            precision: Maximum allowed decimal places.

        Returns:
            Boolean DataFrame of the same shape as `df_data`, `True` where a cell has more than
            `precision` decimal places.
        """
        return df_data.map(
            lambda value_number: NumberFormattingProcessing.check_n_decimals_places(value_number, value_di, precision)
        )

    @staticmethod
    def convert_to_decimal_and_sum(
        df_data: DataFrame,
        value_di: Any,
        precision: int,
    ) -> pd.Series:
        """
        Convert values to Decimal type and calculate row sums.

        Ensures precision handling by truncating decimals before summation.

        Args:
            df_data: DataFrame with values
            value_di: Value to ignore (DI)
            precision: Decimal precision for truncation

        Returns:
            Series containing the sum for each row
        """
        df_decimals = df_data.map(
            lambda value_number: NumberFormattingProcessing.to_decimal_truncated(value_number, value_di, precision)
        )
        return df_decimals.sum(axis=1)

    @staticmethod
    def find_zero_sum_violations(
        row_sums: pd.Series,
        ids: pd.Series,
        df_data: DataFrame,
        sp_df_values: DataFrame,
        column_name_id: str,
        value_di: Any,
    ) -> List[Tuple[Any, str]]:
        """
        Find rows whose factors sum to zero but whose `valores` counterpart is not zero/DI.

        For every proportionality row that sums to 0, the corresponding indicator values in the
        values spreadsheet must also be 0 or DI; every child column that disagrees is reported.

        Args:
            row_sums: Series of row sums.
            ids: Series of IDs corresponding to rows.
            df_data: Proportionality DataFrame (only its column names are read).
            sp_df_values: Values spreadsheet DataFrame.
            column_name_id: Name of the ID column.
            value_di: DI value string.

        Returns:
            List of `(row_id, child_column)` pairs that violate the zero-sum statement, in the
            order the zero-sum rows and their matching value columns were encountered.
        """
        violations: List[Tuple[Any, str]] = []
        zero_sum_mask = row_sums == 0

        if not zero_sum_mask.any():
            return violations

        zero_indices = zero_sum_mask[zero_sum_mask].index
        zero_ids = ids.loc[zero_indices]

        relevant_values = sp_df_values[sp_df_values[column_name_id].isin(zero_ids)]
        df_check = relevant_values.set_index(column_name_id)

        for idx in zero_indices:
            row_id = ids[idx]
            if row_id not in df_check.index:
                continue

            values_row = df_check.loc[row_id]
            cols_to_check = [c for c in df_data.columns if c in values_row.index]

            for col in cols_to_check:
                val = values_row[col]
                if val == value_di:
                    continue

                try:
                    if float(str(val).replace(",", ".")) != 0:
                        violations.append((row_id, col))
                except (ValueError, TypeError):
                    continue

        return violations

    @staticmethod
    def sum_tolerance_indices(row_sums: pd.Series) -> Tuple[pd.Index, pd.Index]:
        """
        Split row indices into the error/warning tolerance buckets around a sum of 1.

        Tolerance range: `[0.99, 1.01]`. A sum outside that range (and not exactly 0) is an
        error; a sum inside it but not exactly 1 is a warning.

        Args:
            row_sums: Series of row sums.

        Returns:
            Tuple of `(error_index, warning_index)`.
        """
        error_mask = (row_sums != 0) & ((row_sums < _TOLERANCE_LOWER_BOUND) | (row_sums > _TOLERANCE_UPPER_BOUND))
        warning_mask = (row_sums != 1) & (row_sums >= _TOLERANCE_LOWER_BOUND) & (row_sums <= _TOLERANCE_UPPER_BOUND)
        return row_sums.index[error_mask], row_sums.index[warning_mask]
