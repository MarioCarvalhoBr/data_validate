#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Dict, Any
from types import MappingProxyType

from .sp_scenario import SpScenario
from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.data_cleaning import clean_dataframe

class SpDescription(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "descricao",
        "SP_DESCRIPTION": "Esta planilha deve conter informações necessárias para a identificar os índices e indicadores do SE.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_CODE": "codigo",
        "COLUMN_LEVEL": "nivel",
        "COLUMN_SIMPLE_NAME": "nome_simples",
        "COLUMN_COMPLETE_NAME": "nome_completo",
        "COLUMN_SIMPLE_DESC": "desc_simples",
        "COLUMN_COMPLETE_DESC": "desc_completa",
        "COLUMN_SOURCES": "fontes",
        "COLUMN_META": "meta",
    })

    REQUIRED_DYNAMIC_COLUMNS = MappingProxyType({
        "COLUMN_SCENARIO": "cenario",
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

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)
        self.color = "blue"
        self.run()

    def pre_processing(self):
        self.color = "yellow"
        expected_columns = list(self.REQUIRED_COLUMNS.values())
        # 1. Tratamento de colunas dinâmicas: cenarios
        if not self.LIST_SCENARIOS:
            ## 1.1: Se não houver cenários, remove a coluna de cenário
            if self.REQUIRED_DYNAMIC_COLUMNS["COLUMN_SCENARIO"] in self.DATA_MODEL.df_data.columns:
                self.STRUCTURE_LIST_ERRORS.append(
                    f"{self.FILENAME}: A coluna '{self.REQUIRED_DYNAMIC_COLUMNS['COLUMN_SCENARIO']}' não pode existir se o arquivo '{SpScenario.INFO['SP_NAME']}' não estiver configurado ou não existir.")
                self.DATA_MODEL.df_data = self.DATA_MODEL.df_data.drop(
                    columns=[self.REQUIRED_DYNAMIC_COLUMNS["COLUMN_SCENARIO"]])
        else:
            # 1.2: Se houver cenários, adiciona a coluna de cenário
            expected_columns.append(self.REQUIRED_DYNAMIC_COLUMNS["COLUMN_SCENARIO"])

        # 2. Tratamento de colunas opicionais
        # 2.1: Adiciona colunas opcionais: relação
        if self.OPTIONAL_COLUMNS["COLUMN_RELATION"] not in self.DATA_MODEL.df_data.columns:
            self.DATA_MODEL.df_data[self.OPTIONAL_COLUMNS["COLUMN_RELATION"]] = 1
        # 2.2: Adiciona colunas opcionais: unidade
        if self.OPTIONAL_COLUMNS["COLUMN_UNIT"] not in self.DATA_MODEL.df_data.columns:
            self.DATA_MODEL.df_data[self.OPTIONAL_COLUMNS["COLUMN_UNIT"]] = ""

        for opt_column_name in self.OPTIONAL_COLUMNS.values():
            if (opt_column_name in self.DATA_MODEL.df_data.columns) and (opt_column_name not in expected_columns):
                expected_columns.append(opt_column_name)

        self.EXPECTED_COLUMNS = expected_columns

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:

        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL.df_data, self.EXPECTED_COLUMNS)
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # Limpeza e validação das colunas principais usando clean_dataframe
        # 1. Limpar e validar a coluna 'codigo' (mínimo 1)
        col_codigo = self.REQUIRED_COLUMNS["COLUMN_CODE"]
        df, errors_codigo = clean_dataframe(self.DATA_MODEL.df_data, self.FILENAME, [col_codigo], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_codigo)

        # 2. Limpar e validar a coluna 'nivel' (mínimo 1)
        col_nivel = self.REQUIRED_COLUMNS["COLUMN_LEVEL"]
        df, errors_nivel = clean_dataframe(self.DATA_MODEL.df_data, self.FILENAME, [col_nivel], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_nivel)

        # 3. Se houver cenários, limpar e validar a coluna 'cenario' (mínimo -1)
        col_cenario = self.REQUIRED_DYNAMIC_COLUMNS["COLUMN_SCENARIO"]
        df, errors_cenario = clean_dataframe(self.DATA_MODEL.df_data, self.FILENAME, [col_cenario], min_value=-1)
        self.DATA_CLEAN_ERRORS.extend(errors_cenario)

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()
        self.data_cleaning()


if __name__ == '__main__':
    # Test the SpDescription class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_description = SpDescription(data_model=data[SpDescription.INFO["SP_NAME"]])
    print(sp_description)