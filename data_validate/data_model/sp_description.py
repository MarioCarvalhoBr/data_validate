#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Dict, Any
import pandas as pd

from controller.context.general_context import GeneralContext
from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.data_cleaning import clean_dataframe_integers

class SpDescription(SpModelABC):

    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "descricao"
            self.SP_DESCRIPTION = "Planilha de descricao"
            self.MAX_TITLE_LENGTH = 40
            self.MAX_SIMPLE_DESC_LENGTH = 150
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
        COLUMN_LEGEND = pd.Series(dtype="str", name="legenda")
        ALL = [
            COLUMN_SCENARIO.name,
            COLUMN_LEGEND.name
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

    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
        super().__init__(context, data_model, **kwargs)
        self.run()

    def pre_processing(self):
        local_expected_columns = list(self.RequiredColumn.ALL)

        # 1. Tratamento de colunas dinâmicas: cenarios
        if not self.list_scenarios:
            ## 1.1: Se não houver cenários, remove a coluna de cenário se existir no dataframe
            if self.DynamicColumn.COLUMN_SCENARIO.name in self.data_loader_model.df_data.columns:
                self.STRUCTURE_LIST_ERRORS.append(
                    f"{self.filename}: A coluna '{self.DynamicColumn.COLUMN_SCENARIO.name}' não pode existir se o arquivo '{self.VAR_CONSTS.SP_NAMAE_SCENARIO}' não estiver configurado ou não existir.")
                self.data_loader_model.df_data = self.data_loader_model.df_data.drop(
                    columns=[self.DynamicColumn.COLUMN_SCENARIO.name])
        else:
            # 1.2: Se houver cenários, adiciona a coluna de cenário
            local_expected_columns.append(self.DynamicColumn.COLUMN_SCENARIO.name)

        # 1. Tratamento de colunas dinâmicas: legenda
        if not self.exists_legend:
            if self.DynamicColumn.COLUMN_LEGEND.name in self.data_loader_model.df_data.columns:
                self.STRUCTURE_LIST_ERRORS.append(
                    f"{self.filename}: A coluna '{self.DynamicColumn.COLUMN_LEGEND.name}' não pode existir se o arquivo de legenda não estiver configurado ou não existir.")
                self.data_loader_model.df_data = self.data_loader_model.df_data.drop(columns=[self.DynamicColumn.COLUMN_LEGEND.name])
        else:
            local_expected_columns.append(self.DynamicColumn.COLUMN_LEGEND.name)

        # 2. Tratamento de colunas opcionais
        if self.OptionalColumn.COLUMN_RELATION.name not in self.data_loader_model.df_data.columns:
            self.data_loader_model.df_data[self.OptionalColumn.COLUMN_RELATION.name] = 1
        if self.OptionalColumn.COLUMN_UNIT.name not in self.data_loader_model.df_data.columns:
            self.data_loader_model.df_data[self.OptionalColumn.COLUMN_UNIT.name] = ""

        for opt_column_name in self.OptionalColumn.ALL:
            if (opt_column_name in self.data_loader_model.df_data.columns) and (opt_column_name not in local_expected_columns):
                local_expected_columns.append(opt_column_name)
        self.EXPECTED_COLUMNS = local_expected_columns

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, self.EXPECTED_COLUMNS)
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.STRUCTURE_LIST_ERRORS.extend(col_errors)
        self.STRUCTURE_LIST_WARNINGS.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # 1. Create mapping of column names to their corresponding class attributes codigo (mínimo 1) e nivel (mínimo 1)
        column_attribute_mapping = {
            self.RequiredColumn.COLUMN_CODE.name: "COLUMN_CODE",
            self.RequiredColumn.COLUMN_LEVEL.name: "COLUMN_LEVEL"
        }

        # Clean and validate required columns (minimum value: 1)
        for column_name in column_attribute_mapping.keys():
            df, errors = clean_dataframe_integers(self.data_loader_model.df_data, self.filename, [column_name], min_value=1)
            self.DATA_CLEAN_ERRORS.extend(errors)

            if column_name in df.columns:
                # Use setattr to dynamically set the attribute
                attribute_name = column_attribute_mapping[column_name]
                setattr(self.RequiredColumn, attribute_name, df[column_name])

        # 2. Se houver cenários, limpar e validar a coluna 'cenario' (mínimo -1)
        if self.list_scenarios:
            col_cenario = self.DynamicColumn.COLUMN_SCENARIO.name
            df, errors_cenario = clean_dataframe_integers(self.data_loader_model.df_data, self.filename, [col_cenario], min_value=-1)
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
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    sp_description = SpDescription(data_model=data[SpDescription.INFO["SP_NAME"]])
    print(sp_description)