import pandas as pd
from typing import List, Tuple


def check_column_names(
    df: pd.DataFrame, expected_columns: List[str]
) -> Tuple[List[str], List[str]]:
    """
    Checks for missing and extra columns in a DataFrame compared to the expected columns.

    Args:
        df (pd.DataFrame): The DataFrame to check.
        expected_columns (List[str]): List of expected column names.

    Returns:
        Tuple[List[str], List[str]]: A tuple containing a list of missing columns and a list of extra columns.
    """
    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]
    # Remove unnamed extra columns - handle both string and numeric column names
    extra_columns = [
        col for col in extra_columns if not str(col).lower().startswith("unnamed")
    ]
    return missing_columns, extra_columns
