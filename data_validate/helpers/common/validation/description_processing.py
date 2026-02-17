#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module providing description data validation utilities.

This module defines the `DescriptionProcessing` class, which offers methods
to extract and validate codes from description DataFrames, filtering by levels
and checking for integer validity.
"""

from typing import Set

from pandas import DataFrame

from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing


class DescriptionProcessing:
    """
    Utility class for processing description data.

    Provides static methods to retrieve valid codes from description datasets
    by applying business rules regarding hierarchy levels and indicator status.
    """

    def __init__(self) -> None:
        """Initialize the DescriptionProcessing class."""
        pass

    @staticmethod
    def get_valids_codes_from_description(
        df_description: DataFrame, column_name_level: str, column_name_code: str, column_name_scenario: str
    ) -> Set[str]:
        """
        Extract valid codes from the description DataFrame.

        Filters the description data to get codes that are not at level 1 and,
        if applicable, excludes specific scenarios (e.g. level 2 with scenario 0).
        Ensures returned codes are valid integers.

        Args:
            df_description: The DataFrame containing description data
            column_name_level: Column name for hierarchy levels
            column_name_code: Column name for codes
            column_name_scenario: Column name for scenario identifiers

        Returns:
            Set of valid code strings
        """
        df_description = df_description.copy()
        df_description = df_description[df_description[column_name_level] != "1"]

        if column_name_scenario in df_description.columns:
            df_description = df_description[~((df_description[column_name_level] == "2") & (df_description[column_name_scenario] == "0"))]

        codes_cleaned = set(df_description[column_name_code].astype(str))
        valid_codes = set()

        for code in codes_cleaned:
            is_correct, __ = NumberFormattingProcessing.check_cell_integer(code, 1)
            if is_correct:
                valid_codes.add(code)

        set_valid_codes = set(str(code) for code in valid_codes)
        return set_valid_codes
