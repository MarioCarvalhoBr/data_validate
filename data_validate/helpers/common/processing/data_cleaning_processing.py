#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module providing data cleaning utilities including integer validation.

This module defines the `DataCleaningProcessing` class, which offers methods
to clean and validate DataFrame columns, specifically ensuring integer integrity
and handling empty values.
"""

from typing import Tuple, List

import pandas as pd

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class DataCleaningProcessing:
    """
    Utility class for data cleaning and validation operations.

    Provides static methods to clean DataFrame columns by validating data types
    (e.g., integrity checks for integer columns) and filtering out invalid rows.
    """

    def __init__(self) -> None:
        """Initialize the DataCleaningProcessing class."""
        pass

    @staticmethod
    def clean_column_integer(
        df: pd.DataFrame,
        column: str,
        file_name: str,
        min_value: int = 0,
        allow_empty: bool = False,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Validate and clean a single DataFrame column, enforcing integer constraints.

        Iterates through the column to verify each cell contains a valid integer
        (or is empty if allowed). Drops invalid rows and returns cleaning errors.

        Args:
            df (pd.DataFrame): The DataFrame containing the column to clean.
            column (str): The name of the column to validate.
            file_name (str): Original file name for error reporting context.
            min_value (int, optional): The minimum allowed integer value. Defaults to 0.
            allow_empty (bool, optional): If True, treats empty cells as valid. Defaults to False.

        Returns:
            Tuple[pd.DataFrame, List[str]]: A tuple containing:
                - pd.DataFrame: A new DataFrame with only valid rows for this column.
                - List[str]: A list of error messages for invalid cells found.
        """
        errors: List[str] = []
        if column not in df.columns:
            errors.append(f"{file_name}: A coluna '{column}' não foi encontrada.")
            return df, errors

        mask_valid: List[bool] = []
        for idx, raw in df[column].items():
            if allow_empty and (pd.isna(raw) or str(raw).strip() == ""):
                mask_valid.append(True)
                continue
            is_valid, message = NumberFormattingProcessing.check_cell_integer(raw, min_value)
            if not is_valid:
                errors.append(f"{file_name}, linha {idx + 2}: A coluna '{column}' contém um valor inválido: {message}")
                mask_valid.append(False)
            else:
                mask_valid.append(True)

        df_clean = df.loc[mask_valid].copy()
        if not allow_empty:
            df_clean[column] = df_clean[column].apply(lambda x: int(float(str(x).replace(",", "."))))
        else:
            df_clean[column] = df_clean[column].apply(lambda x: (int(float(str(x).replace(",", "."))) if pd.notna(x) and str(x).strip() != "" else x))
        return df_clean, errors

    @staticmethod
    def clean_dataframe_integers(
        df: pd.DataFrame,
        file_name: str,
        columns_to_clean: List[str],
        min_value: int = 0,
        allow_empty: bool = False,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        Clean multiple columns in the DataFrame, enforcing integer validation on all.

        Sequentially applies `clean_column_integer` to each specified column,
        accumulating errors and progressively filtering the DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to process.
            file_name (str): Original file name for error reporting context.
            columns_to_clean (List[str]): List of column names to validate and clean.
            min_value (int, optional): Minimum allowed value for integers. Defaults to 0.
            allow_empty (bool, optional): If True, allows empty values in the columns. Defaults to False.

        Returns:
            Tuple[pd.DataFrame, List[str]]: A tuple containing:
                - pd.DataFrame: The fully cleaned DataFrame.
                - List[str]: Aggregated list of all validation errors encountered.
        """
        df_work = df.copy()
        all_errors: List[str] = []

        for col in columns_to_clean:
            df_work, errors = DataCleaningProcessing.clean_column_integer(df_work, col, file_name, min_value, allow_empty)
            all_errors.extend(errors)

        return df_work, all_errors
