#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Tuple, Dict, Any, Set
import pandas as pd
from decimal import Decimal

def get_filtered_description_dataframe(
    df_code_level_cleaned: pd.DataFrame,
    level_column_name: str,
    scenario_column_name: str = None
) -> pd.DataFrame:
    """
    Get cleaned description dataframe with level filters applied.

    Args:
        df_code_level_cleaned: The cleaned code-level dataframe
        level_column_name: Name of the level column
        scenario_column_name: Name of the scenario column (optional)

    Returns:
        Filtered dataframe
    """
    # Remove level 1 indicators
    df_filtered = df_code_level_cleaned[df_code_level_cleaned[level_column_name] != '1']

    # Remove level 2 indicators with scenario 0 if scenario column exists
    if scenario_column_name and scenario_column_name in df_filtered.columns:
        df_filtered = df_filtered[
            ~((df_filtered[level_column_name] == '2') &
              (df_filtered[scenario_column_name] == '0'))
        ]

    return df_filtered


def extract_level_one_codes(
    df_code_level_cleaned: pd.DataFrame,
    code_column_name: str,
    level_column_name: str
) -> List[str]:
    """
    Extract level 1 codes to be ignored during validation.

    Args:
        df_code_level_cleaned: The cleaned code-level dataframe
        code_column_name: Name of the code column
        level_column_name: Name of the level column

    Returns:
        List of level 1 codes as strings
    """
    return df_code_level_cleaned[
        df_code_level_cleaned[level_column_name] == '1'
    ][code_column_name].astype(str).tolist()


def process_invalid_columns(invalid_columns: List[str]) -> List[str]:
    """
    Process and clean invalid column names, returning sorted list.

    Args:
        invalid_columns: List of invalid column names

    Returns:
        Sorted list of filtered invalid columns
    """
    # Filter out columns containing ':'
    filtered_columns = {col for col in invalid_columns if ':' not in col}
    return sorted(filtered_columns)


def validate_scenario_columns_exist(
    scenario_dataframe: pd.DataFrame,
    scenario_column_names: List[str],
    exists_scenario: bool
) -> List[str]:
    """
    Validate scenario columns if scenarios exist.

    Args:
        scenario_dataframe: The scenario dataframe to check
        scenario_column_names: List of required scenario column names
        exists_scenario: Whether scenarios should exist

    Returns:
        List of error messages
    """
    if not exists_scenario:
        return []

    errors = []
    for column in scenario_column_names:
        if column not in scenario_dataframe.columns:
            errors.append(f"Coluna obrigatória '{column}' não encontrada no arquivo de cenários.")

    return errors


def prepare_values_dataframe(dataframe: pd.DataFrame, id_column_name: str) -> pd.DataFrame:
    """
    Prepare values dataframe by removing ID column if it exists.

    Args:
        dataframe: The input dataframe
        id_column_name: Name of the ID column to remove

    Returns:
        Dataframe with ID column removed if it existed
    """
    df_values = dataframe.copy()

    if id_column_name in df_values.columns:
        df_values = df_values.drop(columns=[id_column_name])

    return df_values


def validate_numeric_value(
    value: Any,
    row_index: int,
    column: str,
    filename: str
) -> Tuple[bool, str, bool]:
    """
    Validate a single numeric value.

    Args:
        value: The value to validate
        row_index: Index of the row (0-based)
        column: Name of the column
        filename: Name of the file for error messages

    Returns:
        Tuple of (is_valid, error_message, has_excessive_decimals)
    """
    # Skip DI (Data Unavailable) values
    if value == "DI":
        return True, "", False

    # Check if value is NaN or can't be converted to numeric
    numeric_value = pd.to_numeric(str(value).replace(',', '.'), errors='coerce')
    if pd.isna(value) or pd.isna(numeric_value):
        error_msg = (f"{filename}, linha {row_index + 2}: "
                    f"O valor não é um número válido e nem DI (Dado Indisponível) "
                    f"para a coluna '{column}'.")
        return False, error_msg, False

    # Check decimal places using Decimal for precision
    try:
        decimal_value = Decimal(str(value).replace(',', '.'))
        has_excessive_decimals = decimal_value.as_tuple().exponent < -2
        return True, "", has_excessive_decimals
    except (ValueError, TypeError):
        error_msg = (f"{filename}, linha {row_index + 2}: "
                    f"Erro ao processar valor decimal para a coluna '{column}'.")
        return False, error_msg, False


def process_column_validation(
    df_values: pd.DataFrame,
    column: str,
    filename: str
) -> Tuple[List[str], Set[int]]:
    """
    Process validation for a single column.

    Args:
        df_values: The dataframe containing values to validate
        column: The column name to validate
        filename: The filename for error messages

    Returns:
        Tuple of (error_messages, rows_with_excessive_decimals)
    """
    errors = []
    excessive_decimal_rows = set()

    invalid_values = []
    first_invalid_row = None
    last_invalid_row = None

    for index, value in df_values[column].items():
        is_valid, error_msg, has_excessive_decimals = validate_numeric_value(
            value, index, column, filename
        )

        if not is_valid:
            invalid_values.append((index + 2, error_msg))
            if first_invalid_row is None:
                first_invalid_row = index + 2
            last_invalid_row = index + 2

        if has_excessive_decimals:
            excessive_decimal_rows.add(index + 2)

    # Generate error messages based on count
    if len(invalid_values) == 1:
        errors.append(invalid_values[0][1])
    elif len(invalid_values) > 1:
        error_msg = (f"{filename}: {len(invalid_values)} valores que não são "
                    f"número válido nem DI (Dado Indisponível) para a coluna '{column}', "
                    f"entre as linhas {first_invalid_row} e {last_invalid_row}.")
        errors.append(error_msg)

    return errors, excessive_decimal_rows


def generate_decimal_warning(
    all_excessive_decimal_rows: Set[int],
    count_excessive_decimal_rows: int,
    filename: str
) -> str:
    """
    Generate warning message for values with excessive decimal places.

    Args:
        all_excessive_decimal_rows: Set of row numbers with excessive decimals
        count_excessive_decimal_rows: Total count of values with excessive decimals
        filename: The filename for the warning message

    Returns:
        Warning message string or empty string if no warnings
    """
    if not all_excessive_decimal_rows:
        return ""

    count = len(all_excessive_decimal_rows)
    text_existem = "Existem" if count > 1 else "Existe"
    text_valores = "valores" if count > 1 else "valor"

    sorted_rows = sorted(all_excessive_decimal_rows)
    first_row = sorted_rows[0]
    last_row = sorted_rows[-1]

    return (f"{filename}: {text_existem} {count_excessive_decimal_rows} {text_valores} com mais de 2 "
           f"casas decimais, serão consideradas apenas as 2 primeiras casas decimais. "
           f"Entre as linhas {first_row} e {last_row}.")


def validate_data_values_in_columns(
    dataframe: pd.DataFrame,
    valid_columns: List[str],
    filename: str
) -> Tuple[List[str], List[str]]:
    """
    Validate data values in specified columns for numeric validity and decimal places.

    Args:
        dataframe: The dataframe to validate
        valid_columns: List of column names to validate
        filename: The filename for error/warning messages

    Returns:
        Tuple of (errors, warnings) lists
    """
    errors, warnings = [], []

    # Process each valid column
    all_excessive_decimal_rows = set()
    count_excessive_decimal_rows = 0

    for column in valid_columns:
        column_errors, excessive_decimal_rows = process_column_validation(
            dataframe, column, filename
        )
        errors.extend(column_errors)
        count_excessive_decimal_rows += len(excessive_decimal_rows)
        all_excessive_decimal_rows.update(excessive_decimal_rows)

    # Generate warning for excessive decimal places
    decimal_warning = generate_decimal_warning(
        all_excessive_decimal_rows, count_excessive_decimal_rows, filename
    )
    if decimal_warning:
        warnings.append(decimal_warning)

    return errors, warnings
