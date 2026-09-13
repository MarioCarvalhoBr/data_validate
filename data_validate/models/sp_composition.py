#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Composition spreadsheet model.

This module defines the `SpComposition` class, which handles the loading,
validation, and processing of composition data (parent-child relationships).
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


class SpComposition(SpModelABC):
    """
    Model for the Composition spreadsheet.

    Manages specific validations for composition data, defining
    parent-child relationships between indicators.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Composition model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('composicao').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_COMPOSITION
            self.SP_DESCRIPTION = "Composition sheet representing parent-child indicator relationships."
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Composition spreadsheet.

        Attributes:
            COLUMN_PARENT_CODE (Series): Column definition for the parent code (integer).
            COLUMN_CHILD_CODE (Series): Column definition for the child code (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_PARENT_CODE = pd.Series(dtype="int64", name="codigo_pai")
        COLUMN_CHILD_CODE = pd.Series(dtype="int64", name="codigo_filho")

        ALL: List[str] = [
            COLUMN_PARENT_CODE.name,
            COLUMN_CHILD_CODE.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpComposition model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

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
            self.frame, list(self.RequiredColumn.ALL)
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
        1. Clean and validate 'codigo_pai' and 'codigo_filho' columns ensuring they contain
           positive integers (minimum 1).

        Returns:
            List[str]: List of data cleaning errors (unused return in this implementation).
        """
        # Clean and validate required columns (minimum value: 1); store the cleaned data on
        # this instance (BUG-002) instead of overwriting the class-level `RequiredColumn`
        # placeholder Series that every instance/run in the process shares.
        for column_name in (self.RequiredColumn.COLUMN_PARENT_CODE.name, self.RequiredColumn.COLUMN_CHILD_CODE.name):
            df, errors = DataCleaningProcessing.clean_dataframe_integers(
                self.frame,
                self.filename,
                [str(column_name)],
                min_value=1,
            )
            self.data_cleaning_errors.extend(errors)

            if column_name in df.columns:
                self.cleaned[column_name] = df[column_name]

    def post_processing(self):
        """Run post-processing steps (currently empty)."""
        pass

    def run(self):
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        self.initialize()

        if self.data_loader_model.does_file_exist:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
