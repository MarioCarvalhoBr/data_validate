from typing import Dict, Any

import pandas as pd

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.formatting.error_formatting import (
    format_errors_and_warnings,
)
from data_validate.helpers.common.validation.column_validation import check_column_names
from data_validate.helpers.common.validation.legend_processing import LegendProcessing
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpLegend(SpModelABC):

    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
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
        if not self.data_loader_model.exists_file or self.data_loader_model.df_data.empty:
            return

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs):
        """
        Performs data cleaning and validation on the legend data.
        """
        errors = []
        dataframe = self.data_loader_model.df_data
        if dataframe.empty:
            return errors

        # Se tiver errors de estrutura, não prosseguir com a limpeza de dados
        if self.structural_errors:
            return errors

        legend_validator = LegendProcessing(self.context, self.filename)

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
        pass

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
