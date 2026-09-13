#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Scenario spreadsheet model.

This module defines the `SpScenario` class, which handles the loading,
validation, and processing of scenario data (e.g., SSPs, climate scenarios).
"""

from types import MappingProxyType
from typing import Any, List

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.models.sp_model_abc import SpModelABC


class SpScenario(SpModelABC):
    """
    Model for the Scenario spreadsheet.

    Manages specific validations for scenario data, ensuring structure integrity
    and valid symbols.

    Attributes:
        CONSTANTS (Constants): Immutable constants specific to this model.
    """

    # CONSTANTS
    class Constants(ConstantBase):
        """
        Immutable constants for the Scenario model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('cenarios').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self) -> None:
            """Initialize the model constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_SCENARIOS
            self.SP_DESCRIPTION = "Scenario sheet listing scenario symbols and descriptions."

            self._finalize_initialization()

    CONSTANTS = Constants()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Scenario spreadsheet.

        Attributes:
            COLUMN_NAME (Series): Column definition for the scenario name (string).
            COLUMN_DESCRIPTION (Series): Column definition for the scenario description (string).
            COLUMN_SYMBOL (Series): Column definition for the scenario symbol (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_NAME = pd.Series(dtype="str", name="nome")
        COLUMN_DESCRIPTION = pd.Series(dtype="str", name="descricao")
        COLUMN_SYMBOL = pd.Series(dtype="int64", name="simbolo")

        ALL: List[str] = [str(COLUMN_NAME.name), str(COLUMN_DESCRIPTION.name), str(COLUMN_SYMBOL.name)]

    OPTIONAL_COLUMNS: MappingProxyType[str, str] = MappingProxyType({})

    COLUMNS_PLURAL: MappingProxyType[str, str] = MappingProxyType({})

    def __init__(
        self,
        context: GeneralContext,
        data_model: LoadedSheet,
        **kwargs: object,
    ) -> None:
        """
        Initialize the SpScenario model.

        Args:
            context (GeneralContext): The application general context.
            data_model (LoadedSheet): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

    def pre_processing(self) -> None:
        """Run pre-processing steps."""
        translate = self.context.language_manager.text

        # SCEN-001: a delivered scenarios file must define at least one symbol.
        if self.scenario_exists_file and not self.scenarios:
            self.structural_errors.append(translate("rule.SCEN-001.error", filename=self.filename))

        # SCEN-002: repeated values in the 'simbolo' column (structural pass).
        if self.RequiredColumn.COLUMN_SYMBOL.name in self.data_loader_model.raw_data.columns:
            duplicated_symbols = self.data_loader_model.raw_data[self.RequiredColumn.COLUMN_SYMBOL.name].duplicated(
                keep=False
            )
            if duplicated_symbols.any():
                duplicated_values = self.data_loader_model.raw_data[duplicated_symbols][
                    self.RequiredColumn.COLUMN_SYMBOL.name
                ].unique()
                self.structural_errors.append(
                    translate(
                        "rule.SCEN-002.error",
                        filename=self.filename,
                        column=self.RequiredColumn.COLUMN_SYMBOL.name,
                        values=", ".join(map(str, duplicated_values)),
                    )
                )

    def expected_structure_columns(self, *args: Any, **kwargs: Any) -> None:
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
            self.filename, missing_columns, extra_columns, translate=self.context.language_manager.text
        )

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args: Any, **kwargs: Any) -> None:
        """Run data cleaning steps (currently empty)."""

    def post_processing(self) -> None:
        """Run post-processing steps (currently empty)."""

    def run(self) -> None:
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        self.initialize()

        if self.data_loader_model.does_file_exist:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
