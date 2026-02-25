#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Temporal Reference spreadsheet model.

This module defines the `SpTemporalReference` class, which handles the loading,
validation, and processing of temporal reference data (e.g., years, periods)
used in the data validation process.
"""

from typing import List, Dict, Any

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpTemporalReference(SpModelABC):
    """
    Model for the Temporal Reference spreadsheet.

    Manages specific validations for temporal reference data, including structure
    verification and data cleaning to ensure valid temporal symbols.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Temporal Reference model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('referencia_temporal').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()

            self.SP_NAME = SHEET.SP_NAME_TEMPORAL_REFERENCE
            self.SP_DESCRIPTION = "Temporal reference sheet defining time symbols and descriptions."
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Temporal Reference spreadsheet.

        Attributes:
            COLUMN_NAME (Series): Column definition for the name.
            COLUMN_DESCRIPTION (Series): Column definition for the description.
            COLUMN_SYMBOL (Series): Column definition for the symbol (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_NAME = pd.Series(dtype="int64", name="nome")
        COLUMN_DESCRIPTION = pd.Series(dtype="str", name="descricao")
        COLUMN_SYMBOL = pd.Series(dtype="int64", name="simbolo")

        ALL: List[str] = [COLUMN_NAME.name, COLUMN_DESCRIPTION.name, COLUMN_SYMBOL.name]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpTemporalReference model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        """Run pre-processing steps (currently empty)."""
        pass

    def expected_structure_columns(self, *args, **kwargs):
        """
        Validate the structure of columns in the DataFrame.

        Checks for missing required columns and identifies extra columns not in the specification.
        Updates structural errors and warnings lists.
        """
        # Check missing columns, expected columns, and extra columns
        missing_columns, extra_columns = DataFrameProcessing.check_dataframe_column_names(
            self.data_loader_model.raw_data, list(self.RequiredColumn.ALL)
        )
        col_errors, col_warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            self.filename, missing_columns, extra_columns
        )

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs):
        """
        Perform data cleaning operations.

        Specific rules:
        1. If scenarios list is empty, the table must strictly contain one row (default).
        2. Clean and validate the 'simbolo' (symbol) column to be non-negative integers.

        Returns:
            List[str]: List of data cleaning errors (unused return in this implementation).
        """
        # Verify if the scenarios list is empty and handle single-value constraint
        if (not self.scenarios) and (len(self.data_loader_model.raw_data) != 1):
            self.data_cleaning_errors.append(
                f"{self.filename}: A tabela deve ter apenas um valor porque o arquivo '{SHEET.SP_NAME_SCENARIOS}' não existe ou está vazio."
            )

            if self.RequiredColumn.COLUMN_SYMBOL.name in self.data_loader_model.raw_data.columns:
                self.RequiredColumn.COLUMN_SYMBOL = self.data_loader_model.raw_data[self.RequiredColumn.COLUMN_SYMBOL.name].iloc[0:1]
        else:
            # 1. Clean and validate the 'symbol' column (minimum 0)
            col_symbol = self.RequiredColumn.COLUMN_SYMBOL.name

            df, errors_symbol = DataCleaningProcessing.clean_dataframe_integers(
                self.data_loader_model.raw_data, self.filename, [str(col_symbol)], min_value=0
            )
            self.data_cleaning_errors.extend(errors_symbol)

            if self.RequiredColumn.COLUMN_SYMBOL.name in df.columns:
                self.RequiredColumn.COLUMN_SYMBOL = df[self.RequiredColumn.COLUMN_SYMBOL.name]

    def post_processing(self):
        """Run post-processing steps (currently empty)."""
        pass

    def run(self):
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        if self.data_loader_model.does_file_exist:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
