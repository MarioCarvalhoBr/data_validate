from typing import List, Dict, Any
import pandas as pd

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.models.sp_model_abc import SpModelABC
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.helpers.common.validation.column_validation import check_column_names
from data_validate.helpers.common.formatting.error_formatting import (
    format_errors_and_warnings,
)
from data_validate.helpers.common.processing.data_cleaning import (
    clean_dataframe_integers,
)


class SpComposition(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "composicao"
            self.SP_DESCRIPTION = "Planilha de composicao"
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_PARENT_CODE = pd.Series(dtype="int64", name="codigo_pai")
        COLUMN_CHILD_CODE = pd.Series(dtype="int64", name="codigo_filho")

        ALL = [
            COLUMN_PARENT_CODE.name,
            COLUMN_CHILD_CODE.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # 1. Create mapping of column names to their corresponding class attributes 'codigo_pai' (mínimo 1) e 'codigo_filho' (mínimo 1)
        column_attribute_mapping = {
            self.RequiredColumn.COLUMN_PARENT_CODE.name: "COLUMN_PARENT_CODE",
            self.RequiredColumn.COLUMN_CHILD_CODE.name: "COLUMN_CHILD_CODE",
        }

        # Clean and validate required columns (minimum value: 1)
        for column_name in column_attribute_mapping.keys():
            df, errors = clean_dataframe_integers(
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

    def post_processing(self):
        pass

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
