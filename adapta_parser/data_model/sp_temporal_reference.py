from pathlib import Path
from types import MappingProxyType
from typing import List

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade


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
    # Test the SpTemporalReference class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/adapta_parser/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_temporal_reference = SpTemporalReference(data_model=data[SpTemporalReference.INFO["SP_NAME"]])
    print(sp_temporal_reference)