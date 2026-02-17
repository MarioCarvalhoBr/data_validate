#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module representing the Dictionary spreadsheet model.

This module defines the `SpDictionary` class, which handles the loading and
verification of dictionary data (allowed/ignored words) for spellchecking validation.
"""

from typing import List, Dict, Any

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import (
    DataLoaderModel,
)
from data_validate.models.sp_model_abc import SpModelABC


class SpDictionary(SpModelABC):
    """
    Model for the Dictionary spreadsheet.

    Manages validations for dictionary files, primarily used for ignoring
    specific terms during spell checking operations.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
        words_to_ignore (List[str]): List of words loaded from the dictionary to be ignored in spell checking.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Dictionary model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('dicionario').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_DICTIONARY
            self.SP_DESCRIPTION = "Dictionary sheet listing custom words to ignore in spell checking."
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Dictionary spreadsheet.

        Attributes:
            COLUMN_WORD (Series): Column definition for the word (string).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_WORD = pd.Series(dtype="str", name="palavra")

        ALL: List[str] = [
            COLUMN_WORD.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpDictionary model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        self.words_to_ignore: List[str] = []

        self.run()

    def pre_processing(self):
        """
        Pre-process the dictionary file to extract words.

        Reads the words from the dictionary dataframe. Each line is considered a word.
        Handles cases where the file has no explicit header by reading the first column as data.
        """
        self.words_to_ignore = []
        if self.data_loader_model and self.data_loader_model.df_data is not None:
            df = self.data_loader_model.df_data

            if len(df.columns) > 0:
                remaining_words = []
                if not df.empty:
                    remaining_words = df.iloc[:, 0].astype(str).tolist()

                self.words_to_ignore = remaining_words

    def expected_structure_columns(self, *args, **kwargs):
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

    def data_cleaning(self, *args, **kwargs):
        """
        Perform data cleaning operations.

        Currently empty as dictionary cleaning is handled during pre-processing
        or extraction.

        Returns:
            List[str]: Empty list (placeholder).
        """
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
            self.expected_structure_columns()
            self.data_cleaning()
