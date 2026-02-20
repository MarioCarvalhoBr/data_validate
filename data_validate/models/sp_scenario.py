#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Scenario spreadsheet model.

This module defines the `SpScenario` class, which handles the loading,
validation, and processing of scenario data (e.g., SSPs, climate scenarios).
"""

from types import MappingProxyType
from typing import List, Dict, Any

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpScenario(SpModelABC):
    """
    Model for the Scenario spreadsheet.

    Manages specific validations for scenario data, ensuring structure integrity
    and valid symbols.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Scenario model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('cenarios').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_SCENARIOS
            self.SP_DESCRIPTION = "Scenario sheet listing scenario symbols and descriptions."

            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Scenario spreadsheet.

        Attributes:
            COLUMN_NAME (Series): Column definition for the scenario name (integer).
            COLUMN_DESCRIPTION (Series): Column definition for the scenario description (string).
            COLUMN_SYMBOL (Series): Column definition for the scenario symbol (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_NAME = pd.Series(dtype="int64", name="nome")
        COLUMN_DESCRIPTION = pd.Series(dtype="str", name="descricao")
        COLUMN_SYMBOL = pd.Series(dtype="int64", name="simbolo")

        ALL: List[str] = [COLUMN_NAME.name, COLUMN_DESCRIPTION.name, COLUMN_SYMBOL.name]

    OPTIONAL_COLUMNS = MappingProxyType({})

    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpScenario model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        """Run pre-processing steps."""
        if self.scenario_exists_file and not self.scenarios_list:
            self.structural_errors.extend(
                [f"{self.filename}: Arquivo de cenários com configuração incorreta. Consulte a especificação do modelo de dados."]
            )

        # Repeated values in the 'simbolo' column
        if self.RequiredColumn.COLUMN_SYMBOL.name in self.data_loader_model.df_data.columns:
            duplicated_symbols = self.data_loader_model.df_data[self.RequiredColumn.COLUMN_SYMBOL.name].duplicated(keep=False)
            if duplicated_symbols.any():
                duplicated_values = self.data_loader_model.df_data[duplicated_symbols][self.RequiredColumn.COLUMN_SYMBOL.name].unique()
                self.structural_errors.append(
                    f"{self.filename}: Valores duplicados encontrados na coluna '{self.RequiredColumn.COLUMN_SYMBOL.name}': [{', '.join(map(str, duplicated_values))}]"
                )

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
            self.expected_structure_columns()
            self.data_cleaning()
