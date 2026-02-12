#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""Data validation utilities for DataFrame processing.

This module provides functions for validating pandas DataFrames against
common data quality issues such as vertical bars, unnamed columns,
punctuation rules, special characters, and text length constraints.
"""

from typing import List, Tuple

import pandas as pd


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
    def check_dataframe_vertical_bar(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
        """Check for vertical bar characters in DataFrame columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting

        Returns:
            Tuple of (is_valid, error_messages) where is_valid is True if no errors found
        """
        dataframe = dataframe.copy()
        errors: List[str] = []

        try:
            # Check column names for vertical bars
            if isinstance(dataframe.columns, pd.MultiIndex):
                for col_tuple in dataframe.columns:
                    if "|" in str(col_tuple[0]):
                        errors.append(f"{file_name}: O nome da coluna de nível 0 '{col_tuple[0]}' não pode conter o caracter '|'.")

                    if len(col_tuple) > 1 and "|" in str(col_tuple[1]):
                        errors.append(
                            f"{file_name}: O nome da subcoluna de nível 1 '{col_tuple[1]}' do pai '{col_tuple[0]}' de nível 0 não pode conter o caracter '|'."
                        )
            else:
                for column_name in dataframe.columns:
                    if "|" in str(column_name):
                        errors.append(f"{file_name}: A coluna '{column_name}' não pode conter o caractere '|'.")

            # Check data values for vertical bars using vectorized operations
            string_data = dataframe.astype(str)
            mask = string_data.apply(lambda col: col.str.contains(r"\|", na=False))

            for column in mask.columns:
                if mask[column].any():
                    error_indices = mask.index[mask[column]].tolist()
                    col_display_name = str(column) if not isinstance(column, tuple) else ".".join(map(str, column))

                    for row_idx in error_indices:
                        errors.append(f"{file_name}, linha {row_idx + 2}: A coluna '{col_display_name}' não pode conter o caracter '|'.")

        except Exception as e:
            errors.append(f"{file_name}: Erro ao processar a checagem de barra vertical: {str(e)}")

        return not bool(errors), errors

    @staticmethod
    def check_dataframe_column_names(dataframe: pd.DataFrame, expected_columns: List[str]) -> Tuple[List[str], List[str]]:
        """
        Checks for missing and extra columns in a DataFrame compared to the expected columns.

        Args:
            dataframe (pd.DataFrame): The DataFrame to check.
            expected_columns (List[str]): List of expected column names.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing a list of missing columns and a list of extra columns.
        """
        missing_columns = [col for col in expected_columns if col not in dataframe.columns]
        extra_columns = [col for col in dataframe.columns if col not in expected_columns]

        # Remove unnamed extra columns - handle both string and numeric column names
        extra_columns = [col for col in extra_columns if not str(col).lower().startswith("unnamed")]
        return missing_columns, extra_columns

    @staticmethod
    def check_dataframe_unnamed_columns(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
        """Check for unnamed columns and validate row data consistency.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting

        Returns:
            Tuple of (is_valid, error_messages) where is_valid is True if no errors found
        """
        dataframe = dataframe.copy()
        errors: List[str] = []

        try:
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
                for idx in invalid_indices:
                    text_column = "coluna válida" if valid_columns_count == 1 else "colunas válidas"
                    errors.append(
                        f"{file_name}, linha {idx + 2}: A linha possui {non_null_counts[idx]} valores, mas a tabela possui apenas {valid_columns_count} {text_column}."
                    )

        except Exception as e:
            errors.append(f"{file_name}: Erro ao processar a checagem de colunas sem nome: {str(e)}")

        return not bool(errors), errors

    @staticmethod
    def check_dataframe_titles_uniques(
        dataframe: pd.DataFrame, column_one: str, column_two: str, plural_column_one: str, plural_column_two: str
    ) -> List[str]:
        """
        Check for duplicate values in specified columns and return warnings.

        Iterates over the given columns (singular/plural variations) and identifies
        duplicated entries.

        Args:
            dataframe: The pandas DataFrame to check
            column_one: First column name to check for duplicates
            column_two: Second column name to check for duplicates
            plural_column_one: Plural name of first column for reporting
            plural_column_two: Plural name of second column for reporting

        Returns:
            List of warning messages about duplicates
        """
        dataframe = dataframe.copy()
        warnings = []

        if dataframe.empty:
            return warnings

        columns_to_check = [column_one, column_two]
        columns_to_check = [col for col in columns_to_check if col in dataframe.columns]

        for column in columns_to_check:
            # Convert to string
            dataframe[column] = dataframe[column].astype(str).str.strip()
            duplicated = dataframe[column].duplicated().any()

            if duplicated:
                # Get unique duplicated values using a different approach
                value_counts = dataframe[column].value_counts()
                duplicated_values = value_counts[value_counts > 1].index.tolist()
                # Rename columns to plural
                if column == column_one:
                    column = plural_column_one
                elif column == column_two:
                    column = plural_column_two

                warnings.append(f"Existem {column.replace('_', ' ')} duplicados: {duplicated_values}.")

        return warnings

    @staticmethod
    def check_dataframe_unique_values(dataframe: pd.DataFrame, file_name: str, columns_uniques: List[str]) -> Tuple[bool, List[str]]:
        """Check for unique values in specified columns.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            columns_uniques: List of columns that should contain unique values

        Returns:
            Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
        """
        dataframe = dataframe.copy()
        warnings: List[str] = []
        existing_columns = [col for col in columns_uniques if col in dataframe.columns]

        for column in existing_columns:
            if not dataframe[column].is_unique:
                warnings.append(f"{file_name}: A coluna '{column}' não deve conter valores repetidos.")

        return not bool(warnings), warnings

    @staticmethod
    def column_exists(dataframe: pd.DataFrame, file_name: str, column: str) -> Tuple[bool, str]:
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
    def check_dataframe_text_length(dataframe: pd.DataFrame, file_name: str, column: str, max_length: int) -> Tuple[bool, List[str]]:
        """Validate text length in a specific column.

        Args:
            dataframe: The pandas DataFrame to validate
            file_name: Name of the file being validated for error reporting
            column: Column name to check text length
            max_length: Maximum allowed text length

        Returns:
            Tuple of (is_valid, error_messages) where is_valid is True if no errors found
        """

        dataframe = dataframe.copy()
        errors: List[str] = []

        column_exists_result, error_message = DataFrameProcessing.column_exists(dataframe, file_name, column)
        if not column_exists_result:
            return False, [error_message]

        # Vectorized text length check
        text_series = dataframe[column].astype(str)
        non_null_mask = dataframe[column].notna()

        if non_null_mask.any():
            text_lengths = text_series[non_null_mask].str.len()
            exceeds_limit = text_lengths > max_length

            for idx in text_lengths[exceeds_limit].index:
                actual_length = text_lengths[idx]
                errors.append(
                    f'{file_name}, linha {idx + 2}: O texto da coluna "{column}" excede o limite de {max_length} caracteres (encontrado: {actual_length}).'
                )

        return not bool(errors), errors
