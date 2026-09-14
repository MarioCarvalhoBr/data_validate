#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Description spreadsheet model.

This module defines the `SpDescription` class, which handles the loading,
validation, and processing of description data (metadata for indicators).
"""

from typing import Any, List

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.processing.data_cleaning_processing import DataCleaningProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.tools.data_loader.api.facade import (
    LoadedSheet,
)
from data_validate.models.sp_model_abc import SpModelABC


class SpDescription(SpModelABC):
    """
    Model for the Description spreadsheet.

    Manages specific validations for description data, including structure
    verification, dynamic column handling (e.g., scenarios, legends), and data cleaning
    to ensure valid codes, levels, and consistent metadata.

    Attributes:
        CONSTANTS (Constants): Immutable constants specific to this model.
    """

    # CONSTANTS
    class Constants(ConstantBase):
        """
        Immutable constants for the Description model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('descricao').
            SP_DESCRIPTION (str): Description of the dataset.
            MAX_TITLE_LENGTH (int): Maximum allowed length for titles.
            MAX_SIMPLE_DESC_LENGTH (int): Maximum allowed length for simple descriptions.
        """

        def __init__(self) -> None:
            """Initialize the model constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_DESCRIPTION
            self.SP_DESCRIPTION = "Description sheet defining indicator metadata, names, and narrative fields."
            self.MAX_TITLE_LENGTH = 40
            self.MAX_SIMPLE_DESC_LENGTH = 150
            self._finalize_initialization()

    CONSTANTS = Constants()

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
            COLUMN_META (Series): Column definition for the meta information (string).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_CODE = pd.Series(dtype="int64", name="codigo")
        COLUMN_LEVEL = pd.Series(dtype="int64", name="nivel")
        COLUMN_SIMPLE_NAME = pd.Series(dtype="str", name="nome_simples")
        COLUMN_COMPLETE_NAME = pd.Series(dtype="str", name="nome_completo")
        COLUMN_SIMPLE_DESC = pd.Series(dtype="str", name="desc_simples")
        COLUMN_COMPLETE_DESC = pd.Series(dtype="str", name="desc_completa")
        COLUMN_META = pd.Series(dtype="str", name="meta")

        ALL: List[str] = [
            str(COLUMN_CODE.name),
            str(COLUMN_LEVEL.name),
            str(COLUMN_SIMPLE_NAME.name),
            str(COLUMN_COMPLETE_NAME.name),
            str(COLUMN_SIMPLE_DESC.name),
            str(COLUMN_COMPLETE_DESC.name),
            str(COLUMN_META.name),
        ]

    class DynamicColumn:
        """
        Definitions of dynamic columns that depend on external files/configurations.

        Attributes:
            COLUMN_SCENARIO (Series): Column definition for the scenario.
            COLUMN_LEGEND (Series): Column definition for the legend (nullable integer: cleaned as
                an integer >= 1 with empty cells allowed, see ``SpDescription.data_cleaning``).
            ALL (List[str]): List of all dynamic column names.
        """

        COLUMN_SCENARIO = pd.Series(dtype="int64", name="cenario")
        COLUMN_LEGEND = pd.Series(dtype="Int64", name="legenda")
        ALL: List[str] = [str(COLUMN_SCENARIO.name), str(COLUMN_LEGEND.name)]

    class OptionalColumn:
        """
        Definitions of optional columns.

        Attributes:
            COLUMN_UNIT (Series): Column definition for the unit.
            COLUMN_ORDER (Series): Column definition for the order.
            COLUMN_CATEGORY (Series): Column definition for the category (`social`/`economico`/
                `ambiental`/`climatico` — domain validated by `rules/description.py::DESC-013`,
                PROTO-004; staged as optional until a future re-baseline makes it required).
            ALL (List[str]): List of all optional column names.
        """

        COLUMN_UNIT = pd.Series(dtype="str", name="unidade")
        COLUMN_ORDER = pd.Series(dtype="int64", name="ordem")
        COLUMN_CATEGORY = pd.Series(dtype="str", name="categoria")

        ALL: List[str] = [
            str(COLUMN_UNIT.name),
            str(COLUMN_ORDER.name),
            str(COLUMN_CATEGORY.name),
        ]

    class DeprecatedColumn:
        """
        Definitions of columns the protocol no longer defines (PROTO-001/PROTO-002).

        Never required, never injected with a default value when absent, and never flagged
        as an unexpected/extra column when present — accepted silently for bundles still
        carrying them from a pre-v1.15/v1.16 delivery.

        Attributes:
            COLUMN_SOURCES (Series): Column definition for the sources (`fontes`, removed by
                protocol v1.16: "não é usada").
            COLUMN_RELATION (Series): Column definition for the relation (`relacao`, removed by
                protocol v1.15: "parâmetro desnecessário").
            ALL (List[str]): List of all deprecated column names.
        """

        COLUMN_SOURCES = pd.Series(dtype="str", name="fontes")
        COLUMN_RELATION = pd.Series(dtype="int64", name="relacao")

        ALL: List[str] = [
            str(COLUMN_SOURCES.name),
            str(COLUMN_RELATION.name),
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: LoadedSheet,
        **kwargs: object,
    ) -> None:
        """
        Initialize the SpDescription model.

        Args:
            context (GeneralContext): The application general context.
            data_model (LoadedSheet): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

    def pre_processing(self) -> None:
        """
        Run pre-processing steps including dynamic column handling and filling optional columns.

        1. Handles dynamic columns 'cenario' and 'legenda' based on file existence/read success.
        2. Fills optional columns with default values if missing ('unidade' -> "").
        3. Updates EXPECTED_COLUMNS list to include found optional columns and any deprecated
           column ('fontes', 'relacao' — PROTO-001/PROTO-002) that happens to be present, so it
           is accepted silently: never reported missing, never reported as an unexpected column.
        """
        translate = self.context.language_manager.text
        local_expected_columns = list(self.RequiredColumn.ALL)

        # 1.0. Handling dynamic columns: scenarios (DESC-011)
        if (not self.scenario_read_success) and (self.DynamicColumn.COLUMN_SCENARIO.name in self.frame.columns):
            self.structural_errors.append(
                translate(
                    "rule.DESC-011.error",
                    filename=self.filename,
                    column=self.DynamicColumn.COLUMN_SCENARIO.name,
                    scenarios_file=SHEET.SP_NAME_SCENARIOS,
                )
            )
            # BUG-003: reassign `self.frame` to the (new) frame `.drop` returns instead of
            # writing into `self.data_loader_model.raw_data`, which every other model and
            # validator also reads.
            self.frame = self.frame.drop(columns=[self.DynamicColumn.COLUMN_SCENARIO.name])
        elif self.scenario_exists_file:
            local_expected_columns.append(str(self.DynamicColumn.COLUMN_SCENARIO.name))

        # 1.1 Handling dynamic columns: legend (DESC-012)
        if (not self.legend_read_success) and (self.DynamicColumn.COLUMN_LEGEND.name in self.frame.columns):
            self.structural_errors.append(
                translate("rule.DESC-012.error", filename=self.filename, column=self.DynamicColumn.COLUMN_LEGEND.name)
            )
            self.frame = self.frame.drop(columns=[self.DynamicColumn.COLUMN_LEGEND.name])
        elif self.legend_exists_file:
            local_expected_columns.append(str(self.DynamicColumn.COLUMN_LEGEND.name))

        # 2. Handling optional columns. `.assign` returns a new frame rather than mutating
        # `self.frame`/`raw_data` in place (BUG-003).
        if self.OptionalColumn.COLUMN_UNIT.name not in self.frame.columns:
            self.frame = self.frame.assign(**{str(self.OptionalColumn.COLUMN_UNIT.name): ""})

        for opt_column_name in self.OptionalColumn.ALL:
            if (opt_column_name in self.frame.columns) and (opt_column_name not in local_expected_columns):
                local_expected_columns.append(opt_column_name)

        # 3. Deprecated columns (PROTO-001/PROTO-002): no default injection, only added to
        # EXPECTED_COLUMNS when the bundle still carries them, so `expected_structure_columns`
        # neither reports them missing (they are simply absent from EXPECTED_COLUMNS when the
        # bundle omits them) nor reports them as an unexpected extra column (they are present in
        # EXPECTED_COLUMNS whenever the bundle carries them).
        for deprecated_column_name in self.DeprecatedColumn.ALL:
            if (deprecated_column_name in self.frame.columns) and (
                deprecated_column_name not in local_expected_columns
            ):
                local_expected_columns.append(deprecated_column_name)

        self.EXPECTED_COLUMNS = local_expected_columns

    def expected_structure_columns(self, *args: Any, **kwargs: Any) -> None:
        """
        Validate the structure of columns in the DataFrame.

        Checks for missing required columns and identifies extra columns not in the specification.
        Updates structural errors and warnings lists.
        """
        # Check missing columns, expected columns, and extra columns
        missing_columns, extra_columns = DataFrameProcessing.check_dataframe_column_names(
            self.frame, self.EXPECTED_COLUMNS
        )
        col_errors, col_warnings = MessageFormattingProcessing.format_text_to_missing_and_expected_columns(
            self.filename, missing_columns, extra_columns, translate=self.context.language_manager.text
        )

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args: Any, **kwargs: Any) -> None:
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
        translate = self.context.language_manager.text

        # 1. Clean and validate required columns (minimum value: 1); store the cleaned data on
        # this instance (BUG-002) instead of overwriting the class-level `RequiredColumn`
        # placeholder Series that every instance/run in the process shares. (CLEAN-001)
        for column_name in (self.RequiredColumn.COLUMN_CODE.name, self.RequiredColumn.COLUMN_LEVEL.name):
            dataframe_cleaned, errors_data_clean_local = DataCleaningProcessing.clean_dataframe_integers(
                self.frame,
                self.filename,
                [str(column_name)],
                min_value=1,
                translate=translate,
                rule_id="CLEAN-001",
            )
            self.data_cleaning_errors.extend(errors_data_clean_local)

            if column_name in dataframe_cleaned.columns:
                self.cleaned[str(column_name)] = dataframe_cleaned[column_name]

        # 2. If scenarios exist, clean and validate 'cenario' column (minimum -1) (CLEAN-002)
        if self.scenarios:
            column_name_scenario = str(self.DynamicColumn.COLUMN_SCENARIO.name)
            dataframe_cleaned, errors_data_clean_local = DataCleaningProcessing.clean_dataframe_integers(
                self.frame,
                self.filename,
                [str(column_name_scenario)],
                min_value=-1,
                translate=translate,
                rule_id="CLEAN-002",
            )
            if column_name_scenario in dataframe_cleaned.columns:
                self.cleaned[column_name_scenario] = dataframe_cleaned[column_name_scenario]
            self.data_cleaning_errors.extend(errors_data_clean_local)

        # 3. If legend column exists, ensure values are integers (minimum 1) or empty (CLEAN-003)
        if self.legend_exists_file and (self.DynamicColumn.COLUMN_LEGEND.name in self.frame.columns):
            column_name_legend = str(self.DynamicColumn.COLUMN_LEGEND.name)
            dataframe_cleaned, errors_data_clean_local = DataCleaningProcessing.clean_dataframe_integers(
                self.frame,
                self.filename,
                [str(column_name_legend)],
                min_value=1,
                allow_empty=True,
                translate=translate,
                rule_id="CLEAN-003",
            )
            if column_name_legend in dataframe_cleaned.columns:
                self.cleaned[column_name_legend] = dataframe_cleaned[column_name_legend]
            self.data_cleaning_errors.extend(errors_data_clean_local)

    def post_processing(self) -> None:
        """Run post-processing steps (currently empty)."""

    def run(self) -> None:
        """
        Execute the full validation pipeline for this model.

        Runs pre-processing, structure validation, and data cleaning if the file exists.
        """
        self.initialize()

        # If dataframe is empty, it doesn't make sense to continue
        if self.data_loader_model.does_file_exist:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
