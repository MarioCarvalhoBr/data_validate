from typing import List, Dict, Any

import pandas as pd

from data_validate.controllers.context.general_context import GeneralContext
from data_validate.helpers.base.constant_base import ConstantBase
from data_validate.helpers.common.processing.collections_processing import (
    extract_numeric_ids_and_unmatched_strings_from_list,
)  # Added
from data_validate.helpers.tools.data_loader.api.facade import DataLoaderModel
from data_validate.models.sp_model_abc import SpModelABC


class SpValue(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "valores"
            self.SP_DESCRIPTION = "Planilha de valores"
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

        __, extras_columns = extract_numeric_ids_and_unmatched_strings_from_list(
            source_list=self.DF_COLUMNS,
            strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
            suffixes_for_matching=self.scenarios_list,
        )

        for extra_column in extras_columns:
            if extra_column.lower().startswith("unnamed"):
                continue
            self.structural_errors.append(f"{self.filename}: A coluna '{extra_column}' não é esperada.")
        for col in self.EXPECTED_COLUMNS:
            if col not in self.DF_COLUMNS:
                self.structural_errors.append(f"{self.filename}: Coluna '{col}' esperada mas não foi encontrada.")

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def post_processing(self):
        pass

    def run(self):
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.data_cleaning()
            self.expected_structure_columns()
