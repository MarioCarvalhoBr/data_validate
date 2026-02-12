#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module providing proportionality data cleaning and validation utilities.

This module defines the `ProportionalityProcessing` class, which offers methods
to construct subdatasets for proportionality analysis, validate numeric types,
sum constraints, and decimal precisions in proportionality datasets.
"""

from decimal import Decimal
from typing import List, Tuple, Any

import pandas as pd
from pandas import DataFrame

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class ProportionalityProcessing:
    """
    Utility class for processing proportionality data.

    Provides static methods to build hierarchical sub-datasets, check sums equal 1 (or 100%),
    verify decimal precision, and validate numeric consistency in proportionality tables.
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
        columns_level_one_prop_cleaned = [col for col in columns_level_one_prop if not col.lower().startswith("unnamed")]

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
    def validate_numeric_format(
        df_data: DataFrame,
        is_di: DataFrame,
        value_di: Any,
        parent_id: str,
        sp_name: str,
    ) -> Tuple[DataFrame, List[str]]:
        """
        Validate that data contains valid numeric values.

        Checks for non-numeric values that are not marked as 'Data Unavailable' (DI).
        Invalid entries are collected as errors and replaced with DI value in the returned DataFrame.

        Args:
            df_data: DataFrame with data to validate
            is_di: boolean DataFrame mask indicating DI values
            value_di: Value representing 'Data Unavailable'
            parent_id: ID of the parent indicator
            sp_name: Name of the spreadsheet for error reporting

        Returns:
            Tuple of (cleaned DataFrame, list of error messages)
        """
        errors = []

        df_numeric = df_data.replace(",", ".", regex=True).apply(pd.to_numeric, errors="coerce")
        is_invalid = df_numeric.isna() & (~is_di) & (df_data.notna())

        if not is_invalid.any().any():
            return df_data, errors

        rows_with_errors = is_invalid.any(axis=1)
        error_indices = rows_with_errors[rows_with_errors].index
        excel_indices = error_indices + 3
        count_errors = is_invalid.sum().sum()

        if count_errors == 1:
            row_idx = error_indices[0]
            errors.append(
                f"{sp_name}, linha {row_idx + 3}: O valor não é um número válido e nem {value_di} (Dado Indisponível) para o indicador pai '{parent_id}'."
            )
        else:
            line_init = excel_indices.min()
            line_end = excel_indices.max()
            errors.append(
                f"{sp_name}: {count_errors} valores que não são número válido nem {value_di} (Dado Indisponível) para o indicador pai '{parent_id}' entre as linhas {line_init} e {line_end}."
            )

        df_data[is_invalid] = value_di
        return df_data, errors

    @staticmethod
    def check_excessive_decimals(
        df_data: DataFrame,
        value_di: Any,
        precision: int,
    ) -> Tuple[bool, int, int]:
        """
        Check for values exceeding the allowed decimal precision.

        Args:
            df_data: DataFrame to check
            value_di: Value to ignore (DI)
            precision: Maximum allowed decimal places

        Returns:
            Tuple of (has_excess, count_of_errors, first_line_index)
        """
        has_excess_decimals_mask = df_data.map(
            lambda value_number: NumberFormattingProcessing.check_n_decimals_places(value_number, value_di, precision)
        )
        count_excess = has_excess_decimals_mask.sum().sum()

        if count_excess == 0:
            return False, 0, 0

        first_row_idx = has_excess_decimals_mask.any(axis=1).idxmax()
        first_line_excel = first_row_idx + 3

        return True, count_excess, first_line_excel

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
        df_decimals = df_data.map(lambda value_number: NumberFormattingProcessing.to_decimal_truncated(value_number, value_di, precision))
        return df_decimals.sum(axis=1)

    @staticmethod
    def validate_zero_sum_rows(
        row_sums: pd.Series,
        ids: pd.Series,
        df_data: DataFrame,
        sp_df_values: DataFrame,
        column_name_id: str,
        value_di: Any,
        sp_name: str,
        sp_name_value: str,
    ) -> List[str]:
        """
        Validate that rows summing to zero also have zero values in the source values spreadsheet.

        If a proportionality row sums to 0, the corresponding indicator values in the values spreadsheet
        must also be 0 or DI. Deviations generate errors.

        Args:
            row_sums: Series of row sums
            ids: Series of IDs corresponding to rows
            df_data: Proportionality DataFrame
            sp_df_values: Values spreadsheet DataFrame
            column_name_id: Name of ID column
            value_di: DI value string
            sp_name: Name of proportionality spreadsheet
            sp_name_value: Name of values spreadsheet

        Returns:
            List of error messages
        """
        errors = []
        zero_sum_mask = row_sums == 0

        if not zero_sum_mask.any():
            return errors

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
                        errors.append(
                            f"{sp_name}: A soma de fatores influenciadores para o ID '{row_id}' no pai '{col}' é 0 (zero). "
                            f"Na planilha {sp_name_value}, existe(m) valor(es) para os filhos do indicador '{col}', "
                            f"no mesmo ID, que não é (são) zero ou DI (Dado Indisponível)."
                        )
                except (ValueError, TypeError, Exception):
                    pass

        return errors

    @staticmethod
    def validate_sum_tolerance(
        row_sums: pd.Series,
        parent_id: str,
        sp_name: str,
        current_language: str,
    ) -> Tuple[List[str], List[str]]:
        """
        Validate that row sums are within acceptable tolerance of 1 (100%).

        Checks if sums fall strictly outside tolerance (error) or just slightly off 1 within tolerance (warning).
        Tolerance range: [0.99, 1.01].

        Args:
            row_sums: Series of row sums
            parent_id: Parent indicator ID
            sp_name: Spreadsheet name
            current_language: Language code for number formatting

        Returns:
            Tuple of (list of errors, list of warnings)
        """
        errors = []
        warnings = []

        limit_low = Decimal("0.99")
        limit_high = Decimal("1.01")

        # Critical errors: sum outside [0.99, 1.01] and != 0
        error_mask = (row_sums != 0) & ((row_sums < limit_low) | (row_sums > limit_high))

        for idx in error_mask[error_mask].index:
            val_sum = row_sums[idx]
            formatted_sum = NumberFormattingProcessing.format_number_brazilian(val_sum, current_language)
            errors.append(f"{sp_name}, linha {idx + 3}: A soma dos valores para o indicador pai {parent_id} é {formatted_sum}, e não 1.")

        # Warnings: sum within [0.99, 1.01] but != 1
        warning_mask = (row_sums != 1) & (row_sums >= limit_low) & (row_sums <= limit_high)

        for idx in warning_mask[warning_mask].index:
            val_sum = row_sums[idx]
            formatted_sum = NumberFormattingProcessing.format_number_brazilian(val_sum, current_language)
            warnings.append(f"{sp_name}, linha {idx + 3}: A soma dos valores para o indicador pai {parent_id} é {formatted_sum}, e não 1.")

        return errors, warnings
