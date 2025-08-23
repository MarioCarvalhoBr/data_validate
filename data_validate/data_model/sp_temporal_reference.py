from typing import List, Dict, Any

import pandas as pd

from controller.context.general_context import GeneralContext
from data_validate.common.base.constant_base import ConstantBase
from .sp_model_abc import SpModelABC
from tools.data_loader.api.facade import DataLoaderModel, DataLoaderFacade
from data_validate.common.utils.validation.column_validation import check_column_names
from data_validate.common.utils.formatting.error_formatting import format_errors_and_warnings
from data_validate.common.utils.processing.data_cleaning import clean_dataframe_integers


class SpTemporalReference(SpModelABC):

    # CONSTANTS
    class INFO(ConstantBase):
        def __init__(self):
            super().__init__()

            self.SP_NAME = "referencia_temporal"
            self.SP_DESCRIPTION = "Planilha de referência temporal"
            self.SP_SCENARIO_NAME = "cenarios"
            self._finalize_initialization()

    CONSTANTS = INFO()
    # COLUMN SERIES
    class RequiredColumn:
        COLUMN_NAME = pd.Series(dtype="int64", name="nome")
        COLUMN_DESCRIPTION = pd.Series(dtype="str", name="descricao")
        COLUMN_SYMBOL = pd.Series(dtype="int64", name="simbolo")

        ALL = [
            COLUMN_NAME.name,
            COLUMN_DESCRIPTION.name,
            COLUMN_SYMBOL.name
        ]
    def __init__(self, context: GeneralContext, data_model: DataLoaderModel, **kwargs: Dict[str, Any]):
        super().__init__(context, data_model, **kwargs)

        self.run()

    def pre_processing(self):
        pass

    def expected_structure_columns(self, *args, **kwargs) -> None:
        # Check missing columns expected columns and extra columns
        missing_columns, extra_columns = check_column_names(self.data_loader_model.df_data, list(self.RequiredColumn.ALL))
        col_errors, col_warnings = format_errors_and_warnings(self.filename, missing_columns, extra_columns)

        self.structural_errors.extend(col_errors)
        self.structural_warnings.extend(col_warnings)

    def data_cleaning(self, *args, **kwargs) -> List[str]:
        # Verify if the scenario file exists: Verifica se self.LIST_SCENARIOS: está vazio
        if (not self.scenarios_list) and (len(self.data_loader_model.df_data) != 1):
            self.data_cleaning_errors.append(f"{self.filename}: A tabela deve ter apenas um valor porque o arquivo '{self.CONSTANTS.SP_SCENARIO_NAME}' não existe ou está vazio.")

            if self.RequiredColumn.COLUMN_SYMBOL.name in self.data_loader_model.df_data.columns:
                self.RequiredColumn.COLUMN_SYMBOL = self.data_loader_model.df_data[self.RequiredColumn.COLUMN_SYMBOL.name].iloc[0:1]
        else:
            # 1. Limpar e validar a coluna 'codigo' (mínimo 1)
            col_symbol = self.RequiredColumn.COLUMN_SYMBOL.name

            df, errors_symbol = clean_dataframe_integers(self.data_loader_model.df_data, self.filename, [col_symbol], min_value=0)
            self.data_cleaning_errors.extend(errors_symbol)

            if self.RequiredColumn.COLUMN_SYMBOL.name in df.columns:
                self.RequiredColumn.COLUMN_SYMBOL = df[self.RequiredColumn.COLUMN_SYMBOL.name]

    def run(self):
        self.pre_processing()
        self.expected_structure_columns()
        self.data_cleaning()

if __name__ == '__main__':
    # Test the SpTemporalReference class
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataLoaderFacade(input_dir)
    data = importer.load_all

    sp_temporal_reference = SpTemporalReference(data_model=data[SpTemporalReference.INFO["SP_NAME"]])
    print(sp_temporal_reference)