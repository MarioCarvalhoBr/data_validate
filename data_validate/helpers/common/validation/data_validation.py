"""Data validation utilities for DataFrame processing.

This module provides functions for validating pandas DataFrames against
common data quality issues such as vertical bars, unnamed columns,
punctuation rules, special characters, and text length constraints.
"""

import re
from typing import List, Tuple, Optional

import pandas as pd


def check_vertical_bar(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
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


def check_unnamed_columns(dataframe: pd.DataFrame, file_name: str) -> Tuple[bool, List[str]]:
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


def check_punctuation(
    dataframe: pd.DataFrame,
    file_name: str,
    columns_dont_punctuation: Optional[List[str]] = None,
    columns_must_end_with_dot: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """Check punctuation rules for specified columns.

    Args:
        dataframe: The pandas DataFrame to validate
        file_name: Name of the file being validated for error reporting
        columns_dont_punctuation: Columns that should not end with punctuation
        columns_must_end_with_dot: Columns that must end with a dot

    Returns:
        Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
    """
    dataframe = dataframe.copy()
    warnings: List[str] = []

    columns_dont_punctuation = columns_dont_punctuation or []
    columns_must_end_with_dot = columns_must_end_with_dot or []

    # Filter existing columns
    existing_no_punct = [col for col in columns_dont_punctuation if col in dataframe.columns]
    existing_with_dot = [col for col in columns_must_end_with_dot if col in dataframe.columns]

    punctuation_chars = {",", ".", ";", ":", "!", "?"}

    for column in existing_no_punct:
        non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
        if non_empty_mask.any():
            text_series = dataframe.loc[non_empty_mask, column].astype(str).str.strip()
            ends_with_punct = text_series.str[-1].isin(punctuation_chars)

            for idx in text_series[ends_with_punct].index:
                warnings.append(f"{file_name}, linha {idx + 2}: O valor da coluna '{column}' não deve terminar com pontuação.")

    for column in existing_with_dot:
        non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
        if non_empty_mask.any():
            text_series = dataframe.loc[non_empty_mask, column].astype(str).str.strip()
            not_ends_with_dot = ~text_series.str.endswith(".")

            for idx in text_series[not_ends_with_dot].index:
                warnings.append(f"{file_name}, linha {idx + 2}: O valor da coluna '{column}' deve terminar com ponto.")

    return not bool(warnings), warnings


def check_special_characters_cr_lf_columns_start_end(
    dataframe: pd.DataFrame,
    file_name: str,
    columns_start_end: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """Check for CR/LF characters at start and end of text in specified columns.

    Args:
        dataframe: The pandas DataFrame to validate
        file_name: Name of the file being validated for error reporting
        columns_start_end: Columns to check for CR/LF at start/end

    Returns:
        Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
    """
    dataframe = dataframe.copy()
    warnings: List[str] = []
    columns_start_end = columns_start_end or []

    existing_columns = [col for col in columns_start_end if col in dataframe.columns]

    for column in existing_columns:
        non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
        if not non_empty_mask.any():
            continue

        # Get non-empty values safely
        non_empty_values = dataframe[column][non_empty_mask]
        if len(non_empty_values) == 0:
            continue
            
        text_series = non_empty_values.astype(str)

        # Check for CR/LF at positions using vectorized operations
        patterns = {
            "end_cr": (
                text_series.str.endswith("\x0d"),
                "O texto da coluna '{column}' possui um caracter inválido (CR) no final do texto. Remova o último caractere do texto.",
            ),
            "end_lf": (
                text_series.str.endswith("\x0a"),
                "O texto da coluna '{column}' possui um caracter inválido (LF) no final do texto. Remova o último caractere do texto.",
            ),
            "start_cr": (
                text_series.str.startswith("\x0d"),
                "O texto da coluna '{column}' possui um caracter inválido (CR) no início do texto. Remova o primeiro caractere do texto.",
            ),
            "start_lf": (
                text_series.str.startswith("\x0a"),
                "O texto da coluna '{column}' possui um caracter inválido (LF) no início do texto. Remova o primeiro caractere do texto.",
            ),
        }

        for pattern_name, (mask, message_template) in patterns.items():
            for idx in text_series[mask].index:
                warnings.append(f"{file_name}, linha {idx + 2}: " + message_template.format(column=column))

    return not bool(warnings), warnings


def check_special_characters_cr_lf_columns_anywhere(
    dataframe: pd.DataFrame,
    file_name: str,
    columns_anywhere: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """Check for CR/LF characters anywhere in text in specified columns.

    Args:
        dataframe: The pandas DataFrame to validate
        file_name: Name of the file being validated for error reporting
        columns_anywhere: Columns to check for CR/LF anywhere in text

    Returns:
        Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
    """
    dataframe = dataframe.copy()
    warnings: List[str] = []
    columns_anywhere = columns_anywhere or []

    existing_columns = [col for col in columns_anywhere if col in dataframe.columns]

    for column in existing_columns:
        non_empty_mask = dataframe[column].notna() & (dataframe[column] != "")
        if not non_empty_mask.any():
            continue

        # Get non-empty values safely
        non_empty_values = dataframe[column][non_empty_mask]
        if len(non_empty_values) == 0:
            continue
            
        text_series = non_empty_values.astype(str)

        def find_cr_lf_positions(text: str) -> List[Tuple[int, str]]:
            """Find positions of CR/LF characters in text."""
            return [(match.start() + 1, "CR" if match.group() == "\x0d" else "LF") for match in re.finditer(r"[\x0D\x0A]", text)]

        cr_lf_positions = text_series.apply(find_cr_lf_positions)

        for idx, positions in cr_lf_positions.items():
            for pos, char_type in positions:
                warnings.append(
                    f"{file_name}, linha {idx + 2}: O texto da coluna '{column}' possui um caracter inválido ({char_type}) na posição {pos}. Remova o caractere do texto."
                )

    return not bool(warnings), warnings


def check_special_characters_cr_lf(
    dataframe: pd.DataFrame,
    file_name: str,
    columns_start_end: Optional[List[str]] = None,
    columns_anywhere: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """Check for CR/LF special characters in DataFrame columns.

    Args:
        dataframe: The pandas DataFrame to validate
        file_name: Name of the file being validated for error reporting
        columns_start_end: Columns to check for CR/LF at start/end positions
        columns_anywhere: Columns to check for CR/LF anywhere in text

    Returns:
        Tuple of (is_valid, warning_messages) where is_valid is True if no warnings found
    """
    dataframe = dataframe.copy()
    all_warnings: List[str] = []

    _, warnings_start_end = check_special_characters_cr_lf_columns_start_end(dataframe, file_name, columns_start_end)
    all_warnings.extend(warnings_start_end)

    _, warnings_anywhere = check_special_characters_cr_lf_columns_anywhere(dataframe, file_name, columns_anywhere)
    all_warnings.extend(warnings_anywhere)

    return not bool(all_warnings), all_warnings


def check_unique_values(dataframe: pd.DataFrame, file_name: str, columns_uniques: List[str]) -> Tuple[bool, List[str]]:
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


def check_text_length(dataframe: pd.DataFrame, file_name: str, column: str, max_length: int) -> Tuple[bool, List[str]]:
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

    column_exists_result, error_message = column_exists(dataframe, file_name, column)
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


def check_dataframe_titles_uniques(
    dataframe: pd.DataFrame, column_one: str, column_two: str, plural_column_one: str, plural_column_two: str
) -> List[str]:
    dataframe = dataframe.copy()
    warnings = []

    # Se tiver vazio
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
