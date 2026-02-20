#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Value spreadsheet model.

This module defines the `SpValue` class, which handles the loading,
validation, and processing of numerical value data across indicators.
"""

from typing import List, Dict, Any

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.processing.collections_processing import CollectionsProcessing
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpValue(SpModelABC):
    """
    Model for the Value spreadsheet.

    Manages specific validations for value data, primarily ensuring that the
    'codigo' column exists and contains valid integer identifiers.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Value model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('valores').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_VALUES
            self.SP_DESCRIPTION = "Values sheet storing indicator values across scenarios and time."
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Value spreadsheet.

        Attributes:
            COLUMN_CODE (Series): Column definition for the code (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_ID = pd.Series(dtype="int64", name="id")

        ALL: List[str] = [
            COLUMN_ID.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpValue model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        """Run pre-processing steps."""
        self.EXPECTED_COLUMNS = list(self.RequiredColumn.ALL)

        unique_columns = self.data_loader_model.df_data.columns.unique().tolist()

        # Remove ID self.RequiredColumn.COLUMN_ID.name
        unique_columns = [col for col in unique_columns if col != self.RequiredColumn.COLUMN_ID.name]

        __, codes_not_matched_by_pattern = CollectionsProcessing.categorize_strings_by_id_pattern_from_list(
            unique_columns, self.scenarios_list
        )

        if codes_not_matched_by_pattern:
            self.structural_errors.append(
                f"{self.filename}, linha 1: Colunas fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): {codes_not_matched_by_pattern}"
            )

    def expected_structure_columns(self, *args, **kwargs):
        """
        Validate the structure of columns in the DataFrame.

        Checks primarily for the presence of the 'codigo' column.
        Updates structural errors and warnings lists.
        """
        __, extras_columns = CollectionsProcessing.extract_numeric_ids_and_unmatched_strings_from_list(
            source_list=self.DF_COLUMNS,
            strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
            suffixes_for_matching=self.scenarios_list,
        )

        for extra_column in extras_columns:
            if extra_column.lower().startswith("unnamed"):
                continue
            self.structural_errors.append(f"{self.filename}: A coluna '{extra_column}' não é esperada.")
        for col in self.EXPECTED_COLUMNS:
            if col not in self.DF_COLUMNS:
                self.structural_errors.append(f"{self.filename}: Coluna '{col}' esperada mas não foi encontrada.")

    def data_cleaning(self, *args, **kwargs):
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
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.data_cleaning()
            self.expected_structure_columns()
