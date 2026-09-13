#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module representing the Legend spreadsheet model.

This module defines the `SpLegend` class, which handles the loading,
validation, and processing of legend data (e.g., labels, min/max values, colors).
"""

from typing import Any, List

import pandas as pd

from data_validate.config import SHEET
from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.common.validation.legend_processing import LegendProcessing
from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.models.sp_model_abc import SpModelABC


class SpLegend(SpModelABC):
    """
    Model for the Legend spreadsheet.

    Manages specific validations for legend data, handling dynamic grouping
    of legends based on codes and validating min/max ranges, colors, and labels.

    Attributes:
        CONSTANTS (Constants): Immutable constants specific to this model.
    """

    # CONSTANTS
    class Constants(ConstantBase):
        """
        Immutable constants for the Legend model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('legenda').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self) -> None:
            """Initialize the model constants."""
            super().__init__()
            self.SP_NAME = SHEET.SP_NAME_LEGEND
            self.SP_DESCRIPTION = "Legend sheet defining labels, colors, and value ranges for classification."
            # Others constants
            self.MIN_LOWER_LEGEND_DEFAULT = 0
            self.MAX_UPPER_LEGEND_DEFAULT = 1
            self._finalize_initialization()

    CONSTANTS = Constants()

    # COLUMN SERIES
    class RequiredColumn:
        """
        Definitions of required columns for the Legend spreadsheet.

        Attributes:
            COLUMN_CODE (Series): Column definition for the code (integer).
            COLUMN_LABEL (Series): Column definition for the label (string).
            COLUMN_COLOR (Series): Column definition for the color hex code (string).
            COLUMN_MINIMUM (Series): Column definition for the minimum value (float).
            COLUMN_MAXIMUM (Series): Column definition for the maximum value (float).
            COLUMN_ORDER (Series): Column definition for the sorting order (integer).
            ALL (List[str]): List of all required column names.
        """

        COLUMN_CODE = pd.Series(dtype="int64", name="codigo")
        COLUMN_LABEL = pd.Series(dtype="str", name="label")
        COLUMN_COLOR = pd.Series(dtype="str", name="cor")
        COLUMN_MINIMUM = pd.Series(dtype="float64", name="minimo")
        COLUMN_MAXIMUM = pd.Series(dtype="float64", name="maximo")
        COLUMN_ORDER = pd.Series(dtype="int64", name="ordem")

        ALL: List[str] = [
            str(COLUMN_CODE.name),
            str(COLUMN_LABEL.name),
            str(COLUMN_COLOR.name),
            str(COLUMN_MINIMUM.name),
            str(COLUMN_MAXIMUM.name),
            str(COLUMN_ORDER.name),
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: LoadedSheet,
        **kwargs: object,
    ) -> None:
        """
        Initialize the SpLegend model.

        Args:
            context (GeneralContext): The application general context.
            data_model (LoadedSheet): The loaded data model containing the dataframe.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(context, data_model, **kwargs)

        # SETUP NAMES COLUMN
        self.column_name_code = str(self.RequiredColumn.COLUMN_CODE.name)
        self.column_name_label = str(self.RequiredColumn.COLUMN_LABEL.name)
        self.column_name_color = str(self.RequiredColumn.COLUMN_COLOR.name)
        self.column_name_minimum = str(self.RequiredColumn.COLUMN_MINIMUM.name)
        self.column_name_maximum = str(self.RequiredColumn.COLUMN_MAXIMUM.name)
        self.column_name_order = str(self.RequiredColumn.COLUMN_ORDER.name)

    def pre_processing(self) -> None:
        """Run pre-processing steps (currently empty)."""

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
        """
        Perform data cleaning operations.

        Specific rules:
        1. Clean and validate the 'legenda' column ensuring it contains positive integers (minimum 1).
        2. Perform specific legend validations (LEG-001…011, `LegendProcessing`); the
           cross-sheet relation/range checks (LEG-012…015) run in `rules/legend.py` instead.
        """
        errors: List[str] = []
        dataframe = self.data_loader_model.raw_data
        translate = self.context.language_manager.text

        legend_validator = LegendProcessing(
            value_data_unavailable=self.context.config.LABEL_DATA_UNAVAILABLE, filename=self.filename
        )

        errors.extend(legend_validator.validate_code_sequence(dataframe, self.column_name_code, translate=translate))

        # Group by legend code_value and perform group-wise validations
        for code_value, group in dataframe.groupby(self.column_name_code):
            errors_dtypes = []
            errors_dtypes.extend(
                legend_validator.validate_legend_columns_dtypes_numeric(
                    group,
                    code_value,
                    self.column_name_code,
                    self.column_name_label,
                    self.column_name_minimum,
                    self.column_name_maximum,
                    self.column_name_order,
                    translate=translate,
                )
            )
            errors.extend(errors_dtypes)

            if not errors_dtypes:
                errors.extend(
                    legend_validator.validate_legend_labels(
                        group, code_value, self.column_name_label, translate=translate
                    )
                )
                errors.extend(
                    legend_validator.validate_color_format(
                        group, code_value, self.column_name_color, translate=translate
                    )
                )
                errors.extend(
                    legend_validator.validate_min_max_has_excessive_decimals(
                        group,
                        code_value,
                        self.column_name_minimum,
                        self.column_name_maximum,
                        self.column_name_label,
                        translate=translate,
                    )
                )
                errors.extend(
                    legend_validator.validate_min_max_values(
                        group,
                        code_value,
                        self.column_name_minimum,
                        self.column_name_maximum,
                        self.column_name_label,
                        translate=translate,
                    )
                )
                errors.extend(
                    legend_validator.validate_order_sequence(
                        group, code_value, self.column_name_order, translate=translate
                    )
                )

        self.data_cleaning_errors.extend(errors)

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
        if self.is_sanity_check_passed:
            self.data_cleaning()
