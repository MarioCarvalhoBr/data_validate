#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
"""
Module representing the Legend spreadsheet model.

This module defines the `SpLegend` class, which handles the loading,
validation, and processing of legend data (e.g., labels, min/max values, colors).
"""

from typing import List, Dict, Any

import pandas as pd

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.message_formatting_processing import MessageFormattingProcessing
from data_validate.helpers.common.validation.dataframe_processing import DataFrameProcessing
from data_validate.helpers.common.validation.legend_processing import LegendProcessing
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpLegend(SpModelABC):
    """
    Model for the Legend spreadsheet.

    Manages specific validations for legend data, handling dynamic grouping
    of legends based on codes and validating min/max ranges, colors, and labels.

    Attributes:
        CONSTANTS (INFO): Immutable constants specific to this model.
    """

    # CONSTANTS
    class INFO(ConstantBase):
        """
        Immutable constants for the Legend model.

        Attributes:
            SP_NAME (str): Internal name of the spreadsheet/dataset ('legenda').
            SP_DESCRIPTION (str): Description of the dataset.
        """

        def __init__(self):
            """Initialize the INFO constants."""
            super().__init__()
            self.SP_NAME = "legenda"
            self.SP_DESCRIPTION = "Planilha de legendas"
            # Others constants
            self.MIN_LOWER_LEGEND_DEFAULT = 0
            self.MAX_UPPER_LEGEND_DEFAULT = 1
            self._finalize_initialization()

    CONSTANTS = INFO()

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

        ALL = [
            COLUMN_CODE.name,
            COLUMN_LABEL.name,
            COLUMN_COLOR.name,
            COLUMN_MINIMUM.name,
            COLUMN_MAXIMUM.name,
            COLUMN_ORDER.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        """
        Initialize the SpLegend model.

        Args:
            context (GeneralContext): The application general context.
            data_model (DataLoaderModel): The loaded data model containing the dataframe.
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

        self.run()

    def pre_processing(self):
        """Run pre-processing steps (currently empty)."""
        if not self.data_loader_model.exists_file or self.data_loader_model.df_data.empty:
            return

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
        1. Clean and validate the 'legenda' column ensuring it contains positive integers (minimum 1).
        2. Perform specific legend validations (handled in SpLegendValidator now).

        Returns:
            List[str]: List of data cleaning errors (unused return in this implementation).
        """
        errors = []
        dataframe = self.data_loader_model.df_data
        if dataframe.empty:
            return errors

        # If there are structural errors, do not proceed with data cleaning
        if self.structural_errors:
            return errors

        legend_validator = LegendProcessing(value_data_unavailable=self.context.config.LABEL_DATA_UNAVAILABLE, filename=self.filename)

        errors.extend(legend_validator.validate_code_sequence(dataframe, self.column_name_code))

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
                )
            )
            errors.extend(errors_dtypes)

            if not errors_dtypes:
                errors.extend(legend_validator.validate_legend_labels(group, code_value, self.column_name_label))
                errors.extend(legend_validator.validate_color_format(group, code_value, self.column_name_color))
                errors.extend(
                    legend_validator.validate_min_max_has_excessive_decimals(
                        group,
                        code_value,
                        self.column_name_minimum,
                        self.column_name_maximum,
                        self.column_name_label,
                    )
                )
                errors.extend(
                    legend_validator.validate_min_max_values(
                        group,
                        code_value,
                        self.column_name_minimum,
                        self.column_name_maximum,
                        self.column_name_label,
                    )
                )
                errors.extend(legend_validator.validate_order_sequence(group, code_value, self.column_name_order))

        self.data_cleaning_errors.extend(errors)

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
