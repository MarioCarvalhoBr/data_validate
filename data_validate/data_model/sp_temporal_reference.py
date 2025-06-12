from pathlib import Path
from types import MappingProxyType
from typing import List, Dict, Any

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings


class SpTemporalReference(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "referencia_temporal",
        "SP_DESCRIPTION": "This spreadsheet must contain information about temporal references, including their names, descriptions, and symbols.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_NAME": "nome",
        "COLUMN_DESCRIPTION": "descricao",
        "COLUMN_SYMBOL": "simbolo",
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

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL.df_data, list(self.REQUIRED_COLUMNS.values()))
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.structure_errors.extend(col_errors)
        self.structure_warnings.extend(col_warnings)

    def run(self):
        self.expected_structure_columns()

if __name__ == '__main__':
    # Test the SpTemporalReference class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_temporal_reference = SpTemporalReference(data_model=data[SpTemporalReference.INFO["SP_NAME"]])
    print(sp_temporal_reference)