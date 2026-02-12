#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module representing the Composition spreadsheet model.

This module defines the `SpComposition` class, which handles the loading,
validation, and processing of composition data (parent-child relationships).
"""

from typing import List, Dict, Any

import pandas as pd

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
            self.SP_NAME = "composicao"
            self.SP_DESCRIPTION = "Planilha de composicao"
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

        ALL = [
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

        self.run()

    def pre_processing(self):
        """Run pre-processing steps (currently empty)."""
        pass

    def expected_structure_columns(self, *args, **kwargs) -> None:
        """
        Validate the structure of columns in the DataFrame.

        Checks for missing required columns and identifies extra columns not in the specification.
        Updates structural errors and warnings lists.
        """
        # Check missing columns, expected columns, and extra columns
        missing_columns, extra_columns = DataFrameProcessing.check_dataframe_column_names(
            self.data_loader_model.df_data, list(self.RequiredColumn.ALL)
        )
        col_errors, col_warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            self.filename, missing_columns, extra_columns
        )

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        """
        Perform data cleaning operations.

        Specific rules:
        1. Clean and validate 'codigo_pai' and 'codigo_filho' columns ensuring they contain
           positive integers (minimum 1).

        Returns:
            List[str]: List of data cleaning errors (unused return in this implementation).
        """
        # 1. Create mapping of column names to their corresponding class attributes 'parent_code' (min 1) and 'child_code' (min 1)
        column_attribute_mapping = {
            self.RequiredColumn.COLUMN_PARENT_CODE.name: "COLUMN_PARENT_CODE",
            self.RequiredColumn.COLUMN_CHILD_CODE.name: "COLUMN_CHILD_CODE",
        }

        # Clean and validate required columns (minimum value: 1)
        for column_name in column_attribute_mapping.keys():
            df, errors = DataCleaningProcessing.clean_dataframe_integers(
                self.data_loader_model.df_data,
                self.filename,
                [column_name],
                min_value=1,
            )
            self.data_cleaning_errors.extend(errors)

            if column_name in df.columns:
                # Use setattr to dynamically set the attribute
                attribute_name = column_attribute_mapping[column_name]
                setattr(self.RequiredColumn, attribute_name, df[column_name])

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
            self.expected_structure_columns()
            self.data_cleaning()
