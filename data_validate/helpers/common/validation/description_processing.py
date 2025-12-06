#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import Set

from pandas import DataFrame

from data_validate.helpers.common.formatting.number_formatting import check_cell_integer


class DescriptionProcessing:
    def __init__(self, dataframe: DataFrame) -> None:
        self.df_description = dataframe

    def get_valids_codes_from_description(self, column_name_level: str, column_name_code: str, column_name_scenario: str) -> Set[str]:
        df_description = self.df_description.copy()
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
