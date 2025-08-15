import re
from typing import List, Dict, Any
import pandas as pd

from common.utils.processing.data_cleaning import clean_dataframe_integers, clean_dataframe_floats
from common.utils.validation.legend_processing import LegendProcessing
from controller.context.general_context import GeneralContext
from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings

class SpLegend(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "legenda"
            self.SP_DESCRIPTION = "Planilha de legendas"
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

    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
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

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        """
        Performs data cleaning and validation on the legend data.
        """
        errors = []
        dataframe = self.data_loader_model.df_data
        if dataframe.empty:
            return errors

        legend_validator = LegendProcessing(self.context, self.filename)

        # Group by legend code_value and perform group-wise validations
        exists_errors_dtypes = False
        for code_value, group in dataframe.groupby(self.column_name_code):

            errors_dtypes = []
            errors_dtypes.extend(legend_validator.validate_legend_columns_dtypes_numeric(group, code_value, self.column_name_code, self.column_name_label, self.column_name_minimum, self.column_name_maximum, self.column_name_order))
            errors.extend(errors_dtypes)

            if errors_dtypes:
                exists_errors_dtypes = True

            if not errors_dtypes:
                errors.extend(legend_validator.validate_legend_labels(group, code_value, self.column_name_label))
                errors.extend(legend_validator.validate_color_format(group, code_value, self.column_name_color))
                errors.extend(legend_validator.validate_min_max_values(group, code_value, self.column_name_minimum, self.column_name_maximum, self.column_name_label))
                errors.extend(legend_validator.validate_order_sequence(group, code_value, self.column_name_order))

        if not exists_errors_dtypes:
            errors.extend(legend_validator.validate_code_sequence(dataframe, self.column_name_code))

        self.DATA_CLEAN_ERRORS.extend(errors)

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()