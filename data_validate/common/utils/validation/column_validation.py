import pandas as pd

def check_column_names(df: pd.DataFrame, expected_columns: list):
    missing_columns = []
    extra_columns = []

    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]

    # Clean up extra columns that are unnamed
    extra_columns = [col for col in extra_columns if not col.lower().startswith('unnamed')]

    return missing_columns, extra_columns
