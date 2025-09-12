#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import Set

import pandas as pd
from pandas import DataFrame

from data_validate.helpers.common.formatting.number_formatting import check_cell_integer


def get_valids_codes_from_description(
    df_description: pd.DataFrame, column_name_level: str, column_name_code: str, column_name_scenario: str
) -> Set[str]:
    df_description = df_description[df_description[column_name_level] != "1"]

    if column_name_scenario in df_description.columns:
        df_description = df_description[~((df_description[column_name_level] == "2") & (df_description[column_name_scenario] == "0"))]

    codes_cleaned = set(df_description[column_name_code].astype(str))
    valid_codes = set()

    for code in codes_cleaned:
        is_correct, __ = check_cell_integer(code, 1)
        if is_correct:
            valid_codes.add(code)

    set_valid_codes = set(str(code) for code in valid_codes)
    return set_valid_codes


def build_subdatasets(df_proportionalities: DataFrame, column_name_id: str):
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
