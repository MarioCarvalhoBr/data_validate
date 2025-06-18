from pathlib import Path
from types import MappingProxyType
from typing import List, Dict, Any

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.data_cleaning import clean_dataframe

class SpComposition(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "composicao",
        "SP_DESCRIPTION": "This spreadsheet must contain information about parent-child relationships in the composition.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_PARENT_CODE": "codigo_pai",
        "COLUMN_CHILD_CODE": "codigo_filho",
    })

    OPTIONAL_COLUMNS = MappingProxyType({})

    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL.df_data,
                                                            list(self.REQUIRED_COLUMNS.values()))
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # 1. Limpar e validar a coluna 'codigo' (mínimo 1)
        col_parent = self.REQUIRED_COLUMNS["COLUMN_PARENT_CODE"]
        df, errors_parent = clean_dataframe(self.DATA_MODEL.df_data, self.FILENAME, [col_parent], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_parent)

        # 2. Limpar e validar a coluna 'codigo_filho' (mínimo 1)
        col_child = self.REQUIRED_COLUMNS["COLUMN_CHILD_CODE"]
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