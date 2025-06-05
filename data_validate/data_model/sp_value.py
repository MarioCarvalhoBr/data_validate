from pathlib import Path
from types import MappingProxyType
from typing import List

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade


class SpValue(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "valores",
        "SP_DESCRIPTION": "This spreadsheet must contain information about the values associated with specific IDs.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_ID": "id",
    })

    OPTIONAL_COLUMNS = MappingProxyType({})

    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(self, data_model: DataModelImporter):
        super().__init__(data_model)

        # Vars
        structure_errors = []
        structure_warnings = []

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self) -> List[str]:
        pass

    def run(self):
        pass


if __name__ == '__main__':
    # Test the SpValues class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_values = SpValue(data_model=data[SpValue.INFO["SP_NAME"]])
    print(sp_values)