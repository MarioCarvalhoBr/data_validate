from typing import List, Dict, Any
import pandas as pd

from controller.context.general_context import GeneralContext
from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.processing.collections_processing import extract_numeric_ids_and_unmatched_strings_from_list  # Added


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

    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        self.EXPECTED_COLUMNS = list(self.RequiredColumn.ALL)

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:

        __, extras_columns = extract_numeric_ids_and_unmatched_strings_from_list(
            source_list=self.DF_COLUMNS,
            strings_to_ignore=[self.RequiredColumn.COLUMN_ID.name],
            suffixes_for_matching=self.list_scenarios
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

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()


if __name__ == '__main__':
    # Test the SpValues class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    sp_values = SpValue(data_model=data[SpValue.INFO["SP_NAME"]])
    print(sp_values)