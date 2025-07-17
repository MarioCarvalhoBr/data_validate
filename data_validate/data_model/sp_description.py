#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Dict, Any
import pandas as pd

from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.data_cleaning import clean_dataframe

class SpDescription(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "descricao"
            self.SP_DESCRIPTION = "Planilha de descricao"
            self.MAX_TITLE_LENGTH = 40
            self.MAX_SIMPLE_DESC_LENGTH = 150
            self.SP_SCENARIO_NAME = "cenarios"
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_CODE = pd.Series(dtype="int64", name="codigo")
        COLUMN_LEVEL = pd.Series(dtype="int64", name="nivel")
        COLUMN_SIMPLE_NAME = pd.Series(dtype="str", name="nome_simples")
        COLUMN_COMPLETE_NAME = pd.Series(dtype="str", name="nome_completo")
        COLUMN_SIMPLE_DESC = pd.Series(dtype="str", name="desc_simples")
        COLUMN_COMPLETE_DESC = pd.Series(dtype="str", name="desc_completa")
        COLUMN_SOURCES = pd.Series(dtype="str", name="fontes")
        COLUMN_META = pd.Series(dtype="str", name="meta")

        ALL = [
            COLUMN_CODE.name,
            COLUMN_LEVEL.name,
            COLUMN_SIMPLE_NAME.name,
            COLUMN_COMPLETE_NAME.name,
            COLUMN_SIMPLE_DESC.name,
            COLUMN_COMPLETE_DESC.name,
            COLUMN_SOURCES.name,
            COLUMN_META.name,
        ]

    class DynamicColumn:
        COLUMN_SCENARIO = pd.Series(dtype="int64", name="cenario")

        ALL = [
            COLUMN_SCENARIO.name,
        ]

    class OptionalColumn:
        COLUMN_UNIT = pd.Series(dtype="str", name="unidade")
        COLUMN_RELATION = pd.Series(dtype="int64", name="relacao")
        COLUMN_ORDER = pd.Series(dtype="int64", name="ordem")

        ALL = [
            COLUMN_UNIT.name,
            COLUMN_RELATION.name,
            COLUMN_ORDER.name,
        ]

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)
        self.color = "blue"
        self.run()

    def pre_processing(self):
        self.color = "yellow"
        expected_columns = list(self.RequiredColumn.ALL)
        # 1. Tratamento de colunas dinâmicas: cenarios
        if not self.LIST_SCENARIOS:
            ## 1.1: Se não houver cenários, remove a coluna de cenário
            if self.DynamicColumn.COLUMN_SCENARIO.name in self.DATA_MODEL_IMPORTER.df_data.columns:
                self.STRUCTURE_LIST_ERRORS.append(
                    f"{self.FILENAME}: A coluna '{self.DynamicColumn.COLUMN_SCENARIO.name}' não pode existir se o arquivo '{self.CONSTANTS.SP_SCENARIO_NAME}' não estiver configurado ou não existir.")
                self.DATA_MODEL_IMPORTER.df_data = self.DATA_MODEL_IMPORTER.df_data.drop(
                    columns=[self.DynamicColumn.COLUMN_SCENARIO.name])
        else:
            # 1.2: Se houver cenários, adiciona a coluna de cenário
            expected_columns.append(self.DynamicColumn.COLUMN_SCENARIO.name)

        # 2. Tratamento de colunas opcionais
        # 2.1: Adiciona colunas opcionais: relação
        if self.OptionalColumn.COLUMN_RELATION.name not in self.DATA_MODEL_IMPORTER.df_data.columns:
            self.DATA_MODEL_IMPORTER.df_data[self.OptionalColumn.COLUMN_RELATION.name] = 1
        # 2.2: Adiciona colunas opcionais: unidade
        if self.OptionalColumn.COLUMN_UNIT.name not in self.DATA_MODEL_IMPORTER.df_data.columns:
            self.DATA_MODEL_IMPORTER.df_data[self.OptionalColumn.COLUMN_UNIT.name] = ""

        for opt_column_name in self.OptionalColumn.ALL:
            if (opt_column_name in self.DATA_MODEL_IMPORTER.df_data.columns) and (opt_column_name not in expected_columns):
                expected_columns.append(opt_column_name)

        self.EXPECTED_COLUMNS = expected_columns

    def expected_structure_columns(self, *args, **kwargs) -> None:

        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.DATA_MODEL_IMPORTER.df_data, self.EXPECTED_COLUMNS)
        col_errors, col_warnings = format_errors_and_warnings(self.FILENAME, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # Limpeza e validação das colunas principais usando clean_dataframe
        # 1. Limpar e validar a coluna 'codigo' (mínimo 1)
        df, errors_codigo = clean_dataframe(self.DATA_MODEL_IMPORTER.df_data, self.FILENAME, [self.RequiredColumn.COLUMN_CODE.name], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_codigo)
        if self.RequiredColumn.COLUMN_CODE.name in df.columns:
            self.RequiredColumn.COLUMN_CODE = df[self.RequiredColumn.COLUMN_CODE.name]

        # 2. Limpar e validar a coluna 'nivel' (mínimo 1)
        col_nivel = self.RequiredColumn.COLUMN_LEVEL.name
        df, errors_nivel = clean_dataframe(self.DATA_MODEL_IMPORTER.df_data, self.FILENAME, [col_nivel], min_value=1)
        self.DATA_CLEAN_ERRORS.extend(errors_nivel)
        if col_nivel in df.columns:
            self.RequiredColumn.COLUMN_LEVEL = df[col_nivel]

        # 3. Se houver cenários, limpar e validar a coluna 'cenario' (mínimo -1)
        if self.LIST_SCENARIOS:
            col_cenario = self.DynamicColumn.COLUMN_SCENARIO.name
            df, errors_cenario = clean_dataframe(self.DATA_MODEL_IMPORTER.df_data, self.FILENAME, [col_cenario], min_value=-1)
            if col_cenario in df.columns:
                self.DynamicColumn.COLUMN_SCENARIO = df[col_cenario]
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