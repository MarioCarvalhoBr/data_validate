#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from pathlib import Path
from types import MappingProxyType
from typing import List

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade


class SpDescription(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "descricao",
        "SP_DESCRIPTION": "Esta planilha deve conter informações necessárias para a identificar os índices e indicadores do SE.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_CODE": "codigo",
        "COLUMN_NAME": "nome",
        "COLUMN_LEVEL": "nivel",
        "COLUMN_SIMPLE_NAME": "nome_simples",
        "COLUMN_COMPLETE_NAME": "nome_completo",
        "COLUMN_SIMPLE_DESC": "desc_simples",
        "COLUMN_COMPLETE_DESC": "desc_completa",
        "COLUMN_SCENARIO": "cenario",
        "COLUMN_SOURCES": "fontes",
        "COLUMN_META": "meta",
    })

    OPTIONAL_COLUMNS = MappingProxyType({
        "COLUMN_UNIT": "unidade",
        "COLUMN_RELATION": "relacao",
        "COLUMN_ORDER": "ordem",
    })

    COLUMNS_PLURAL = MappingProxyType({
        "COLUMN_SIMPLE_NAMES": "nomes_simples",
        "COLUMN_COMPLETE_NAMES": "nomes_completos",
    })

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
    # Test the SpDescription class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_description = SpDescription(data_model=data[SpDescription.INFO["SP_NAME"]])
    print(sp_description)