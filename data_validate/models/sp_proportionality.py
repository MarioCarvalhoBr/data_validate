#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module representing the Proportionality spreadsheet model.

This module defines the `SpProportionality` class, which handles the loading,
validation, and processing of proportionality data (influence weights between indicators).
"""

from typing import List, Dict, Any

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase

from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing

from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpProportionality(SpModelABC):
    """
    Model for the Proportionality spreadsheet.

    Manages specific validations for proportionality data, handling multi-level
    column structures (ID/Indicator) and verifying calculation integrity.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Proportionality model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('proporcionalidade').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_PROPORTIONALITIES
            self.SP_DESCRIPTION = "Proportionality sheet with influence weights between indicators."
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Proportionality spreadsheet.

        Attributes:
            COLUMN_ID (Series): Column definition for the ID (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_ID = pd.Series(dtype="int64", name="id")

        ALL = [
            COLUMN_ID.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpProportionality model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        """
        Run pre-processing steps.

        Performs checks on level 1 and level 2 column names to ensure they follow the expected pattern.
        """
        self.EXPECTED_COLUMNS = list(self.RequiredColumn.ALL)

        unique_columns_level_1 = self.data_loader_model.df_data.columns.get_level_values(0).unique().tolist()
        unique_columns_level_1 = [col for col in unique_columns_level_1 if not col.lower().startswith("unnamed: 0_level_0")]

        __, level_1_codes_not_matched_by_pattern = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
            unique_columns_level_1, self.scenarios_list
        )

        if level_1_codes_not_matched_by_pattern:
            self.structural_errors.append(
                f"{self.filename}, linha 1: Colunas de nível 1 fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): {level_1_codes_not_matched_by_pattern}"
            )
        else:
            unique_columns_level_2 = self.data_loader_model.df_data.columns.get_level_values(1).unique().tolist()
            unique_columns_level_2 = [col for col in unique_columns_level_2 if col != self.RequiredColumn.COLUMN_ID.name]

            __, level_2_codes_not_matched_by_pattern = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
                unique_columns_level_2, self.scenarios_list
            )

            if level_2_codes_not_matched_by_pattern and not level_1_codes_not_matched_by_pattern:
                self.structural_errors.append(
                    f"{self.filename}, linha 2: Colunas de nível 2 fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): {level_2_codes_not_matched_by_pattern}"
                )

        if self.structural_errors:
            self.data_loader_model.df_data = pd.DataFrame()  # Clear DataFrame to avoid further processing
            self.data_loader_model.header_type = "invalid"

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        """
        Validate the structure of columns in the DataFrame.

        Checks for missing required columns and identifies extra columns not in the specification.
        Updates structural errors list.
        """
        if self.data_loader_model.header_type == "double":
            unique_columns_level_1 = self.data_loader_model.df_data.columns.get_level_values(0).unique().tolist()
            unique_columns_level_2 = self.data_loader_model.df_data.columns.get_level_values(1).unique().tolist()

            # Check extra columns in level 1 (do not ignore 'id')
            _, extras_level_1 = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=unique_columns_level_1,
                strings_to_ignore=[],  # Do not ignore 'id' here
                suffixes_for_matching=self.scenarios_list,
            )
            for extra_column in extras_level_1:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(f"{self.filename}: A coluna de nível 1 '{extra_column}' não é esperada.")

            # Check extra columns in level 2 (ignore 'id')
            _, extras_level_2 = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=unique_columns_level_2,
                strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
                suffixes_for_matching=self.scenarios_list,
            )
            for extra_column in extras_level_2:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(f"{self.filename}: A coluna de nível 2 '{extra_column}' não é esperada.")

            # Check for missing expected columns in level 2
            for col in self.EXPECTED_COLUMNS:
                if col not in unique_columns_level_2:
                    self.structural_errors.append(f"{self.filename}: Coluna de nível 2 '{col}' esperada mas não foi encontrada.")

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        """Run data cleaning steps (currently empty)."""
        pass

    def post_processing(self):
        """Run post-processing steps (currently empty)."""
        pass

    def run(self):
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        if self.data_loader_model.exists_file and not self.data_loader_model.df_data.empty and self.data_loader_model.header_type == "double":
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
