from typing import List, Dict, Any
import pandas as pd

from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.data_cleaning import clean_dataframe

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

    def __init__(self, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # 1. Limpar e validar as coluna 'codigo_pai' (mínimo 1) e 'codigo_filho' (mínimo 1)

        col_names = [self.RequiredColumn.COLUMN_PARENT_CODE.name, self.RequiredColumn.COLUMN_CHILD_CODE.name]
        for col_name in col_names:
            col_name = str(col_name)
            df, errors = clean_dataframe(self.data_loader_model.df_data, self.filename, [col_name], min_value=1)
            self.DATA_CLEAN_ERRORS.extend(errors)
            if col_name in df.columns:
                setattr(self.RequiredColumn, col_name, df[col_name])

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()
        self.data_cleaning()


if __name__ == '__main__':
    # Test the SpComposition class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    sp_composition = SpComposition(data_model=data[SpComposition.INFO["SP_NAME"]])
    print(sp_composition)