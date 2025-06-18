#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
from types import MappingProxyType
from typing import List, Dict, Any

from data_validate.common.utils.processing.list_processing import extract_numeric_ids_and_unmatched_strings  # Added
from data_validate.controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from .sp_model_abc import SpModelABC


class SpProportionality(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "proporcionalidades",
        "SP_DESCRIPTION": "This spreadsheet must contain information about proportionalities associated with specific IDs.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_ID": "id",
    })

    OPTIONAL_COLUMNS = MappingProxyType({})

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)

        self.run()

    def pre_processing(self):
        self.EXPECTED_COLUMNS = list(self.REQUIRED_COLUMNS.values())

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        if self.DATA_MODEL.header_type == "double":
            colunas_nivel_1 = self.DATA_MODEL.df_data.columns.get_level_values(0).unique().tolist()
            colunas_nivel_2 = self.DATA_MODEL.df_data.columns.get_level_values(1).unique().tolist()

            # Check extra columns in level 1 (do not ignore 'id')
            _, extras_level_1 = extract_numeric_ids_and_unmatched_strings(
                source_list=colunas_nivel_1,
                strings_to_ignore=[],  # Do not ignore 'id' here
                scenario_suffixes_for_matching=self.LIST_SCENARIOS
            )
            for extra_column in extras_level_1:
                if not extra_column.lower().startswith("unnamed"):
                    self.STRUCTURE_LIST_ERRORS.append(f"{self.FILENAME}: A coluna de nível 1 '{extra_column}' não é esperada.")

            # Check extra columns in level 2 (ignore 'id')
            _, extras_level_2 = extract_numeric_ids_and_unmatched_strings(
                source_list=colunas_nivel_2,
                strings_to_ignore=[self.REQUIRED_COLUMNS["COLUMN_ID"]],
                scenario_suffixes_for_matching=self.LIST_SCENARIOS
            )
            for extra_column in extras_level_2:
                if not extra_column.lower().startswith("unnamed"):
                    self.STRUCTURE_LIST_ERRORS.append(f"{self.FILENAME}: A coluna de nível 2 '{extra_column}' não é esperada.")

            # Check for missing expected columns in level 2
            for col in self.EXPECTED_COLUMNS:
                if col not in colunas_nivel_2:
                    self.STRUCTURE_LIST_ERRORS.append(f"{self.FILENAME}: Coluna de nível 2 '{col}' esperada mas não foi encontrada.")

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()


if __name__ == '__main__':
    # Test the SpValues class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all

    sp_values = SpValue(data_model=data[SpValue.INFO["SP_NAME"]])
    print(sp_values)