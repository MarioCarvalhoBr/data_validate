import re
from typing import List, Dict, Any
import pandas as pd

from controller.context.general_context import GeneralContext
from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.validation import legend_data_validation as legend_validator

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
        df = self.data_loader_model.df_data
        if df.empty:
            return

        errors = []

        # Validate code sequence
        errors.extend(legend_validator.validate_code_sequence(df, self.RequiredColumn.COLUMN_CODE.name, self.filename))

        # Group by legend code and perform group-wise validations
        for code, group in df.groupby(self.RequiredColumn.COLUMN_CODE.name):
            errors.extend(legend_validator.validate_legend_labels(group, code, self.filename, self.RequiredColumn.COLUMN_LABEL.name))
            errors.extend(legend_validator.validate_color_format(group, code, self.filename, self.RequiredColumn.COLUMN_COLOR.name))
            errors.extend(legend_validator.validate_min_max_values(group, code, self.filename, self.RequiredColumn.COLUMN_MINIMUM.name, self.RequiredColumn.COLUMN_MAXIMUM.name, self.RequiredColumn.COLUMN_LABEL.name))
            errors.extend(legend_validator.validate_order_sequence(group, code, self.filename, self.RequiredColumn.COLUMN_ORDER.name))

        self.DATA_CLEAN_ERRORS.extend(errors)

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()


if __name__ == '__main__':
    # Test the SpLegends class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    # Assuming 'legendas' is a valid key in the data loaded by the importer
    # You might need to adjust this part if the SpTemporalReference was a placeholder name
    if SpLegend.INFO["SP_NAME"] in data:
        sp_legends_instance = SpLegend(data_model=data[SpLegend.INFO["SP_NAME"]])
        print(sp_legends_instance)
    else:
        print(f"Data for '{SpLegend.INFO['SP_NAME']}' not found. Please check your input data.")
