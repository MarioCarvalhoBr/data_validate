from types import MappingProxyType
from typing import List, Dict, Any
import pandas as pd

from common.base.constant_base import ConstantBase
from controller.context.general_context import GeneralContext
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings

class SpScenario(SpModelABC):
    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()
            self.SP_NAME = "cenarios"
            self.SP_DESCRIPTION = "Planilha de cenarios"

            self._finalize_initialization()
    CONSTANTS = INFO()

    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_NAME = pd.Series(dtype="int64", name='nome')
        COLUMN_DESCRIPTION = pd.Series(dtype="str", name='descricao')
        COLUMN_SYMBOL = pd.Series(dtype="int64", name='simbolo')

        ALL = [
            COLUMN_NAME.name,
            COLUMN_DESCRIPTION.name,
            COLUMN_SYMBOL.name
        ]

    OPTIONAL_COLUMNS = MappingProxyType({})

    COLUMNS_PLURAL = MappingProxyType({})

    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        if self.scenario_exists_file and not self.scenarios_list:
            self.structural_errors.extend([f"{self.filename}: Arquivo de cenários com configuração incorreta. Consulte a especificação do modelo de dados."])

        # Valores repetidos na coluna 'simbolo'
        if self.RequiredColumn.COLUMN_SYMBOL.name in self.data_loader_model.df_data.columns:
            duplicated_symbols = self.data_loader_model.df_data[self.RequiredColumn.COLUMN_SYMBOL.name].duplicated(keep=False)
            if duplicated_symbols.any():
                duplicated_values = self.data_loader_model.df_data[duplicated_symbols][self.RequiredColumn.COLUMN_SYMBOL.name].unique()
                self.structural_errors.append(f"{self.filename}: Valores duplicados encontrados na coluna '{self.RequiredColumn.COLUMN_SYMBOL.name}': [{', '.join(map(str, duplicated_values))}]")

    def expected_structure_columns(self, *args, **kwargs) -> List[str]:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data,
                                                            list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        pass

    def run(self):

        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()


if __name__ == '__main__':
    # Test the SpScenario class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    sp_scenario = SpScenario(data_model=data[SpScenario.INFO["SP_NAME"]])
    print(sp_scenario)