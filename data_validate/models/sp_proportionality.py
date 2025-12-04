#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Dict, Any

import pandas as pd

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.processing.collections_processing import (
    extract_numeric_ids_and_unmatched_strings_from_list,
    categorize_strings_by_id_pattern_from_list,
)  # Added
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpProportionality(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "proporcionalidades"
            self.SP_DESCRIPTION = "Planilha de proporcionalidades"
            self._finalize_initialization()

    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_ID = pd.Series(dtype="int64", name="id")

        ALL = [
            COLUMN_ID.name,
        ]

    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ):
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        self.EXPECTED_COLUMNS = list(self.RequiredColumn.ALL)

        colunas_nivel_1 = self.data_loader_model.df_data.columns.get_level_values(0).unique().tolist()
        colunas_nivel_1 = [col for col in colunas_nivel_1 if not col.lower().startswith("unnamed: 0_level_0")]

        __, level_1_codes_not_matched_by_pattern = categorize_strings_by_id_pattern_from_list(colunas_nivel_1, self.scenarios_list)

        if level_1_codes_not_matched_by_pattern:
            self.structural_errors.append(
                f"{self.filename}, linha 1: Colunas de nível 1 fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): {level_1_codes_not_matched_by_pattern}"
            )
        else:
            colunas_nivel_2 = self.data_loader_model.df_data.columns.get_level_values(1).unique().tolist()
            colunas_nivel_2 = [col for col in colunas_nivel_2 if col != self.RequiredColumn.COLUMN_ID.name]

            __, level_2_codes_not_matched_by_pattern = categorize_strings_by_id_pattern_from_list(colunas_nivel_2, self.scenarios_list)

            if level_2_codes_not_matched_by_pattern and not level_1_codes_not_matched_by_pattern:
                self.structural_errors.append(
                    f"{self.filename}, linha 2: Colunas de nível 2 fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): {level_2_codes_not_matched_by_pattern}"
                )

        if self.structural_errors:
            self.data_loader_model.df_data = pd.DataFrame()  # Limpa o DataFrame para evitar processamento adicional
            self.data_loader_model.header_type = "invalid"

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        if not self.data_loader_model.df_data.empty and self.data_loader_model.header_type == "double":
            colunas_unicas_nivel_1 = self.data_loader_model.df_data.columns.get_level_values(0).unique().tolist()
            colunas_unicas_nivel_2 = self.data_loader_model.df_data.columns.get_level_values(1).unique().tolist()

            # Check extra columns in level 1 (do not ignore 'id')
            _, extras_level_1 = extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=colunas_unicas_nivel_1,
                strings_to_ignore=[],  # Do not ignore 'id' here
                suffixes_for_matching=self.scenarios_list,
            )
            for extra_column in extras_level_1:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(f"{self.filename}: A coluna de nível 1 '{extra_column}' não é esperada.")

            # Check extra columns in level 2 (ignore 'id')
            _, extras_level_2 = extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=colunas_unicas_nivel_2,
                strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
                suffixes_for_matching=self.scenarios_list,
            )
            for extra_column in extras_level_2:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(f"{self.filename}: A coluna de nível 2 '{extra_column}' não é esperada.")

            # Check for missing expected columns in level 2
            for col in self.EXPECTED_COLUMNS:
                if col not in colunas_unicas_nivel_2:
                    self.structural_errors.append(f"{self.filename}: Coluna de nível 2 '{col}' esperada mas não foi encontrada.")

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def post_processing(self):
        pass

    def run(self):
        # Verificar se precisa do read_success também
        if self.data_loader_model.exists_file and self.data_loader_model.header_type == "double":
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
