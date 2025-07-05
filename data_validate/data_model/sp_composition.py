from typing import List, Dict, Any
import pandas as pd

from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
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

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # 1. Limpar e validar a coluna 'codigo_pai' (mínimo 1)
        col_parent = self.RequiredColumn.COLUMN_PARENT_CODE.name
        df, errors_parent = clean_dataframe(self.DATA_MODEL.df_data, self.FILENAME, [col_parent], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_parent)

        # 2. Limpar e validar a coluna 'codigo_filho' (mínimo 1)
        col_child = self.RequiredColumn.COLUMN_CHILD_CODE.name
        df, errors_child = clean_dataframe(self.DATA_MODEL.df_data, self.FILENAME, [col_child], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_child)

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()
        self.data_cleaning()


if __name__ == '__main__':
    # Test the SpComposition class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_composition = SpComposition(data_model=data[SpComposition.INFO["SP_NAME"]])
    print(sp_composition)