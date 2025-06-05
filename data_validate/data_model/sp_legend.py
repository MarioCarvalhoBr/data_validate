from pathlib import Path
from types import MappingProxyType
from typing import List

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade


class SpLegend(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "legendas",
        "SP_DESCRIPTION": "Esta planilha deve conter informações sobre as legendas, incluindo seus códigos, rótulos, cores, valores mínimos e máximos, e ordem de exibição.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_CODE": "codigo",
        "COLUMN_LABEL": "label",
        "COLUMN_COLOR": "cor",
        "COLUMN_MINIMUM": "minimo",
        "COLUMN_MAXIMUM": "maximo",
        "COLUMN_ORDER": "ordem",
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
    # Test the SpLegends class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    # Assuming 'legendas' is a valid key in the data loaded by the importer
    # You might need to adjust this part if the SpTemporalReference was a placeholder name
    if SpLegend.INFO["SP_NAME"] in data:
        sp_legends_instance = SpLegend(data_model=data[SpLegend.INFO["SP_NAME"]])
        print(sp_legends_instance)
    else:
        print(f"Data for '{SpLegend.INFO['SP_NAME']}' not found. Please check your input data.")
