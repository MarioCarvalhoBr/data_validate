#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from typing import List, Dict, Any

import pandas as pd

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.processing.collections_processing import (
    extract_numeric_ids_and_unmatched_strings_from_list,
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

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        if self.data_loader_model.header_type == "double":
            colunas_nivel_1 = self.data_loader_model.df_data.columns.get_level_values(0).unique().tolist()
            colunas_nivel_2 = self.data_loader_model.df_data.columns.get_level_values(1).unique().tolist()

            # Check extra columns in level 1 (do not ignore 'id')
            _, extras_level_1 = extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=colunas_nivel_1,
                strings_to_ignore=[],  # Do not ignore 'id' here
                suffixes_for_matching=self.scenarios_list,
            )
            for extra_column in extras_level_1:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(f"{self.filename}: A coluna de nível 1 '{extra_column}' não é esperada.")

            # Check extra columns in level 2 (ignore 'id')
            _, extras_level_2 = extract_numeric_ids_and_unmatched_strings_from_list(
                source_list=colunas_nivel_2,
                strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
                suffixes_for_matching=self.scenarios_list,
            )
            for extra_column in extras_level_2:
                if not extra_column.lower().startswith("unnamed"):
                    self.structural_errors.append(f"{self.filename}: A coluna de nível 2 '{extra_column}' não é esperada.")

            # Check for missing expected columns in level 2
            for col in self.EXPECTED_COLUMNS:
                if col not in colunas_nivel_2:
                    self.structural_errors.append(f"{self.filename}: Coluna de nível 2 '{col}' esperada mas não foi encontrada.")

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def post_processing(self):
        pass

    def run(self):
        # Verificar se precisa do read_success também
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
