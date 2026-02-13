#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module representing the Description spreadsheet model.

This module defines the `SpDescription` class, which handles the loading,
validation, and processing of description data (metadata for indicators).
"""

from typing import List, Dict, Any

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import (
    DataLoaderModel,
)
from data_validate.models.sp_model_abc import SpModelABC


class SpDescription(SpModelABC):
    """
    Model for the Description spreadsheet.

    Manages specific validations for description data, including structure
    verification, dynamic column handling (e.g., scenarios, legends), and data cleaning
    to ensure valid codes, levels, and consistent metadata.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Description model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('descricao').
            SP_DESCRIPTION (str): Description of the dataset.
            MAX_TITLE_LENGTH (int): Maximum allowed length for titles.
            MAX_SIMPLE_DESC_LENGTH (int): Maximum allowed length for simple descriptions.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_DESCRIPTION
            self.SP_DESCRIPTION = "Description sheet defining indicator metadata, names, and narrative fields."
            self.MAX_TITLE_LENGTH = 40
            self.MAX_SIMPLE_DESC_LENGTH = 150
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Description spreadsheet.

        Attributes:
            COLUMN_CODE (Series): Column definition for the code (integer).
            COLUMN_LEVEL (Series): Column definition for the level (integer).
            COLUMN_SIMPLE_NAME (Series): Column definition for the simple name (string).
            COLUMN_COMPLETE_NAME (Series): Column definition for the complete name (string).
            COLUMN_SIMPLE_DESC (Series): Column definition for the simple description (string).
            COLUMN_COMPLETE_DESC (Series): Column definition for the complete description (string).
            COLUMN_SOURCES (Series): Column definition for the sources (string).
            COLUMN_META (Series): Column definition for the meta information (string).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_CODE = pd.Series(dtype="int64", name="codigo")
        COLUMN_LEVEL = pd.Series(dtype="int64", name="nivel")
        COLUMN_SIMPLE_NAME = pd.Series(dtype="str", name="nome_simples")
        COLUMN_COMPLETE_NAME = pd.Series(dtype="str", name="nome_completo")
        COLUMN_SIMPLE_DESC = pd.Series(dtype="str", name="desc_simples")
        COLUMN_COMPLETE_DESC = pd.Series(dtype="str", name="desc_completa")
        COLUMN_SOURCES = pd.Series(dtype="str", name="fontes")
        COLUMN_META = pd.Series(dtype="str", name="meta")

        ALL = [
            COLUMN_CODE.name,
            COLUMN_LEVEL.name,
            COLUMN_SIMPLE_NAME.name,
            COLUMN_COMPLETE_NAME.name,
            COLUMN_SIMPLE_DESC.name,
            COLUMN_COMPLETE_DESC.name,
            COLUMN_SOURCES.name,
            COLUMN_META.name,
        ]

    class DynamicColumn:
        """
        Definitions of dynamic columns that depend on external files/configurations.

        Attributes:
            COLUMN_SCENARIO (Series): Column definition for the scenario.
            COLUMN_LEGEND (Series): Column definition for the legend.
            ALL (List[str]): List of all dynamic column names.
        """

        COLUMN_SCENARIO = pd.Series(dtype="int64", name="cenario")
        COLUMN_LEGEND = pd.Series(dtype="str", name="legenda")
        ALL = [COLUMN_SCENARIO.name, COLUMN_LEGEND.name]

    class OptionalColumn:
        """
        Definitions of optional columns.

        Attributes:
            COLUMN_UNIT (Series): Column definition for the unit.
            COLUMN_RELATION (Series): Column definition for the relation.
            COLUMN_ORDER (Series): Column definition for the order.
            ALL (List[str]): List of all optional column names.
        """

        COLUMN_UNIT = pd.Series(dtype="str", name="unidade")
        COLUMN_RELATION = pd.Series(dtype="int64", name="relacao")
        COLUMN_ORDER = pd.Series(dtype="int64", name="ordem")

        ALL = [
            COLUMN_UNIT.name,
            COLUMN_RELATION.name,
            COLUMN_ORDER.name,
        ]

    class PluralColumn:
        """
        Definitions of plural column variations.

        Attributes:
            COLUMN_PLURAL_SIMPLE_NAME (Series): Plural form for simple names.
            COLUMN_PLURAL_COMPLETE_NAME (Series): Plural form for complete names.
            ALL (List[str]): List of all plural column names.
        """

        COLUMN_PLURAL_SIMPLE_NAME = pd.Series(dtype="str", name="nomes_simples")
        COLUMN_PLURAL_COMPLETE_NAME = pd.Series(dtype="str", name="nomes_completos")
        ALL = [COLUMN_PLURAL_SIMPLE_NAME.name, COLUMN_PLURAL_COMPLETE_NAME.name]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpDescription model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)
        self.run()

    def pre_processing(self):
        """
        Run pre-processing steps including dynamic column handling and filling optional columns.

        1. Handles dynamic columns 'cenario' and 'legenda' based on file existence/read success.
        2. Fills optional columns with default values if missing ('relacao' -> 1, 'unidade' -> "").
        3. Updates EXPECTED_COLUMNS list to include found optional columns.
        """
        local_expected_columns = list(self.RequiredColumn.ALL)

        # 1.0. Handling dynamic columns: scenarios
        if (not self.scenario_read_success) and (self.DynamicColumn.COLUMN_SCENARIO.name in self.data_loader_model.df_data.columns):
            self.structural_errors.append(
                f"{self.filename}: A coluna '{self.DynamicColumn.COLUMN_SCENARIO.name}' não pode existir se o arquivo '{SHEET.SP_NAME_SCENARIOS}' não estiver configurado ou não existir."
            )
            self.data_loader_model.df_data = self.data_loader_model.df_data.drop(columns=[self.DynamicColumn.COLUMN_SCENARIO.name])
        elif self.scenario_exists_file:
            local_expected_columns.append(self.DynamicColumn.COLUMN_SCENARIO.name)

        # 1.1 Handling dynamic columns: legend
        if (not self.legend_read_success) and (self.DynamicColumn.COLUMN_LEGEND.name in self.data_loader_model.df_data.columns):
            self.structural_errors.append(
                f"{self.filename}: A coluna '{self.DynamicColumn.COLUMN_LEGEND.name}' não pode existir se o arquivo de legenda não estiver configurado ou não existir."
            )
            self.data_loader_model.df_data = self.data_loader_model.df_data.drop(columns=[self.DynamicColumn.COLUMN_LEGEND.name])
        elif self.legend_exists_file:
            local_expected_columns.append(self.DynamicColumn.COLUMN_LEGEND.name)

        # 2. Handling optional columns
        if self.OptionalColumn.COLUMN_RELATION.name not in self.data_loader_model.df_data.columns:
            self.data_loader_model.df_data[self.OptionalColumn.COLUMN_RELATION.name] = 1
        if self.OptionalColumn.COLUMN_UNIT.name not in self.data_loader_model.df_data.columns:
            self.data_loader_model.df_data[self.OptionalColumn.COLUMN_UNIT.name] = ""

        for opt_column_name in self.OptionalColumn.ALL:
            if (opt_column_name in self.data_loader_model.df_data.columns) and (opt_column_name not in local_expected_columns):
                local_expected_columns.append(opt_column_name)
        self.EXPECTED_COLUMNS = local_expected_columns

    def expected_structure_columns(self, *args, **kwargs) -> None:
        """
        Validate the structure of columns in the DataFrame.

        Checks for missing required columns and identifies extra columns not in the specification.
        Updates structural errors and warnings lists.
        """
        # Check missing columns, expected columns, and extra columns
        missing_columns, extra_columns = DataFrameProcessing.check_dataframe_column_names(self.data_loader_model.df_data, self.EXPECTED_COLUMNS)
        col_errors, col_warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            self.filename, missing_columns, extra_columns
        )

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        """
        Perform data cleaning operations.

        Specific rules:
        1. Clean and validate 'codigo' and 'nivel' columns ensuring they contain
           positive integers (minimum 1).
        2. If scenarios exist, clean and validate 'cenario' column (minimum -1).
        3. If legends exist, clean and validate 'legenda' column (positive integers),
           allowing empty values.

        Returns:
            List[str]: List of data cleaning errors (unused return in this implementation).
        """
        # 1. Create mapping of column names to their corresponding class attributes code (min 1) and level (min 1)
        column_attribute_mapping = {
            self.RequiredColumn.COLUMN_CODE.name: "COLUMN_CODE",
            self.RequiredColumn.COLUMN_LEVEL.name: "COLUMN_LEVEL",
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

        # 2. If scenarios exist, clean and validate 'cenario' column (minimum -1)
        if self.scenarios_list:
            col_cenario = self.DynamicColumn.COLUMN_SCENARIO.name
            df, errors_cenario = DataCleaningProcessing.clean_dataframe_integers(
                self.data_loader_model.df_data,
                self.filename,
                [col_cenario],
                min_value=-1,
            )
            if col_cenario in df.columns:
                self.DynamicColumn.COLUMN_SCENARIO = df[col_cenario]
            self.data_cleaning_errors.extend(errors_cenario)

        # 3. If legend column exists, ensure values are integers (minimum 1) or empty
        if self.legend_exists_file and (self.DynamicColumn.COLUMN_LEGEND.name in self.data_loader_model.df_data.columns):
            col_legenda = self.DynamicColumn.COLUMN_LEGEND.name
            df, errors_legenda = DataCleaningProcessing.clean_dataframe_integers(
                self.data_loader_model.df_data,
                self.filename,
                [col_legenda],
                min_value=1,
                allow_empty=True,
            )
            if col_legenda in df.columns:
                self.DynamicColumn.COLUMN_LEGEND = df[col_legenda]
            self.data_cleaning_errors.extend(errors_legenda)

    def post_processing(self):
        """Run post-processing steps (currently empty)."""
        pass

    def run(self):
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        # If dataframe is empty, it doesn't make sense to continue
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
