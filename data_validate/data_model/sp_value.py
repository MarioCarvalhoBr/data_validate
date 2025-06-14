from pathlib import Path
from types import MappingProxyType
from typing import List, Dict, Any

from .sp_model_abc import SpModelABC
from controller.data_importer.api.facade import DataModelImporter, DataImporterFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.list_processing import extract_numeric_ids_and_unmatched_strings  # Added


class SpValue(SpModelABC):
    INFO = MappingProxyType({
        "SP_NAME": "valores",
        "SP_DESCRIPTION": "This spreadsheet must contain information about the values associated with specific IDs.",
    })
    REQUIRED_COLUMNS = MappingProxyType({
        "COLUMN_ID": "id",
    })

    OPTIONAL_COLUMNS = MappingProxyType({})

    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(self, data_model: DataModelImporter, **kwargs: Dict[str, Any]):
        super().__init__(data_model, **kwargs)

        # Vars
        self.structure_errors = []
        self.structure_warnings = []

        self.run()

    def pre_processing(self):
        self.EXPECTED_COLUMNS = list(self.REQUIRED_COLUMNS.values())

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:

        __, extras_columns = extract_numeric_ids_and_unmatched_strings(
            source_list=self.DF_COLUMNS,
            strings_to_ignore=[self.REQUIRED_COLUMNS["COLUMN_ID"]],
            scenario_suffixes_for_matching=self.LIST_SCENARIOS
        )

        for extra_column in extras_columns:
            if extra_column.lower().startswith("unnamed"):
                continue
            self.structure_errors.append(f"{self.FILENAME}: A coluna '{extra_column}' não é esperada.")
        for col in self.EXPECTED_COLUMNS:
            if col not in self.DF_COLUMNS:
                self.structure_errors.append(f"{self.FILENAME}: Coluna '{col}' esperada mas não foi encontrada.")

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