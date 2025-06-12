from pathlib import Path
from types import MappingProxyType
from typing import List, Dict, Any

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings

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
        super().__init__(data_model)

        # Vars
        self.structure_errors = []
        self.structure_warnings = []

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL.df_data,
                                                            list(self.REQUIRED_COLUMNS.values()))
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.structure_errors.extend(col_errors)
        self.structure_warnings.extend(col_warnings)

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()


if __name__ == '__main__':
    # Test the SpComposition class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_composition = SpComposition(data_model=data[SpComposition.INFO["SP_NAME"]])
    print(sp_composition)