from types import MappingProxyType
from typing import List, Dict, Any
import pandas as pd

from common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings

class SpScenario(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "cenarios"
            self.SP_DESCRIPTION = "Planilha de cenarios"

            self._finalize_initialization()
    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:

        COLUMN_NAME = pd.Series(dtype="int64", name='nome')
        COLUMN_DESCRIPTION = pd.Series(dtype="str", name='descricao')
        COLUMN_SYMBOL = pd.Series(dtype="int64", name='simbolo')

        ALL = [
            COLUMN_NAME.name,
            COLUMN_DESCRIPTION.name,
            COLUMN_SYMBOL.name
        ]

    OPTIONAL_COLUMNS = MappingProxyType({})

    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model)

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL.df_data,
                                                            list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def run(self):
        self.expected_structure_columns()


if __name__ == '__main__':
    # Test the SpScenario class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_scenario = SpScenario(data_model=data[SpScenario.INFO["SP_NAME"]])
    print(sp_scenario)