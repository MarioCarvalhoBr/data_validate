#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Data validation utilities for DataFrame processing.

This module provides functions for validating pandas DataFrames against
common data quality issues such as vertical bars, unnamed columns,
punctuation rules, special characters, and text length constraints.

SEC-004: `check_dataframe_vertical_bar` and `check_dataframe_unnamed_columns`
no longer wrap their pure pandas logic in a broad `except Exception` --
there is no plausible failure mode in this pure vectorised code path that
should be reported to the user as a data-quality error, so any failure
(a genuine programming error) propagates to `main()`'s boundary and exits
with code 2, per `.claude/rules/security.md`.
"""

from typing import Callable

import pandas as pd

from data_validate.helpers.common.default_translate import get_default_translate


class DataFrameProcessing:
    """
    Utility class for general DataFrame validation and structural checks.

    Provides static methods to check valid column naming (no vertical bars),
    missing or extra columns, unnamed columns, duplicates, and text length limits.
    """

    def __init__(self) -> None:
        """Initialize the DataFrameProcessing class."""
        pass

    @staticmethod
    def check_dataframe_vertical_bar(
        dataframe: pd.DataFrame, file_name: str, translate: Callable[..., str] | None = None
    ) -> tuple[bool, list[str]]:
        """Check for vertical bar characters in DataFrame columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            translate: Message-catalog renderer (`key, **params -> str`). ARC-005:
                every error message is a catalog key (`rule.STRUCT-009.*`), never a
                hardcoded literal; defaults to `get_default_translate()` so existing
                direct callers keep working unchanged.

        Returns:
            Tuple of (is_valid, error_messages) where is_valid is True if no errors found
        """
        translate = translate or get_default_translate()
        dataframe = dataframe.copy()
        errors: list[str] = []

        # Check column names for vertical bars
        if isinstance(dataframe.columns, pd.MultiIndex):
            for col_tuple in dataframe.columns:
                if "|" in str(col_tuple[0]):
                    errors.append(
                        translate("rule.STRUCT-009.header_multiindex_level0", filename=file_name, column=col_tuple[0])
                    )

                if len(col_tuple) > 1 and "|" in str(col_tuple[1]):
                    errors.append(
                        translate(
                            "rule.STRUCT-009.header_multiindex_level1",
                            filename=file_name,
                            child_column=col_tuple[1],
                            parent_column=col_tuple[0],
                        )
                    )
        else:
            for column_name in dataframe.columns:
                if "|" in str(column_name):
                    errors.append(translate("rule.STRUCT-009.header_single", filename=file_name, column=column_name))

        # Check data values for vertical bars using vectorized operations
        string_data = dataframe.astype(str)
        mask = string_data.apply(lambda col: col.str.contains(r"\|", na=False))

        for column in mask.columns:
            if mask[column].any():
                error_indices = mask.index[mask[column]].tolist()
                col_display_name = str(column) if not isinstance(column, tuple) else ".".join(map(str, column))

                for row_idx in error_indices:
                    errors.append(
                        translate("rule.STRUCT-009.cell", filename=file_name, row=row_idx + 2, column=col_display_name)
                    )

        return not bool(errors), errors

    @staticmethod
    def check_dataframe_column_names(
        dataframe: pd.DataFrame, expected_columns: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Checks for missing and extra columns in a DataFrame compared to the expected columns.

        Args:
            dataframe (pd.DataFrame): The DataFrame to check.
            expected_columns (List[str]): List of expected column names.

        Returns:
            tuple[list[str], list[str]]: A tuple containing a list of missing columns and a list of extra columns.
        """
        missing_columns = [col for col in expected_columns if col not in dataframe.columns]
        extra_columns = [col for col in dataframe.columns if col not in expected_columns]

        # Remove unnamed extra columns - handle both string and numeric column names
        extra_columns = [col for col in extra_columns if not str(col).lower().startswith("unnamed")]
        return missing_columns, extra_columns

    @staticmethod
    def check_dataframe_unnamed_columns(
        dataframe: pd.DataFrame, file_name: str, translate: Callable[..., str] | None = None
    ) -> tuple[bool, list[str]]:
        """Check for unnamed columns and validate row data consistency.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            translate: Message-catalog renderer (`key, **params -> str`). ARC-005:
                every error message is a catalog key (`rule.STRUCT-010.*`), never a
                hardcoded literal; defaults to `get_default_translate()` so existing
                direct callers keep working unchanged.

        Returns:
            Tuple of (is_valid, error_messages) where is_valid is True if no errors found
        """
        translate = translate or get_default_translate()
        dataframe = dataframe.copy()
        errors: list[str] = []

        columns = dataframe.columns
        is_multi_level_2 = isinstance(columns, pd.MultiIndex) and columns.nlevels == 2

        unnamed_indices = []
        for i, col_identifier in enumerate(columns):
            col_str = str(col_identifier[1] if is_multi_level_2 else col_identifier).strip().lower()

            if col_str.startswith("unnamed"):
                unnamed_indices.append(i)

        valid_columns_count = len(columns) - len(unnamed_indices)

        # Vectorized check for row data consistency
        non_null_counts = dataframe.notna().sum(axis=1)
        invalid_rows = non_null_counts > valid_columns_count

        if invalid_rows.any():
            invalid_indices = invalid_rows[invalid_rows].index
            key = "rule.STRUCT-010.singular" if valid_columns_count == 1 else "rule.STRUCT-010.plural"
            for idx in invalid_indices:
                errors.append(
                    translate(
                        key,
                        filename=file_name,
                        row=idx + 2,
                        count=non_null_counts[idx],
                        valid_columns_count=valid_columns_count,
                    )
                )

        return not bool(errors), errors

    @staticmethod
    def check_dataframe_unique_values(
        dataframe: pd.DataFrame, file_name: str, columns_uniques: list[str]
    ) -> tuple[bool, list[str]]:
        """Check for unique values in specified columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            columns_uniques: List of columns that should contain unique values

        Returns:
            Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
        """
        dataframe = dataframe.copy()
        warnings: list[str] = []
        existing_columns = [col for col in columns_uniques if col in dataframe.columns]

        for column in existing_columns:
            if not dataframe[column].is_unique:
                warnings.append(f"{file_name}: A coluna '{column}' não deve conter valores repetidos.")

        return not bool(warnings), warnings

    @staticmethod
    def column_exists(dataframe: pd.DataFrame, file_name: str, column: str) -> tuple[bool, str]:
        """Check if a column exists in the DataFrame (supports MultiIndex).

        Args:
            dataframe: The pandas DataFrame to check
            file_name: Name of the file being validated for error reporting
            column: Column name to check for existence

        Returns:
            Tuple of (exists, error_message) where exists is True if column found
        """

        # Check index type
        if isinstance(dataframe.columns, pd.MultiIndex):
            # Dataframe is <class 'pandas.core.indexes.multi.MultiIndex'>
            if column not in dataframe.columns.get_level_values(1):
                return (
                    False,
                    f"{file_name}: A verificação foi abortada para a coluna nível 2 obrigatória '{column}' que está ausente.",
                )

        else:
            # Dataframe is <class 'pandas.core.indexes.base.Index'>
            if column not in dataframe.columns:
                return (
                    False,
                    f"{file_name}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente.",
                )
        return True, ""

    @staticmethod
    def numeric_equals_mask(series: pd.Series, value: int) -> pd.Series:
        """Compare a column against an integer, tolerant of string formatting.

        Business columns such as ``nivel`` or ``codigo_pai`` are frequently loaded
        as `str` (or `object`); a cell written as `"1.0"`, `" 1"` or `"01"` fails an
        exact `series == "1"` comparison even though it represents the same number.
        This helper coerces `series` with `pd.to_numeric(errors="coerce")` before
        comparing, so every one of those representations matches `value`
        (BUG-014).

        Args:
            series: Column to compare; may hold strings, ints, or floats.
            value: Integer to compare each (coerced) cell against.

        Returns:
            Boolean mask, `True` where the cell equals `value` numerically. A
            cell that cannot be parsed as a number (including a missing/`NaN`
            cell) never matches: it evaluates to `False`.
        """
        return pd.to_numeric(series, errors="coerce") == value

    @staticmethod
    def numeric_not_equals_mask(series: pd.Series, value: int) -> pd.Series:
        """Inverse of :meth:`numeric_equals_mask`.

        Args:
            series: Column to compare; may hold strings, ints, or floats.
            value: Integer to compare each (coerced) cell against.

        Returns:
            Boolean mask, `True` where the cell does not equal `value`
            numerically. A cell that cannot be parsed as a number (including a
            missing/`NaN` cell) always matches here (`True`), mirroring the
            historical `series != "1"`-style string comparison, where a
            non-matching or missing cell also counted as "not equal".
        """
        return ~DataFrameProcessing.numeric_equals_mask(series, value)
